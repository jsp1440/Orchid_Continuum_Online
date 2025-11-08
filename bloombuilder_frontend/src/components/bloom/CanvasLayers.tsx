import { fabric } from 'fabric';
import { SpurLength, PetalColor } from '@/contexts/AppContext';

export interface LayerConfig {
  spurLength: SpurLength;
  petalColor: PetalColor;
  imageUrl: string;
}

export const crossfadeToLayer = (
  canvas: fabric.Canvas,
  currentLayer: fabric.Image | null,
  targetUrl: string,
  onComplete: (newLayer: fabric.Image) => void
) => {
  // Load the target image
  fabric.Image.fromURL(targetUrl, (newImg) => {
    const scale = Math.min(800 / (newImg.width || 1), 600 / (newImg.height || 1)) * 0.9;
    newImg.scale(scale);
    newImg.set({ 
      selectable: false, 
      evented: false,
      opacity: 0,
      originX: 'center',
      originY: 'center',
      left: 400,
      top: 300,
    });

    // Add new image behind current one
    canvas.insertAt(newImg, 0, false);

    // Animate crossfade
    fabric.util.animate({
      startValue: 0,
      endValue: 1,
      duration: 600,
      easing: fabric.util.ease.easeInOutCubic,
      onChange: (value) => {
        newImg.set({ opacity: value });
        if (currentLayer) {
          currentLayer.set({ opacity: 1 - value });
        }
        canvas.renderAll();
      },
      onComplete: () => {
        // Remove old layer
        if (currentLayer) {
          canvas.remove(currentLayer);
        }
        canvas.renderAll();
        onComplete(newImg);
      }
    });
  });
};
