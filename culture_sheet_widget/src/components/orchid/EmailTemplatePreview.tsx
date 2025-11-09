import React from 'react';

interface EmailTemplatePreviewProps {
  template: 'minimal' | 'detailed' | 'botanical';
  orchidName?: string;
}

export const EmailTemplatePreview: React.FC<EmailTemplatePreviewProps> = ({ 
  template, 
  orchidName = 'Phalaenopsis amabilis' 
}) => {
  const renderMinimal = () => (
    <div className="bg-white p-4 rounded border text-sm">
      <h3 className="font-bold text-lg mb-2">Culture Sheet Saved</h3>
      <p className="mb-2">Your culture sheet for <strong>{orchidName}</strong> has been saved.</p>
      <button className="bg-blue-500 text-white px-3 py-1 rounded text-xs">View Sheet</button>
    </div>
  );

  const renderDetailed = () => (
    <div className="bg-gradient-to-br from-blue-50 to-purple-50 p-6 rounded border">
      <h2 className="text-2xl font-bold text-blue-900 mb-3">Culture Sheet Saved Successfully</h2>
      <div className="bg-white p-4 rounded-lg shadow-sm mb-4">
        <p className="text-gray-700 mb-2">Your culture sheet for:</p>
        <p className="text-xl font-semibold text-purple-700 mb-3">{orchidName}</p>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div><span className="font-medium">Light:</span> Bright indirect</div>
          <div><span className="font-medium">Water:</span> Weekly</div>
          <div><span className="font-medium">Temp:</span> 65-80°F</div>
          <div><span className="font-medium">Humidity:</span> 50-70%</div>
        </div>
      </div>
      <button className="bg-blue-600 text-white px-4 py-2 rounded">View Full Sheet</button>
    </div>
  );

  const renderBotanical = () => (
    <div className="bg-gradient-to-b from-green-50 to-emerald-50 p-6 rounded border-2 border-green-200">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center text-white text-2xl">🌸</div>
        <div>
          <h2 className="text-xl font-serif text-green-900">Orchid Culture Sheet</h2>
          <p className="text-sm text-green-700 italic">Successfully Preserved</p>
        </div>
      </div>
      <div className="bg-white/80 backdrop-blur p-4 rounded-lg border border-green-300 mb-4">
        <p className="font-serif text-green-900 mb-2"><em>{orchidName}</em></p>
        <p className="text-sm text-gray-700">Your botanical care guide has been carefully saved to your collection.</p>
      </div>
      <button className="bg-green-700 text-white px-4 py-2 rounded-lg font-serif">View Collection</button>
    </div>
  );

  return (
    <div className="scale-75 origin-top">
      {template === 'minimal' && renderMinimal()}
      {template === 'detailed' && renderDetailed()}
      {template === 'botanical' && renderBotanical()}
    </div>
  );
};
