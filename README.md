# Memory SDK 
An experimental SDK for using Letta agents for long-term memory and learning in a pluggable way. When messages are added, subconsious memory agents process them to generate *learned context* that can be plugged into your system prompt, such as a user profile or a conversational summary. 
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
You can customize the prompt format by getting the raw summary or user block string with `prompt_formatted=False`.

## Quickstart 
1. Create an [Letta API Key](https://app.letta.com/api-keys)
2. Run `export LETTA_API_KEY=...`
3. Install: `pip install letta-memory`

### Usage: Conversational Memory 
You can save conversation histories using the Memory SDK, and later retrieve the learned context block to place into your system prompt. This allows your agents to have an evolving understand of the user. 
**Example:** Create a basic OpenAI `gpt-4o-mini` chat agent with memory 
```python
from openai import OpenAI
from letta_memory import Memory

openai_client = OpenAI()
memory = Memory()

def chat_with_memories(message: str, user_id: str = "default_user") -> str:

    # get the user memory 
    user_memory = memory.get_user_memory(user_id)
    if not user_memory:
        memory.initialize_user_memory(user_id, reset=True)
        user_memory = memory.get_user_memory(user_id)
    
    # format the user memory 
    user_memory_prompt= memory.get_user_memory(user_id, prompt_formatted=True)

    # generate the assistant response
    system_prompt = f"<system>You are a helpful AI assistant</system>"
    system_prompt += f"\n{user_memory_prompt}"
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]
    response = openai_client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    assistant_response = response.choices[0].message.content

    # Create new memories from the conversation
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

## SDK Reference
You can initialize the memory SDK with:
```python
from letta_memory import Memory

memory = Memory()
```

### Adding memories 
Save messages by adding them to memory: 
```python
run = memory.add_messages("user_id", [{"role": "user", "content": "hi"}])
```
This will send the messages to the memory agent for processing. Note that each time you add messages, this will trigger an invocation of the memory agent. To reduce costs, you may want to batch together multiple messages (recommended 5-10). 

### Waiting for learning completition
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

