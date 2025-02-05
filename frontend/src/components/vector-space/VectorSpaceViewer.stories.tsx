import type { Meta, StoryObj } from '@storybook/react';
import { VectorSpaceViewer } from './VectorSpaceViewer';

const meta: Meta<typeof VectorSpaceViewer> = {
  title: 'Vector Space/VectorSpaceViewer',
  component: VectorSpaceViewer,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof VectorSpaceViewer>;

// Generate some sample points in 3D space
const generatePoints = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    id: `point-${i}`,
    position: [
      Math.random() * 10 - 5,
      Math.random() * 10 - 5,
      Math.random() * 10 - 5,
    ] as [number, number, number],
    color: `hsl(${Math.random() * 360}, 70%, 50%)`,
  }));
};

// Sample query point and its neighbors
const queryPoint = {
  id: 'query',
  position: [2, 2, 2] as [number, number, number],
  isQuery: true,
};

const neighbors = Array.from({ length: 5 }, (_, i) => ({
  id: `neighbor-${i}`,
  position: [
    2 + Math.random() * 2 - 1,
    2 + Math.random() * 2 - 1,
    2 + Math.random() * 2 - 1,
  ] as [number, number, number],
  isNeighbor: true,
}));

export const Default: Story = {
  args: {
    points: generatePoints(50),
  },
};

export const WithQueryAndNeighbors: Story = {
  args: {
    points: [...generatePoints(30), queryPoint, ...neighbors],
    dimensions: 3,
  },
};

export const HighDimensionalProjection: Story = {
  args: {
    points: generatePoints(100),
    dimensions: 1536,
  },
}; 