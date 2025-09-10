import { formatMessages, formatFiles } from '../src/prompt-formatter';
import { MessageCreate, File } from '../src/schemas';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

function testFormatMessages() {
  console.log('Testing formatMessages...');

  const messages: MessageCreate[] = [
    {
      role: 'user',
      content: 'hi my name is sarah'
    },
    {
      role: 'assistant',
      content: 'Hello Sarah! I\'m Sam. *smiles warmly* There\'s something special about first meetings, don\'t you think?'
    },
    {
      role: 'assistant',
      content: 'Tool call returned Sent message successfully.'
    }
  ];

  const formatted = formatMessages(messages);
  
  if (formatted.length !== 1) {
    throw new Error(`Expected 1 formatted message, got ${formatted.length}`);
  }

  if (formatted[0].role !== 'user') {
    throw new Error(`Expected role 'user', got '${formatted[0].role}'`);
  }

  const content = formatted[0].content;
  const expectedParts = [
    '<messages>',
    'The following message interactions have occured',
    'user: hi my name is sarah',
    'assistant: Hello Sarah!',
    'assistant: Tool call returned',
    '</messages>'
  ];

  for (const part of expectedParts) {
    if (!content.includes(part)) {
      throw new Error(`Expected content to contain '${part}', got: ${content}`);
    }
  }

  console.log('✓ formatMessages works correctly');
}

function testFormatMessagesEmpty() {
  console.log('Testing formatMessages with empty array...');

  const messages: MessageCreate[] = [];
  const formatted = formatMessages(messages);
  
  if (formatted.length !== 1) {
    throw new Error(`Expected 1 formatted message, got ${formatted.length}`);
  }

  const content = formatted[0].content;
  if (!content.includes('<messages>') || !content.includes('</messages>')) {
    throw new Error(`Expected content to contain messages tags, got: ${content}`);
  }

  console.log('✓ formatMessages handles empty array correctly');
}

function testFormatMessagesWithMetadata() {
  console.log('Testing formatMessages with metadata...');

  const messages: MessageCreate[] = [
    {
      role: 'user',
      content: 'Hello',
      name: 'testUser',
      metadata: { timestamp: '2023-01-01' }
    }
  ];

  const formatted = formatMessages(messages);
  const content = formatted[0].content;
  
  if (!content.includes('user: Hello')) {
    throw new Error(`Expected content to contain 'user: Hello', got: ${content}`);
  }

  console.log('✓ formatMessages handles metadata correctly');
}

function testFormatFilesSmall() {
  console.log('Testing formatFiles with small file...');

  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'test-'));
  const testFile = path.join(tempDir, 'test.txt');
  const fileContent = 'This is a test file content.';

  try {
    fs.writeFileSync(testFile, fileContent);

    const files: File[] = [
      {
        id: 1,
        agent_id: 'test-agent',
        file_path: testFile,
        file_hash: 'test-hash',
        size: fileContent.length,
        last_modified: new Date(),
        processed: false,
        label: 'test-file',
        description: 'A test file'
      }
    ];

    const formatted = formatFiles(files);
    
    if (formatted.length !== 1) {
      throw new Error(`Expected 1 formatted file, got ${formatted.length}`);
    }

    if (formatted[0].role !== 'user') {
      throw new Error(`Expected role 'user', got '${formatted[0].role}'`);
    }

    const content = formatted[0].content;
    const expectedParts = [
      '<file label="test-file" description="A test file">',
      '<file_part part=1/1>',
      fileContent,
      '</file_part>',
      '</file>'
    ];

    for (const part of expectedParts) {
      if (!content.includes(part)) {
        throw new Error(`Expected content to contain '${part}', got: ${content}`);
      }
    }

    console.log('✓ formatFiles handles small files correctly');

  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

function testFormatFilesLarge() {
  console.log('Testing formatFiles with large file...');

  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'test-'));
  const testFile = path.join(tempDir, 'test.txt');
  // Create a file larger than FILE_CHAR_LIMIT (20000)
  const largeContent = 'a'.repeat(25000);

  try {
    fs.writeFileSync(testFile, largeContent);

    const files: File[] = [
      {
        id: 1,
        agent_id: 'test-agent',
        file_path: testFile,
        file_hash: 'test-hash',
        size: largeContent.length,
        last_modified: new Date(),
        processed: false,
        label: 'large-file',
        description: 'A large test file'
      }
    ];

    const formatted = formatFiles(files);
    
    if (formatted.length <= 1) {
      throw new Error(`Expected multiple formatted messages for large file, got ${formatted.length}`);
    }

    if (!formatted[0].content.includes('part=1/2')) {
      throw new Error(`Expected first part to contain 'part=1/2', got: ${formatted[0].content}`);
    }

    if (!formatted[1].content.includes('part=2/2')) {
      throw new Error(`Expected second part to contain 'part=2/2', got: ${formatted[1].content}`);
    }

    console.log('✓ formatFiles chunks large files correctly');

  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

function testFormatFilesError() {
  console.log('Testing formatFiles with non-existent file...');

  const files: File[] = [
    {
      id: 1,
      agent_id: 'test-agent',
      file_path: '/non/existent/file.txt',
      file_hash: 'test-hash',
      size: 0,
      last_modified: new Date(),
      processed: false,
      label: 'missing-file',
      description: 'A missing file'
    }
  ];

  const formatted = formatFiles(files);
  
  if (formatted.length !== 1) {
    throw new Error(`Expected 1 formatted message for error case, got ${formatted.length}`);
  }

  const content = formatted[0].content;
  if (!content.includes('[Error reading file:') || !content.includes('missing-file')) {
    throw new Error(`Expected error message and file label, got: ${content}`);
  }

  console.log('✓ formatFiles handles file errors gracefully');
}

function testFormatFilesMultiple() {
  console.log('Testing formatFiles with multiple files...');

  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'test-'));
  const file1Content = 'Content of file 1';
  const file2Content = 'Content of file 2';
  const testFile1 = path.join(tempDir, 'test1.txt');
  const testFile2 = path.join(tempDir, 'test2.txt');

  try {
    fs.writeFileSync(testFile1, file1Content);
    fs.writeFileSync(testFile2, file2Content);

    const files: File[] = [
      {
        id: 1,
        agent_id: 'test-agent',
        file_path: testFile1,
        file_hash: 'test-hash-1',
        size: file1Content.length,
        last_modified: new Date(),
        processed: false,
        label: 'file1',
        description: 'First test file'
      },
      {
        id: 2,
        agent_id: 'test-agent',
        file_path: testFile2,
        file_hash: 'test-hash-2',
        size: file2Content.length,
        last_modified: new Date(),
        processed: false,
        label: 'file2',
        description: 'Second test file'
      }
    ];

    const formatted = formatFiles(files);
    
    if (formatted.length !== 2) {
      throw new Error(`Expected 2 formatted messages, got ${formatted.length}`);
    }

    if (!formatted[0].content.includes('file1') || !formatted[0].content.includes(file1Content)) {
      throw new Error(`First formatted message missing file1 content: ${formatted[0].content}`);
    }

    if (!formatted[1].content.includes('file2') || !formatted[1].content.includes(file2Content)) {
      throw new Error(`Second formatted message missing file2 content: ${formatted[1].content}`);
    }

    console.log('✓ formatFiles handles multiple files correctly');

  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

function runAllTests() {
  console.log('Running Prompt Formatter tests...\n');

  try {
    testFormatMessages();
    console.log();
    
    testFormatMessagesEmpty();
    console.log();
    
    testFormatMessagesWithMetadata();
    console.log();
    
    testFormatFilesSmall();
    console.log();
    
    testFormatFilesLarge();
    console.log();
    
    testFormatFilesError();
    console.log();
    
    testFormatFilesMultiple();
    console.log();

    console.log('✅ All Prompt Formatter tests passed!');
  } catch (error) {
    console.error('❌ Test failed:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

if (require.main === module) {
  runAllTests();
}