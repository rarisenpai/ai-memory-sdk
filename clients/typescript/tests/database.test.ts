import { SubconsciousDatabase } from '../src/database';
import { writeFileSync, unlinkSync, existsSync } from 'fs';
import { join } from 'path';
import type { MessageCreate } from '../src/types';

describe('SubconsciousDatabase', () => {
  const testDbPath = 'test_subconscious.db';
  const testFilePath = join(__dirname, 'test_file.txt');
  let db: SubconsciousDatabase;

  beforeEach(() => {
    // Remove existing test database
    if (existsSync(testDbPath)) {
      unlinkSync(testDbPath);
    }
    
    // Create test file
    writeFileSync(testFilePath, 'Test file content for database testing');
    
    db = new SubconsciousDatabase(testDbPath);
  });

  afterEach(() => {
    db.close();
    
    // Clean up test files
    if (existsSync(testDbPath)) {
      unlinkSync(testDbPath);
    }
    if (existsSync(testFilePath)) {
      unlinkSync(testFilePath);
    }
  });

  describe('registerMessages', () => {
    it('should register new messages', () => {
      const agentId = 'test-agent-1';
      const messages: MessageCreate[] = [
        { content: 'Hello', role: 'user' },
        { content: 'Hi there!', role: 'assistant' }
      ];

      const count = db.registerMessages(agentId, messages);
      expect(count).toBe(2);
    });

    it('should not register duplicate messages', () => {
      const agentId = 'test-agent-1';
      const messages: MessageCreate[] = [
        { content: 'Hello', role: 'user' }
      ];

      const count1 = db.registerMessages(agentId, messages);
      const count2 = db.registerMessages(agentId, messages);
      
      expect(count1).toBe(1);
      expect(count2).toBe(0);
    });

    it('should register messages with metadata', () => {
      const agentId = 'test-agent-1';
      const messages: MessageCreate[] = [
        { 
          content: 'Hello', 
          role: 'user',
          name: 'John',
          metadata: { timestamp: '2024-01-01', source: 'chat' }
        }
      ];

      const count = db.registerMessages(agentId, messages);
      expect(count).toBe(1);

      const unprocessed = db.getUnprocessedMessages(agentId);
      expect(unprocessed).toHaveLength(1);
      expect(unprocessed[0].name).toBe('John');
      expect(unprocessed[0].metadata).toEqual({ timestamp: '2024-01-01', source: 'chat' });
    });
  });

  describe('registerFile', () => {
    it('should register a new file', () => {
      const agentId = 'test-agent-1';
      const label = 'Test File';
      const description = 'A test file for unit testing';

      const result = db.registerFile(agentId, testFilePath, label, description);
      expect(result).toBe(true);
    });

    it('should not register the same file twice', () => {
      const agentId = 'test-agent-1';
      const label = 'Test File';
      const description = 'A test file for unit testing';

      const result1 = db.registerFile(agentId, testFilePath, label, description);
      const result2 = db.registerFile(agentId, testFilePath, label, description);
      
      expect(result1).toBe(true);
      expect(result2).toBe(false);
    });

    it('should throw error for non-existent file', () => {
      const agentId = 'test-agent-1';
      const nonExistentPath = 'non-existent-file.txt';

      expect(() => {
        db.registerFile(agentId, nonExistentPath, 'label', 'description');
      }).toThrow('File not found');
    });
  });

  describe('getUnprocessedMessages', () => {
    it('should return unprocessed messages', () => {
      const agentId = 'test-agent-1';
      const messages: MessageCreate[] = [
        { content: 'Message 1', role: 'user' },
        { content: 'Message 2', role: 'assistant' }
      ];

      db.registerMessages(agentId, messages);
      const unprocessed = db.getUnprocessedMessages(agentId);
      
      expect(unprocessed).toHaveLength(2);
      expect(unprocessed[0].content).toBe('Message 1');
      expect(unprocessed[1].content).toBe('Message 2');
    });

    it('should not return processed messages', () => {
      const agentId = 'test-agent-1';
      const messages: MessageCreate[] = [
        { content: 'Message 1', role: 'user' }
      ];

      db.registerMessages(agentId, messages);
      const unprocessed1 = db.getUnprocessedMessages(agentId);
      
      db.markMessagesProcessed([unprocessed1[0].id]);
      const unprocessed2 = db.getUnprocessedMessages(agentId);
      
      expect(unprocessed1).toHaveLength(1);
      expect(unprocessed2).toHaveLength(0);
    });
  });

  describe('getUnprocessedFiles', () => {
    it('should return unprocessed files', () => {
      const agentId = 'test-agent-1';
      
      db.registerFile(agentId, testFilePath, 'Test File', 'Test description');
      const unprocessed = db.getUnprocessedFiles(agentId);
      
      expect(unprocessed).toHaveLength(1);
      expect(unprocessed[0].label).toBe('Test File');
      expect(unprocessed[0].description).toBe('Test description');
    });
  });

  describe('markMessagesProcessed', () => {
    it('should mark messages as processed', () => {
      const agentId = 'test-agent-1';
      const messages: MessageCreate[] = [
        { content: 'Message 1', role: 'user' }
      ];

      db.registerMessages(agentId, messages);
      const unprocessed = db.getUnprocessedMessages(agentId);
      
      db.markMessagesProcessed([unprocessed[0].id]);
      const stillUnprocessed = db.getUnprocessedMessages(agentId);
      
      expect(stillUnprocessed).toHaveLength(0);
    });
  });

  describe('resetProcessingStatus', () => {
    it('should reset all items to unprocessed', () => {
      const agentId = 'test-agent-1';
      const messages: MessageCreate[] = [
        { content: 'Message 1', role: 'user' }
      ];

      db.registerMessages(agentId, messages);
      db.registerFile(agentId, testFilePath, 'Test File', 'Test description');
      
      const unprocessed1 = db.getUnprocessedMessages(agentId);
      const unprocessedFiles1 = db.getUnprocessedFiles(agentId);
      
      db.markMessagesProcessed([unprocessed1[0].id]);
      db.markFilesProcessed([unprocessedFiles1[0].id]);
      
      db.resetProcessingStatus(agentId);
      
      const unprocessed2 = db.getUnprocessedMessages(agentId);
      const unprocessedFiles2 = db.getUnprocessedFiles(agentId);
      
      expect(unprocessed2).toHaveLength(1);
      expect(unprocessedFiles2).toHaveLength(1);
    });
  });

  describe('getStats', () => {
    it('should return correct statistics', () => {
      const agentId = 'test-agent-1';
      const messages: MessageCreate[] = [
        { content: 'Message 1', role: 'user' },
        { content: 'Message 2', role: 'assistant' }
      ];

      db.registerMessages(agentId, messages);
      db.registerFile(agentId, testFilePath, 'Test File', 'Test description');
      
      const unprocessed = db.getUnprocessedMessages(agentId);
      db.markMessagesProcessed([unprocessed[0].id]);
      
      const stats = db.getStats(agentId);
      
      expect(stats.totalMessages).toBe(2);
      expect(stats.processedMessages).toBe(1);
      expect(stats.unprocessedMessages).toBe(1);
      expect(stats.totalFiles).toBe(1);
      expect(stats.processedFiles).toBe(0);
      expect(stats.unprocessedFiles).toBe(1);
    });
  });
});