import Database from 'better-sqlite3';
import { createHash } from 'crypto';
import { readFileSync, statSync } from 'fs';
import { resolve } from 'path';
import type { Message, FileRecord, MessageCreate, DatabaseStats } from './types.js';

export class SubconsciousDatabase {
  private db: Database.Database;

  constructor(dbPath: string = 'subconscious.db') {
    this.db = new Database(dbPath);
    this.initDatabase();
  }

  private initDatabase(): void {
    // Table for registered messages
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        message_hash TEXT NOT NULL,
        content TEXT NOT NULL,
        role TEXT NOT NULL,
        name TEXT,
        metadata TEXT,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed BOOLEAN DEFAULT FALSE,
        processed_at TIMESTAMP NULL,
        UNIQUE(agent_id, message_hash)
      )
    `);

    // Table for registered files
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_hash TEXT NOT NULL,
        size INTEGER,
        last_modified TIMESTAMP,
        label TEXT NOT NULL,
        description TEXT NOT NULL,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed BOOLEAN DEFAULT FALSE,
        processed_at TIMESTAMP NULL,
        UNIQUE(agent_id, file_path, file_hash)
      )
    `);

    // Create indexes
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_messages_agent_hash ON messages(agent_id, message_hash);
      CREATE INDEX IF NOT EXISTS idx_messages_agent_processed ON messages(agent_id, processed);
      CREATE INDEX IF NOT EXISTS idx_files_agent_path ON files(agent_id, file_path);
      CREATE INDEX IF NOT EXISTS idx_files_agent_processed ON files(agent_id, processed);
    `);
  }

  private getMessageHash(message: MessageCreate): string {
    const messageStr = JSON.stringify(message, Object.keys(message).sort());
    return createHash('sha256').update(messageStr).digest('hex');
  }

  private getFileHash(filePath: string): string {
    try {
      const content = readFileSync(filePath);
      return createHash('sha256').update(content).digest('hex');
    } catch (error) {
      return '';
    }
  }

  registerMessages(agentId: string, messages: MessageCreate[]): number {
    let registeredCount = 0;
    const insertMessage = this.db.prepare(`
      INSERT INTO messages (agent_id, message_hash, content, role, name, metadata)
      VALUES (?, ?, ?, ?, ?, ?)
    `);

    for (const message of messages) {
      const messageHash = this.getMessageHash(message);
      const metadataJson = message.metadata ? JSON.stringify(message.metadata) : null;

      try {
        insertMessage.run(
          agentId,
          messageHash,
          message.content,
          message.role,
          message.name || null,
          metadataJson
        );
        registeredCount++;
      } catch (error) {
        // Message already exists for this agent (UNIQUE constraint violation)
        continue;
      }
    }

    return registeredCount;
  }

  registerFile(agentId: string, filePath: string, label: string, description: string): boolean {
    const absolutePath = resolve(filePath);
    
    try {
      const stats = statSync(absolutePath);
      const fileHash = this.getFileHash(absolutePath);

      // Check if file already registered with same hash
      const existing = this.db.prepare(`
        SELECT id FROM files WHERE agent_id = ? AND file_path = ? AND file_hash = ?
      `).get(agentId, absolutePath, fileHash);

      if (existing) {
        return false;
      }

      // Register new file or update if content changed
      const insertFile = this.db.prepare(`
        INSERT OR REPLACE INTO files (agent_id, file_path, file_hash, size, last_modified, label, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `);

      insertFile.run(
        agentId,
        absolutePath,
        fileHash,
        stats.size,
        stats.mtime.toISOString(),
        label,
        description
      );

      return true;
    } catch (error) {
      throw new Error(`File not found: ${filePath}`);
    }
  }

  getUnprocessedMessages(agentId: string): Message[] {
    const query = this.db.prepare(`
      SELECT id, agent_id, content, role, name, metadata, registered_at, processed_at
      FROM messages
      WHERE agent_id = ? AND processed = FALSE
      ORDER BY registered_at ASC
    `);

    const rows = query.all(agentId) as any[];
    return rows.map(row => ({
      id: row.id,
      agentId: row.agent_id,
      content: row.content,
      processed: false,
      role: row.role,
      name: row.name,
      registeredAt: row.registered_at ? new Date(row.registered_at) : undefined,
      processedAt: row.processed_at ? new Date(row.processed_at) : undefined,
      metadata: row.metadata ? JSON.parse(row.metadata) : undefined
    }));
  }

  getUnprocessedFiles(agentId: string): FileRecord[] {
    const query = this.db.prepare(`
      SELECT id, agent_id, file_path, file_hash, size, last_modified, label, description, registered_at, processed_at
      FROM files
      WHERE agent_id = ? AND processed = FALSE
      ORDER BY registered_at ASC
    `);

    const rows = query.all(agentId) as any[];
    return rows.map(row => ({
      id: row.id,
      agentId: row.agent_id,
      filePath: row.file_path,
      fileHash: row.file_hash,
      size: row.size,
      lastModified: new Date(row.last_modified),
      processed: false,
      label: row.label,
      description: row.description,
      registeredAt: row.registered_at ? new Date(row.registered_at) : undefined,
      processedAt: row.processed_at ? new Date(row.processed_at) : undefined
    }));
  }

  markMessagesProcessed(messageIds: number[]): void {
    if (messageIds.length === 0) return;
    
    const placeholders = messageIds.map(() => '?').join(',');
    const query = this.db.prepare(`
      UPDATE messages SET processed = TRUE, processed_at = CURRENT_TIMESTAMP
      WHERE id IN (${placeholders})
    `);
    
    query.run(...messageIds);
  }

  markFilesProcessed(fileIds: number[]): void {
    if (fileIds.length === 0) return;
    
    const placeholders = fileIds.map(() => '?').join(',');
    const query = this.db.prepare(`
      UPDATE files SET processed = TRUE, processed_at = CURRENT_TIMESTAMP
      WHERE id IN (${placeholders})
    `);
    
    query.run(...fileIds);
  }

  resetProcessingStatus(agentId: string): void {
    this.db.prepare('UPDATE messages SET processed = FALSE, processed_at = NULL WHERE agent_id = ?').run(agentId);
    this.db.prepare('UPDATE files SET processed = FALSE, processed_at = NULL WHERE agent_id = ?').run(agentId);
  }

  getStats(agentId: string): DatabaseStats {
    const totalMessages = (this.db.prepare('SELECT COUNT(*) as count FROM messages WHERE agent_id = ?').get(agentId) as any).count;
    const processedMessages = (this.db.prepare('SELECT COUNT(*) as count FROM messages WHERE agent_id = ? AND processed = TRUE').get(agentId) as any).count;
    const totalFiles = (this.db.prepare('SELECT COUNT(*) as count FROM files WHERE agent_id = ?').get(agentId) as any).count;
    const processedFiles = (this.db.prepare('SELECT COUNT(*) as count FROM files WHERE agent_id = ? AND processed = TRUE').get(agentId) as any).count;

    return {
      totalMessages,
      processedMessages,
      unprocessedMessages: totalMessages - processedMessages,
      totalFiles,
      processedFiles,
      unprocessedFiles: totalFiles - processedFiles
    };
  }

  close(): void {
    this.db.close();
  }
}