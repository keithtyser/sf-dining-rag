import type { Meta, StoryObj } from '@storybook/react';
import { DataTable } from './DataTable';
import { ColumnDef } from '@tanstack/react-table';

interface Document {
  id: string;
  title: string;
  type: string;
  tokens: number;
  similarity: number;
}

const columns: ColumnDef<Document, unknown>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
  },
  {
    accessorKey: 'title',
    header: 'Title',
  },
  {
    accessorKey: 'type',
    header: 'Type',
  },
  {
    accessorKey: 'tokens',
    header: 'Tokens',
  },
  {
    accessorKey: 'similarity',
    header: 'Similarity',
    cell: ({ row }) => {
      const similarity = row.getValue('similarity') as number;
      return `${(similarity * 100).toFixed(2)}%`;
    },
  },
];

const data: Document[] = [
  {
    id: 'doc1',
    title: 'Introduction to RAG',
    type: 'markdown',
    tokens: 150,
    similarity: 0.95,
  },
  {
    id: 'doc2',
    title: 'Vector Databases',
    type: 'pdf',
    tokens: 300,
    similarity: 0.85,
  },
  {
    id: 'doc3',
    title: 'Embeddings Guide',
    type: 'markdown',
    tokens: 200,
    similarity: 0.78,
  },
  {
    id: 'doc4',
    title: 'Performance Tuning',
    type: 'pdf',
    tokens: 450,
    similarity: 0.72,
  },
  {
    id: 'doc5',
    title: 'API Documentation',
    type: 'markdown',
    tokens: 180,
    similarity: 0.68,
  },
  {
    id: 'doc6',
    title: 'Best Practices',
    type: 'pdf',
    tokens: 280,
    similarity: 0.65,
  },
  {
    id: 'doc7',
    title: 'Getting Started',
    type: 'markdown',
    tokens: 120,
    similarity: 0.62,
  },
  {
    id: 'doc8',
    title: 'Advanced Topics',
    type: 'pdf',
    tokens: 500,
    similarity: 0.58,
  },
  {
    id: 'doc9',
    title: 'Troubleshooting',
    type: 'markdown',
    tokens: 250,
    similarity: 0.55,
  },
  {
    id: 'doc10',
    title: 'Security Guide',
    type: 'pdf',
    tokens: 350,
    similarity: 0.52,
  },
  {
    id: 'doc11',
    title: 'Deployment Guide',
    type: 'markdown',
    tokens: 220,
    similarity: 0.48,
  },
  {
    id: 'doc12',
    title: 'Architecture Overview',
    type: 'pdf',
    tokens: 400,
    similarity: 0.45,
  },
];

type DataTableType = typeof DataTable<Document, unknown>;

const meta = {
  title: 'UI/DataTable',
  component: DataTable as DataTableType,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<DataTableType>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    columns,
    data,
  },
};

export const WithFilters: Story = {
  args: {
    columns,
    data,
    showFilters: true,
  },
};

export const CustomPageSize: Story = {
  args: {
    columns,
    data,
    pageSize: 5,
  },
}; 