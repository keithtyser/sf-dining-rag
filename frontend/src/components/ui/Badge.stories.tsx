import type { Meta, StoryObj } from '@storybook/react';
import { Badge } from './Badge';

const meta = {
  title: 'UI/Badge',
  component: Badge,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: [
        'default',
        'secondary',
        'destructive',
        'outline',
        'success',
        'warning',
        'info',
        'ghost',
      ],
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg'],
    },
    isInteractive: {
      control: 'boolean',
    },
    withDot: {
      control: 'boolean',
    },
    dotColor: {
      control: 'color',
    },
  },
} satisfies Meta<typeof Badge>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: 'Badge',
  },
};

export const Secondary: Story = {
  args: {
    children: 'Secondary',
    variant: 'secondary',
  },
};

export const Destructive: Story = {
  args: {
    children: 'Destructive',
    variant: 'destructive',
  },
};

export const Outline: Story = {
  args: {
    children: 'Outline',
    variant: 'outline',
  },
};

export const Success: Story = {
  args: {
    children: 'Success',
    variant: 'success',
  },
};

export const Warning: Story = {
  args: {
    children: 'Warning',
    variant: 'warning',
  },
};

export const Info: Story = {
  args: {
    children: 'Info',
    variant: 'info',
  },
};

export const Ghost: Story = {
  args: {
    children: 'Ghost',
    variant: 'ghost',
  },
};

export const Small: Story = {
  args: {
    children: 'Small',
    size: 'sm',
  },
};

export const Large: Story = {
  args: {
    children: 'Large',
    size: 'lg',
  },
};

export const InteractiveSingle: Story = {
  args: {
    children: 'Interactive',
    isInteractive: true,
    onClick: () => alert('Badge clicked!'),
  },
};

export const WithDot: Story = {
  args: {
    children: 'Online',
    withDot: true,
    dotColor: '#22c55e',
  },
};

export const WithCustomDot: Story = {
  args: {
    children: 'Offline',
    variant: 'destructive',
    withDot: true,
    dotColor: '#ef4444',
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Badge>Default</Badge>
      <Badge variant="secondary">Secondary</Badge>
      <Badge variant="destructive">Destructive</Badge>
      <Badge variant="outline">Outline</Badge>
      <Badge variant="success">Success</Badge>
      <Badge variant="warning">Warning</Badge>
      <Badge variant="info">Info</Badge>
      <Badge variant="ghost">Ghost</Badge>
    </div>
  ),
};

export const AllSizes: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Badge size="sm">Small</Badge>
      <Badge>Default</Badge>
      <Badge size="lg">Large</Badge>
    </div>
  ),
};

export const WithDots: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Badge withDot dotColor="#22c55e">
        Online
      </Badge>
      <Badge variant="secondary" withDot dotColor="#f59e0b">
        Away
      </Badge>
      <Badge variant="destructive" withDot dotColor="#ef4444">
        Offline
      </Badge>
      <Badge variant="outline" withDot dotColor="#3b82f6">
        In Meeting
      </Badge>
    </div>
  ),
};

export const InteractiveGroup: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Badge isInteractive onClick={() => alert('Default clicked!')}>
        Click me
      </Badge>
      <Badge
        variant="success"
        isInteractive
        onClick={() => alert('Success clicked!')}
      >
        Click me
      </Badge>
      <Badge
        variant="warning"
        isInteractive
        onClick={() => alert('Warning clicked!')}
      >
        Click me
      </Badge>
      <Badge
        variant="destructive"
        isInteractive
        onClick={() => alert('Destructive clicked!')}
      >
        Click me
      </Badge>
    </div>
  ),
}; 