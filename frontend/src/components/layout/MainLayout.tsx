"use client";

import { Button } from '@/components/ui/Button';
import { Settings, Menu, Sun, Moon, Compass } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { cn } from '@/lib/utils';

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const [showSidebar, setShowSidebar] = useState(false);
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // After mounting, we have access to the theme
  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="relative flex h-screen flex-col overflow-hidden">
      {/* Dynamic SF-themed background */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-[hsl(var(--sf-fog))] opacity-20 animate-fog" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background to-background" />
      </div>

      {/* Header */}
      <header className="sf-glass sticky top-0 z-50 border-b px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Compass className="h-6 w-6 sf-icon animate-bridge" />
            <h1 className="sf-heading text-lg">SF Dining Guide</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="hover:bg-[hsl(var(--sf-golden-gate))]/10"
            >
              {mounted && (
                theme === 'dark' ? (
                  <Sun className="h-5 w-5" />
                ) : (
                  <Moon className="h-5 w-5" />
                )
              )}
            </Button>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <div className={cn(
        "fixed inset-y-0 left-0 z-40 w-64 transform sf-glass border-r transition-transform duration-300 ease-out",
        showSidebar ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex h-full flex-col p-4">
          <div className="flex items-center justify-between border-b pb-4">
            <h2 className="sf-heading">Explore SF</h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowSidebar(false)}
              className="hover:bg-[hsl(var(--sf-golden-gate))]/10"
            >
              <Menu className="h-5 w-5" />
            </Button>
          </div>
          {/* Add sidebar content here */}
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <div className="h-full p-4">
          <div className="h-full rounded-lg">
            {children}
          </div>
        </div>
      </main>

      {/* Backdrop */}
      {showSidebar && (
        <div
          className="fixed inset-0 z-30 bg-background/80 backdrop-blur-sm transition-opacity duration-300"
          onClick={() => setShowSidebar(false)}
        />
      )}
    </div>
  );
} 