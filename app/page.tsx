/* eslint-disable react/no-unescaped-entities */
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
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDown } from "lucide-react";

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

const ToolResult = ({ result, tool }: { result: any; tool: string }) => {
  const [isOpen, setIsOpen] = useState(false);

  const getSummary = () => {
    switch (tool) {
      case "get_pubmed_studies":
        return result.studies?.length
          ? `${result.studies.length} studies found${
              result.query ? ` for &quot;${result.query}&quot;` : ""
            }`
          : "No studies found";
      case "get_clinvar_data":
        if (!result.found) return result.message;
        const significance = result.variants?.[0]?.clinical_significance;
        return `${result.total_results} variant${
          result.total_results !== 1 ? "s" : ""
        } found${significance ? ` • ${significance}` : ""}`;
      case "genome_browser":
        return `${result.gene} • ${result.coordinates}`;
      default:
        return "Results available";
    }
  };

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className="rounded-lg border bg-card text-card-foreground shadow-sm transition hover:shadow-md"
    >
      <CollapsibleTrigger className="flex w-full items-center justify-between p-4 font-medium hover:bg-muted/50 transition-colors">
        <div className="flex items-center gap-4 text-left">
          <span className="text-sm">{getSummary()}</span>
        </div>
        <ChevronDown
          className={`h-4 w-4 text-muted-foreground transition-transform ${
            isOpen ? "transform rotate-180" : ""
          }`}
        />
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="border-t p-6">
          {tool === "get_pubmed_studies" && (
            <PubmedResultContent result={result} />
          )}
          {tool === "get_clinvar_data" && (
            <ClinVarResultContent result={result} />
          )}
          {tool === "genome_browser" && (
            <GenomeBrowserContent result={result} />
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
};

const PubmedResultContent = ({ result }: { result: any }) => {
  if (!result.studies?.length) {
    return <p className="text-sm text-muted-foreground">No studies found.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4">
        {result.studies.map((study: any, index: number) => (
          <HoverCard key={index}>
            <HoverCardTrigger asChild>
              <a
                href={`https://pubmed.ncbi.nlm.nih.gov/${study.pmid}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block -mx-2 rounded-md p-4 transition-colors hover:bg-muted/50"
              >
                <h4 className="font-medium text-base mb-2 leading-tight">
                  {study.title}
                </h4>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="font-medium">{study.journal}</span>
                  <span>•</span>
                  <span>{study.year}</span>
                  <span>•</span>
                  <span className="font-mono">PMID: {study.pmid}</span>
                </div>
              </a>
            </HoverCardTrigger>
            <HoverCardContent
              side="right"
              align="start"
              className="w-[450px] p-6"
            >
              <div className="space-y-4">
                <h4 className="font-medium text-base leading-tight">
                  {study.title}
                </h4>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="font-medium">{study.journal}</span>
                  <span>•</span>
                  <span>{study.year}</span>
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {study.summary}
                </p>
                <div className="pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 text-xs"
                    asChild
                  >
                    <a
                      href={`https://pubmed.ncbi.nlm.nih.gov/${study.pmid}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View on PubMed
                    </a>
                  </Button>
                </div>
              </div>
            </HoverCardContent>
          </HoverCard>
        ))}
      </div>
    </div>
  );
};

const ClinVarResultContent = ({ result }: { result: any }) => {
  if (!result.found) {
    return <p className="text-sm text-muted-foreground">{result.message}</p>;
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-6">
        {result.variants.map((variant: any, index: number) => (
          <div key={index} className="space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h4 className="font-medium text-base mb-2">{variant.title}</h4>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      variant.clinical_significance
                        ?.toLowerCase()
                        .includes("pathogenic")
                        ? "destructive"
                        : variant.clinical_significance
                            ?.toLowerCase()
                            .includes("benign")
                        ? "secondary"
                        : "outline"
                    }
                    className="rounded-md px-2.5 py-0.5 font-medium"
                  >
                    {variant.clinical_significance || "No Classification"}
                  </Badge>
                  {variant.is_fda_recognized && (
                    <Badge
                      variant="secondary"
                      className="rounded-md px-2.5 py-0.5 bg-blue-50 text-blue-700 border-blue-200"
                    >
                      FDA Recognized
                    </Badge>
                  )}
                </div>
              </div>
              <HoverCard>
                <HoverCardTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 px-3 rounded-md"
                  >
                    Details
                  </Button>
                </HoverCardTrigger>
                <HoverCardContent side="left" className="w-96 p-6">
                  <div className="space-y-4">
                    <div>
                      <div className="font-medium text-sm mb-1">
                        Review Status
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {variant.review_status}
                      </div>
                    </div>
                    <div>
                      <div className="font-medium text-sm mb-1">
                        Last Evaluated
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {variant.last_evaluated}
                      </div>
                    </div>
                    <div>
                      <div className="font-medium text-sm mb-1">
                        Molecular Consequences
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {variant.molecular_consequences.join(", ")}
                      </div>
                    </div>
                  </div>
                </HoverCardContent>
              </HoverCard>
            </div>

            {variant.associated_conditions?.length > 0 && (
              <div className="space-y-2 bg-muted/40 rounded-lg p-4">
                <div className="text-sm font-medium">Associated Conditions</div>
                <div className="flex flex-wrap gap-2">
                  {variant.associated_conditions.map(
                    (condition: any, idx: number) => (
                      <Badge
                        key={idx}
                        variant="outline"
                        className="rounded-md px-2.5 py-0.5 text-xs bg-background"
                      >
                        {condition.name}
                      </Badge>
                    )
                  )}
                </div>
              </div>
            )}

            {variant.allele_frequencies?.length > 0 && (
              <div className="space-y-2 bg-muted/40 rounded-lg p-4">
                <div className="text-sm font-medium">
                  Population Frequencies
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  {variant.allele_frequencies.map((freq: any, idx: number) => (
                    <div
                      key={idx}
                      className="flex justify-between items-center"
                    >
                      <span className="text-muted-foreground">
                        {freq.source.split("(")[0].trim()}
                      </span>
                      <span className="font-mono text-xs bg-muted px-2 py-1 rounded">
                        {parseFloat(freq.frequency).toExponential(2)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">Evidence:</span>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger className="text-primary font-medium hover:underline">
                    {variant.supporting_submissions.clinical.length} clinical
                    submission
                    {variant.supporting_submissions.clinical.length !== 1
                      ? "s"
                      : ""}
                  </TooltipTrigger>
                  <TooltipContent className="p-4">
                    <div className="space-y-2">
                      <div className="font-medium">Clinical Variation IDs</div>
                      <div className="font-mono text-xs bg-muted p-2 rounded">
                        {variant.supporting_submissions.clinical.join(", ")}
                      </div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const GenomeBrowserContent = ({ result }: { result: any }) => {
  const [showBrowser, setShowBrowser] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowBrowser(!showBrowser)}
          className="h-8 px-3 rounded-md"
        >
          {showBrowser ? "Hide Browser" : "Show Browser"}
        </Button>
      </div>

      {showBrowser && (
        <div className="rounded-lg overflow-hidden border shadow-sm">
          <iframe
            src={`https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&position=${result.coordinates.replace(
              /,/g,
              ""
            )}`}
            width="100%"
            height="500"
            style={{ border: "none" }}
            title="UCSC Genome Browser"
          />
        </div>
      )}
    </div>
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
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout

      const response = await fetch(
        `/api/py/chat?message=${encodeURIComponent(message)}`,
        {
          signal: controller.signal,
        }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setConversation((prev) => [...prev, ...data.conversation.slice(1)]);
    } catch (error) {
      console.error("Error:", error);
      let errorMessage = "Sorry, there was an error processing your request.";

      if (error instanceof Error) {
        if (error.name === "AbortError") {
          errorMessage =
            "The request took too long to complete. Please try again.";
        } else if (error.message.includes("fetch")) {
          errorMessage =
            "Network error. Please check your connection and try again.";
        }
      }

      setConversation((prev) => [
        ...prev,
        {
          role: "assistant",
          type: "message",
          content: errorMessage,
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
            className={`group flex items-start gap-3 ${
              msg.role === "user" ? "justify-end" : ""
            }`}
          >
            {msg.role !== "user" && (
              <Avatar className="flex-none mt-0.5">
                <AvatarFallback>AI</AvatarFallback>
              </Avatar>
            )}
            <div
              className={`flex-1 max-w-3xl overflow-hidden ${
                msg.role === "user" ? "text-right" : ""
              }`}
            >
              <div
                className={`inline-block px-3 py-2 rounded-lg ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                {msg.role === "user" ? (
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <ReactMarkdown
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
                      } as Components
                    }
                  >
                    {msg.content}
                  </ReactMarkdown>
                )}
              </div>
            </div>
            {msg.role === "user" && (
              <Avatar className="flex-none mt-0.5">
                <AvatarFallback>U</AvatarFallback>
              </Avatar>
            )}
          </div>
        );

      case "tool_result":
        console.log(msg);
        return (
          <div className="flex items-start gap-3">
            <div className="flex-none mt-0.5 w-9 h-9 rounded-full bg-muted/50 flex items-center justify-center">
              <span className="text-base" aria-hidden="true">
                {msg.tool === "get_pubmed_studies"
                  ? "📚"
                  : msg.tool === "get_clinvar_data"
                  ? "🧬"
                  : msg.tool === "genome_browser"
                  ? "🔬"
                  : "🔍"}
              </span>
            </div>
            <div className="flex-1 max-w-3xl">
              <div className="flex items-center gap-2 mb-2">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  {msg.tool === "get_pubmed_studies"
                    ? "Literature"
                    : msg.tool === "get_clinvar_data"
                    ? "Variant"
                    : msg.tool === "genome_browser"
                    ? "Genomic View"
                    : "Results"}
                </div>
                <div className="text-[10px] text-muted-foreground/50">
                  {msg.tool === "get_pubmed_studies"
                    ? `Search: "${
                        msg.arguments?.query ||
                        msg.result?.query ||
                        "unknown query"
                      }"`
                    : msg.tool === "get_clinvar_data"
                    ? `Variant: ${msg.arguments?.gene} ${msg.arguments?.variant}`
                    : msg.tool === "genome_browser"
                    ? `Gene: ${msg.arguments?.gene}`
                    : ""}
                </div>
              </div>
              <ToolResult result={msg.result} tool={msg.tool || ""} />
            </div>
          </div>
        );

      case "tool_use":
        return null;

      default:
        return null;
    }
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
            {conversation.map((msg, index) => (
              <div key={index}>{renderMessage(msg, index)}</div>
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
              value={message}
              onChange={(e) => setMessage(e.target.value)}
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
                setMessage(
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
                setMessage(
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
                setMessage(
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
                setMessage(
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
