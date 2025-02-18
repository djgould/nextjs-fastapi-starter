import { useState } from "react";
import { Button } from "@/components/ui/button";

interface GenomeBrowserContentProps {
  result: {
    coordinates: string;
  };
}

export const GenomeBrowserContent = ({ result }: GenomeBrowserContentProps) => {
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
