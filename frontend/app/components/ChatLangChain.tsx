"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  AppendMessage,
  AssistantRuntimeProvider,
  useExternalStoreRuntime,
} from "@assistant-ui/react";
import { v4 as uuidv4 } from "uuid";
import { useExternalMessageConverter } from "@assistant-ui/react";
import { BaseMessage, HumanMessage } from "@langchain/core/messages";
import { useToast } from "../hooks/use-toast";
import {
  convertToOpenAIFormat,
  convertLangchainMessages,
} from "../utils/convert_messages";
import { ThreadChat } from "./chat-interface";
import { ThreadHistory } from "./thread-history";
import { Toaster } from "./ui/toaster";
import { useGraphContext } from "../contexts/GraphContext";
import { useQueryState } from "nuqs";
import { usePermissions } from "../hooks/usePermissions";
import { useSearchParams } from "next/navigation";
import { Badge } from "./ui/badge";

// Add this debug component near the top of the file
const DebugInfo = () => {
  if (process.env.NODE_ENV === 'production') {
    return null; // Hide in production
  }
  
  return (
    <div className="fixed top-2 right-2 bg-card text-card-foreground text-xs p-2 rounded border z-50">
      <div>API_URL: {process.env.NEXT_PUBLIC_API_URL || 'NOT SET'}</div>
      <div>ENV: {process.env.NODE_ENV}</div>
    </div>
  );
};

function ChatLangChainComponent(): React.ReactElement {
  const { toast } = useToast();
  const { threadsData, userData, graphData } = useGraphContext();
  const { userId } = userData;
  const { getUserThreads, createThread, getThreadById } = threadsData;
  const { messages, setMessages, streamMessage, switchSelectedThread } =
    graphData;
  const [isRunning, setIsRunning] = useState(false);
  const [threadId, setThreadId] = useQueryState("threadId");
  const { permissions, loading: permissionsLoading, hasAgent } = usePermissions();
  const searchParams = useSearchParams();
  const [activePrompt, setActivePrompt] = useState<{ id: string; name: string } | null>(null);
  const [promptInitialized, setPromptInitialized] = useState(false);

  const hasCheckedThreadIdParam = useRef(false);
  useEffect(() => {
    if (typeof window === "undefined" || hasCheckedThreadIdParam.current)
      return;
    if (!threadId) {
      hasCheckedThreadIdParam.current = true;
      return;
    }

    hasCheckedThreadIdParam.current = true;

    try {
      getThreadById(threadId).then((thread) => {
        if (!thread) {
          setThreadId(null);
          return;
        }

        switchSelectedThread(thread);
      });
    } catch (e) {
      console.error("Failed to fetch thread in query param", e);
      setThreadId(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [threadId]);

  // Handle prompt parameter from URL
  useEffect(() => {
    const promptId = searchParams.get('prompt');
    if (process.env.NODE_ENV === 'development') {
      console.log('Prompt ID from URL:', promptId);
      console.log('Prompt initialized:', promptInitialized);
      console.log('Permissions loading:', permissionsLoading);
    }
    
    if (promptId && !promptInitialized && !permissionsLoading) {
      if (process.env.NODE_ENV === 'development') {
        console.log('Fetching prompt details for:', promptId);
      }
      // Fetch prompt details
      fetch(`/api/prompts/${promptId}`)
        .then(res => res.json())
        .then(data => {
          if (process.env.NODE_ENV === 'development') {
            console.log('Prompt data received:', data);
          }
          if (data.success && data.prompt) {
            if (process.env.NODE_ENV === 'development') {
              console.log('Setting active prompt:', data.prompt.name);
            }
            setActivePrompt({ id: promptId, name: data.prompt.name });
            setPromptInitialized(true);
          }
        })
        .catch(err => {
          console.error('Failed to load prompt:', err);
          toast({
            title: "Failed to load prompt",
            description: "The selected prompt could not be loaded.",
            variant: "destructive"
          });
        });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, promptInitialized, permissionsLoading]);

  // Auto-start conversation for issue review prompt
  useEffect(() => {
    if (activePrompt && 
        activePrompt.id === 'bali-love-issue-review' && 
        messages.length === 0 && 
        !isRunning &&
        userId &&
        !permissionsLoading) {
      const initialMessage: AppendMessage = {
        parentId: null,
        role: "user",
        content: [{ type: "text", text: "I'd like to review issues by category" }],
      };
      
      // Small delay to ensure everything is ready
      const timer = setTimeout(() => {
        onNew(initialMessage);
      }, 100);
      
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePrompt, messages.length, isRunning, userId, permissionsLoading]);

  const isSubmitDisabled = !userId || permissionsLoading || !permissions?.canCreateThreads;

  async function onNew(message: AppendMessage): Promise<void> {
    if (isSubmitDisabled) {
      toast({
        title: "Failed to send message",
        description: !userId 
          ? "Unable to find user ID. Please try again later." 
          : !permissions?.canCreateThreads 
          ? "You don't have permission to create new threads."
          : "Please wait while we load your permissions.",
      });
      return;
    }
    
    // Check if user has access to the chat agent
    if (!hasAgent('chat')) {
      toast({
        title: "Access Denied",
        description: "You don't have access to the chat agent.",
        variant: "destructive"
      });
      return;
    }
    if (message.content[0]?.type !== "text") {
      throw new Error("Only text messages are supported");
    }

    setIsRunning(true);

    let currentThreadId = threadId;
    if (!currentThreadId) {
      const thread = await createThread(userId);
      if (!thread) {
        toast({
          title: "Error",
          description: "Thread creation failed.",
        });
        return;
      }
      setThreadId(thread.thread_id);
      currentThreadId = thread.thread_id;
    }

    try {
      const humanMessage = new HumanMessage({
        content: message.content[0].text,
        id: uuidv4(),
      });

      setMessages((prevMessages) => [...prevMessages, humanMessage]);

      await streamMessage(currentThreadId, {
        messages: [convertToOpenAIFormat(humanMessage)],
        ...(activePrompt ? { promptId: activePrompt.id } : {})
      });
    } finally {
      setIsRunning(false);
      // Re-fetch threads so that the current thread's title is updated.
      await getUserThreads(userId);
    }
  }

  const threadMessages = useExternalMessageConverter<BaseMessage>({
    callback: convertLangchainMessages,
    messages: messages,
    isRunning,
  });

  const runtime = useExternalStoreRuntime({
    messages: threadMessages,
    isRunning,
    onNew,
  });

  // Debug log for active prompt
  if (process.env.NODE_ENV === 'development') {
    console.log('Render - activePrompt:', activePrompt);
  }
  
  return (
    <div className="h-full w-full flex md:flex-row flex-col relative">
      <DebugInfo />
      {activePrompt && (
        <div className="absolute top-4 right-4 z-10">
          <Badge variant="secondary" className="px-3 py-1">
            <span className="text-xs font-medium">Active: {activePrompt.name}</span>
          </Badge>
        </div>
      )}
      <div>
        <ThreadHistory />
      </div>
      <div className="flex-1 overflow-hidden">
        <AssistantRuntimeProvider runtime={runtime}>
          <ThreadChat submitDisabled={isSubmitDisabled} messages={messages} />
        </AssistantRuntimeProvider>
      </div>
      <Toaster />
    </div>
  );
}

export const ChatLangChain = React.memo(ChatLangChainComponent);
