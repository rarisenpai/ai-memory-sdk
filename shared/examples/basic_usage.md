# Basic Usage Examples

This document shows how to use the Learned Context SDK in both Python and TypeScript.

## Python Example

```python
from learned_context import LearnedContextClient, ConversationalMemoryClient

# Basic client usage
client = LearnedContextClient(letta_api_key="your-api-key")

# Create agent with tags
agent = client.create_subconscious_agent(tags=["user123", "chat"])

# Register conversation messages
messages = [
    {"role": "user", "content": "I love Python programming"},
    {"role": "assistant", "content": "That's great! Python is versatile."},
    {"role": "user", "content": "Can you help me with async programming?"}
]
agent.register_messages(messages)

# Register a code file
agent.register_file(
    file_path="./my_script.py",
    label="user_code",
    description="User's Python script for learning async"
)

# Learn from all registered content
run = agent.learn()

# Create context block for user preferences
agent.create_learned_context_block(
    label="coding_style",
    value="User prefers clean, readable code with good documentation",
    description="User's coding style preferences"
)

# Get processing statistics
stats = agent.get_stats()
print(f"Processed {stats.processed_messages} messages, {stats.processed_files} files")

# Using ConversationalMemoryClient for simpler user memory management
memory_client = ConversationalMemoryClient(letta_api_key="your-api-key")

# Add conversation for a user
conversation = [
    {"role": "user", "content": "My favorite color is blue"},
    {"role": "assistant", "content": "I'll remember that you like blue!"}
]
memory_client.add("user123", conversation)

# Retrieve user's memory
user_memory = memory_client.get_user_memory("user123")
print(f"User memory: {user_memory.value}")
```

## TypeScript Example

```typescript
import { LearnedContextClient, ConversationalMemoryClient } from 'learned-context-sdk';

async function main() {
    // Basic client usage
    const client = new LearnedContextClient("your-letta-api-key");

    // Create agent with tags
    const agent = await client.createSubconsciousAgent(["user123", "chat"]);

    // Register conversation messages
    const messages = [
        { role: "user", content: "I love TypeScript programming" },
        { role: "assistant", content: "That's great! TypeScript adds type safety." },
        { role: "user", content: "Can you help me with generics?" }
    ];
    agent.registerMessages(messages);

    // Register a code file
    agent.registerFile(
        "./my-script.ts",
        "user_code",
        "User's TypeScript code for learning generics"
    );

    // Learn from all registered content
    const run = await agent.learn();

    // Create context block for user preferences
    await agent.createLearnedContextBlock(
        "coding_style",
        "User prefers strongly typed code with clear interfaces",
        "User's coding style preferences"
    );

    // Get processing statistics
    const stats = agent.getStats();
    console.log(`Processed ${stats.processedMessages} messages, ${stats.processedFiles} files`);

    // Using ConversationalMemoryClient for simpler user memory management
    const memoryClient = new ConversationalMemoryClient("your-letta-api-key");

    // Add conversation for a user
    const conversation = [
        { role: "user", content: "My favorite programming language is TypeScript" },
        { role: "assistant", content: "I'll remember your preference for TypeScript!" }
    ];
    await memoryClient.add("user123", conversation);

    // Retrieve user's memory
    const userMemory = await memoryClient.getUserMemory("user123");
    console.log(`User memory: ${userMemory?.value}`);
}

main().catch(console.error);
```

## Common Patterns

### Learning from Files

Both clients support learning from various file types:

```python
# Python
agent.register_file("./docs/api.md", "api_docs", "API documentation")
agent.register_file("./config.json", "config", "Application configuration")
agent.register_file("./logs/app.log", "logs", "Application logs for debugging")
```

```typescript
// TypeScript
agent.registerFile("./docs/api.md", "api_docs", "API documentation");
agent.registerFile("./config.json", "config", "Application configuration");  
agent.registerFile("./logs/app.log", "logs", "Application logs for debugging");
```

### Batch Learning

Process multiple items efficiently:

```python
# Python - register multiple items then learn
agent.register_messages(conversation_history)
agent.register_file("doc1.txt", "doc1", "First document")
agent.register_file("doc2.txt", "doc2", "Second document")

# Single learn call processes everything
run = agent.learn()
```

```typescript
// TypeScript - register multiple items then learn
agent.registerMessages(conversationHistory);
agent.registerFile("doc1.txt", "doc1", "First document");
agent.registerFile("doc2.txt", "doc2", "Second document");

// Single learn call processes everything
const run = await agent.learn();
```

### Context Block Management

Create and manage learned context blocks:

```python
# Create different types of context blocks
agent.create_learned_context_block("user_info", "Name: Sarah, Role: Developer", "User information")
agent.create_learned_context_block("project_context", "Working on ML pipeline", "Current project")

# List all blocks
blocks = agent.list_learned_context_blocks()

# Delete specific block
agent.delete_learned_context_block("old_context")
```

```typescript
// Create different types of context blocks
await agent.createLearnedContextBlock("user_info", "Name: Sarah, Role: Developer", "User information");
await agent.createLearnedContextBlock("project_context", "Working on ML pipeline", "Current project");

// List all blocks
const blocks = await agent.listLearnedContextBlocks();

// Delete specific block
await agent.deleteLearnedContextBlock("old_context");
```