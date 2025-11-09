import React from 'react';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatSignificanceProps {
  pValue: number;
  improvement: number;
}

export function StatSignificance({ pValue, improvement }: StatSignificanceProps) {
  const isSignificant = pValue < 0.05;
  const confidence = (1 - pValue) * 100;

  return (
    <div className="flex items-center gap-2">
      {improvement > 0 ? (
        <TrendingUp className="h-4 w-4 text-green-600" />
      ) : improvement < 0 ? (
        <TrendingDown className="h-4 w-4 text-red-600" />
      ) : (
        <Minus className="h-4 w-4 text-gray-400" />
      )}
      <span className={`font-semibold ${improvement > 0 ? 'text-green-600' : improvement < 0 ? 'text-red-600' : 'text-gray-600'}`}>
        {improvement > 0 ? '+' : ''}{improvement.toFixed(1)}%
      </span>
      <Badge variant={isSignificant ? 'default' : 'secondary'}>
        {isSignificant ? `${confidence.toFixed(0)}% confident` : 'Not significant'}
      </Badge>
    </div>
  );
}
