import React from 'react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const AboutModal: React.FC<Props> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-8 shadow-2xl" onClick={e => e.stopPropagation()}>
        <h2 className="text-3xl font-bold mb-6 text-gray-900">How to Use</h2>
        
        <div className="space-y-4 text-gray-700">
          <p className="text-lg">Search your orchid, set your location, choose which sections to include, then generate a tailored culture sheet.</p>
          
          <div className="bg-[var(--color-bg)] p-6 rounded-xl">
            <h3 className="font-bold text-xl mb-3 text-gray-900">Quick Tour</h3>
            <ol className="list-decimal list-inside space-y-2">
              <li><strong>Search</strong> – type a genus or species</li>
              <li><strong>Location</strong> – use GPS or type a city</li>
              <li><strong>Sections</strong> – toggle what to include</li>
              <li><strong>Themes</strong> – change look & feel anytime</li>
              <li><strong>Generate</strong> – view, save, or print</li>
            </ol>
          </div>

          <p className="text-sm italic text-gray-600 border-l-4 border-[var(--color-primary)] pl-4">
            Species ranges, climate, and pollinator data are compiled from multiple sources. Always observe your plant and adjust care accordingly.
          </p>
        </div>

        <button onClick={onClose} className="mt-6 px-8 py-3 bg-[var(--color-primary)] text-white rounded-xl hover:opacity-90 transition-opacity font-medium">
          Got it!
        </button>
      </div>
    </div>
  );
};
