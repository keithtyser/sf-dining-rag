import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';
import { Mail, Send, Loader2, Github } from 'lucide-react';

const meta = {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link', 'success', 'warning', 'info'],
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg', 'icon', 'xl'],
    },
    isLoading: {
      control: 'boolean',
    },
    isFullWidth: {
      control: 'boolean',
    },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: 'Button',
    variant: 'default',
  },
};

export const WithIcon: Story = {
  args: {
    children: 'Send Email',
    leftIcon: <Mail className="h-4 w-4" />,
  },
};

export const WithRightIcon: Story = {
  args: {
    children: 'Send Message',
    rightIcon: <Send className="h-4 w-4" />,
  },
};

export const Loading: Story = {
  args: {
    children: 'Loading',
    isLoading: true,
    loadingText: 'Sending...',
  },
};

export const LoadingWithoutText: Story = {
  args: {
    children: 'Submit',
    isLoading: true,
  },
};

export const IconButton: Story = {
  args: {
    size: 'icon',
    isIcon: true,
    children: <Github className="h-4 w-4" />,
    'aria-label': 'Github',
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

export const Large: Story = {
  args: {
    children: 'Large Button',
    size: 'lg',
  },
};

export const Small: Story = {
  args: {
    children: 'Small Button',
    size: 'sm',
  },
};

export const ExtraLarge: Story = {
  args: {
    children: 'Extra Large Button',
    size: 'xl',
  },
};

export const FullWidth: Story = {
  args: {
    children: 'Full Width Button',
    isFullWidth: true,
  },
};

export const Destructive: Story = {
  args: {
    children: 'Delete',
    variant: 'destructive',
  },
};

export const Outline: Story = {
  args: {
    children: 'Outline',
    variant: 'outline',
  },
};

export const Ghost: Story = {
  args: {
    children: 'Ghost',
    variant: 'ghost',
  },
};

export const Link: Story = {
  args: {
    children: 'Link Button',
    variant: 'link',
  },
};

export const AsChild: Story = {
  args: {
    asChild: true,
    children: <a href="https://github.com">Github Link</a>,
  },
};

export const ButtonGroup: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Button variant="outline" size="sm">
        Back
      </Button>
      <Button>Save Changes</Button>
      <Button variant="success" size="sm">
        Publish
      </Button>
    </div>
  ),
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-4">
        <Button>Default</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="destructive">Destructive</Button>
        <Button variant="outline">Outline</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="link">Link</Button>
        <Button variant="success">Success</Button>
        <Button variant="warning">Warning</Button>
        <Button variant="info">Info</Button>
      </div>
      <div className="flex flex-wrap items-center gap-4">
        <Button size="sm">Small</Button>
        <Button>Default</Button>
        <Button size="lg">Large</Button>
        <Button size="xl">Extra Large</Button>
        <Button size="icon" isIcon>
          <Mail className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex flex-wrap items-center gap-4">
        <Button isLoading>Loading</Button>
        <Button isLoading loadingText="Saving...">
          Save
        </Button>
        <Button leftIcon={<Mail className="h-4 w-4" />}>With Icon</Button>
        <Button rightIcon={<Send className="h-4 w-4" />}>Send</Button>
      </div>
    </div>
  ),
}; 