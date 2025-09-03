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

### Quickstart 
1. Create an [Letta API Key](https://app.letta.com/api-keys)
2. Run `export LETTA_API_KEY=...`
3. Install: `pip install letta-memory`

### Usage: Conversational Memory 
You can save conversation histories using the Memory SDK, and later retrieve the learned context block to place into your system prompt. This allows your agents to have an evolving understand of the user. 
**Example:** Create a basic OpenAI `gpt-4o-mini` chat agent with memory 
```python
from openai import OpenAI
from memory import Memory

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


## Roadmap 
- [ ] Learning from files
- [ ] Query historical messages 
- [ ] Save messages as archival memories
- [ ] Query archival memory
- [ ] Add "sleep" (offline collective revisioning of all data)  

