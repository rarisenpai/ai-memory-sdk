from re import I
from openai import OpenAI
from memory import Memory

openai_client = OpenAI()
memory = Memory()

max_messages = 10
keep_last_n_messages = 3

def compact(messages, user_id: str = "default_user") -> str:
    """ Compact the messages to keep only the last n messages """

    # learn message state 
    run = memory.add_messages(user_id, messages)
    messages = messages[-keep_last_n_messages:]

    # get the user memory and summary (can also run in another thread)
    memory.wait_for_run(run)

    return messages 

def chat_with_memories(message: str, user_id: str = "default_user") -> str:

    # get the user memory 
    user_memory = memory.get_user_memory(user_id)
    if not user_memory:
        memory.initialize_user_memory(user_id, reset=True)
        user_memory = memory.get_user_memory(user_id)
    
    # format the user memory 
    user_memory_prompt= memory.get_user_memory(user_id, prompt_formatted=True)
    summary_prompt = memory.get_summary(user_id, prompt_formatted=True)

    # generate the assistant response
    system_prompt = f"<system>You are a helpful AI assistant</system>"
    system_prompt += f"\n{user_memory_prompt}"
    system_prompt += f"\n{summary_prompt}"
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]
    response = openai_client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    assistant_response = response.choices[0].message.content

    # Create new memories from the conversation
    messages.append({"role": "assistant", "content": assistant_response})

    # compact the messages and update the memory/summary
    if len(messages) > keep_last_n_messages:
        print(f"Messages len is {len(messages)}, compacting...")
        messages = compact(messages, user_id)
        print(f"Messages len is {len(messages)}, compacted")

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