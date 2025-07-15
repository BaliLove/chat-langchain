import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  return NextResponse.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    env: {
      hasSupabaseUrl: !!process.env.NEXT_PUBLIC_SUPABASE_URL,
      hasSupabaseKey: !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
      hasApiBaseUrl: !!process.env.API_BASE_URL,
      hasLangsmithKey: !!process.env.LANGSMITH_API_KEY,
      apiBaseUrl: process.env.API_BASE_URL
    }
  });
}