from letta_client import Letta
try:
    from .database import SubconsciousDatabase, Message, File, MessageCreate, DatabaseStats
except ImportError:
    from database import SubconsciousDatabase, Message, File, MessageCreate, DatabaseStats
from typing import List, Dict, Any
import json
try:
    from .prompt_formatter import format_messages, format_files
except ImportError:
    # Fallback to local implementation if prompt_formatter doesn't exist
    def format_messages(messages: List[Message]) -> List[Dict[str, str]]:
        """Format messages for API call"""
        return [{"role": "user", "content": f"<messages>The following message interactions have occured:\n" + 
                "\n".join([f"{msg.role}: {msg.content}" for msg in messages]) + "</messages>"}]
    
    def format_files(files: List[File]) -> List[Dict[str, str]]:
        """Format files for API call"""  
        return []

class Run: 
    """ Represents a Letta agent run, which is an invocation of an gent. 

    """

    def __init__(self, run_id: str, letta_client: Letta):
        self.run_id = run_id
        self.letta_client = letta_client

    def get_status(self): 
        return self.letta_client.runs.retrieve(self.run_id).status


class SubconsciousAgent:
    """ A subconscious agent that learns over time. 

    This agent generates "learned context" that is written to context blocks. These context blocks can be customized to 
    store specific learnings, or they can be used to store general context about the user's state. 

    You can register messages or data from external agents/applications with this agent. 

    When you call `learn()`, the agent will process all registered messages and data, and generate learned context. 
    """
    def __init__(self, agent_id: str, letta_client: Letta, db_path: str = "subconscious.db"):
        self.agent_id = agent_id
        self.letta_client = letta_client
        self.db = SubconsciousDatabase(db_path)  

    def learn(self, revise: bool = False) -> Run: 
        """ Learn about the existing state """ 
        if revise:
            self.db.reset_processing_status(self.agent_id)
        
        # Get unprocessed items
        unprocessed_messages = self.db.get_unprocessed_messages(self.agent_id)
        unprocessed_files = self.db.get_unprocessed_files(self.agent_id)

        # aggregate messages to send 
        message_to_send = []
        
        # Process messages
        if unprocessed_messages:
            self.db.mark_messages_processed([msg.id for msg in unprocessed_messages])
            message_to_send += format_messages(unprocessed_messages)
        
        # Process files  
        if unprocessed_files:
            self.db.mark_files_processed([file_obj.id for file_obj in unprocessed_files])
            # TODO: implement this - chunk into message chunks
            message_to_send += format_files(unprocessed_files)
        
        # Create a run to track the learning process
        if message_to_send:
            print("SENDING MESSAGES", message_to_send)
            # Format messages properly for the API
            
            run = self.letta_client.agents.messages.create_async(
                agent_id=self.agent_id,
                messages=message_to_send
            )
        else:
            # No messages to process, create a dummy run
            run = type('Run', (), {'id': 'no-processing-needed'})()
         
        return Run(run_id=run.id, letta_client=self.letta_client)

    def register_messages(self, messages: List[Dict[str, Any]]) -> int:
        """ Register a list of messages to the subconscious agent """
        # Convert dict messages to MessageCreate objects
        message_objects = []
        for msg in messages:
            message_obj = MessageCreate(
                content=msg.get('content', ''),
                role=msg.get('role'),
                name=msg.get('name'),
                metadata={k: v for k, v in msg.items() if k not in ['content', 'role', 'name']}
            )
            message_objects.append(message_obj)
        
        return self.db.register_messages(self.agent_id, message_objects)

    def register_file(self, file_path: str, label: str, description: str) -> bool:
        """ Register a file to the subconscious agent """
        return self.db.register_file(self.agent_id, file_path, label, description)

    def create_learned_context_block(self, label: str, value: str, description: str, char_limit: int = 10000):
        """ Create a context block storing specific learnings """ 
        block = self.letta_client.blocks.create(
            label=label,
            description=description,
            limit=char_limit,
            value=value,
        )
        self.letta_client.agents.blocks.attach(agent_id=self.agent_id, block_id=block.id)
        return block

    def list_learned_context_blocks(self):
        """ List all learned context blocks """ 
        blocks = self.letta_client.agents.blocks.list(agent_id=self.agent_id)
        return blocks

    def delete_learned_context_block(self, label: str):
        """ Delete a learned context block """ 
        blocks = self.list_learned_context_blocks()
        for block in blocks:
            if block.label == label:
                self.letta_client.agents.blocks.delete(agent_id=self.agent_id, block_id=block.id)
                return True
        return False

    def get_learned_context_block(self, label: str):
        """ Get a learned context block """ 
        block = self.letta_client.agents.blocks.retrieve(agent_id=self.agent_id, block_label=label)
        print("AGENT ID", self.agent_id)
        return block

    def get_stats(self) -> DatabaseStats:
        """ Get statistics about registered and processed items """
        return self.db.get_stats(self.agent_id)


class LearnedContextClient:
    def __init__(self, letta_api_key: str):
        self.letta_client = Letta(token=letta_api_key, project="sarah-wooders-s-project_e3e7845a-d823-4ad9-8b8d-0f4debfe8da7")

    def create_subconscious_agent(self):
        """ Create a subconscious agent that learns over time """
        agent = self.letta_client.agents.create(
            name="subconscious_agent",
            model="openai/gpt-4.1",
            agent_type="sleeptime_agent",
            initial_message_sequence=[]
        )
        print("tools", [t.name for t in agent.tools])
        return SubconsciousAgent(agent_id=agent.id, letta_client=self.letta_client)