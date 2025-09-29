# AI Memory SDK

The AI Memory SDK is a lightweight wrapper around [Letta](https://letta.com), a platform for serving stateful agents. The memory SDK simplifies the interface to provide a general-purpose memory layer, similar to mem0, Graphiti, and others.

The AI Memory SDK creates a "subconscious agent" (a standard Letta agent) responsible for managing a set of memory blocks. Subconscious agents begin asynchronously processing information when they receive messages, and will attempt to update all memory blocks. Subconscious agents are designed to be lightweight and efficient, allowing for quick and seamless integration into existing systems.

Memory blocks are scoped to "subjects", which are arbitrary collections of blocks.

- **Subjects**: what memory is “about” (e.g., a particular user, project_alpha, team_support). These are just Letta agents under the hood.
- **Blocks**: named memory sections under a subject (e.g., human, summary, policies, history, study_guide, preferences). Any label and description are permitted. Read more on memory blocks [here](https://docs.letta.com/guides/agents/memory-blocks).
- **Messages**: the conversation turns you feed the agent. Adding messages to a `Memory` instance will kick off the agent's processing.

This enables user profiles and summaries, and broader use cases like policy digests, running histories, study guides, briefs — any domain‑specific memory you define.

See Letta's YouTube channel for more information on how to design memory architecture. [This video](https://youtu.be/o4boci1xSbM) provides a general overview.

Quick mental model:
```
+========================================+
|         SYSTEM PROMPT                  |
+========================================+
|   LEARNED BLOCKS (SUBJECT)             | <- subconscious agent updates over time
|   - <human> ... </human>               |
|   - <summary> ... </summary>           |
|   - <policies> ... </policies>         |
|   - <history> ... </history>           |
+========================================+
|           MESSAGES                     |
|  * User -> Assistant                   |
|  * User -> Assistant                   |
|  * ...                                 |
+========================================+
```

Memories can also be explicitly searched with semantic search to retrieve relevant historical messages and place them back into context.

## Subject Model (Generalized API)

In addition to the user-specific helpers, the SDK supports a generalized "subject" model:
- **Subject**: the unit we learn for (one subject = one Letta agent). For example, `user_sarah`, `team_alpha`, or `project_123`.
- **Blocks**: named pieces of memory (e.g. `human`, `summary`, `preferences`) attached to the subject's agent.
- **Messages**: conversation turns the learner uses to update one or more blocks.

You can bind a Memory instance to a subject at construction time, or pass a subject per call.

### Naming conventions

- **Agents**: the subject_id is embedded in the agent name (e.g., `subconscious_agent_subject_<subject_id>`). Ensure your `subject_id` uses only characters allowed by Letta agent names. Recommended: letters, numbers, underscores, and dashes. Avoid characters like `:` or other punctuation.
- **Blocks and tags**: follow your Letta deployment’s rules. Recommended: letters, numbers, underscores, and dashes.


**Python (instance-scoped)**:
```python
from ai_memory_sdk import Memory

memory = Memory(subject_id="user_sarah")

# Create a new block in this subject (no-op if it exists and reset=False)
memory.initialize_memory(
    label="preferences",
    description="Known user preferences.",
    value="Likes cats",
)

# Add conversation messages to the bound subject (unified API)
memory.add_messages([
    {"role": "user", "content": "I love cats"}
])

# Retrieve a block (raw or prompt formatted)
raw = memory.get_memory("preferences")
formatted = memory.get_memory("preferences", prompt_formatted=True)
```


**Python (explicit subject)**:
```python
from ai_memory_sdk import Memory

memory = Memory()
memory.initialize_subject("project_alpha", reset=True)
memory.initialize_memory("spec", "Project spec", value="v1", subject_id="project_alpha")
run = memory.add_messages_for_subject("project_alpha", [{"role": "user", "content": "Kickoff done"}])
memory.wait_for_run(run)
spec = memory.get_memory("spec", subject_id="project_alpha")
```


**TypeScript (instance-scoped)**:
```ts
import { Memory } from '@letta-ai/memory-sdk'

const memory = new Memory({ subjectId: 'user_sarah' })
await memory.initializeMemory('preferences', 'Known user preferences.', 'Likes cats')
// unified API when instance is bound to a context
await memory.addMessages([{ role: 'user', content: 'I love cats' }])
const formatted = await memory.getMemory('preferences', true)
```


**TypeScript (explicit subject)**:
```ts
const memory = new Memory()
await memory.initializeSubject('project_alpha', true)
await memory.initializeMemory('spec', 'Project spec', 'v1', 10000, false, 'project_alpha')
const run = await memory.addMessagesToSubject('project_alpha', [{ role: 'user', content: 'Kickoff done' }])
await memory.waitForRun(run)
```

## Quickstart

1. Create a [Letta API key](https://app.letta.com/api-keys)
2. Install: `pip install ai-memory-sdk`

### Usage: Generic Memory Blocks
Save conversation histories and let the subconscious agent update any blocks you define (human, summary, policies, history, study_guide, ...). Retrieve learned blocks and plug them into your system prompts.

**Example:** Create a basic OpenAI `gpt-4o-mini` chat agent with subject‑scoped memory

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
    # Retrieve or initialize the subject (using user helpers for simplicity)
    user_memory = memory.get_user_memory(user_id)
    if not user_memory:
        memory.initialize_user_memory(user_id, reset=True)
        user_memory = memory.get_user_memory(user_id)

    # the contents of the human block formatted as a prompt:
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
    # this will update subject blocks and persist messages
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

### Generalized Subject API

You can work with arbitrary subjects (one subject = one Letta agent) and labeled blocks within them. You can bind a `Memory` instance to a subject or pass a subject per call.

Constructor (instance-scoped subject):
```python
from ai_memory_sdk import Memory
memory = Memory(subject_id="user_sarah")
```

**Subject methods (Python)**:
- `initialize_subject(subject_id: str, reset: bool = False) -> str`
- `list_blocks(subject_id: Optional[str] = None) -> list`
- `initialize_memory(label: str, description: str, value: str = "", char_limit: int = 10000, reset: bool = False, subject_id: Optional[str] = None) -> str`
- `get_memory(label: str, prompt_formatted: bool = False, subject_id: Optional[str] = None) -> Optional[str]`
- `delete_block(label: str, subject_id: Optional[str] = None) -> None`
- `add_messages_for_subject(subject_id: str, messages: list, skip_vector_storage: bool = True) -> str`
- Unified: `add_messages(messages: list, skip_vector_storage: bool = True) -> str` (uses bound `subject_id`)

Example:
```python
memory = Memory(subject_id="user_sarah")
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
- Subject-based demo (generalized API): `examples/subject.py`
- TypeScript subject demo: `examples/subject.ts`
- Full tutorial: `docs/tutorial.md`


## Roadmap

- [x] Save messages as archival memories
- [x] Query messages
- [ ] Query messages by time
- [x] TypeScript support
- [ ] Learning from files
- [ ] Add "sleep" (offline collective revisioning of all data)

### Implementation notes

- Agents and passages created by this SDK include the tag `ai-memory-sdk` for discoverability and ops. The default search uses this tag in addition to role tags.
