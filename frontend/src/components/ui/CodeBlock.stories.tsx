import type { Meta, StoryObj } from '@storybook/react';
import { CodeBlock } from './CodeBlock';

const meta = {
  title: 'UI/CodeBlock',
  component: CodeBlock,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof CodeBlock>;

export default meta;
type Story = StoryObj<typeof meta>;

const sampleTypeScript = `interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
}

function getUser(id: string): Promise<User> {
  return fetch(\`/api/users/\${id}\`)
    .then(res => res.json());
}`;

const samplePython = `def process_documents(documents: List[str]) -> List[Dict[str, Any]]:
    """
    Process a list of documents and return their embeddings.
    
    Args:
        documents: List of document strings to process
        
    Returns:
        List of dictionaries containing document metadata and embeddings
    """
    results = []
    for doc in documents:
        # Preprocess the document
        cleaned = preprocess_text(doc)
        
        # Generate embeddings
        embedding = model.encode(cleaned)
        
        results.append({
            "text": doc,
            "embedding": embedding,
            "length": len(cleaned)
        })
    
    return results`;

export const Default: Story = {
  args: {
    code: sampleTypeScript,
    language: 'typescript',
  },
};

export const WithLineNumbers: Story = {
  args: {
    code: sampleTypeScript,
    language: 'typescript',
    showLineNumbers: true,
  },
};

export const WithHighlightedLines: Story = {
  args: {
    code: sampleTypeScript,
    language: 'typescript',
    showLineNumbers: true,
    highlightLines: [1, 2, 3, 4],
  },
};

export const Python: Story = {
  args: {
    code: samplePython,
    language: 'python',
    showLineNumbers: true,
    caption: 'Document processing function with type hints',
  },
};

export const Ghost: Story = {
  args: {
    code: sampleTypeScript,
    language: 'typescript',
    variant: 'ghost',
  },
};

export const Small: Story = {
  args: {
    code: sampleTypeScript,
    language: 'typescript',
    size: 'sm',
  },
};

export const Large: Story = {
  args: {
    code: sampleTypeScript,
    language: 'typescript',
    size: 'lg',
  },
}; 