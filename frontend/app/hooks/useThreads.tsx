"use client";

import { useEffect, useState } from "react";

import { Client, Thread } from "@langchain/langgraph-sdk";
import { useToast } from "./use-toast";
import { useQueryState } from "nuqs";

export const createClient = () => {
  // Always use the API proxy for authentication
  // Use full URL instead of relative path
  const apiUrl = typeof window !== "undefined" 
    ? `${window.location.origin}/api`
    : "http://localhost:3000/api";
  
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
      console.log("[DEBUG] Creating thread for user:", id);
      thread = await client.threads.create({
        metadata: {
          user_id: id,
        },
      });
      console.log("[DEBUG] Thread created:", {
        thread_id: thread?.thread_id,
        metadata: thread?.metadata,
      });
      if (!thread || !thread.thread_id) {
        throw new Error("Thread creation failed.");
      }
      setThreadId(thread.thread_id);
      // Refresh the thread list after creating a new thread
      await getUserThreads(id);
    } catch (e) {
      console.error("Error creating thread", e);
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

      console.log("[DEBUG] Fetching threads for user:", id);

      const userThreads = (await client.threads.search({
        metadata: {
          user_id: id,
        },
        limit: 100,
      })) as Awaited<Thread[]>;

      console.log("[DEBUG] Raw threads fetched:", userThreads.length);
      console.log("[DEBUG] Thread details:", userThreads.map(t => ({
        id: t.thread_id,
        hasValues: !!t.values,
        valuesCount: t.values ? Object.keys(t.values).length : 0,
        metadata: t.metadata
      })));

      if (userThreads.length > 0) {
        const lastInArray = userThreads[0];
        const allButLast = userThreads.slice(1, userThreads.length);
        const filteredThreads = allButLast.filter(
          (thread) => thread.values && Object.keys(thread.values).length > 0,
        );
        console.log("[DEBUG] Filtered threads (excluding last):", filteredThreads.length);
        console.log("[DEBUG] Final thread list length:", [...filteredThreads, lastInArray].length);
        setUserThreads([...filteredThreads, lastInArray]);
      } else {
        console.log("[DEBUG] No threads found for user");
        setUserThreads([]);
      }
    } catch (error) {
      console.error("[DEBUG] Error fetching threads:", error);
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
