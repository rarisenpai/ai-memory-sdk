"""
This is an example of using the subconscious agent to generate customer insights from a knowledge base, containing call transcripts. 
"""

from learned_context_sdk import LearnedContextClient

knowledge_base_folder = "./knowledge_base"

if __name__ == "__main__":
    client = LearnedContextClient(letta_api_key=os.getenv("LETTA_API_KEY"))
    agent = client.create_subconscious_agent()
    agent.register_file(
        file_path="tests/data/documentation/python_reference.md", 
        label="python_reference", 
        description="Python SDK reference"
    )
    run = agent.learn()
    while run.get_status() != "completed":
        time.sleep(1)
        print("STATUS", run.get_status())
    print("Run completed")