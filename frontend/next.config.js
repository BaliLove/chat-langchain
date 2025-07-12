/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    // Supabase
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    
    // Organization restrictions
    NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS: process.env.NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS,
    
    // LangGraph
    NEXT_PUBLIC_LANGGRAPH_API_URL: process.env.NEXT_PUBLIC_LANGGRAPH_API_URL,
    NEXT_PUBLIC_LANGGRAPH_API_KEY: process.env.NEXT_PUBLIC_LANGGRAPH_API_KEY,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    
    // Server-side only (no NEXT_PUBLIC prefix)
    LANGGRAPH_API_KEY: process.env.LANGGRAPH_API_KEY,
    API_BASE_URL: process.env.API_BASE_URL,
    LANGSMITH_API_KEY: process.env.LANGSMITH_API_KEY,
    
    // LangSmith (optional)
    LANGCHAIN_TRACING_V2: process.env.LANGCHAIN_TRACING_V2,
    LANGCHAIN_ENDPOINT: process.env.LANGCHAIN_ENDPOINT,
    LANGCHAIN_PROJECT: process.env.LANGCHAIN_PROJECT,
  },
};

module.exports = nextConfig;
