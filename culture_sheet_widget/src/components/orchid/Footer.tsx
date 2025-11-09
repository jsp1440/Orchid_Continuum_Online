import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white/90 backdrop-blur-lg border-t border-gray-200 mt-20">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div>
            <h3 className="font-bold text-lg mb-4 text-gray-900">Orchid Culture</h3>
            <p className="text-sm text-gray-600">Generate beautiful, evidence-based orchid culture sheets tailored to your species and climate.</p>
          </div>
          
          <div>
            <h4 className="font-bold mb-4 text-gray-900">Features</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>7 Interface Themes</li>
              <li>Climate Comparison</li>
              <li>Pollinator Info</li>
              <li>Companion Plants</li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-bold mb-4 text-gray-900">Resources</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><a href="#" className="hover:text-[var(--color-primary)] transition-colors">Documentation</a></li>
              <li><a href="#" className="hover:text-[var(--color-primary)] transition-colors">API Reference</a></li>
              <li><a href="#" className="hover:text-[var(--color-primary)] transition-colors">Community</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-bold mb-4 text-gray-900">Legal</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><a href="#" className="hover:text-[var(--color-primary)] transition-colors">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-[var(--color-primary)] transition-colors">Terms of Service</a></li>
            </ul>
          </div>
        </div>
        
        <div className="pt-8 border-t border-gray-200 text-center text-sm text-gray-600">
          <p className="mb-2">Educational guidance only. Always observe your plant and adjust care accordingly.</p>
          <p>&copy; 2025 Orchid Culture Sheet Generator. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};
