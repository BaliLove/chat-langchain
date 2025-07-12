/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    // Organization restrictions
    NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS: process.env.NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS || 'bali.love',
    
    // LangGraph API URL (this should be your deployed LangGraph endpoint)
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    
    // Server-side only (no NEXT_PUBLIC prefix)
    API_BASE_URL: process.env.API_BASE_URL,
    LANGSMITH_API_KEY: process.env.LANGSMITH_API_KEY,
    
    // LangSmith (optional)
    LANGCHAIN_TRACING_V2: process.env.LANGCHAIN_TRACING_V2,
    LANGCHAIN_ENDPOINT: process.env.LANGCHAIN_ENDPOINT,
    LANGCHAIN_PROJECT: process.env.LANGCHAIN_PROJECT,
  },
};

module.exports = nextConfig;
