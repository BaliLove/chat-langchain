import os
import logging
from contextlib import contextmanager
from typing import Iterator

# Use the modern pinecone package (not pinecone-client)
from pinecone import Pinecone

from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnableConfig
from langchain_pinecone import PineconeVectorStore

from backend.configuration import BaseConfiguration
from backend.constants import WEAVIATE_DOCS_INDEX_NAME

# Set up logging
logger = logging.getLogger(__name__)


def make_text_encoder(model: str) -> Embeddings:
    """Connect to the configured text encoder."""
    provider, model = model.split("/", maxsplit=1)
    match provider:
        case "openai":
            from langchain_openai import OpenAIEmbeddings
            # Use 1024 dimensions to match Pinecone index
            # text-embedding-3-small supports dimension reduction
            return OpenAIEmbeddings(model=model, dimensions=1024)
        case _:
            raise ValueError(f"Unsupported embedding provider: {provider}")


@contextmanager
def make_pinecone_retriever(
    configuration: BaseConfiguration, embedding_model: Embeddings
) -> Iterator[BaseRetriever]:
    # Initialize Pinecone with the modern API
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index = pc.Index(os.environ["PINECONE_INDEX_NAME"])
    
    # Use the modern constructor style for langchain-pinecone
    store = PineconeVectorStore(index=index, embedding=embedding_model)
    search_kwargs = {**configuration.search_kwargs}
    
    # Log the search_kwargs to debug filtering
    logger.info(f"Creating Pinecone retriever with search_kwargs: {search_kwargs}")
    
    # Create the retriever
    retriever = store.as_retriever(search_kwargs=search_kwargs)
    
    # WORKAROUND: Due to a LangChain bug, we need to ensure search_kwargs are properly set
    # See: https://github.com/langchain-ai/langchain/issues/21492
    if search_kwargs:
        retriever.search_kwargs = search_kwargs
        logger.info(f"Applied workaround - set retriever.search_kwargs directly: {retriever.search_kwargs}")
    
    yield retriever


@contextmanager
def make_retriever(
    config: RunnableConfig,
) -> Iterator[BaseRetriever]:
    """Create a retriever for the agent, based on the current configuration."""
    # Log the incoming config to debug
    logger.info(f"make_retriever called with config: {config}")
    
    configuration = BaseConfiguration.from_runnable_config(config)
    
    # Log the parsed configuration
    logger.info(f"Parsed configuration - search_kwargs: {configuration.search_kwargs}")
    
    embedding_model = make_text_encoder(configuration.embedding_model)
    match configuration.retriever_provider:
        case "pinecone":
            with make_pinecone_retriever(configuration, embedding_model) as retriever:
                yield retriever
        case _:
            raise ValueError(
                "Unrecognized retriever_provider in configuration. "
                f"Expected one of: pinecone\n"
                f"Got: {configuration.retriever_provider}"
            )
