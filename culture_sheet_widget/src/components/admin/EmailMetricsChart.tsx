import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface EmailMetricsChartProps {
  data: Array<{
    date: string;
    sent: number;
    opened: number;
    clicked: number;
  }>;
}

export function EmailMetricsChart({ data }: EmailMetricsChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Email Metrics Over Time</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="sent" stroke="#8884d8" name="Sent" />
            <Line type="monotone" dataKey="opened" stroke="#82ca9d" name="Opened" />
            <Line type="monotone" dataKey="clicked" stroke="#ffc658" name="Clicked" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
