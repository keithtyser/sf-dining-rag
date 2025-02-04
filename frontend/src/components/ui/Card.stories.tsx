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

const meta = {
  title: 'UI/Card',
  component: Card,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card description goes here.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card content with some example text to show the layout.</p>
      </CardContent>
      <CardFooter>
        <Button variant="default">Action</Button>
      </CardFooter>
    </Card>
  ),
};

export const Outline: Story = {
  render: () => (
    <Card variant="outline" className="w-[350px]">
      <CardHeader>
        <CardTitle>Outline Card</CardTitle>
        <CardDescription>With a more prominent border.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card content with outline variant.</p>
      </CardContent>
    </Card>
  ),
};

export const Ghost: Story = {
  render: () => (
    <Card variant="ghost" className="w-[350px]">
      <CardHeader>
        <CardTitle>Ghost Card</CardTitle>
        <CardDescription>Without border or shadow.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card content with ghost variant.</p>
      </CardContent>
    </Card>
  ),
};

export const Elevated: Story = {
  render: () => (
    <Card variant="elevated" className="w-[350px]">
      <CardHeader>
        <CardTitle>Elevated Card</CardTitle>
        <CardDescription>With enhanced shadow.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card content with elevated variant.</p>
      </CardContent>
    </Card>
  ),
};

export const WithHover: Story = {
  render: () => (
    <Card hover="lift" className="w-[350px]">
      <CardHeader>
        <CardTitle>Interactive Card</CardTitle>
        <CardDescription>Hover to see the effect.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>This card lifts up on hover.</p>
      </CardContent>
    </Card>
  ),
};

export const Small: Story = {
  render: () => (
    <Card size="sm" className="w-[350px]">
      <CardHeader>
        <CardTitle>Small Card</CardTitle>
        <CardDescription>With reduced padding.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Compact card content.</p>
      </CardContent>
    </Card>
  ),
};

export const Large: Story = {
  render: () => (
    <Card size="lg" className="w-[350px]">
      <CardHeader>
        <CardTitle>Large Card</CardTitle>
        <CardDescription>With increased padding.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Spacious card content.</p>
      </CardContent>
    </Card>
  ),
}; 