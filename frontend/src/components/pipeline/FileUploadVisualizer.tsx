import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { cn } from '@/lib/utils';
import { Card } from '../ui/Card';
import { Progress } from '../ui/Progress';
import { FileText, Upload, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '../ui/Button';

interface FileStats {
  fileName: string;
  fileSize: number;
  mimeType: string;
  chunks: number;
  tokens: number;
  characters: number;
}

interface FileUploadVisualizerProps {
  onFileAccepted?: (file: File) => Promise<void>;
  onProcessingComplete?: (stats: FileStats) => void;
  className?: string;
  acceptedFileTypes?: string[];
  maxFileSize?: number;
}

export function FileUploadVisualizer({
  onFileAccepted,
  onProcessingComplete,
  className,
  acceptedFileTypes = ['.txt', '.md', '.pdf', '.doc', '.docx'],
  maxFileSize = 10 * 1024 * 1024, // 10MB
}: FileUploadVisualizerProps) {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStage, setProcessingStage] = useState<
    'idle' | 'uploading' | 'processing' | 'complete' | 'error'
  >('idle');
  const [error, setError] = useState<string | null>(null);
  const [fileStats, setFileStats] = useState<FileStats | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      try {
        setProcessingStage('uploading');
        setError(null);

        // Simulate upload progress
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => {
            if (prev >= 90) {
              clearInterval(progressInterval);
              return prev;
            }
            return prev + 10;
          });
        }, 200);

        // Process the file
        if (onFileAccepted) {
          await onFileAccepted(file);
        }

        clearInterval(progressInterval);
        setUploadProgress(100);
        setProcessingStage('processing');

        // Simulate file processing and stats generation
        const stats: FileStats = {
          fileName: file.name,
          fileSize: file.size,
          mimeType: file.type,
          chunks: Math.ceil(file.size / 1000), // Simulated chunk size
          tokens: Math.ceil(file.size / 4), // Simulated token count
          characters: file.size, // Simulated character count
        };

        setTimeout(() => {
          setFileStats(stats);
          setProcessingStage('complete');
          if (onProcessingComplete) {
            onProcessingComplete(stats);
          }
        }, 1000);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to process file');
        setProcessingStage('error');
      }
    },
    [onFileAccepted, onProcessingComplete]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedFileTypes.reduce(
      (acc, type) => ({ ...acc, [type]: [] }),
      {} as Record<string, string[]>
    ),
    maxSize: maxFileSize,
    multiple: false,
  });

  return (
    <div className={cn('space-y-4', className)}>
      <Card
        {...getRootProps()}
        className={cn(
          'cursor-pointer transition-colors',
          isDragActive && 'border-primary/50 bg-primary/5',
          processingStage !== 'idle' && 'pointer-events-none opacity-50'
        )}
      >
        <div className="flex flex-col items-center justify-center gap-4 p-8">
          <input {...getInputProps()} />
          <Upload className="h-12 w-12 text-muted-foreground" />
          <div className="text-center">
            <p className="text-lg font-medium">Drop your file here</p>
            <p className="text-sm text-muted-foreground">
              or click to select a file
            </p>
          </div>
          <div className="text-xs text-muted-foreground">
            Accepted files: {acceptedFileTypes.join(', ')} (max {maxFileSize / 1024 / 1024}MB)
          </div>
        </div>
      </Card>

      {processingStage !== 'idle' && (
        <Card className="p-4">
          <div className="space-y-4">
            {fileStats && (
              <div className="flex items-start gap-4">
                <FileText className="h-8 w-8 text-primary" />
                <div className="flex-1">
                  <h3 className="font-medium">{fileStats.fileName}</h3>
                  <div className="mt-1 grid grid-cols-2 gap-2 text-sm text-muted-foreground">
                    <div>Size: {(fileStats.fileSize / 1024).toFixed(2)}KB</div>
                    <div>Type: {fileStats.mimeType || 'Unknown'}</div>
                    <div>Chunks: {fileStats.chunks}</div>
                    <div>Tokens: {fileStats.tokens}</div>
                    <div>Characters: {fileStats.characters}</div>
                  </div>
                </div>
                {processingStage === 'complete' ? (
                  <CheckCircle className="h-6 w-6 text-green-500" />
                ) : processingStage === 'error' ? (
                  <AlertCircle className="h-6 w-6 text-destructive" />
                ) : null}
              </div>
            )}

            {processingStage === 'uploading' && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Uploading...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} />
              </div>
            )}

            {processingStage === 'processing' && (
              <div className="text-sm">Processing file...</div>
            )}

            {error && (
              <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            {processingStage === 'complete' && (
              <Button
                onClick={() => {
                  setProcessingStage('idle');
                  setUploadProgress(0);
                  setFileStats(null);
                  setError(null);
                }}
              >
                Upload Another File
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
} 