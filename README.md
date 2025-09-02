# Learned Context SDK 
Create a subconsious for your agent that can learn and form memories in the background (using sleeptime compute) that you can plug into your agent's context. Subconsious agents can learn from conversational interactions (`user`/`assistant` messages), files, and other text content. Learned context blocks be appended to your agent's system prompt - a form of "system prompt learning". 
```
+========================================+
|         SYSTEM PROMPT                  |
+========================================+
|    LEARNED CONTEXT (USER)              | <- Subconscious Agent (learning from message history)
+========================================+
|    LEARNED CONTEXT (FILES)             | <- Subconscious Agent (learning from files) 
+========================================+
|           MESSAGES                     |
|  * User -> Assistant                   |
|  * User -> Assistant                   |
|  * User -> Assistant                   |
|  * ...                                 |
+========================================+
```
You can use the Learned Context SDK directly, or user wrapper classes like the `ConversationalMemoryClient` specifically for conversational memory. 

Example: Create a basic OpenAI `gpt-4o-mini` chat agent with memory 
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
The `ConversationalMemoryClient` provides a simple interface for logging conversation history and retrieving user memory.

```python
from learned_context_sdk import ConversationalMemoryClient

client = ConversationalMemoryClient(letta_api_key=os.getenv("LETTA_API_KEY"))

# log conversation history 
client.add(
    user_id="user123",
    messages=[
        {"role": "user", "content": "Hello, my name is Sarah"},
        {"role": "assistant", "content": "Hi Sarah! Nice to meet you."}
    ]
)

# get user memory 
memory = client.get_user_memory(user_id="user123")
print(memory)

# delete user memory 
client.delete_user(user_id="user123")
```
```typescript

import { ConversationalMemoryClient } from 'learned-context-sdk';

const client = new ConversationalMemoryClient(letta_api_key=os.getenv("LETTA_API_KEY"))

client.add(
    user_id="user123",
    messages=[
        {role: "user", content: "Hello, my name is Sarah"},
        {role: "assistant", content: "Hi Sarah! Nice to meet you."}
    ]
)

// get user memory 
const memory = client.get_user_memory(user_id="user123")
console.log(memory)

// delete user memory 
client.delete_user(user_id="user123")
```

#### Knowledge Base Memory 
The `KnowledgeBaseMemoryClient` provides a simple interface for creating subconsious agents that can learn from files or other text content. 
(TODO) 


