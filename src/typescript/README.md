# Letta Memory TypeScript SDK

TypeScript SDK for using Letta subagents for pluggable memory management. This is the TypeScript equivalent of the Python implementation.

## Installation

```bash
npm install
```

## Setup

1. Set your API keys:
```bash
export LETTA_API_KEY="your-letta-api-key"
export OPENAI_API_KEY="your-openai-api-key"  # Required for examples
```

2. Build the project:
```bash
npm run build
```

## Usage

### Basic Memory Operations

```typescript
import { Memory } from 'letta-memory-ts';

const memory = new Memory();

// Initialize memory for a user
await memory.initializeUserMemory('user123');

// Add messages to learn from
const runId = await memory.addMessages('user123', [
  {
    role: 'user',
    content: 'Hi my name is Alice and I love programming'
  },
  {
    role: 'assistant', 
    content: 'Nice to meet you Alice! Programming is awesome.'
  }
]);

// Wait for processing to complete
await memory.waitForRun(runId);

// Retrieve user memory
const userMemory = await memory.getUserMemory('user123');
console.log('User Memory:', userMemory);

// Get formatted memory for prompts
const formattedMemory = await memory.getUserMemory('user123', true);
```

### Chat Example

Run the interactive chat example:

```bash
npm run build
node dist/examples/chat.js
```

## API Reference

### Memory Class

#### Constructor
```typescript
new Memory(config?: MemoryConfig)
```

#### Methods

- `initializeUserMemory(userId: string, options?)`: Initialize memory for a user
- `addMessages(userId: string, messages: Record<string, any>[])`: Add messages to learn from
- `getUserMemory(userId: string, promptFormatted?: boolean)`: Get user memory
- `getSummary(userId: string, promptFormatted?: boolean)`: Get conversation summary
- `deleteUser(userId: string)`: Delete a user's memory
- `waitForRun(runId: string)`: Wait for async processing to complete

### Schemas

#### MessageCreate
```typescript
interface MessageCreate {
  content: string;
  role: string;
  name?: string;
  metadata?: Record<string, any>;
}
```

#### Message
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

#### File
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

## Development

### Running Tests

The tests are written in imperative style and can be run directly:

```bash
# Run all tests
npm test

# Run specific test suites
npm run test:memory
npm run test:formatter

# Run Jest tests (if you prefer)
npm run test:jest
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

## License

MIT