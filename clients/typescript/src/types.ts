export interface Message {
  id: number;
  agentId: string;
  content: string;
  processed: boolean;
  role?: string;
  name?: string;
  registeredAt?: Date;
  processedAt?: Date;
  metadata?: Record<string, any>;
}

export interface FileRecord {
  id: number;
  agentId: string;
  filePath: string;
  fileHash: string;
  size: number;
  lastModified: Date;
  processed: boolean;
  label: string;
  description: string;
  registeredAt?: Date;
  processedAt?: Date;
}

export interface MessageCreate {
  content: string;
  role: string;
  name?: string;
  metadata?: Record<string, any>;
}

export interface DatabaseStats {
  totalMessages: number;
  processedMessages: number;
  unprocessedMessages: number;
  totalFiles: number;
  processedFiles: number;
  unprocessedFiles: number;
}

export interface RunStatus {
  id: string;
  status: string;
}

// Letta-specific types
export interface LettaMessage {
  role: string;
  content: Array<{
    type: string;
    text: string;
  }>;
}

export interface LettaRun {
  id: string;
  status: string;
}

export interface LettaBlock {
  id: string;
  label: string;
  description: string;
  value: string;
  limit?: number;
}

export interface LettaAgent {
  id: string;
  name: string;
  tags?: string[];
}