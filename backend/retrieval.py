import os
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
    yield store.as_retriever(search_kwargs=search_kwargs)


@contextmanager
def make_retriever(
    config: RunnableConfig,
) -> Iterator[BaseRetriever]:
    """Create a retriever for the agent, based on the current configuration."""
    configuration = BaseConfiguration.from_runnable_config(config)
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
