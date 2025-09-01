"""
This is an example of using the subconscious agent to generate a memory for a coding agent. 
The memory is generated from a folder that contains the knowledge base for the coding agent. 
"""
from src.client import LearnedContextClient

knowledge_base_folder = "./knowledge_base"


if __name__ == "__main__":
    client = LearnedContextClient(letta_api_key=os.getenv("LETTA_API_KEY"))

    
