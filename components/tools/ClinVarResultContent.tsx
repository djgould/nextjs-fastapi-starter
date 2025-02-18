import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";

interface ClinVarResultContentProps {
  result: {
    found: boolean;
    message?: string;
    variants?: Array<{
      title: string;
      clinical_significance: string;
      is_fda_recognized: boolean;
      review_status: string;
      last_evaluated: string;
      molecular_consequences: string[];
      associated_conditions?: Array<{
        name: string;
      }>;
      allele_frequencies?: Array<{
        source: string;
        frequency: string;
      }>;
      supporting_submissions: {
        clinical: string[];
      };
    }>;
  };
}

export const ClinVarResultContent = ({ result }: ClinVarResultContentProps) => {
  if (!result.found) {
    return <p className="text-sm text-muted-foreground">{result.message}</p>;
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-6">
        {result.variants?.map((variant, index) => (
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

            {variant.associated_conditions &&
              variant.associated_conditions?.length > 0 && (
                <div className="space-y-2 bg-muted/40 rounded-lg p-4">
                  <div className="text-sm font-medium">
                    Associated Conditions
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {variant.associated_conditions?.map((condition, idx) => (
                      <Badge
                        key={idx}
                        variant="outline"
                        className="rounded-md px-2.5 py-0.5 text-xs bg-background"
                      >
                        {condition.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

            {variant.allele_frequencies &&
              variant.allele_frequencies?.length > 0 && (
                <div className="space-y-2 bg-muted/40 rounded-lg p-4">
                  <div className="text-sm font-medium">
                    Population Frequencies
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    {variant.allele_frequencies?.map((freq, idx) => (
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
              <span className="text-primary font-medium">
                {variant.supporting_submissions.clinical.length} clinical
                submission
                {variant.supporting_submissions.clinical.length !== 1
                  ? "s"
                  : ""}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
