# Letta Memory TypeScript SDK

A TypeScript SDK for using Letta subagents for pluggable memory management. This SDK allows you to easily integrate persistent conversational memory into your applications. This is the TypeScript equivalent of the Python implementation.

## Installation

```bash
npm install @letta-ai/memory-sdk
# or
yarn add @letta-ai/memory-sdk
```

## Setup

1. Set your API keys:
```bash
export LETTA_API_KEY="your-letta-api-key"
```

2. Build the project:
```bash
npm run build
```

## Quick Start

```typescript
import { Memory } from '@letta-ai/memory-sdk';

// Initialize the memory client
const client = new Memory({ 
  lettaApiKey: process.env.LETTA_API_KEY 
});

// Initialize user memory
await client.initializeUserMemory('user_123');

// Add messages to user's memory
const runId = await client.addMessages('user_123', [
  {
    role: 'user',
    content: 'Hi my name is Bob'
  },
  {
    role: 'assistant',
    content: 'Hi Bob, how can I help you today?'
  }
]);

// Wait for processing to complete
await client.waitForRun(runId);

// Retrieve user memory
const memory = await client.getUserMemory('user_123');
console.log('User memory:', memory);

// Search user's message history
const searchResults = await client.search('user_123', 'Bob');
console.log('Search results:', searchResults);
```

## API Reference

### Constructor

#### `new Memory(config?: MemoryConfig)`

Creates a new Memory instance.

```typescript
interface MemoryConfig {
  lettaApiKey?: string;  // Letta API key (or use LETTA_API_KEY env var)
  baseUrl?: string;      // Base URL for local Letta server
}
```

**Examples:**

```typescript
// Using API key
const client = new Memory({ 
  lettaApiKey: "your-api-key" 
});

// Using local server
const client = new Memory({ 
  baseUrl: "http://localhost:8283" 
});

// Using environment variable
const client = new Memory(); // Uses LETTA_API_KEY env var
```

### Methods

#### `initializeUserMemory(userId: string, options?: InitOptions): Promise<string>`

Initialize memory for a new user.

```typescript
interface InitOptions {
  userContextBlockPrompt?: string;      // Default: "Details about the human user you are speaking to."
  userContextBlockCharLimit?: number;   // Default: 10000
  userContextBlockValue?: string;       // Default: ""
  summaryBlockPrompt?: string;         // Default: "A short (1-2 sentences) running summary of the conversation."
  summaryBlockCharLimit?: number;      // Default: 1000
  reset?: boolean;                     // Default: false - whether to reset existing memory
}
```

**Returns:** Agent ID for the user's memory

**Example:**
```typescript
const agentId = await client.initializeUserMemory('user_123', {
  userContextBlockValue: 'User is a software engineer who likes TypeScript',
  reset: true
});
```

#### `addMessages(userId: string, messages: Message[], skipVectorStorage?: boolean): Promise<string>`

Add messages to a user's memory.

```typescript
interface Message {
  role: string;          // 'user' or 'assistant'
  content: string;       // Message content
  name?: string;         // Optional name
  metadata?: Record<string, any>; // Optional metadata
}
```

**Parameters:**
- `userId`: User identifier
- `messages`: Array of messages to add
- `skipVectorStorage`: Whether to skip adding messages to vector search (default: true)

**Returns:** Run ID for the processing task

**Example:**
```typescript
const runId = await client.addMessages('user_123', [
  {
    role: 'user',
    content: 'I love programming in TypeScript'
  },
  {
    role: 'assistant', 
    content: 'TypeScript is a great language! What do you like most about it?'
  }
], false); // Don't skip vector storage for searchability
```

#### `getUserMemory(userId: string, promptFormatted?: boolean): Promise<string | null>`

Retrieve a user's memory.

**Parameters:**
- `userId`: User identifier  
- `promptFormatted`: Whether to return memory in XML format for prompts (default: false)

**Returns:** User memory string or null if user doesn't exist

**Example:**
```typescript
// Get raw memory
const memory = await client.getUserMemory('user_123');

// Get formatted memory for use in prompts
const formattedMemory = await client.getUserMemory('user_123', true);
// Returns: <human description="Details about the human user...">User details here</human>
```

#### `getSummary(userId: string, promptFormatted?: boolean): Promise<string | null>`

Retrieve a user's conversation summary.

**Parameters:**
- `userId`: User identifier
- `promptFormatted`: Whether to return summary in XML format (default: false)

**Returns:** Summary string or null if user doesn't exist

**Example:**
```typescript
// Get raw summary
const summary = await client.getSummary('user_123');

// Get formatted summary  
const formattedSummary = await client.getSummary('user_123', true);
// Returns: <conversation_summary>User discussed TypeScript programming...</conversation_summary>
```

#### `search(userId: string, query: string): Promise<string[]>`

Search a user's message history.

**Parameters:**
- `userId`: User identifier
- `query`: Search query

**Returns:** Array of matching message contents

**Example:**
```typescript
const results = await client.search('user_123', 'programming');
console.log('Found messages:', results);
```

#### `getMemoryAgentId(userId: string): Promise<string | null>`

Get the Letta agent ID associated with a user.

**Parameters:**
- `userId`: User identifier

**Returns:** Agent ID or null if user doesn't exist

#### `waitForRun(runId: string): Promise<void>`

Wait for a background processing run to complete.

**Parameters:**
- `runId`: Run ID returned from `addMessages`

#### `deleteUser(userId: string): Promise<void>`

Delete a user and all associated data.

**Parameters:**
- `userId`: User identifier

**Example:**
```typescript
await client.deleteUser('user_123');
console.log('User deleted');
```

#### `addFiles(files: any[]): Promise<never>`

Add files to memory. Currently not implemented.

**Throws:** "Not implemented" error

## Usage Examples

### Basic Conversation Memory

```typescript
import { Memory } from './src/memory';

const client = new Memory();
const userId = 'user_123';

// Initialize user
await client.initializeUserMemory(userId);

// Simulate a conversation
const messages = [
  { role: 'user', content: 'Hi, I\'m working on a React project' },
  { role: 'assistant', content: 'That\'s great! React is a popular framework. What are you building?' },
  { role: 'user', content: 'A todo app with TypeScript' },
  { role: 'assistant', content: 'Excellent choice! TypeScript adds great type safety to React projects.' }
];

// Add messages with vector storage for searchability
const runId = await client.addMessages(userId, messages, false);
await client.waitForRun(runId);

// Check what the system learned about the user
const memory = await client.getUserMemory(userId);
console.log('User context:', memory);

// Search for specific topics
const reactResults = await client.search(userId, 'React');
const typescriptResults = await client.search(userId, 'TypeScript');

console.log('React mentions:', reactResults);
console.log('TypeScript mentions:', typescriptResults);
```

### Chat Example

Run the interactive chat example:

```bash
npm run build
node dist/examples/chat.js
```

### Managing Multiple Users

```typescript
const client = new Memory();
const users = ['alice', 'bob', 'charlie'];

// Initialize memory for multiple users
for (const userId of users) {
  await client.initializeUserMemory(userId, {
    userContextBlockValue: `User ${userId} preferences and context`
  });
}

// Add different messages for each user
await client.addMessages('alice', [
  { role: 'user', content: 'I prefer Python for data science' }
]);

await client.addMessages('bob', [  
  { role: 'user', content: 'I love JavaScript and web development' }
]);

await client.addMessages('charlie', [
  { role: 'user', content: 'I work with Go for backend services' }
]);

// Retrieve each user's memory
for (const userId of users) {
  const memory = await client.getUserMemory(userId);
  console.log(`${userId}'s memory:`, memory);
}
```

## Development

### Running Tests

The SDK includes comprehensive tests that match the Python SDK functionality:

```bash
# Run all tests (includes build + traditional tests + Jest messages test)
npm test

# Run all test suites separately
npm run test:all

# Run Jest tests specifically  
npm run test:jest

# Run the messages test suite (equivalent to Python test_messages.py)
npm run test:messages

# Run specific test suites
npm run test:memory
npm run test:formatter

# Watch mode for development
npm run test:watch
```

### Watch Mode

```bash
npm run dev
```

### Clean Build

```bash
npm run clean
npm run build
```

## Schemas

### MessageCreate
```typescript
interface MessageCreate {
  content: string;
  role: string;
  name?: string;
  metadata?: Record<string, any>;
}
```

### Message
```typescript
interface Message {
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
```

### File
```typescript
interface File {
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
```

## Environment Variables

Set up your environment:

```bash
# For Letta Cloud
export LETTA_API_KEY="your-api-key-here"

# For local development
# No API key needed, just connect to local server at http://localhost:8283
```

## Error Handling

The SDK throws errors for:
- Invalid API keys or connection issues
- Attempting to reinitialize existing users without `reset: true`
- Network timeouts or server errors
- Calling unimplemented methods like `addFiles`

Always wrap SDK calls in try-catch blocks for production use:

```typescript
try {
  const runId = await client.addMessages(userId, messages);
  await client.waitForRun(runId);
  const memory = await client.getUserMemory(userId);
} catch (error) {
  console.error('Memory operation failed:', error.message);
  // Handle error appropriately
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.
