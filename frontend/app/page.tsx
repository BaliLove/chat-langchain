"use client";

import React from "react";
import { ChatLangChain } from "./components/ChatLangChain";
import ProtectedRoute from "./components/ProtectedRoute";

export default function Page(): React.ReactElement {
  return (
    <ProtectedRoute>
      <main className="w-full h-full flex flex-col">
        <React.Suspense fallback={null}>
          <ChatLangChain />
        </React.Suspense>
      </main>
    </ProtectedRoute>
  );
}
