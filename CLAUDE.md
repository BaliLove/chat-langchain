# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chat LangChain is a production RAG (Retrieval-Augmented Generation) chatbot for answering questions about LangChain documentation. It consists of a Python backend using LangGraph and a Next.js/React frontend.

## Essential Commands

### Backend Development
```bash
# Install dependencies
poetry install

# Format code (run both)
poetry run ruff format .
poetry run ruff --select I --fix .

# Lint code
poetry run ruff .

# Run the graph locally (requires LangGraph license)
langgraph up

# Test the graph
langgraph test
```

### Frontend Development
```bash
cd frontend

# Install dependencies
yarn

# Development server
yarn dev

# Build
yarn build

# Lint
yarn lint
```

## Architecture Overview

### Backend Structure
- **LangGraph-based**: Uses LangGraph for stateful conversation orchestration
- **Main Graph**: `backend/retrieval_graph/graph.py` - Entry point for query processing
- **Research Graph**: `backend/retrieval_graph/researcher_graph/` - Handles complex multi-step queries
- **Ingestion Pipeline**: `backend/ingest.py` - Processes and indexes documentation
- **Vector Store**: Weaviate or Pinecone for document embeddings
- **Record Manager**: PostgreSQL via Supabase for deduplication

### Frontend Structure
- **Next.js App Router**: Located in `frontend/app/`
- **Main Chat Interface**: `frontend/app/components/ChatLangChain.tsx`
- **API Routes**: `frontend/app/api/` - Proxies to LangGraph Cloud
- **UI Components**: Custom components in `frontend/app/components/ui/`
- **Authentication**: Supabase Auth via `frontend/app/contexts/AuthContext.tsx`

### Key Files
- **Backend Configuration**: `backend/configuration.py` - Model and service configs
- **Graph Prompts**: `backend/retrieval_graph/prompts.py` - System prompts
- **Frontend Types**: `frontend/app/types.ts` - TypeScript interfaces
- **API Integration**: `frontend/app/api/[..._path]/route.ts` - Dynamic API proxy

## Development Notes

1. **LangGraph Cloud Required**: The backend requires LangGraph Cloud deployment. Local development uses `langgraph up` but still needs cloud configuration.

2. **Environment Variables**: 
   - Backend: Set in `.env` or LangGraph Cloud dashboard
   - Frontend: Set in `frontend/.env.local`

3. **Testing Approach**:
   - Backend: Use `langgraph test` for graph testing
   - Frontend: Standard Next.js testing patterns
   - E2E Evaluations: `_scripts/evaluate_chains.py`

4. **Deployment**:
   - Frontend: Auto-deploys to Vercel on push
   - Backend: Deploy via LangGraph Cloud
   - Indexing: GitHub Actions on schedule or manual trigger

5. **When Making Changes**:
   - Always format with ruff before committing
   - Test graph changes with `langgraph test`
   - Update types in `frontend/app/types.ts` if changing API responses
   - Consider impact on streaming responses when modifying graph nodes