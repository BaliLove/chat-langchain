import { NextRequest, NextResponse } from "next/server";

export const runtime = "edge";

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
    
    const res = await fetch(targetUrl, options);

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
