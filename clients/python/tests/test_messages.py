import pytest
from learned_context.client import SubconsciousAgent, LearnedContextClient, ConversationalMemoryClient
import os
import time

def test_messages():
    """ Register messages and learn from them """

    client = LearnedContextClient(letta_api_key=os.getenv("LETTA_API_KEY"))

    # create the subconscious agent
    agent = client.create_subconscious_agent()
    print("AGENT ID", agent.agent_id)
    agent.create_learned_context_block(
        label="human", 
        description="Information about the human user you are speaking to", 
        char_limit=10000, 
        value=""
    )
    # get the blocks 
    blocks = agent.list_learned_context_blocks()
    assert len(blocks) == 1, f"Expected 1 block, got {len(blocks)}"
    assert blocks[0].label == "human", f"Expected 'human' block, got {blocks[0].label}"

    # register messages 
    agent.register_messages(messages=[
        {
            "role": "user",
            "content": "Hi my name is Bob"
        }, 
        {
            "role": "assistant",
            "content": "Hi Bob, how are you?"
        }, 
        {
            "role": "user",
            "content": "I'm doing well, thank you!"
        }
    ])

    # do some learning 
    run = agent.learn()

    while run.get_status() != "completed":
        time.sleep(1)
        print("STATUS", run.get_status())

    print("Run completed")



    # get the block data 
    human_block = agent.get_learned_context_block("human")
    assert "Bob" in human_block.value, f"Expected 'Bob' in human block value, got {human_block.value}"

def test_conversational_memory():
    """ Test the conversational memory client """
    client = ConversationalMemoryClient(letta_api_key=os.getenv("LETTA_API_KEY"))
    test_user_id = "test_user_id_123"
    client.delete_user(test_user_id)
    run =  client.add(test_user_id, messages=[
        {
            "role": "user",
            "content": "Hi my name is Bob"
        }
    ])

    # wait for the run to complete
    while run.get_status() != "completed":
        time.sleep(1)
        print("STATUS", run.get_status())

    # get the memory 
    memory = client.get_user_memory(test_user_id)
    assert "Bob" in memory.value, f"Expected 'Bob' in memory value, got {memory.value}"
    print(memory)






    
    
    