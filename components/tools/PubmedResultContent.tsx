import { Button } from "@/components/ui/button";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";

interface Study {
  pmid: string;
  title: string;
  journal: string;
  year: string;
  summary: string;
}

interface PubmedResultContentProps {
  result: {
    studies: Study[];
  };
}

export const PubmedResultContent = ({ result }: PubmedResultContentProps) => {
  if (!result.studies?.length) {
    return <p className="text-sm text-muted-foreground">No studies found.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4">
        {result.studies.map((study, index) => (
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
