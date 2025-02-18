import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface WebsiteResultProps {
  result: {
    url: string;
    title?: string;
    description?: string;
    content: string;
  };
}

export const WebsiteResult = ({ result }: WebsiteResultProps) => (
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
