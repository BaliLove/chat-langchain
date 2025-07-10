"""Load html from files, clean up, split, ingest into Weaviate."""
import logging
import os
import re
from typing import Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Use the modern pinecone package (not pinecone-client)
from pinecone import Pinecone

from bs4 import BeautifulSoup, SoupStrainer
from langchain.document_loaders import RecursiveUrlLoader, SitemapLoader
from langchain.indexes import SQLRecordManager, index
from langchain.utils.html import PREFIXES_TO_IGNORE_REGEX, SUFFIXES_TO_IGNORE_REGEX
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore

from backend.constants import WEAVIATE_DOCS_INDEX_NAME
from backend.embeddings import get_embeddings_model
from backend.parser import langchain_docs_extractor

# NEW: Import Bubble.io loader
try:
    from backend.bubble_loader import load_bubble_data
    BUBBLE_AVAILABLE = True
    logging.info("Bubble.io loader imported successfully")
except ImportError as e:
    BUBBLE_AVAILABLE = False
    logging.warning(f"Bubble.io loader not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def metadata_extractor(
    meta: dict, soup: BeautifulSoup, title_suffix: Optional[str] = None
) -> dict:
    title_element = soup.find("title")
    description_element = soup.find("meta", attrs={"name": "description"})
    html_element = soup.find("html")
    title = title_element.get_text() if title_element else ""
    if title_suffix is not None:
        title += title_suffix

    return {
        "source": meta["loc"],
        "title": title,
        "description": description_element.get("content", "")
        if description_element
        else "",
        "language": html_element.get("lang", "") if html_element else "",
        **meta,
    }


def load_langchain_docs():
    return SitemapLoader(
        "https://python.langchain.com/sitemap.xml",
        filter_urls=["https://python.langchain.com/"],
        parsing_function=langchain_docs_extractor,
        default_parser="lxml",
        bs_kwargs={
            "parse_only": SoupStrainer(
                name=("article", "title", "html", "lang", "content")
            ),
        },
        meta_function=metadata_extractor,
    ).load()


def load_langgraph_docs():
    return SitemapLoader(
        "https://langchain-ai.github.io/langgraph/sitemap.xml",
        parsing_function=simple_extractor,
        default_parser="lxml",
        bs_kwargs={"parse_only": SoupStrainer(name=("article", "title"))},
        meta_function=lambda meta, soup: metadata_extractor(
            meta, soup, title_suffix=" | 🦜🕸️LangGraph"
        ),
    ).load()


def load_langsmith_docs():
    return RecursiveUrlLoader(
        url="https://docs.smith.langchain.com/",
        max_depth=8,
        extractor=simple_extractor,
        prevent_outside=True,
        use_async=True,
        timeout=600,
        # Drop trailing / to avoid duplicate pages.
        link_regex=(
            f"href=[\"']{PREFIXES_TO_IGNORE_REGEX}((?:{SUFFIXES_TO_IGNORE_REGEX}.)*?)"
            r"(?:[\#'\"]|\/[\#'\"])"
        ),
        check_response_status=True,
    ).load()


def simple_extractor(html: str | BeautifulSoup) -> str:
    if isinstance(html, str):
        soup = BeautifulSoup(html, "lxml")
    elif isinstance(html, BeautifulSoup):
        soup = html
    else:
        raise ValueError(
            "Input should be either BeautifulSoup object or an HTML string"
        )
    return re.sub(r"\n\n+", "\n\n", soup.text).strip()


def load_api_docs():
    return RecursiveUrlLoader(
        url="https://api.python.langchain.com/en/latest/",
        max_depth=8,
        extractor=simple_extractor,
        prevent_outside=True,
        use_async=True,
        timeout=600,
        # Drop trailing / to avoid duplicate pages.
        link_regex=(
            f"href=[\"']{PREFIXES_TO_IGNORE_REGEX}((?:{SUFFIXES_TO_IGNORE_REGEX}.)*?)"
            r"(?:[\#'\"]|\/[\#'\"])"
        ),
        check_response_status=True,
        exclude_dirs=(
            "https://api.python.langchain.com/en/latest/_sources",
            "https://api.python.langchain.com/en/latest/_modules",
        ),
    ).load()


def ingest_docs():
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
    embedding = get_embeddings_model()

    # Use modern Pinecone API
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    vectorstore = PineconeVectorStore(index=index, embedding=embedding)

    record_manager = SQLRecordManager(
        f"pinecone/{PINECONE_INDEX_NAME}", db_url=RECORD_MANAGER_DB_URL
    )
    record_manager.create_schema()

    # Load from existing sources
    docs_from_documentation = load_langchain_docs()
    logger.info(f"Loaded {len(docs_from_documentation)} docs from documentation")
    docs_from_api = load_api_docs()
    logger.info(f"Loaded {len(docs_from_api)} docs from API")
    docs_from_langsmith = load_langsmith_docs()
    logger.info(f"Loaded {len(docs_from_langsmith)} docs from LangSmith")
    docs_from_langgraph = load_langgraph_docs()
    logger.info(f"Loaded {len(docs_from_langgraph)} docs from LangGraph")

    # NEW: Load from Bubble.io
    docs_from_bubble = []
    if BUBBLE_AVAILABLE:
        try:
            docs_from_bubble = load_bubble_data()
            logger.info(f"Loaded {len(docs_from_bubble)} docs from Bubble.io")
        except Exception as e:
            logger.error(f"Failed to load Bubble.io data: {e}")
            docs_from_bubble = []  # Continue with other sources
    else:
        logger.info("Bubble.io loader not available, skipping Bubble.io data")

    # Combine all sources
    all_docs = (
        docs_from_documentation
        + docs_from_api
        + docs_from_langsmith
        + docs_from_langgraph
        + docs_from_bubble  # NEW: Include Bubble.io data
    )

    docs_transformed = text_splitter.split_documents(all_docs)
    docs_transformed = [
        doc for doc in docs_transformed if len(doc.page_content) > 10
    ]

    for doc in docs_transformed:
        if "source" not in doc.metadata:
            doc.metadata["source"] = ""
        if "title" not in doc.metadata:
            doc.metadata["title"] = ""

    indexing_stats = index(
        docs_transformed,
        record_manager,
        vectorstore,
        cleanup="full",
        source_id_key="source",
        force_update=(os.environ.get("FORCE_UPDATE") or "false").lower() == "true",
    )

    logger.info(f"Indexing stats: {indexing_stats}")
    
    # Enhanced logging for Bubble.io integration
    total_docs = len(docs_transformed)
    bubble_docs = len([doc for doc in docs_transformed 
                      if doc.metadata.get("source_system") == "bubble.io"])
    
    if bubble_docs > 0:
        logger.info(f"Successfully integrated {bubble_docs} Bubble.io documents "
                   f"out of {total_docs} total documents ({bubble_docs/total_docs*100:.1f}%)")
    
    # Pinecone does not have the same aggregate API as Weaviate, so you may want to log differently here.
    logger.info(
        f"LangChain ingestion to Pinecone index '{PINECONE_INDEX_NAME}' complete."
    )


if __name__ == "__main__":
    ingest_docs()
