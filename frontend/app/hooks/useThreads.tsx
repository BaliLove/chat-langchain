"use client";

import { useEffect, useState } from "react";

import { Client, Thread } from "@langchain/langgraph-sdk";
import { useToast } from "./use-toast";
import { useQueryState } from "nuqs";

export const getApiUrl = () => {
  // Always use the API proxy for authentication
  // Use full URL instead of relative path
  return typeof window !== "undefined" 
    ? `${window.location.origin}/api`
    : "http://localhost:3000/api";
};

export const createClient = () => {
  const apiUrl = getApiUrl();
  
  return new Client({
    apiUrl,
  });
};

export function useThreads(userId: string | undefined) {
  const { toast } = useToast();
  const [isUserThreadsLoading, setIsUserThreadsLoading] = useState(false);
  const [userThreads, setUserThreads] = useState<Thread[]>([]);
  const [threadId, setThreadId] = useQueryState("threadId");

  useEffect(() => {
    if (typeof window == "undefined" || !userId) return;
    getUserThreads(userId);
  }, [userId]);

  const createThread = async (id: string) => {
    const client = createClient();
    let thread;
    try {
      console.log("[THREAD DEBUG] Creating thread for user_id:", id);
      thread = await client.threads.create({
        metadata: {
          user_id: id,
        },
      });
      console.log("[THREAD DEBUG] Thread created successfully:", {
        thread_id: thread?.thread_id,
        metadata: thread?.metadata,
        created_at: thread?.created_at
      });
      
      if (!thread || !thread.thread_id) {
        throw new Error("Thread creation failed.");
      }
      setThreadId(thread.thread_id);
      // Refresh the thread list after creating a new thread
      await getUserThreads(id);
    } catch (e) {
      console.error("[THREAD DEBUG] Error creating thread:", e);
      toast({
        title: "Error creating thread.",
      });
    }
    return thread;
  };

  const getUserThreads = async (id: string) => {
    setIsUserThreadsLoading(true);
    try {
      const client = createClient();

      console.log("[THREAD DEBUG] Searching for threads with user_id:", id);
      console.log("[THREAD DEBUG] API URL being used:", getApiUrl());

      const userThreads = (await client.threads.search({
        metadata: {
          user_id: id,
        },
        limit: 100,
      })) as Awaited<Thread[]>;

      console.log("[THREAD DEBUG] Raw threads response:", userThreads.length, "threads found");
      console.log("[THREAD DEBUG] Thread details:", userThreads.map(t => ({
        id: t.thread_id,
        hasValues: !!t.values,
        valuesCount: t.values ? Object.keys(t.values).length : 0,
        metadata: t.metadata,
        created_at: t.created_at,
        updated_at: t.updated_at
      })));

      if (userThreads.length > 0) {
        const lastInArray = userThreads[0];
        const allButLast = userThreads.slice(1, userThreads.length);
        const filteredThreads = allButLast.filter(
          (thread) => thread.values && Object.keys(thread.values).length > 0,
        );
        console.log("[THREAD DEBUG] Filtered threads:", filteredThreads.length);
        console.log("[THREAD DEBUG] Final thread list:", [...filteredThreads, lastInArray].length);
        setUserThreads([...filteredThreads, lastInArray]);
      } else {
        console.log("[THREAD DEBUG] No threads found for user_id:", id);
        setUserThreads([]);
      }
    } catch (error) {
      console.error("[THREAD DEBUG] Error fetching threads:", error);
    } finally {
      setIsUserThreadsLoading(false);
    }
  };

  const getThreadById = async (id: string) => {
    const client = createClient();
    return (await client.threads.get(id)) as Awaited<Thread>;
  };

  const deleteThread = async (id: string, clearMessages: () => void) => {
    if (!userId) {
      throw new Error("User ID not found");
    }
    setUserThreads((prevThreads) => {
      const newThreads = prevThreads.filter(
        (thread) => thread.thread_id !== id,
      );
      return newThreads;
    });
    const client = createClient();
    await client.threads.delete(id);
    if (id === threadId) {
      // Remove the threadID from query params, and refetch threads to
      // update the sidebar UI.
      clearMessages();
      getUserThreads(userId);
      setThreadId(null);
    }
  };

  return {
    isUserThreadsLoading,
    userThreads,
    getThreadById,
    setUserThreads,
    getUserThreads,
    createThread,
    deleteThread,
  };
}
