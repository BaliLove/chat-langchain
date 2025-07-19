"""Researcher graph used in the conversational retrieval system as a subgraph.

This module defines the core structure and functionality of the researcher graph,
which is responsible for generating search queries and retrieving relevant documents.
"""

from typing import cast
import logging

from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from backend import retrieval
from backend.retrieval_graph.configuration import AgentConfiguration
from backend.retrieval_graph.researcher_graph.state import QueryState, ResearcherState
from backend.utils import load_chat_model
from backend.permissions import permission_manager
from backend.retry_utils import with_retry, OPENAI_RETRY_CONFIG, RETRIEVAL_RETRY_CONFIG

# Set up logging
logger = logging.getLogger(__name__)


async def generate_queries(
    state: ResearcherState, *, config: RunnableConfig
) -> dict[str, list[str]]:
    """Generate search queries based on the question (a step in the research plan).

    This function uses a language model to generate diverse search queries to help answer the question.

    Args:
        state (ResearcherState): The current state of the researcher, including the user's question.
        config (RunnableConfig): Configuration with the model used to generate queries.

    Returns:
        dict[str, list[str]]: A dictionary with a 'queries' key containing the list of generated search queries.
    """
    try:
        class Response(TypedDict):
            queries: list[str]

        configuration = AgentConfiguration.from_runnable_config(config)
        structured_output_kwargs = (
            {"method": "function_calling"} if "openai" in configuration.query_model else {}
        )
        model = load_chat_model(configuration.query_model).with_structured_output(
            Response, **structured_output_kwargs
        )
        messages = [
            {"role": "system", "content": configuration.generate_queries_system_prompt},
            {"role": "human", "content": state.question},
        ]
        # Use retry logic for LLM call
        @with_retry(**OPENAI_RETRY_CONFIG)
        async def generate_with_retry():
            return await model.ainvoke(messages, {"tags": ["langsmith:nostream"]})
        
        response = cast(Response, await generate_with_retry())
        return {"queries": response["queries"]}
    except Exception as e:
        logger.error(f"Error in generate_queries: {str(e)}", exc_info=True)
        # Return a simple fallback query
        return {"queries": [state.question]}


async def retrieve_documents(
    state: QueryState, *, config: RunnableConfig
) -> dict[str, list[Document]]:
    """Retrieve documents based on a given query.

    This function uses a retriever to fetch relevant documents for a given query,
    then filters them based on user permissions.

    Args:
        state (QueryState): The current state containing the query string.
        config (RunnableConfig): Configuration with the retriever used to fetch documents.

    Returns:
        dict[str, list[Document]]: A dictionary with a 'documents' key containing the list of retrieved documents.
    """
    try:
        # Check if this is an issue category review query
        import re
        category_match = re.search(r'Category ID: ([0-9x]+)', state.query)
        all_issues_match = re.search(r'all issues across all categories', state.query.lower())
        
        # Create a modified config with appropriate filters for issue category queries
        modified_config = config.copy() if config else {}
        
        if category_match:
            category_id = category_match.group(1)
            # Add filters for specific issue category queries
            search_kwargs = {
                "filter": {
                    "source_type": "issue",
                    "category": category_id
                },
                "k": 20
            }
            
            # Update the configuration to include the search filters
            if "configurable" not in modified_config:
                modified_config["configurable"] = {}
            modified_config["configurable"]["search_kwargs"] = search_kwargs
            
            logger.info(f"Applying issue category filter: source_type=issue, category={category_id}")
        elif all_issues_match:
            # Filter by source_type only for "all categories" queries
            search_kwargs = {
                "filter": {
                    "source_type": "issue"
                },
                "k": 50
            }
            
            # Update the configuration to include the search filters
            if "configurable" not in modified_config:
                modified_config["configurable"] = {}
            modified_config["configurable"]["search_kwargs"] = search_kwargs
            
            logger.info(f"Applying all issues filter: source_type=issue")
        
        with retrieval.make_retriever(modified_config) as retriever:
            # Retrieve documents with retry logic
            @with_retry(**RETRIEVAL_RETRY_CONFIG)
            async def retrieve_with_retry():
                # For issue category queries, we need to ensure the filter is applied
                # The retriever should already have the search_kwargs from the configuration
                return await retriever.ainvoke(state.query)
            
            documents = await retrieve_with_retry()
            
            # Log the retrieved documents for debugging
            if category_match or all_issues_match:
                logger.info(f"Retrieved {len(documents)} documents for issue query")
                if documents:
                    # Log the first few to check source_type
                    for i, doc in enumerate(documents[:3]):
                        logger.info(f"  Doc {i}: source_type={doc.metadata.get('source_type', 'N/A')}, "
                                  f"category={doc.metadata.get('category', 'N/A')}, "
                                  f"title={doc.metadata.get('title', 'N/A')[:50]}...")
            
            # Get user email from config (this should be passed from the main graph)
            user_email = config.get("configurable", {}).get("user_email", "")
            
            if user_email:
                try:
                    # Get user permissions
                    permissions = await permission_manager.get_user_permissions(user_email)
                    
                    # Filter documents based on permissions
                    filtered_docs = []
                    for doc in documents:
                        # Check document metadata for data source
                        metadata = doc.metadata or {}
                        doc_source = metadata.get("data_source", "public")
                        
                        # Check if user has access to this data source
                        if permissions.has_data_source(doc_source) or doc_source == "public":
                            filtered_docs.append(doc)
                    
                    return {"documents": filtered_docs}
                except Exception as e:
                    logger.error(f"Error filtering documents by permissions: {str(e)}", exc_info=True)
                    # If permission check fails, return unfiltered documents
                    return {"documents": documents}
            
            # If no user email, return all documents (backward compatibility)
            return {"documents": documents}
    except Exception as e:
        logger.error(f"Error in retrieve_documents: {str(e)}", exc_info=True)
        # Return empty documents list on error
        return {"documents": []}


def retrieve_in_parallel(state: ResearcherState) -> list[Send]:
    """Create parallel retrieval tasks for each generated query.

    This function prepares parallel document retrieval tasks for each query in the researcher's state.

    Args:
        state (ResearcherState): The current state of the researcher, including the generated queries.

    Returns:
        Literal["retrieve_documents"]: A list of Send objects, each representing a document retrieval task.

    Behavior:
        - Creates a Send object for each query in the state.
        - Each Send object targets the "retrieve_documents" node with the corresponding query.
    """
    return [
        Send("retrieve_documents", QueryState(query=query)) for query in state.queries
    ]


# Define the graph
builder = StateGraph(ResearcherState)
builder.add_node(generate_queries)
builder.add_node(retrieve_documents)
builder.add_edge(START, "generate_queries")
builder.add_conditional_edges(
    "generate_queries",
    retrieve_in_parallel,  # type: ignore
    path_map=["retrieve_documents"],
)
builder.add_edge("retrieve_documents", END)
# Compile into a graph object that you can invoke and deploy.
graph = builder.compile()
graph.name = "ResearcherGraph"
