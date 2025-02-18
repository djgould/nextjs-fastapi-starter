import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface WeatherResultProps {
  result: {
    temperature: number;
    unit: string;
    elevation: number;
    coordinates: {
      lat: number;
      lon: number;
    };
  };
}

export const WeatherResult = ({ result }: WeatherResultProps) => (
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
