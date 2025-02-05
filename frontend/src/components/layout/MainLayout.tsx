import React from 'react';
import { useAtom } from 'jotai';
import { cn } from '@/lib/utils';
import { uiStateAtom } from '@/lib/atoms';
import { ConnectionStatus } from '../ui/ConnectionStatus';
import { StateDebugger } from '../debug/StateDebugger';

interface MainLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export function MainLayout({ children, className }: MainLayoutProps) {
  const [uiState] = useAtom(uiStateAtom);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="mr-4 flex">
            <a className="mr-6 flex items-center space-x-2" href="/">
              <span className="font-bold">RAG Pipeline</span>
            </a>
          </div>
          <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
            <nav className="flex items-center space-x-6">
              <ConnectionStatus />
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container flex-1 items-start md:grid md:grid-cols-[220px_minmax(0,1fr)] md:gap-6 lg:grid-cols-[240px_minmax(0,1fr)] lg:gap-10">
        {/* Sidebar */}
        <aside className={cn(
          "fixed top-14 z-30 -ml-2 hidden h-[calc(100vh-3.5rem)] w-full shrink-0 overflow-y-auto border-r md:sticky md:block",
          uiState.sidebarOpen ? "block" : "hidden md:block"
        )}>
          <div className="relative overflow-hidden py-6 pr-6 lg:py-8">
            <div className="space-y-4">
              <div className="px-3">
                <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight">
                  Pipeline
                </h2>
                <div className="space-y-1">
                  <a
                    href="#data-ingestion"
                    className="flex items-center rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
                  >
                    Data Ingestion
                  </a>
                  <a
                    href="#embedding"
                    className="flex items-center rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
                  >
                    Embedding
                  </a>
                  <a
                    href="#indexing"
                    className="flex items-center rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
                  >
                    Indexing
                  </a>
                </div>
              </div>
              <div className="px-3">
                <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight">
                  Visualization
                </h2>
                <div className="space-y-1">
                  <a
                    href="#vector-space"
                    className="flex items-center rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
                  >
                    Vector Space
                  </a>
                  <a
                    href="#metrics"
                    className="flex items-center rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
                  >
                    Metrics
                  </a>
                </div>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className={cn(
          "flex w-full flex-col overflow-hidden",
          className
        )}>
          {children}
        </main>
      </div>

      {/* Debug Panel */}
      {uiState.debug && (
        <div className="fixed bottom-4 right-4 z-50 w-96">
          <StateDebugger />
        </div>
      )}
    </div>
  );
} 