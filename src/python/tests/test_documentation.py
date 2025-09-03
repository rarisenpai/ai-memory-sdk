import pytest
import os
import time
from learned_context.client import LearnedContextClient

def test_documentation():

    client = LearnedContextClient(letta_api_key=os.getenv("LETTA_API_KEY"))

    # create the subconscious agent
    agent = client.create_subconscious_agent()
    print("AGENT ID", agent.agent_id)
    agent.create_learned_context_block(
        label="reference", 
        description="Documentation reference with coding examples",
        char_limit=10000, 
        value=""
    )
    # get the blocks 
    blocks = agent.list_learned_context_blocks()
    assert len(blocks) == 1, f"Expected 1 block, got {len(blocks)}"
    assert blocks[0].label == "reference", f"Expected 'reference' block, got {blocks[0].label}"

    # register files 
    agent.register_file(
        file_path="tests/data/documentation/python_reference.md", 
        label="python_reference", 
        description="Python SDK reference"
    )

    # do some learning 
    run = agent.learn()

    while run.get_status() != "completed":
        time.sleep(1)
        print("STATUS", run.get_status())

    print("Run completed")
