import pytest
from memory import Memory 
import os
import time

def test_conversational_memory():
    """ Test the conversational memory client """
    client = Memory(letta_api_key=os.getenv("LETTA_API_KEY"))
    test_user_id = "test_user_id_123"

    # initialize the userA
    client.initialize_user_memory(test_user_id, reset=True)

    # add messages 
    run =  client.add_messages(test_user_id, messages=[
        {
            "role": "user",
            "content": "Hi my name is Bob"
        }
    ])

    # wait for the run to complete
    client.wait_for_run(run)

    # get the memory 
    memory = client.get_user_memory(test_user_id)
    assert "Bob" in memory, f"Expected 'Bob' in memory value, got {memory}"
    print(memory)


