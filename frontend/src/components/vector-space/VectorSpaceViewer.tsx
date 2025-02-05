import React, { useState, useCallback } from 'react';
import { cn } from '@/lib/utils';

interface VectorSpaceViewerProps {
  className?: string;
  points?: Array<{
    id: string;
    position: [number, number, number];
    color?: string;
    isQuery?: boolean;
    isNeighbor?: boolean;
  }>;
  dimensions?: number;
}

function projectTo2D(point: [number, number, number]): [number, number] {
  // Simple isometric projection
  const x = point[0] - point[2] * 0.5;
  const y = point[1] - point[2] * 0.5;
  return [x, y];
}

function GridLines() {
  const gridSize = 20;
  const lines = [];

  // Create grid lines
  for (let i = -gridSize; i <= gridSize; i++) {
    // Vertical lines
    lines.push(
      <line
        key={`v${i}`}
        x1={i * 50}
        y1={-gridSize * 50}
        x2={i * 50}
        y2={gridSize * 50}
        stroke="#374151"
        strokeWidth={i % 5 === 0 ? 1 : 0.5}
        opacity={0.3}
      />
    );
    // Horizontal lines
    lines.push(
      <line
        key={`h${i}`}
        x1={-gridSize * 50}
        y1={i * 50}
        x2={gridSize * 50}
        y2={i * 50}
        stroke="#374151"
        strokeWidth={i % 5 === 0 ? 1 : 0.5}
        opacity={0.3}
      />
    );
  }

  return <>{lines}</>;
}

function Axes() {
  return (
    <>
      {/* X axis */}
      <line
        x1={-500}
        y1={0}
        x2={500}
        y2={0}
        stroke="#ef4444"
        strokeWidth={2}
      />
      <text x={480} y={-10} fill="#ef4444" fontSize={12}>X</text>

      {/* Y axis */}
      <line
        x1={0}
        y1={-500}
        x2={0}
        y2={500}
        stroke="#22c55e"
        strokeWidth={2}
      />
      <text x={10} y={-480} fill="#22c55e" fontSize={12}>Y</text>

      {/* Z axis (projected) */}
      <line
        x1={0}
        y1={0}
        x2={-250}
        y2={-250}
        stroke="#3b82f6"
        strokeWidth={2}
      />
      <text x={-260} y={-260} fill="#3b82f6" fontSize={12}>Z</text>
    </>
  );
}

function DataPoints({ points = [] }: { points: VectorSpaceViewerProps['points'] }) {
  return (
    <>
      {points.map((point) => {
        const [x, y] = projectTo2D(point.position);
        const color = point.color || (point.isQuery ? '#22c55e' : point.isNeighbor ? '#f97316' : '#ffffff');
        
        return (
          <g key={point.id}>
            <circle
              cx={x * 50}
              cy={y * 50}
              r={5}
              fill={color}
              opacity={0.8}
              stroke="#000000"
              strokeWidth={1}
            />
          </g>
        );
      })}
    </>
  );
}

export function VectorSpaceViewer({
  className,
  points = [],
  dimensions = 3,
}: VectorSpaceViewerProps) {
  const [transform, setTransform] = useState({ x: 500, y: 500, scale: 1 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    setTransform(prev => ({
      ...prev,
      scale: Math.max(0.1, Math.min(5, prev.scale * (1 - e.deltaY * 0.001))),
    }));
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - transform.x, y: e.clientY - transform.y });
  }, [transform]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDragging) {
      setTransform(prev => ({
        ...prev,
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      }));
    }
  }, [isDragging, dragStart]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  return (
    <div className={cn('relative h-[600px] w-full rounded-lg border overflow-hidden', className)}>
      <svg
        className="w-full h-full bg-background"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.scale})`}>
          <GridLines />
          <Axes />
          <DataPoints points={points} />
        </g>
      </svg>

      <div className="absolute bottom-4 left-4 rounded-md bg-background/90 p-2 text-sm">
        <div className="font-medium">Dimensions: {dimensions}</div>
        <div className="text-muted-foreground">Points: {points.length}</div>
      </div>

      <div className="absolute top-4 right-4 rounded-md bg-background/90 p-2 text-sm space-y-1">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-white border border-black/20" />
          <span>Regular Points</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span>Query Point</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-orange-500" />
          <span>Nearest Neighbors</span>
        </div>
      </div>

      <div className="absolute bottom-4 right-4 rounded-md bg-background/90 p-2 text-sm">
        <div className="text-muted-foreground">Scroll to zoom • Drag to pan</div>
      </div>
    </div>
  );
}

VectorSpaceViewer.displayName = 'VectorSpaceViewer'; 