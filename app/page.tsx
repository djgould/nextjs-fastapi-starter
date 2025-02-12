"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

type Message = {
  role: string;
  type: string;
  content: string;
  tool?: string;
  arguments?: any;
  result?: any;
  id?: string;
};

const WeatherResult = ({ result }: { result: any }) => (
  <Card className="bg-blue-50">
    <CardContent className="p-4">
      <div className="flex items-center gap-2 mb-2">
        <Badge variant="secondary">Weather</Badge>
        <span className="text-2xl font-bold">
          {result.temperature}°{result.unit === "celsius" ? "C" : "F"}
        </span>
      </div>
      <div className="text-sm text-gray-600">
        <div>Elevation: {result.elevation}m</div>
        <div>
          Location: {result.coordinates.lat}, {result.coordinates.lon}
        </div>
      </div>
    </CardContent>
  </Card>
);

const TimeResult = ({ result }: { result: any }) => (
  <Card className="bg-purple-50">
    <CardContent className="p-4">
      <div className="flex items-center gap-2 mb-2">
        <Badge variant="secondary">Time</Badge>
        <span className="text-2xl font-bold">
          {new Date(result.time).toLocaleTimeString()}
        </span>
      </div>
      <div className="text-sm text-gray-600">Timezone: {result.timezone}</div>
    </CardContent>
  </Card>
);

const SearchResult = ({ result }: { result: any }) => (
  <Card className="bg-green-50">
    <CardContent className="p-4">
      <div className="flex items-center gap-2 mb-2">
        <Badge variant="secondary">Search</Badge>
        <span className="text-sm text-gray-600">"{result.query}"</span>
      </div>
      <div className="space-y-4">
        {result.results.map((item: any, index: number) => (
          <div key={index} className="border-b pb-2 last:border-b-0">
            <a
              href={item.link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline font-medium"
            >
              {item.title}
            </a>
            <p className="text-sm text-gray-700 mt-1">{item.snippet}</p>
          </div>
        ))}
      </div>
    </CardContent>
  </Card>
);

const WebsiteResult = ({ result }: { result: any }) => (
  <Card className="bg-yellow-50">
    <CardContent className="p-4">
      <div className="flex items-center gap-2 mb-2">
        <Badge variant="secondary">Website</Badge>
        <a
          href={result.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline text-lg font-medium"
        >
          {result.title || result.url}
        </a>
      </div>
      {result.description && (
        <p className="text-sm text-gray-600 mt-1 mb-4">{result.description}</p>
      )}
      <div className="prose prose-sm max-h-96 overflow-y-auto">
        {result.content}
      </div>
    </CardContent>
  </Card>
);

const PubmedResult = ({ result }: { result: any }) => {
  return (
    <Card className="bg-indigo-50">
      <CardContent className="p-4">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="secondary">PubMed Studies</Badge>
            {result.query && (
              <span className="text-sm text-gray-600">
                for <span className="font-medium">"{result.query}"</span>
              </span>
            )}
          </div>
          {result.studies && result.studies.length > 0 ? (
            <div className="overflow-x-auto -mx-4 px-4">
              <div className="flex gap-4 pb-2 min-w-0">
                {result.studies.map((study: any, index: number) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded px-3 py-2 bg-white/50 w-[300px] flex-none"
                  >
                    <div className="flex flex-col gap-1">
                      <HoverCard>
                        <HoverCardTrigger asChild>
                          <a
                            href={`https://pubmed.ncbi.nlm.nih.gov/${study.pmid}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-blue-600 hover:underline line-clamp-2 break-words"
                          >
                            {study.title}
                          </a>
                        </HoverCardTrigger>
                        <HoverCardContent
                          side="right"
                          align="start"
                          className="w-[400px] max-h-[300px] overflow-hidden"
                        >
                          <div className="flex flex-col h-full">
                            <div className="flex-none p-4 pb-2">
                              <h4 className="font-semibold text-sm break-words">
                                {study.title}
                              </h4>
                              <div className="flex items-center gap-2 text-xs text-gray-500 mt-1 flex-wrap">
                                <span className="break-words">
                                  {study.journal}
                                </span>
                                <span>·</span>
                                <span>{study.year}</span>
                                <span>·</span>
                                <span>PMID: {study.pmid}</span>
                              </div>
                            </div>
                            {study.summary && (
                              <div className="flex-1 overflow-y-auto px-4 pb-4">
                                <div className="text-sm text-gray-600 leading-relaxed break-words">
                                  {study.summary}
                                </div>
                              </div>
                            )}
                          </div>
                        </HoverCardContent>
                      </HoverCard>
                      <div className="flex items-center gap-2 text-xs text-gray-500 flex-wrap">
                        <span className="break-words">{study.journal}</span>
                        <span>·</span>
                        <span>{study.year}</span>
                        <span>·</span>
                        <span>PMID: {study.pmid}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-600">No studies found.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default function Home() {
  const [message, setMessage] = useState("");
  const [conversation, setConversation] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMessage = { role: "user", type: "message", content: message };
    setConversation((prev) => [...prev, userMessage]);

    setIsLoading(true);
    try {
      const response = await fetch(
        `/api/py/chat?message=${encodeURIComponent(message)}`
      );
      const data = await response.json();

      setConversation((prev) => [...prev, ...data.conversation.slice(1)]);
    } catch (error) {
      console.error("Error:", error);
      setConversation((prev) => [
        ...prev,
        {
          role: "assistant",
          type: "message",
          content: "Sorry, there was an error processing your request.",
        },
      ]);
    }
    setIsLoading(false);
    setMessage("");
  };

  const renderMessage = (msg: Message, index: number) => {
    switch (msg.type) {
      case "message":
        return (
          <div
            className={`mb-4 flex items-start gap-3 ${
              msg.role === "user" ? "flex-row-reverse" : "flex-row"
            }`}
          >
            <Avatar
              className={msg.role === "user" ? "bg-blue-500" : "bg-gray-200"}
            >
              <AvatarFallback>
                {msg.role === "user" ? "U" : "AI"}
              </AvatarFallback>
            </Avatar>
            <Card
              className={`max-w-[80%] ${
                msg.role === "user" ? "bg-blue-500 text-white" : "bg-gray-100"
              }`}
            >
              <CardContent
                className={`p-3 ${
                  msg.role === "user"
                    ? "break-words overflow-wrap-anywhere"
                    : "prose prose-sm dark:prose-invert max-w-none break-words overflow-wrap-anywhere"
                }`}
              >
                {msg.role === "user" ? (
                  msg.content
                ) : (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
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
                          <ol {...props} className="list-decimal pl-4 mt-2" />
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
                      } satisfies Components
                    }
                  >
                    {msg.content}
                  </ReactMarkdown>
                )}
              </CardContent>
            </Card>
          </div>
        );

      case "tool_result": {
        if (msg.tool === "get_pubmed_studies") {
          const toolUseMsg = conversation.find(
            (m) => m.type === "tool_use" && m.id === msg.id
          );
          const query = toolUseMsg?.arguments?.query;
          return (
            <div className="mb-4 ml-8">
              <PubmedResult result={{ ...msg.result, query }} />
            </div>
          );
        }
        return (
          <div className="mb-4 ml-8">
            {msg.tool === "get_weather" ? (
              <WeatherResult result={msg.result} />
            ) : msg.tool === "get_time" ? (
              <TimeResult result={msg.result} />
            ) : msg.tool === "google_search" ? (
              <SearchResult result={msg.result} />
            ) : msg.tool === "read_website" ? (
              <WebsiteResult result={msg.result} />
            ) : (
              <Card>
                <CardContent className="p-2">
                  <pre className="bg-gray-50 rounded overflow-x-auto whitespace-pre-wrap break-words">
                    {JSON.stringify(msg.result, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            )}
          </div>
        );
      }

      case "tool_use":
        return (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="mb-2 ml-4">
                  <Badge variant="outline" className="text-gray-500">
                    Using {msg.tool}
                  </Badge>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <pre className="text-xs">
                  {JSON.stringify(msg.arguments, null, 2)}
                </pre>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        );

      default:
        return null;
    }
  };

  return (
    <main className="min-h-screen flex flex-col">
      <Card className="flex-1 rounded-none border-0">
        <CardHeader className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <h2 className="text-2xl font-bold text-center">AI Assistant</h2>
        </CardHeader>
        <CardContent className="flex flex-col p-4 pt-6 h-[calc(100vh-8rem)]">
          <ScrollArea className="flex-1 pr-4 !block overflow-x-hidden">
            <div className="space-y-4 overflow-x-hidden">
              {conversation.map((msg, index) => (
                <>
                  <div key={index}>{renderMessage(msg, index)}</div>
                  {index < conversation.length - 1 && (
                    <Separator className="my-4" />
                  )}
                </>
              ))}
              {isLoading && (
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <Skeleton className="h-12 w-12 rounded-full" />
                    <div className="space-y-2">
                      <Skeleton className="h-4 w-[250px]" />
                      <Skeleton className="h-4 w-[200px]" />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
          <Separator className="my-4" />
          <div className="pt-2">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <Input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask about weather or time..."
                disabled={isLoading}
                className="flex-1"
              />
              <Button type="submit" disabled={isLoading}>
                Send
              </Button>
            </form>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
