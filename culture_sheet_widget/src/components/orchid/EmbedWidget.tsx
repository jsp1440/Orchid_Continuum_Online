import React, { useState } from 'react';

export const EmbedWidget: React.FC = () => {
  const [width, setWidth] = useState('600');
  const [height, setHeight] = useState('800');
  
  const embedCode = `<iframe src="${window.location.origin}/embed" width="${width}" height="${height}" frameborder="0"></iframe>`;

  return (
    <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-8 shadow-xl">
      <h2 className="text-3xl font-bold mb-6 text-gray-900">Embed Widget</h2>
      <p className="text-gray-600 mb-6">Embed the orchid culture sheet generator on your website</p>
      
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Width (px)</label>
          <input
            type="number"
            value={width}
            onChange={(e) => setWidth(e.target.value)}
            className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-[var(--color-primary)] focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Height (px)</label>
          <input
            type="number"
            value={height}
            onChange={(e) => setHeight(e.target.value)}
            className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-[var(--color-primary)] focus:outline-none"
          />
        </div>
      </div>

      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <code className="text-sm text-gray-800 break-all">{embedCode}</code>
      </div>

      <button
        onClick={() => navigator.clipboard.writeText(embedCode)}
        className="mt-4 px-6 py-3 bg-[var(--color-primary)] text-white rounded-lg hover:opacity-90 transition-opacity font-medium"
      >
        Copy Code
      </button>
    </div>
  );
};
