/* eslint-disable react/no-unescaped-entities */
"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import { useChat } from "ai/react";
import { type Message, type ToolInvocation } from "ai";
import { ToolResult as ToolResultView } from "@/components/tools/ToolResult";

interface ExtendedMessage extends Message {
  content: string;
  parts?: MessagePart[];
}

interface TextPart {
  type: "text";
  text: string;
}

interface ToolInvocationPart {
  type: "tool-invocation";
  toolInvocation: ToolInvocation;
}

type MessagePart = TextPart | ToolInvocationPart;

export default function Home() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } =
    useChat({
      api: "/api/py/chat",
      id: "genetics-chat",
      onError: (error: Error) => {
        console.error("Chat error:", error);
      },
      onResponse: (response: Response) => {
        console.log("Raw response:", response);
        // Log headers to understand streaming configuration
        console.log(
          "Response headers:",
          Object.fromEntries(response.headers.entries())
        );
      },
    });

  // Enhanced debug logging
  console.log(
    "Current messages state:",
    messages.map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      parts: (m as ExtendedMessage).parts,
    }))
  );

  // Create a helper function for the example button clicks
  const handleExampleClick = (text: string) => {
    handleInputChange({
      target: { value: text },
    } as React.ChangeEvent<HTMLInputElement>);
    handleSubmit({
      preventDefault: () => {},
    } as React.FormEvent);
  };

  const parseMessageContent = (content: string): MessagePart[] => {
    console.log("Parsing message content:", content);
    try {
      // Try to parse the entire content as JSON first
      const parsed = JSON.parse(content);
      console.log("Successfully parsed complete JSON:", parsed);
      if (parsed.type === "tool-invocation") {
        return [parsed];
      }
    } catch (e) {
      console.log("Not a complete JSON object, trying to parse parts");
    }

    const parts = content
      .split(/(\{(?:[^{}]|(?:\{[^{}]*\}))*\})/g)
      .filter(Boolean);
    console.log("Split content into parts:", parts);

    return parts.map((part, index) => {
      try {
        const parsed = JSON.parse(part);
        console.log(`Successfully parsed part ${index}:`, parsed);
        if (parsed.type === "tool-invocation") {
          return parsed as ToolInvocationPart;
        }
      } catch (e) {
        console.log(`Part ${index} is not JSON, treating as text:`, part);
      }
      return { type: "text", text: part } as TextPart;
    });
  };

  const renderMessage = (message: ExtendedMessage) => {
    console.log("Rendering message:", {
      id: message.id,
      role: message.role,
      content: message.content,
      parts: message.parts,
    });

    // If the message has parts, use those directly
    const parts = message.parts || parseMessageContent(message.content);
    console.log("Processed message parts:", parts);

    return (
      <div
        className={`group flex items-start gap-3 ${
          message.role === "user" ? "justify-end" : ""
        }`}
      >
        {message.role !== "user" && (
          <Avatar className="flex-none mt-0.5">
            <AvatarFallback>AI</AvatarFallback>
          </Avatar>
        )}
        <div
          className={`flex-1 max-w-3xl overflow-hidden ${
            message.role === "user" ? "text-right" : ""
          }`}
        >
          <div
            className={`inline-block px-3 py-2 rounded-lg ${
              message.role === "user"
                ? "bg-primary text-primary-foreground"
                : "bg-muted"
            }`}
          >
            {message.role === "user" ? (
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="space-y-4">
                {parts.map((part, index) => {
                  if (part.type === "text") {
                    return (
                      <ReactMarkdown
                        key={index}
                        remarkPlugins={[remarkGfm]}
                        className="text-left"
                        components={
                          {
                            a: ({
                              node,
                              ...props
                            }: {
                              node?: any;
                            } & React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
                              <a
                                {...props}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline"
                              />
                            ),
                            p: ({
                              node,
                              ...props
                            }: {
                              node?: any;
                            } & React.HTMLAttributes<HTMLParagraphElement>) => (
                              <p {...props} className="mt-2 first:mt-0" />
                            ),
                            ul: ({
                              node,
                              ...props
                            }: {
                              node?: any;
                            } & React.HTMLAttributes<HTMLUListElement>) => (
                              <ul {...props} className="list-disc pl-4 mt-2" />
                            ),
                            ol: ({
                              node,
                              ...props
                            }: {
                              node?: any;
                            } & React.HTMLAttributes<HTMLOListElement>) => (
                              <ol
                                {...props}
                                className="list-decimal pl-4 mt-2"
                              />
                            ),
                            li: ({
                              node,
                              ...props
                            }: {
                              node?: any;
                            } & React.HTMLAttributes<HTMLLIElement>) => (
                              <li {...props} className="mt-1" />
                            ),
                            code: ({
                              node,
                              inline,
                              ...props
                            }: {
                              node?: any;
                              inline?: boolean;
                            } & React.HTMLAttributes<HTMLElement>) =>
                              inline ? (
                                <code
                                  {...props}
                                  className="px-1 py-0.5 bg-gray-200 dark:bg-gray-800 rounded text-sm"
                                />
                              ) : (
                                <code
                                  {...props}
                                  className="block bg-gray-200 dark:bg-gray-800 p-2 rounded text-sm overflow-x-auto"
                                />
                              ),
                          } as Components
                        }
                      >
                        {part.text}
                      </ReactMarkdown>
                    );
                  } else if (
                    part.type === "tool-invocation" &&
                    part.toolInvocation.state === "result"
                  ) {
                    return (
                      <ToolResultView
                        key={index}
                        result={part.toolInvocation.result}
                        tool={part.toolInvocation.toolName}
                      />
                    );
                  }
                  return null;
                })}
              </div>
            )}
          </div>
        </div>
        {message.role === "user" && (
          <Avatar className="flex-none mt-0.5">
            <AvatarFallback>U</AvatarFallback>
          </Avatar>
        )}
      </div>
    );
  };

  return (
    <main className="flex h-screen flex-col">
      <header className="flex-none border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 max-w-screen-2xl items-center">
          <h1 className="text-lg font-semibold">AI Assistant</h1>
        </div>
      </header>

      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full px-4">
          <div className="container max-w-screen-2xl py-6 space-y-6">
            {messages.map((message) => (
              <div key={message.id}>
                {renderMessage(message as ExtendedMessage)}
              </div>
            ))}
            {isLoading && (
              <div className="flex items-start gap-3">
                <Avatar className="flex-none mt-0.5">
                  <AvatarFallback>AI</AvatarFallback>
                </Avatar>
                <div className="space-y-2.5">
                  <Skeleton className="h-4 w-[250px]" />
                  <Skeleton className="h-4 w-[200px]" />
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      <footer className="flex-none border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container max-w-screen-2xl py-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              type="text"
              value={input}
              onChange={handleInputChange}
              placeholder="Ask a question..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button type="submit" disabled={isLoading}>
              Send
            </Button>
          </form>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleExampleClick(
                  "My patient has a VUS in PALB2 (c.1240G>T). Can you help me understand its potential impact on breast cancer risk and find recent publications about this variant?"
                )
              }
              className="text-xs"
            >
              Analyze PALB2 VUS
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleExampleClick(
                  "What are the latest clinical trials and research findings on germline PTEN mutations in Cowden syndrome? Particularly interested in cancer surveillance guidelines."
                )
              }
              className="text-xs"
            >
              PTEN & Cowden Research
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleExampleClick(
                  "Can you show me the genomic region around the MLH1 gene exon 16? I need to check for common Lynch syndrome variants and nearby splice sites."
                )
              }
              className="text-xs"
            >
              View MLH1 Region
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleExampleClick(
                  "What's the current evidence for reclassifying CDH1 c.1137G>A as pathogenic? Please include recent case studies and functional studies."
                )
              }
              className="text-xs"
            >
              CDH1 Classification
            </Button>
          </div>
        </div>
      </footer>
    </main>
  );
}
