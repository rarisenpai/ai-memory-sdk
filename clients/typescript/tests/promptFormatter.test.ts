import { formatMessages, formatFiles } from '../src/promptFormatter';
import { writeFileSync, unlinkSync, existsSync } from 'fs';
import { join } from 'path';
import type { Message, FileRecord } from '../src/types';

describe('Prompt Formatter', () => {
  const testFilePath = join(__dirname, 'test_format_file.txt');

  beforeAll(() => {
    // Create test file
    writeFileSync(testFilePath, 'This is test content for prompt formatting');
  });

  afterAll(() => {
    // Clean up test file
    if (existsSync(testFilePath)) {
      unlinkSync(testFilePath);
    }
  });

  describe('formatMessages', () => {
    it('should format messages correctly', () => {
      const messages: Message[] = [
        {
          id: 1,
          agentId: 'test-agent',
          content: 'Hello',
          role: 'user',
          processed: false
        },
        {
          id: 2,
          agentId: 'test-agent',
          content: 'Hi there!',
          role: 'assistant',
          processed: false
        }
      ];

      const formatted = formatMessages(messages);
      
      expect(formatted).toHaveLength(1);
      expect(formatted[0].role).toBe('user');
      expect(formatted[0].content).toContain('<messages>');
      expect(formatted[0].content).toContain('user: Hello');
      expect(formatted[0].content).toContain('assistant: Hi there!');
      expect(formatted[0].content).toContain('</messages>');
    });

    it('should handle empty messages array', () => {
      const messages: Message[] = [];
      const formatted = formatMessages(messages);
      
      expect(formatted).toHaveLength(1);
      expect(formatted[0].content).toContain('<messages>');
      expect(formatted[0].content).toContain('</messages>');
    });

    it('should handle messages with names', () => {
      const messages: Message[] = [
        {
          id: 1,
          agentId: 'test-agent',
          content: 'Hello',
          role: 'user',
          name: 'John',
          processed: false
        }
      ];

      const formatted = formatMessages(messages);
      
      expect(formatted[0].content).toContain('user: Hello');
    });
  });

  describe('formatFiles', () => {
    it('should format single file correctly', () => {
      const files: FileRecord[] = [
        {
          id: 1,
          agentId: 'test-agent',
          filePath: testFilePath,
          fileHash: 'test-hash',
          size: 100,
          lastModified: new Date(),
          processed: false,
          label: 'Test File',
          description: 'A test file'
        }
      ];

      const formatted = formatFiles(files);
      
      expect(formatted).toHaveLength(1);
      expect(formatted[0].role).toBe('user');
      expect(formatted[0].content).toContain('<file label="Test File" description="A test file">');
      expect(formatted[0].content).toContain('<file_part part=1/1>');
      expect(formatted[0].content).toContain('This is test content for prompt formatting');
      expect(formatted[0].content).toContain('</file_part>');
      expect(formatted[0].content).toContain('</file>');
    });

    it('should handle large files by chunking', () => {
      // Create a large file
      const largeFilePath = join(__dirname, 'large_test_file.txt');
      const largeContent = 'A'.repeat(25000); // Larger than FILE_CHAR_LIMIT
      writeFileSync(largeFilePath, largeContent);

      try {
        const files: FileRecord[] = [
          {
            id: 1,
            agentId: 'test-agent',
            filePath: largeFilePath,
            fileHash: 'test-hash',
            size: largeContent.length,
            lastModified: new Date(),
            processed: false,
            label: 'Large File',
            description: 'A large test file'
          }
        ];

        const formatted = formatFiles(files);
        
        // Should be split into multiple messages
        expect(formatted.length).toBeGreaterThan(1);
        
        // First chunk should contain part 1/2
        expect(formatted[0].content).toContain('<file_part part=1/');
        
        // Last chunk should contain the final part
        const lastMessage = formatted[formatted.length - 1];
        expect(lastMessage.content).toContain(`part=${formatted.length}/${formatted.length}`);
        
      } finally {
        unlinkSync(largeFilePath);
      }
    });

    it('should handle non-existent files gracefully', () => {
      const files: FileRecord[] = [
        {
          id: 1,
          agentId: 'test-agent',
          filePath: 'non-existent-file.txt',
          fileHash: 'test-hash',
          size: 0,
          lastModified: new Date(),
          processed: false,
          label: 'Missing File',
          description: 'A missing test file'
        }
      ];

      const formatted = formatFiles(files);
      
      expect(formatted).toHaveLength(1);
      expect(formatted[0].content).toContain('[Error reading file:');
      expect(formatted[0].content).toContain('Missing File');
    });

    it('should handle multiple files', () => {
      // Create second test file
      const testFile2Path = join(__dirname, 'test_format_file2.txt');
      writeFileSync(testFile2Path, 'This is the second test file');

      try {
        const files: FileRecord[] = [
          {
            id: 1,
            agentId: 'test-agent',
            filePath: testFilePath,
            fileHash: 'test-hash1',
            size: 100,
            lastModified: new Date(),
            processed: false,
            label: 'File 1',
            description: 'First test file'
          },
          {
            id: 2,
            agentId: 'test-agent',
            filePath: testFile2Path,
            fileHash: 'test-hash2',
            size: 100,
            lastModified: new Date(),
            processed: false,
            label: 'File 2',
            description: 'Second test file'
          }
        ];

        const formatted = formatFiles(files);
        
        expect(formatted).toHaveLength(2);
        expect(formatted[0].content).toContain('File 1');
        expect(formatted[1].content).toContain('File 2');
        expect(formatted[0].content).toContain('This is test content for prompt formatting');
        expect(formatted[1].content).toContain('This is the second test file');
        
      } finally {
        unlinkSync(testFile2Path);
      }
    });
  });
});