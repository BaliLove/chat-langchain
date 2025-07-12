"use client";

import React from "react";
import { GraphProvider } from "./contexts/GraphContext";
import { ChatLangChain } from "./components/ChatLangChain";
import ProtectedRoute from "./components/ProtectedRoute";

export default function Page(): React.ReactElement {
  return (
    <ProtectedRoute>
      <main className="w-full h-full">
        <React.Suspense fallback={null}>
          <GraphProvider>
            <ChatLangChain />
          </GraphProvider>
        </React.Suspense>
      </main>
    </ProtectedRoute>
  );
}
