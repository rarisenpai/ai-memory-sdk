# AI Memory SDK 
An experimental SDK for adding agentic memory and learning in a pluggable way. When messages are added, subconsious memory agents process them to generate *learned context* that can be plugged into your system prompt, such as a user profile or a conversational summary. 
```
+========================================+
|         SYSTEM PROMPT                  |
+========================================+
|      LEARNED CONTEXT (HUMAN)           | <- memory agent (learning from message history)
+========================================+
|           MESSAGES                     |
|  * User -> Assistant                   |
|  * User -> Assistant                   |
|  * User -> Assistant                   |
|  * ...                                 |
+========================================+
```
For a specific user, the memory agent will learn a `summary` block and a `human` block, formatted as follows:
```html
<conversation_summary>
Sarah introduced herself and asked the assistant to tell about itself. The assistant provided a brief self-description and offered further help.
</conversation_summary>

<human description="Details about the human user you are speaking to.">
Name: Sarah
Interests: Likes cats (2025-09-03)
</human>
```
Memories can also be explicitly searched with semantic search to retrieve relevant historical messages to place back into context. 

## Context Model (Generalized API)
In addition to the user-specific helpers, the SDK supports a generalized "context" model:
- Context: the unit we learn for (one context = one Letta agent). For example, `user:sarah`, `team:alpha`, or `project:123`.
- Blocks: named pieces of context (e.g. `human`, `summary`, `preferences`) attached to the context's agent.
- Messages: conversation turns the learner uses to update one or more blocks.

You can bind a Memory instance to a context at construction time, or pass a context per call.

Naming conventions
- Agents: the context_id is embedded in the agent name (e.g., `subconscious_agent_ctx_<context_id>`). Ensure your `context_id` uses only characters allowed by Letta agent names. Recommended: letters, numbers, underscores, and dashes. Avoid characters like `:` or other punctuation.
- Blocks and tags: follow your Letta deployment’s rules. Recommended: letters, numbers, underscores, and dashes.

Python (instance-scoped):
```python
from ai_memory_sdk import Memory

memory = Memory(context_id="user_sarah")

# Create a new block in this context (no-op if it exists and reset=False)
memory.initialize_memory(
    label="preferences",
    description="Known user preferences.",
    value="Likes cats",
)

# Add conversation messages to the bound context (unified API)
memory.add_messages([
    {"role": "user", "content": "I love cats"}
])

# Retrieve a block (raw or prompt formatted)
raw = memory.get_memory("preferences")
formatted = memory.get_memory("preferences", prompt_formatted=True)
```

Python (explicit context):
```python
from ai_memory_sdk import Memory

memory = Memory()
memory.initialize_context("project_alpha", reset=True)
memory.initialize_memory("spec", "Project spec", value="v1", context_id="project_alpha")
run = memory.add_messages_for_context("project_alpha", [{"role": "user", "content": "Kickoff done"}])
memory.wait_for_run(run)
spec = memory.get_memory("spec", context_id="project_alpha")
```

TypeScript (instance-scoped):
```ts
import { Memory } from '@letta-ai/memory-sdk'

const memory = new Memory({ contextId: 'user_sarah' })
await memory.initializeMemory('preferences', 'Known user preferences.', 'Likes cats')
// unified API when instance is bound to a context
await memory.addMessages([{ role: 'user', content: 'I love cats' }])
const formatted = await memory.getMemory('preferences', true)
```

TypeScript (explicit context):
```ts
const memory = new Memory()
await memory.initializeContext('project_alpha', true)
await memory.initializeMemory('spec', 'Project spec', 'v1', 10000, false, 'project_alpha')
const run = await memory.addMessagesToContext('project_alpha', [{ role: 'user', content: 'Kickoff done' }])
await memory.waitForRun(run)
```

## Quickstart 
1. Create a [Letta API key](https://app.letta.com/api-keys)
2. Install: `pip install ai-memory-sdk`

### Usage: Conversational Memory 
You can save conversation histories using the Memory SDK, and later retrieve the learned context block to place into your system prompt. This allows your agents to have an evolving understand of the user. 

**Example:** Create a basic OpenAI `gpt-4o-mini` chat agent with memory 

```python
from openai import OpenAI
from ai_memory_sdk import Memory

# Memory is a lightweight client around Letta, and will handle storing information
# about user conversations.
#
# Assumes the existence of the LETTA_API_KEY environment variable, but you can
# set this manually with Memory(api_key="your_api_key")
memory = Memory()

# Set up your OpenAI client like you normally would.
# This example assumes that the OpenAI key is stored in the OPENAI_API_KEY
# environment variable.
openai_client = OpenAI()

def chat_with_memories(message: str, user_id: str = "default_user") -> str:
    # Retrieve the user memory block if it exists, otherwise initialize it
    # User memory blocks are pieces of information about whoever is talking
    # to your assistant, and can be created/retrieved using arbitrary string
    # identifier keys.
    user_memory = memory.get_user_memory(user_id)
    if not user_memory:
        # User doesn't exist, create a new memory block
        memory.initialize_user_memory(user_id, reset=True)
        user_memory = memory.get_user_memory(user_id)

    # the contents of the user block formatted as a prompt:
    #
    # <human description="Details about the human user you are speaking to.">
    # Name: Sarah
    # Interests: Likes cats (2025-09-04)
    # </human>
    user_memory_prompt= memory.get_user_memory(user_id, prompt_formatted=True)
    print(user_memory_prompt)

    # Generate the assistant response using the inference engine of your choice,
    # OpenAI in this case.
    system_prompt = f"<system>You are a helpful AI assistant</system>"
    system_prompt += f"\n{user_memory_prompt}"

    # Create the list of message
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]

    # Send the messages to the OpenAI API
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    # Extract the assistant's message from the API response
    assistant_response = response.choices[0].message.content

    # Create new memories from the conversation --
    # this will update the user's memory block and persist messages
    print("Creating new memories...")
    messages.append({"role": "assistant", "content": assistant_response})
    memory.add_messages(user_id, messages)

    return assistant_response

def main():
    print("Chat with AI (type 'exit' to quit)")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        print(f"AI: {chat_with_memories(user_input)}")

if __name__ == "__main__":
    main()

```
You can also search memories (semantic search) with `memory.search(user_id, query)` to retrieve relevant historical messages.

## SDK Reference
You can initialize the memory SDK with:
```python
from ai_memory_sdk import Memory

memory = Memory(api_key="LETTA_API_KEY")
```

### Adding memories 
Save messages by adding them to memory: 
```python
run = memory.add_messages("user_id", [{"role": "user", "content": "hi"}])
```
The memory agent will process the messages asynchronously, tracked by the `run`. 
> [!WARNING]
> Each each call to `add_messages(...)` will invoke the memory agent. To reduce costs, you may want to send messages in batches (recommended 5-10) or only when messages are evicted from context. 

### Waiting for learning to complete
Messages are processed asynchronously, so to ensure all memory updates are reflected you should wait for the agent learning to complete.
```python
memory.wait_for_run(run)
```
This will block until the memory agent has completed processing. 

### Getting memories for a user
You can get the context blocks for the summary and/or user memory with: 
```python
summary = memory.get_summary("user_id", prompt_formatted=True)
user_memory = memory.get_user_memory("user_id", prompt_formatted=True)
```
To get the raw value of the context block, you can pass `prompt_formatted=False`. 

### Generalized Context API
You can work with arbitrary contexts (one context = one Letta agent) and labeled blocks within them. You can bind a `Memory` instance to a context or pass a context per call.

Constructor (instance-scoped context):
```python
from ai_memory_sdk import Memory
memory = Memory(context_id="user:sarah")
```

Context methods (Python):
- `initialize_context(context_id: str, reset: bool = False) -> str`
- `list_blocks(context_id: Optional[str] = None) -> list`
- `initialize_memory(label: str, description: str, value: str = "", char_limit: int = 10000, reset: bool = False, context_id: Optional[str] = None) -> str`
- `get_memory(label: str, prompt_formatted: bool = False, context_id: Optional[str] = None) -> Optional[str]`
- `delete_block(label: str, context_id: Optional[str] = None) -> None`
- `add_messages_for_context(context_id: str, messages: list, skip_vector_storage: bool = True) -> str`
- Unified: `add_messages(messages: list, skip_vector_storage: bool = True) -> str` (uses bound `context_id`)

Example:
```python
memory = Memory(context_id="user:sarah")
memory.initialize_memory("preferences", "Known user preferences.", "Likes cats")
run = memory.add_messages([{ "role": "user", "content": "I love cats" }])
memory.wait_for_run(run)
print(memory.get_memory("preferences", prompt_formatted=True))
```

### Searching messages 
You can search messages with semantic search with: 
```python
messages = memory.search("user_id", query="Favorite foods")
```
By default this filters to SDK-authored user messages (tags=["ai-memory-sdk", "user"]). To customize:
```python
messages = memory.search("user_id", query="system prompts", tags=["assistant"])  # assistant passages
messages = memory.search("user_id", query="any", tags=[])  # no tag filter
```

### Retrieving the memory agent 
Memories are formed by Letta agents using the sleeptime architecture. You can get the agent's ID with: 
```python
agent_id = memory.get_memory_agent_id("user_id")
```
The agent can be viewed at `https://app.letta.com/agents/<AGENT_ID>`. 

### Deleting user memories 
All memories and data associated with a user can be deleted with: 
```python
memory.delete_user("user_id")
```


## Examples
- Conversational memory with user helpers: `examples/chat.py`
- Context-based demo (generalized API): `examples/context.py`
- TypeScript context demo: `examples/context.ts`


## Roadmap
- [x] Save messages as archival memories
- [x] Query messages
- [ ] Query messages by time
- [ ] TypeScript support 
- [ ] Learning from files
- [ ] Add "sleep" (offline collective revisioning of all data)  
You can also bind a context and call the unified method:
```python
memory = Memory(context_id="user_sarah")
run = memory.add_messages([{"role": "user", "content": "hi"}])
```

Implementation notes
- Agents and passages created by this SDK include the tag `ai-memory-sdk` for discoverability and ops. The default search uses this tag in addition to role tags.
