import React from 'react';
import { Pollinator } from '../../types/orchid';
import { PollinatorCard } from './PollinatorCard';

interface Props {
  pollinators: Pollinator[];
  themeStyle?: 'scientific' | 'fantasy';
}

export const PollinatorSection: React.FC<Props> = ({ pollinators, themeStyle = 'scientific' }) => {
  const title = themeStyle === 'fantasy' ? 'Magical Helpers' : 'Pollination Biology';
  
  return (
    <section className="mb-12">
      <h3 className="text-2xl font-bold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600 mb-6">Who visits this orchid in the wild</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {pollinators.map((pollinator, idx) => (
          <PollinatorCard key={idx} pollinator={pollinator} />
        ))}
      </div>
    </section>
  );
};
