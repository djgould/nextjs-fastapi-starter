import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface SearchResultProps {
  result: {
    query: string;
    results: Array<{
      title: string;
      link: string;
      snippet: string;
    }>;
  };
}

export const SearchResult = ({ result }: SearchResultProps) => (
  <Card className="bg-green-50">
    <CardContent className="p-4">
      <div className="flex items-center gap-2 mb-2">
        <Badge variant="secondary">Search</Badge>
        <span className="text-sm text-gray-600">
          &quot;{result.query}&quot;
        </span>
      </div>
      <div className="space-y-4">
        {result.results.map((item, index) => (
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
