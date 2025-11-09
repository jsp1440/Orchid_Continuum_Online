import React from 'react';

export const HeroSection: React.FC = () => {
  return (
    <div className="relative h-[500px] rounded-3xl overflow-hidden mb-12 shadow-2xl">
      <img 
        src="https://d64gsuwffb70l.cloudfront.net/69101c9bf3c933dcdd06e831_1762663637008_788d9b06.webp"
        alt="Beautiful orchids"
        className="w-full h-full object-cover"
      />
      <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/50 to-transparent flex items-center">
        <div className="max-w-2xl px-8 md:px-16">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 leading-tight">
            Orchid Culture Sheet Generator
          </h1>
          <p className="text-xl text-white/90 mb-6">
            Generate beautiful, evidence-based orchid culture sheets tailored to your species and climate.
          </p>
          <p className="text-sm text-white/80">
            Species ranges, climate, and pollinator data compiled from multiple sources.
          </p>
        </div>
      </div>
    </div>
  );
};
