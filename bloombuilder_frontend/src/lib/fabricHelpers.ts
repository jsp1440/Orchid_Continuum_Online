import { fabric } from 'fabric';

export function createArrow(points: number[], color: string) {
  const [x1, y1, x2, y2] = points;
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const headlen = 15;

  const arrowLine = new fabric.Line([x1, y1, x2, y2], {
    stroke: color,
    strokeWidth: 3,
    selectable: true,
  });

  const arrowHead = new fabric.Triangle({
    left: x2,
    top: y2,
    angle: (angle * 180) / Math.PI + 90,
    width: headlen,
    height: headlen,
    fill: color,
    selectable: false,
  });

  return new fabric.Group([arrowLine, arrowHead], {
    selectable: true,
  });
}

export function setupShapeDrawing(
  canvas: fabric.Canvas,
  tool: string,
  color: string,
  onComplete: () => void
) {
  let isDrawing = false;
  let startX = 0;
  let startY = 0;
  let shape: fabric.Object | null = null;

  const handleMouseDown = (e: fabric.IEvent) => {
    if (!['rect', 'circle', 'arrow'].includes(tool)) return;
    
    isDrawing = true;
    const pointer = canvas.getPointer(e.e);
    startX = pointer.x;
    startY = pointer.y;

    if (tool === 'rect') {
      shape = new fabric.Rect({
        left: startX,
        top: startY,
        width: 0,
        height: 0,
        fill: 'transparent',
        stroke: color,
        strokeWidth: 3,
      });
      canvas.add(shape);
    } else if (tool === 'circle') {
      shape = new fabric.Circle({
        left: startX,
        top: startY,
        radius: 0,
        fill: 'transparent',
        stroke: color,
        strokeWidth: 3,
      });
      canvas.add(shape);
    }
  };

  const handleMouseMove = (e: fabric.IEvent) => {
    if (!isDrawing || !shape) return;
    const pointer = canvas.getPointer(e.e);

    if (tool === 'rect') {
      const rect = shape as fabric.Rect;
      rect.set({
        width: Math.abs(pointer.x - startX),
        height: Math.abs(pointer.y - startY),
        left: Math.min(startX, pointer.x),
        top: Math.min(startY, pointer.y),
      });
    } else if (tool === 'circle') {
      const circle = shape as fabric.Circle;
      const radius = Math.sqrt(Math.pow(pointer.x - startX, 2) + Math.pow(pointer.y - startY, 2));
      circle.set({ radius: radius / 2 });
    }
    canvas.renderAll();
  };

  const handleMouseUp = (e: fabric.IEvent) => {
    if (!isDrawing) return;
    isDrawing = false;

    if (tool === 'arrow') {
      const pointer = canvas.getPointer(e.e);
      const arrow = createArrow([startX, startY, pointer.x, pointer.y], color);
      canvas.add(arrow);
    }

    shape = null;
    onComplete();
  };

  canvas.on('mouse:down', handleMouseDown);
  canvas.on('mouse:move', handleMouseMove);
  canvas.on('mouse:up', handleMouseUp);

  return () => {
    canvas.off('mouse:down', handleMouseDown);
    canvas.off('mouse:move', handleMouseMove);
    canvas.off('mouse:up', handleMouseUp);
  };
}
