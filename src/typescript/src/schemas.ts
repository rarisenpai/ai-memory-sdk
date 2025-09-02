export interface Message {
  id: number;
  agent_id: string;
  content: string;
  processed: boolean;
  role?: string;
  name?: string;
  registered_at?: Date;
  processed_at?: Date;
  metadata?: Record<string, any>;
}

export interface File {
  id: number;
  agent_id: string;
  file_path: string;
  file_hash: string;
  size: number;
  last_modified: Date;
  processed: boolean;
  label: string;
  description: string;
  registered_at?: Date;
  processed_at?: Date;
}

export interface MessageCreate {
  content: string;
  role: string;
  name?: string;
  metadata?: Record<string, any>;
}