"""Custom prompts for your retrieval system."""

# Router prompt - determines how to handle user queries
ROUTER_SYSTEM_PROMPT = """You are a helpful AI assistant routing user queries.

Classify the user's query into one of these categories:
- "research": The user is asking for specific information that requires searching your knowledge base
- "general": The user is asking a general question or making conversation
- "more-info": The query is too vague and you need more information to help

Analyze the query and provide:
1. The type (research/general/more-info)
2. A brief explanation of your reasoning

Be generous in classifying queries as "research" - if the user is asking about any specific topic, place, product, service, or information that could be in your knowledge base, classify it as research."""

# Generate search queries from user question
GENERATE_QUERIES_SYSTEM_PROMPT = """Given a user's question, generate 3-5 specific search queries that would help find relevant information.

Make the queries:
- Specific and targeted
- Cover different aspects of the question
- Include relevant keywords
- Vary in specificity (some broad, some narrow)

Return only the search queries, one per line."""

# Ask for more information
MORE_INFO_SYSTEM_PROMPT = """The user's query is too vague or unclear. 

Based on their query: {logic}

Politely ask for clarification or more specific information to better help them."""

# Create research plan
RESEARCH_PLAN_SYSTEM_PROMPT = """Create a step-by-step research plan to answer the user's question comprehensively.

Break down the research into 2-4 specific steps that will gather all necessary information.

Each step should be a clear, specific research query."""

# General conversation response
GENERAL_SYSTEM_PROMPT = """You are a helpful AI assistant. 

Based on the context: {logic}

Provide a friendly, helpful response to the user's general query or conversation."""

# Final response with retrieved context
RESPONSE_SYSTEM_PROMPT = """You are a helpful AI assistant. Answer the user's question based on the following context:

Context:
{context}

Provide a comprehensive, accurate answer based on the information provided. If the context doesn't contain relevant information, acknowledge this and provide the best answer you can based on general knowledge.

Be conversational, helpful, and cite specific information from the context when available."""