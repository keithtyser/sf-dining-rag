import type { Meta, StoryObj } from '@storybook/react';
import {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
} from './Card';
import { Button } from './Button';
import { Badge } from './Badge';

const meta = {
  title: 'UI/Card',
  component: Card,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'ghost', 'outline', 'elevated', 'interactive'],
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg', 'compact'],
    },
    isFullWidth: {
      control: 'boolean',
    },
    isClickable: {
      control: 'boolean',
    },
    isSelected: {
      control: 'boolean',
    },
  },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Create project</CardTitle>
        <CardDescription>Deploy your new project in one-click.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Your new project will be created in your current workspace.</p>
      </CardContent>
      <CardFooter className="justify-between">
        <Button variant="ghost">Cancel</Button>
        <Button>Deploy</Button>
      </CardFooter>
    </Card>
  ),
};

export const Interactive: Story = {
  render: () => (
    <Card variant="interactive" className="w-[350px]">
      <CardHeader>
        <CardTitle>Interactive Card</CardTitle>
        <CardDescription>This card has hover and active states.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Try hovering and clicking this card to see the animations.</p>
      </CardContent>
    </Card>
  ),
};

export const Ghost: Story = {
  render: () => (
    <Card variant="ghost" className="w-[350px]">
      <CardHeader>
        <CardTitle>Ghost Card</CardTitle>
        <CardDescription>A minimal card without borders or shadow.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Perfect for subtle grouping of content.</p>
      </CardContent>
    </Card>
  ),
};

export const Outline: Story = {
  render: () => (
    <Card variant="outline" className="w-[350px]">
      <CardHeader>
        <CardTitle>Outline Card</CardTitle>
        <CardDescription>A card with just a border.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Great for secondary content.</p>
      </CardContent>
    </Card>
  ),
};

export const Elevated: Story = {
  render: () => (
    <Card variant="elevated" className="w-[350px]">
      <CardHeader>
        <CardTitle>Elevated Card</CardTitle>
        <CardDescription>A card with enhanced shadow.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Perfect for highlighting important content.</p>
      </CardContent>
    </Card>
  ),
};

export const Selected: Story = {
  render: () => (
    <Card isSelected className="w-[350px]">
      <CardHeader>
        <CardTitle>Selected Card</CardTitle>
        <CardDescription>This card is in a selected state.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Notice the primary border and subtle background.</p>
      </CardContent>
    </Card>
  ),
};

export const WithBadge: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Project Status</CardTitle>
          <Badge variant="success">Active</Badge>
        </div>
        <CardDescription>Current project metrics and status.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>All systems are running smoothly.</p>
      </CardContent>
      <CardFooter>
        <Button variant="ghost" size="sm">View Details</Button>
      </CardFooter>
    </Card>
  ),
};

export const Compact: Story = {
  render: () => (
    <Card size="compact" className="w-[350px]">
      <CardHeader size="compact">
        <CardTitle>Compact Card</CardTitle>
        <CardDescription>A more condensed layout.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Perfect for dense information display.</p>
      </CardContent>
      <CardFooter size="compact">
        <Button size="sm">Action</Button>
      </CardFooter>
    </Card>
  ),
};

export const FullWidth: Story = {
  render: () => (
    <Card isFullWidth>
      <CardHeader>
        <CardTitle>Full Width Card</CardTitle>
        <CardDescription>This card spans the full width of its container.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Useful for responsive layouts and main content areas.</p>
      </CardContent>
    </Card>
  ),
};

export const Clickable: Story = {
  render: () => (
    <Card isClickable className="w-[350px]">
      <CardHeader>
        <CardTitle>Clickable Card</CardTitle>
        <CardDescription>This entire card is clickable.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Click anywhere on the card to trigger an action.</p>
      </CardContent>
    </Card>
  ),
};

export const AllVariants: Story = {
  render: () => (
    <div className="grid grid-cols-2 gap-4 p-4">
      <Card>
        <CardHeader>
          <CardTitle>Default</CardTitle>
          <CardDescription>Default card variant</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Basic card with standard styling</p>
        </CardContent>
      </Card>
      
      <Card variant="ghost">
        <CardHeader>
          <CardTitle>Ghost</CardTitle>
          <CardDescription>Ghost card variant</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Minimal styling without borders</p>
        </CardContent>
      </Card>
      
      <Card variant="outline">
        <CardHeader>
          <CardTitle>Outline</CardTitle>
          <CardDescription>Outline card variant</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Simple border without shadow</p>
        </CardContent>
      </Card>
      
      <Card variant="elevated">
        <CardHeader>
          <CardTitle>Elevated</CardTitle>
          <CardDescription>Elevated card variant</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Enhanced shadow effect</p>
        </CardContent>
      </Card>
      
      <Card variant="interactive">
        <CardHeader>
          <CardTitle>Interactive</CardTitle>
          <CardDescription>Interactive card variant</CardDescription>
        </CardHeader>
        <CardContent>
          <p>With hover and active states</p>
        </CardContent>
      </Card>
      
      <Card isSelected>
        <CardHeader>
          <CardTitle>Selected</CardTitle>
          <CardDescription>Selected card state</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Highlighted with primary color</p>
        </CardContent>
      </Card>
    </div>
  ),
}; 