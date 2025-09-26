AI Memory SDK Tutorial

This guide walks through the core concepts and end‑to‑end usage of the AI Memory SDK in both Python and TypeScript. You will learn how to:

- Model “subject” (what the SDK learns for)
- Create and manage labeled blocks of memory (e.g., human, summary, preferences)
- Add messages with the unified API and wait for learning to complete
- Search past messages with semantic search
- Use the user‑focused helpers for backward compatibility

Prerequisites
- Letta account and API key (LETTA_API_KEY)
- Python 3.8+ or Node.js 18+

Key Concepts
- Subject: the unit we learn for. One subject maps to one Letta agent (e.g., user_sarah, project_alpha). All blocks and messages under a subject are co‑learned by the same agent.
- Blocks: named pieces of subject state attached to the agent (e.g., human, summary, preferences).
- Messages: conversation turns that the learner processes to update blocks.
- Tagging: agents and passages created by this SDK are tagged with ai-memory-sdk for discoverability. Default search uses this tag + role filters.

Naming Conventions
- Use letters, numbers, underscores, or dashes for subject ids, block labels, and tags.
- Avoid characters like ':' in names to prevent API validation errors.

Python Setup
1) Install from PyPI (recommended):
   pip install ai-memory-sdk

   For local development from the repo root:
   cd src/python
   uv pip install -e .

2) Set your API key:
   export LETTA_API_KEY="your_letta_api_key"

TypeScript Setup
1) Install package:
   npm install @letta-ai/memory-sdk

2) Set your API key:
   export LETTA_API_KEY="your_letta_api_key"

3) Build TypeScript if using local sources:
   npm run build

Quickstart: Instance‑Scoped Subject
Python
   from ai_memory_sdk import Memory

   # Bind a Memory instance to a subject
   memory = Memory(subject_id="user_sarah")

   # Create a block (no‑op if it exists and reset=False)
   memory.initialize_memory(
       label="preferences",
       description="Known user preferences.",
       value="Likes cats",
   )

   # Add messages (unified API) and wait for the learner
   run = memory.add_messages([{ "role": "user", "content": "I love cats" }])
   memory.wait_for_run(run)

   # Retrieve the block
   print(memory.get_memory("preferences", prompt_formatted=True))

TypeScript
   import { Memory } from '@letta-ai/memory-sdk'

   const memory = new Memory({ subjectId: 'user_sarah' })
   await memory.initializeMemory('preferences', 'Known user preferences.', 'Likes cats')

   const run = await memory.addMessages([{ role: 'user', content: 'I love cats' }])
   await memory.waitForRun(run)

   console.log(await memory.getMemory('preferences', true))

Explicit Subject Per Call
Python
   from ai_memory_sdk import Memory

   memory = Memory()
   memory.initialize_subject("project_alpha", reset=True)
   memory.initialize_memory("spec", "Project spec", value="v1", subject_id="project_alpha")

   run = memory.add_messages_for_subject("project_alpha", [
       { "role": "user", "content": "Kickoff complete" }
   ])
   memory.wait_for_run(run)

   print(memory.get_memory("spec", subject_id="project_alpha"))

TypeScript
   import { Memory } from '@letta-ai/memory-sdk'

   const memory = new Memory()
   await memory.initializeSubject('project_alpha', true)
   await memory.initializeMemory('spec', 'Project spec', 'v1', 10000, false, 'project_alpha')

   const run = await memory.addMessagesToSubject('project_alpha', [
     { role: 'user', content: 'Kickoff complete' },
   ])
   await memory.waitForRun(run)

   console.log(await memory.getMemory('spec', false, 'project_alpha'))

Managing Blocks
- Create or reset a block
  - Python: initialize_memory(label, description, value='', char_limit=10000, reset=False, subject_id=None)
  - TS: initializeMemory(label, description, value?, charLimit=10000, reset=false, subjectId?)
- List blocks
  - Python: list_blocks(subject_id=None)
  - TS: listBlocks(subjectId?)
- Delete a block
  - Python: delete_block(label, subject_id=None)
  - TS: deleteBlock(label, subjectId?)
- Read a block
  - Python: get_memory(label, prompt_formatted=False, subject_id=None)
  - TS: getMemory(label, promptFormatted=false, subjectId?)

Adding Messages (Unified)
- If your Memory instance is bound to a subject:
  - Python: add_messages(messages, skip_vector_storage=True)
  - TS: addMessages(messages, skipVectorStorage = true)
- Legacy user form stays supported:
  - Python: add_messages(user_id, messages, ...)
  - TS: addMessages(userId, messages, ...)

Tips
- skip_vector_storage=False also inserts messages into the archival store for semantic search. It costs more; use for important turns or batching.
- Always call wait_for_run(run_id) when you need the latest learned blocks immediately after sending messages.

Searching Messages
- Python: search(user_id, query, tags=None)
- TS: search(userId, query, tags?)
- Defaults to tags=["ai-memory-sdk", "user"]. Examples:
  - Only assistant: tags=["assistant"]
  - No filter: tags=[]

User‑Focused Helpers (Back‑Compat)
- initialize_user_memory(user_id, ...) creates an agent (one per user) and sets up two blocks: human and summary.
- get_user_memory(user_id, prompt_formatted=False) reads the human block.
- get_summary(user_id, prompt_formatted=False) reads the summary block.
- add_messages(user_id, messages, ...) adds messages to the user agent.

System‑Prompt Integration
Python
   from openai import OpenAI
   from ai_memory_sdk import Memory

   openai_client = OpenAI()
   memory = Memory()

   def chat_with_memories(message: str, user_id: str = "default_user") -> str:
       user_memory = memory.get_user_memory(user_id)
       if not user_memory:
           memory.initialize_user_memory(user_id, reset=True)
           user_memory = memory.get_user_memory(user_id)

       user_memory_prompt = memory.get_user_memory(user_id, prompt_formatted=True)
       system_prompt = f"<system>You are a helpful AI assistant</system>\n{user_memory_prompt}"
       messages = [
           {"role": "system", "content": system_prompt},
           {"role": "user", "content": message},
       ]
       resp = openai_client.chat.completions.create(model="gpt-4o-mini", messages=messages)
       assistant = resp.choices[0].message.content

       messages.append({"role": "assistant", "content": assistant})
       memory.add_messages(user_id, messages)  # legacy user form
       return assistant

Troubleshooting
- Invalid agent name: ensure your context id contains only letters, numbers, underscores, or dashes (e.g., user_sarah).
- Missing LETTA_API_KEY: set it in your environment before running.
- Costs: prefer batching messages (e.g., 5–10) before calling add_messages to reduce compute.

Testing Locally (Offline)
- Python: run the offline subject tests (no network):
   cd src/python
   uv pip install -e .
   uv run pytest -q tests/test_subject.py

- TypeScript: subject tests (no network):
   npm run build
   npm run test:subject
