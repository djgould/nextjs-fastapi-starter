import { useState } from "react";
import { WeatherResult } from "./WeatherResult";
import { TimeResult } from "./TimeResult";
import { SearchResult } from "./SearchResult";
import { WebsiteResult } from "./WebsiteResult";
import { PubmedResultContent } from "./PubmedResultContent";
import { ClinVarResultContent } from "./ClinVarResultContent";
import { GenomeBrowserContent } from "./GenomeBrowserContent";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDown } from "lucide-react";

interface ToolResultProps {
  result: any;
  tool: string;
}

export const ToolResult = ({ result, tool }: ToolResultProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const getSummary = () => {
    switch (tool) {
      case "get_pubmed_studies":
        return result.studies?.length
          ? `${result.studies.length} studies found${
              result.query ? ` for "${result.query}"` : ""
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
      case "get_weather":
        return `Weather: ${result.temperature}°${
          result.unit === "celsius" ? "C" : "F"
        }`;
      case "get_time":
        return `Time: ${new Date(result.time).toLocaleTimeString()}`;
      case "search":
        return `Search: "${result.query}"`;
      case "get_website":
        return `Website: ${result.title || result.url}`;
      default:
        return "Results available";
    }
  };

  const renderContent = () => {
    switch (tool) {
      case "get_weather":
        return <WeatherResult result={result} />;
      case "get_time":
        return <TimeResult result={result} />;
      case "search":
        return <SearchResult result={result} />;
      case "get_website":
        return <WebsiteResult result={result} />;
      case "get_pubmed_studies":
        return <PubmedResultContent result={result} />;
      case "get_clinvar_data":
        return <ClinVarResultContent result={result} />;
      case "genome_browser":
        return <GenomeBrowserContent result={result} />;
      default:
        return (
          <pre className="p-4 bg-muted rounded-lg overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        );
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
        <div className="border-t p-6">{renderContent()}</div>
      </CollapsibleContent>
    </Collapsible>
  );
};
