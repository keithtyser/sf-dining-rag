import type { Meta, StoryObj } from '@storybook/react';
import {
  Modal,
  ModalTrigger,
  ModalHeader,
  ModalFooter,
  ModalTitle,
  ModalDescription,
} from './Modal';
import { Button } from './Button';

const meta = {
  title: 'UI/Modal',
  component: Modal,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Modal>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Modal>
      <ModalTrigger asChild>
        <Button variant="default">Open Modal</Button>
      </ModalTrigger>
      <ModalHeader>
        <ModalTitle>Modal Title</ModalTitle>
        <ModalDescription>This is a description of the modal's purpose.</ModalDescription>
      </ModalHeader>
      <div className="py-4">
        <p>Modal content goes here. This can include any React components.</p>
      </div>
      <ModalFooter>
        <Button variant="outline">Cancel</Button>
        <Button>Continue</Button>
      </ModalFooter>
    </Modal>
  ),
};

export const Small: Story = {
  render: () => (
    <Modal size="sm">
      <ModalTrigger asChild>
        <Button variant="default">Open Small Modal</Button>
      </ModalTrigger>
      <ModalHeader>
        <ModalTitle>Small Modal</ModalTitle>
        <ModalDescription>A more compact modal dialog.</ModalDescription>
      </ModalHeader>
      <div className="py-4">
        <p>Content for a small modal dialog.</p>
      </div>
      <ModalFooter>
        <Button>Close</Button>
      </ModalFooter>
    </Modal>
  ),
};

export const Large: Story = {
  render: () => (
    <Modal size="lg">
      <ModalTrigger asChild>
        <Button variant="default">Open Large Modal</Button>
      </ModalTrigger>
      <ModalHeader>
        <ModalTitle>Large Modal</ModalTitle>
        <ModalDescription>A more spacious modal dialog for complex content.</ModalDescription>
      </ModalHeader>
      <div className="py-4">
        <p>Content for a large modal dialog. This can include tables, forms, or other complex UI elements.</p>
        <div className="mt-4 grid gap-4">
          <p>Additional content can go here...</p>
          <p>More content...</p>
        </div>
      </div>
      <ModalFooter>
        <Button variant="outline">Cancel</Button>
        <Button>Save Changes</Button>
      </ModalFooter>
    </Modal>
  ),
};

export const NoCloseButton: Story = {
  render: () => (
    <Modal showClose={false}>
      <ModalTrigger asChild>
        <Button variant="default">Modal without Close Button</Button>
      </ModalTrigger>
      <ModalHeader>
        <ModalTitle>No Close Button</ModalTitle>
        <ModalDescription>This modal doesn't show the close button in the corner.</ModalDescription>
      </ModalHeader>
      <div className="py-4">
        <p>Modal content without a close button in the corner.</p>
      </div>
      <ModalFooter>
        <Button>Close</Button>
      </ModalFooter>
    </Modal>
  ),
};

export const CustomContent: Story = {
  render: () => (
    <Modal>
      <ModalTrigger asChild>
        <Button variant="default">Custom Content Modal</Button>
      </ModalTrigger>
      <div className="grid gap-4">
        <img
          src="https://via.placeholder.com/400x200"
          alt="Example"
          className="rounded-lg object-cover"
        />
        <ModalHeader>
          <ModalTitle>Custom Content</ModalTitle>
          <ModalDescription>A modal with custom content layout.</ModalDescription>
        </ModalHeader>
        <div className="grid gap-2">
          <p>Custom content can include images, forms, or any other components.</p>
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-lg border p-2">Panel 1</div>
            <div className="rounded-lg border p-2">Panel 2</div>
          </div>
        </div>
        <ModalFooter>
          <Button variant="outline">Cancel</Button>
          <Button>Save</Button>
        </ModalFooter>
      </div>
    </Modal>
  ),
}; 