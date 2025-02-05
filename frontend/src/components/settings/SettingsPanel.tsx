import React, { useState } from 'react';
import { useAtom } from 'jotai';
import { cn } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { Label } from '../ui/Label';
import { Save, RotateCcw } from 'lucide-react';

interface PipelineConfig {
  batchSize: number;
  maxTokens: number;
  chunkOverlap: number;
  similarityThreshold: number;
  maxResults: number;
}

interface ModelParams {
  model: string;
  temperature: number;
  topP: number;
  frequencyPenalty: number;
  presencePenalty: number;
  maxTokens: number;
}

interface SystemPrefs {
  theme: 'light' | 'dark' | 'system';
  debug: boolean;
  autoSave: boolean;
  notifications: boolean;
}

interface SettingsPanelProps {
  className?: string;
  initialValues?: {
    pipeline: PipelineConfig;
    model: ModelParams;
    system: SystemPrefs;
  };
  onSave?: (settings: {
    pipeline: PipelineConfig;
    model: ModelParams;
    system: SystemPrefs;
  }) => Promise<void>;
  onReset?: () => Promise<void>;
}

export function SettingsPanel({
  className,
  initialValues,
  onSave,
  onReset,
}: SettingsPanelProps) {
  const [pipelineConfig, setPipelineConfig] = useState<PipelineConfig>(
    initialValues?.pipeline ?? {
      batchSize: 32,
      maxTokens: 500,
      chunkOverlap: 50,
      similarityThreshold: 0.7,
      maxResults: 10,
    }
  );

  const [modelParams, setModelParams] = useState<ModelParams>(
    initialValues?.model ?? {
      model: 'gpt-3.5-turbo',
      temperature: 0.7,
      topP: 1,
      frequencyPenalty: 0,
      presencePenalty: 0,
      maxTokens: 1000,
    }
  );

  const [systemPrefs, setSystemPrefs] = useState<SystemPrefs>(
    initialValues?.system ?? {
      theme: 'light',
      debug: false,
      autoSave: true,
      notifications: true,
    }
  );

  const handleSave = async () => {
    if (!onSave) return;

    try {
      await onSave({
        pipeline: pipelineConfig,
        model: modelParams,
        system: systemPrefs,
      });
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const handleReset = async () => {
    if (!onReset) return;

    try {
      await onReset();
      // Reset to default values would go here
    } catch (error) {
      console.error('Failed to reset settings:', error);
    }
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Pipeline Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="batchSize">Batch Size</Label>
              <Input
                id="batchSize"
                type="number"
                value={pipelineConfig.batchSize}
                onChange={(e) =>
                  setPipelineConfig(prev => ({
                    ...prev,
                    batchSize: parseInt(e.target.value),
                  }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="maxTokens">Max Tokens</Label>
              <Input
                id="maxTokens"
                type="number"
                value={pipelineConfig.maxTokens}
                onChange={(e) =>
                  setPipelineConfig(prev => ({
                    ...prev,
                    maxTokens: parseInt(e.target.value),
                  }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="chunkOverlap">Chunk Overlap</Label>
              <Input
                id="chunkOverlap"
                type="number"
                value={pipelineConfig.chunkOverlap}
                onChange={(e) =>
                  setPipelineConfig(prev => ({
                    ...prev,
                    chunkOverlap: parseInt(e.target.value),
                  }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="similarityThreshold">Similarity Threshold</Label>
              <Input
                id="similarityThreshold"
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={pipelineConfig.similarityThreshold}
                onChange={(e) =>
                  setPipelineConfig(prev => ({
                    ...prev,
                    similarityThreshold: parseFloat(e.target.value),
                  }))
                }
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Model Parameters */}
      <Card>
        <CardHeader>
          <CardTitle>Model Parameters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="model">Model</Label>
            <select
              id="model"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              value={modelParams.model}
              onChange={(e) =>
                setModelParams(prev => ({
                  ...prev,
                  model: e.target.value,
                }))
              }
            >
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="temperature">Temperature</Label>
              <Input
                id="temperature"
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={modelParams.temperature}
                onChange={(e) =>
                  setModelParams(prev => ({
                    ...prev,
                    temperature: parseFloat(e.target.value),
                  }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="topP">Top P</Label>
              <Input
                id="topP"
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={modelParams.topP}
                onChange={(e) =>
                  setModelParams(prev => ({
                    ...prev,
                    topP: parseFloat(e.target.value),
                  }))
                }
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Preferences */}
      <Card>
        <CardHeader>
          <CardTitle>System Preferences</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="theme">Theme</Label>
            <select
              id="theme"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              value={systemPrefs.theme}
              onChange={(e) =>
                setSystemPrefs(prev => ({
                  ...prev,
                  theme: e.target.value as SystemPrefs['theme'],
                }))
              }
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="system">System</option>
            </select>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="debug"
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              checked={systemPrefs.debug}
              onChange={(e) =>
                setSystemPrefs(prev => ({
                  ...prev,
                  debug: e.target.checked,
                }))
              }
            />
            <Label htmlFor="debug">Enable Debug Mode</Label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="autoSave"
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              checked={systemPrefs.autoSave}
              onChange={(e) =>
                setSystemPrefs(prev => ({
                  ...prev,
                  autoSave: e.target.checked,
                }))
              }
            />
            <Label htmlFor="autoSave">Auto-save Changes</Label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="notifications"
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              checked={systemPrefs.notifications}
              onChange={(e) =>
                setSystemPrefs(prev => ({
                  ...prev,
                  notifications: e.target.checked,
                }))
              }
            />
            <Label htmlFor="notifications">Enable Notifications</Label>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-2">
        <Button variant="outline" onClick={handleReset}>
          <RotateCcw className="w-4 h-4 mr-2" />
          Reset
        </Button>
        <Button onClick={handleSave}>
          <Save className="w-4 h-4 mr-2" />
          Save Changes
        </Button>
      </div>
    </div>
  );
} 