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

### Retrieving memories for a user
You can retrieve the summary and/or user memory for a given user with: 
```python
summary = memory.get_summary("user_id", prompt_formatted=True)
user_memory = memory.get_user_memory("user_id", prompt_formatted=True)
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


## Roadmap 
- [ ] TypeScript support 
- [ ] Learning from files
- [ ] Query historical messages 
- [ ] Save messages as archival memories
- [ ] Query archival memory
- [ ] Add "sleep" (offline collective revisioning of all data)  

