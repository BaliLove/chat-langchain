"use client";

import React from "react";
import { ChatLangChain } from "./components/ChatLangChain";
import ProtectedRoute from "./components/ProtectedRoute";
import { ThreadDebugInfo } from "./components/ThreadDebugInfo";

export default function Page(): React.ReactElement {
  return (
    <ProtectedRoute>
      <main className="w-full h-full flex flex-col">
        <React.Suspense fallback={null}>
          <ChatLangChain />
        </React.Suspense>
        <ThreadDebugInfo />
      </main>
    </ProtectedRoute>
  );
}
