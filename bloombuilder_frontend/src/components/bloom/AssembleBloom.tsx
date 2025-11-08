import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Pause, RotateCcw, Sparkles } from 'lucide-react';
import { Species } from '@/types/bloombuilder';

interface AssembleBloomProps {
  species: Species;
  onComplete: () => void;
  onBack: () => void;
}

export function AssembleBloom({ species, onComplete, onBack }: AssembleBloomProps) {
  const [isAnimating, setIsAnimating] = useState(false);
  const [animationComplete, setAnimationComplete] = useState(false);
  const [styleFilter, setStyleFilter] = useState<'watercolor' | 'oils' | 'cartoon' | 'whimsical'>('watercolor');
  const [animationSpeed, setAnimationSpeed] = useState(1);
  const [transition, setTransition] = useState<'crossfade' | 'flip'>('crossfade');

  const startAnimation = () => {
    setIsAnimating(true);
    setAnimationComplete(false);
    
    // Simulate animation completion after 3 seconds
    setTimeout(() => {
      setIsAnimating(false);
      setAnimationComplete(true);
    }, 3000 / animationSpeed);
  };

  const resetAnimation = () => {
    setIsAnimating(false);
    setAnimationComplete(false);
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Assemble 3D Bloom - The Magic Moment!</h2>
        <p className="text-gray-600 mb-4">
          Watch the orchid parts lift from the botanical plate, float, swirl, and assemble into a complete flower.
        </p>
        {animationComplete && (
          <Badge variant="success" className="text-base">
            <Sparkles className="w-4 h-4 mr-2" />
            Assembly Complete!
          </Badge>
        )}
      </div>

      <div className="grid lg:grid-cols-3 gap-6 mb-8">
        {/* Animation Canvas */}
        <div className="lg:col-span-2">
          <Card className="p-6 bg-gradient-to-br from-purple-50 to-white">
            <div className="relative bg-white rounded-lg overflow-hidden border-2 border-purple-200" style={{ minHeight: '500px' }}>
              {/* Animation Area */}
              <div className="absolute inset-0 flex items-center justify-center">
                {!isAnimating && !animationComplete && (
                  <div className="text-center">
                    <Sparkles className="w-16 h-16 text-purple-400 mx-auto mb-4" />
                    <p className="text-gray-500">Ready to assemble</p>
                    <p className="text-sm text-gray-400">Click "Start Animation" below</p>
                  </div>
                )}

                {isAnimating && (
                  <div className={`w-full h-full flex items-center justify-center animation-${transition}`}>
                    {/* Animated flower parts */}
                    <div className="relative" style={{ animation: `float ${3 / animationSpeed}s ease-in-out` }}>
                      <div className={`flower-${styleFilter}`}>
                        {/* Placeholder flower visualization */}
                        <div className="text-center">
                          <div className="animate-spin-slow">
                            <svg width="200" height="200" viewBox="0 0 200 200" className="mx-auto">
                              {/* Center */}
                              <circle cx="100" cy="100" r="15" fill="#FFD700" />
                              
                              {/* Petals */}
                              {[0, 60, 120, 180, 240, 300].map((angle, i) => (
                                <ellipse
                                  key={i}
                                  cx="100"
                                  cy="50"
                                  rx="20"
                                  ry="40"
                                  fill={styleFilter === 'watercolor' ? '#E6B3FF' : 
                                        styleFilter === 'oils' ? '#D580FF' :
                                        styleFilter === 'cartoon' ? '#FF80BF' : '#FFB3E6'}
                                  transform={`rotate(${angle} 100 100)`}
                                  style={{ 
                                    animation: `petal-float ${3 / animationSpeed}s ease-in-out ${i * 0.1}s`,
                                    opacity: 0,
                                    animationFillMode: 'forwards'
                                  }}
                                />
                              ))}
                            </svg>
                          </div>
                          <p className="text-purple-600 font-semibold mt-4">Assembling...</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {animationComplete && (
                  <div className={`flower-${styleFilter} assembled`}>
                    <div className="text-center">
                      <svg width="250" height="250" viewBox="0 0 200 200" className="mx-auto">
                        {/* Center */}
                        <circle cx="100" cy="100" r="15" fill="#FFD700" />
                        
                        {/* Assembled Petals */}
                        {[0, 60, 120, 180, 240, 300].map((angle, i) => (
                          <ellipse
                            key={i}
                            cx="100"
                            cy="50"
                            rx="20"
                            ry="40"
                            fill={styleFilter === 'watercolor' ? '#E6B3FF' : 
                                  styleFilter === 'oils' ? '#D580FF' :
                                  styleFilter === 'cartoon' ? '#FF80BF' : '#FFB3E6'}
                            transform={`rotate(${angle} 100 100)`}
                          />
                        ))}
                      </svg>
                      <p className="text-purple-900 font-bold text-lg mt-4">
                        {species.scientificName}
                      </p>
                      <p className="text-green-600 flex items-center justify-center gap-2 mt-2">
                        <Sparkles className="w-4 h-4" />
                        Assembly Complete!
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Animation Controls */}
            <div className="flex gap-2 mt-4">
              {!animationComplete && (
                <Button
                  onClick={startAnimation}
                  disabled={isAnimating}
                  className="flex-1 bg-purple-600 hover:bg-purple-700"
                >
                  {isAnimating ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                  {isAnimating ? 'Animating...' : 'Start Animation'}
                </Button>
              )}
              
              {animationComplete && (
                <Button
                  onClick={resetAnimation}
                  variant="outline"
                  className="flex-1"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Replay Animation
                </Button>
              )}
            </div>
          </Card>
        </div>

        {/* Style & Settings Panel */}
        <div className="space-y-4">
          <Card className="p-4">
            <h3 className="font-bold mb-3">Style Filters</h3>
            <div className="grid grid-cols-2 gap-2">
              {(['watercolor', 'oils', 'cartoon', 'whimsical'] as const).map(style => (
                <Button
                  key={style}
                  onClick={() => setStyleFilter(style)}
                  variant={styleFilter === style ? 'default' : 'outline'}
                  size="sm"
                  className={styleFilter === style ? 'bg-purple-600' : ''}
                >
                  {style.charAt(0).toUpperCase() + style.slice(1)}
                </Button>
              ))}
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="font-bold mb-3">Animation Settings</h3>
            
            <div className="mb-4">
              <label className="block text-sm font-semibold mb-2">
                Animation Speed: {animationSpeed}x
              </label>
              <input
                type="range"
                min="0.5"
                max="2"
                step="0.5"
                value={animationSpeed}
                onChange={(e) => setAnimationSpeed(parseFloat(e.target.value))}
                className="w-full"
                disabled={isAnimating}
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Slow</span>
                <span>Fast</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Transition Effect</label>
              <div className="flex gap-2">
                <Button
                  onClick={() => setTransition('crossfade')}
                  variant={transition === 'crossfade' ? 'default' : 'outline'}
                  size="sm"
                  disabled={isAnimating}
                  className={transition === 'crossfade' ? 'bg-purple-600 flex-1' : 'flex-1'}
                >
                  Crossfade
                </Button>
                <Button
                  onClick={() => setTransition('flip')}
                  variant={transition === 'flip' ? 'default' : 'outline'}
                  size="sm"
                  disabled={isAnimating}
                  className={transition === 'flip' ? 'bg-purple-600 flex-1' : 'flex-1'}
                >
                  Flip
                </Button>
              </div>
            </div>
          </Card>

          <Card className="p-4 bg-purple-50">
            <h3 className="font-bold mb-2 text-purple-900">About This Stage</h3>
            <p className="text-sm text-gray-700">
              This magical moment transforms individual orchid structures from historical botanical plates into a cohesive, living representation—bridging centuries of botanical documentation with modern visualization.
            </p>
          </Card>
        </div>
      </div>

      <style>{`
        @keyframes float {
          0% { transform: translateY(100px) scale(0.5); opacity: 0; }
          50% { transform: translateY(-20px) scale(1.1) rotate(180deg); opacity: 1; }
          100% { transform: translateY(0) scale(1) rotate(360deg); opacity: 1; }
        }
        
        @keyframes petal-float {
          0% { opacity: 0; transform: translate(0, 100px) scale(0); }
          70% { opacity: 1; transform: translate(0, -10px) scale(1.1); }
          100% { opacity: 1; transform: translate(0, 0) scale(1); }
        }
        
        .animate-spin-slow {
          animation: spin 3s linear infinite;
        }
        
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button
          onClick={onComplete}
          className="bg-purple-600 hover:bg-purple-700"
          disabled={!animationComplete}
        >
          Continue to Export
        </Button>
      </div>
    </div>
  );
}
