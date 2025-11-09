import React from 'react';

interface Section {
  id: string;
  label: string;
  tooltip: string;
  enabled: boolean;
}

interface Props {
  sections: Section[];
  onToggle: (id: string) => void;
}

export const SectionToggles: React.FC<Props> = ({ sections, onToggle }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {sections.map(section => (
        <button
          key={section.id}
          onClick={() => onToggle(section.id)}
          className={`p-4 rounded-xl border-2 transition-all text-left group ${
            section.enabled 
              ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/10 shadow-md' 
              : 'border-gray-200 hover:border-gray-300 bg-white'
          }`}
          title={section.tooltip}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="font-semibold text-gray-900">{section.label}</span>
            <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
              section.enabled ? 'border-[var(--color-primary)] bg-[var(--color-primary)]' : 'border-gray-300'
            }`}>
              {section.enabled && <div className="w-2 h-2 bg-white rounded-full"></div>}
            </div>
          </div>
          <div className="text-xs text-gray-500 line-clamp-1">{section.tooltip}</div>
        </button>
      ))}
    </div>
  );
};
