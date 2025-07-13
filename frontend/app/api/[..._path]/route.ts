import { NextRequest, NextResponse } from "next/server";

export const runtime = "edge";

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY_BASE = 1000; // 1 second
const RETRYABLE_STATUS_CODES = [502, 503, 504, 429]; // Bad Gateway, Service Unavailable, Gateway Timeout, Too Many Requests

async function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function getCorsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "*",
  };
}

async function handleRequest(req: NextRequest, method: string) {
  try {
    const path = req.nextUrl.pathname.replace(/^\/?api\//, "");
    const url = new URL(req.url);
    const searchParams = new URLSearchParams(url.search);
    searchParams.delete("_path");
    searchParams.delete("nxtP_path");
    const queryString = searchParams.toString()
      ? `?${searchParams.toString()}`
      : "";

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    // Add API key for LangGraph authentication
    if (process.env.LANGSMITH_API_KEY) {
      headers["x-api-key"] = process.env.LANGSMITH_API_KEY;
    }

    const options: RequestInit = {
      method,
      headers,
    };

    if (["POST", "PUT", "PATCH"].includes(method)) {
      options.body = await req.text();
    }

    const targetUrl = `${process.env.API_BASE_URL}/${path}${queryString}`;
    console.log(`Proxying ${method} request to: ${targetUrl}`);
    
    // Implement retry logic
    let lastError: Error | null = null;
    let res: Response | null = null;
    
    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
      try {
        res = await fetch(targetUrl, options);
        
        // If successful or non-retryable status, break
        if (!RETRYABLE_STATUS_CODES.includes(res.status)) {
          break;
        }
        
        // Log retryable error
        console.warn(`Retryable status ${res.status} on attempt ${attempt + 1}/${MAX_RETRIES + 1}`);
        
      } catch (error) {
        lastError = error as Error;
        console.error(`Network error on attempt ${attempt + 1}/${MAX_RETRIES + 1}:`, error);
      }
      
      // If this wasn't the last attempt, wait before retrying
      if (attempt < MAX_RETRIES) {
        const delayMs = RETRY_DELAY_BASE * Math.pow(2, attempt) * (0.5 + Math.random() * 0.5); // Exponential backoff with jitter
        console.log(`Retrying in ${delayMs}ms...`);
        await delay(delayMs);
      }
    }
    
    // If we never got a response, throw the last error
    if (!res) {
      throw lastError || new Error("Failed to fetch after retries");
    }

    const responseHeaders = new Headers(res.headers);
    // Add CORS headers
    Object.entries(getCorsHeaders()).forEach(([key, value]) => {
      responseHeaders.set(key, value);
    });

    return new NextResponse(res.body, {
      status: res.status,
      statusText: res.statusText,
      headers: responseHeaders,
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: e.status ?? 500 });
  }
}

export const GET = (req: NextRequest) => handleRequest(req, "GET");
export const POST = (req: NextRequest) => handleRequest(req, "POST");
export const PUT = (req: NextRequest) => handleRequest(req, "PUT");
export const PATCH = (req: NextRequest) => handleRequest(req, "PATCH");
export const DELETE = (req: NextRequest) => handleRequest(req, "DELETE");

// Add a new OPTIONS handler
export const OPTIONS = () => {
  return new NextResponse(null, {
    status: 204,
    headers: {
      ...getCorsHeaders(),
    },
  });
};
