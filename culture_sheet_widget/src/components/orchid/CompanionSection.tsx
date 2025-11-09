import React from 'react';
import { CompanionPlant } from '../../types/orchid';
import { CompanionCard } from './CompanionCard';

interface Props {
  companions: CompanionPlant[];
}

export const CompanionSection: React.FC<Props> = ({ companions }) => {
  return (
    <section className="mb-12">
      <h3 className="text-2xl font-bold text-gray-900 mb-2">Companion Plants</h3>
      <p className="text-sm text-gray-600 mb-2">Plants in same habitat</p>
      <p className="text-xs text-amber-600 mb-6 italic">Note: Companion plants are habitat context—don't co-pot.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {companions.map((plant, idx) => (
          <CompanionCard key={idx} plant={plant} />
        ))}
      </div>
    </section>
  );
};
