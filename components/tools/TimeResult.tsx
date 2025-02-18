import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface TimeResultProps {
  result: {
    time: string;
    timezone: string;
  };
}

export const TimeResult = ({ result }: TimeResultProps) => (
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
