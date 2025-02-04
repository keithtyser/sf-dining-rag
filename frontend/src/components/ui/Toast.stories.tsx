import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';
import { ToastProvider } from './ToastProvider';
import { useToast } from '@/hooks/useToast';

const meta = {
  title: 'Components/Toast',
  component: ToastProvider,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof ToastProvider>;

export default meta;
type Story = StoryObj<typeof meta>;

const ToastDemo = () => {
  const { success, error, info, warning } = useToast();

  return (
    <div className="flex flex-col gap-4">
      <Button
        onClick={() =>
          success({
            title: 'Success Toast',
            description: 'Your action was completed successfully.',
          })
        }
      >
        Show Success Toast
      </Button>
      <Button
        variant="destructive"
        onClick={() =>
          error({
            title: 'Error Toast',
            description: 'There was a problem with your request.',
          })
        }
      >
        Show Error Toast
      </Button>
      <Button
        variant="secondary"
        onClick={() =>
          info({
            title: 'Info Toast',
            description: 'Here is some important information.',
          })
        }
      >
        Show Info Toast
      </Button>
      <Button
        variant="outline"
        onClick={() =>
          warning({
            title: 'Warning Toast',
            description: 'Please be careful with this action.',
          })
        }
      >
        Show Warning Toast
      </Button>
    </div>
  );
};

export const Default: Story = {
  args: {
    children: null,
  },
  render: () => (
    <ToastProvider>
      <ToastDemo />
    </ToastProvider>
  ),
};

export const WithAction: Story = {
  args: {
    children: null,
  },
  render: () => {
    const { addToast } = useToast();
    return (
      <ToastProvider>
        <Button
          onClick={() =>
            addToast({
              title: 'Action Required',
              description: 'Please confirm this action.',
              action: {
                label: 'Confirm',
                onClick: () => console.log('Action confirmed'),
              },
            })
          }
        >
          Show Toast with Action
        </Button>
      </ToastProvider>
    );
  },
};

export const LongDuration: Story = {
  args: {
    children: null,
  },
  render: () => {
    const { addToast } = useToast();
    return (
      <ToastProvider>
        <Button
          onClick={() =>
            addToast({
              title: 'Long Duration Toast',
              description: 'This toast will stay visible for 10 seconds.',
              duration: 10000,
            })
          }
        >
          Show Long Duration Toast
        </Button>
      </ToastProvider>
    );
  },
}; 