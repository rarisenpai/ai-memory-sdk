from re import A
from letta_client import Letta
import time
try:
    from .database import SubconsciousDatabase, Message, File, MessageCreate, DatabaseStats
except ImportError:
    from database import SubconsciousDatabase, Message, File, MessageCreate, DatabaseStats
from typing import List, Dict, Any
import json
try:
    from .prompt_formatter import format_messages, format_files
except ImportError:
    from prompt_formatter import format_messages, format_files

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
            # Format messages properly for the API
            index = 0   
            for messages in message_to_send:
                print("SENDING MESSAGES", len(str(messages)))
                letta_run = self.letta_client.agents.messages.create_async(
                    agent_id=self.agent_id,
                    messages=[messages]
                )
                # wait until run is completed
                run = Run(run_id=letta_run.id, letta_client=self.letta_client)
                while run.get_status() != "completed":
                    time.sleep(1)
                    print(f"Run {index}/{len(message_to_send)} STATUS", run.get_status())
                index += 1
        else:
            # No messages to process, create a dummy run
            run = type('Run', (), {'id': 'no-processing-needed'})()
         
        return Run(run_id=run.id, letta_client=self.letta_client)

    def learn_messages(self, messages: List[Dict[str, Any]]) -> Run:
        """ Learn from a list of messages """ 
        self.register_messages(messages)

        unprocessed_messages = self.db.get_unprocessed_messages(self.agent_id)
        formatted_messages = format_messages(unprocessed_messages)
        print("FORMATTED MESSAGES", formatted_messages)
        letta_run = self.letta_client.agents.messages.create_async(
            agent_id=self.agent_id,
            messages=formatted_messages
        )
        return Run(run_id=letta_run.id, letta_client=self.letta_client)

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
        self.letta_client = Letta(token=letta_api_key)

    def create_subconscious_agent(self, tags: List[str], name: str = "subconscious_agent"):
        """ Create a subconscious agent that learns over time """
        agent = self.letta_client.agents.create(
            name=name,
            model="openai/gpt-4.1",
            agent_type="sleeptime_agent",
            initial_message_sequence=[], 
            tags=tags
        )
        print("tools", [t.name for t in agent.tools])
        print("NAME", agent.name)
        agent =self.letta_client.agents.modify(agent_id=agent.id, tags=tags)
        print("UPDATE TAGS", agent.tags)
        #assert self.list_subconscious_agents(tags=tags), f"Agent with tags {tags} not found"
        return SubconsciousAgent(agent_id=agent.id, letta_client=self.letta_client)

    def list_subconscious_agents(self, tags: List[str]):
        #agents = self.letta_client.agents.list()
        #for agent in agents:
        #    print("TAGS MATCH", tags, agent.tags)
        return self.letta_client.agents.list(name=f"subconscious_agent_user_{tags[0]}")
        return self.letta_client.agents.list(tags=tags, match_all_tags=False)
        

class ConversationalMemoryClient: 
    def __init__(self, letta_api_key: str):
        self.letta_client = Letta(token=letta_api_key)
        self.client = LearnedContextClient(letta_api_key)

    def add(self, user_id: str, messages: List[Dict[str, Any]]): 
        """ Add messages corresponding to a specific user """
        agent = self.client.list_subconscious_agents(tags=[user_id])
        if agent:
            agent = agent[0]
            print("AGENT EXISTS", agent)
            return agent.learn_messages(messages)
        else:
            print("CREATING AGENT")
            agent = self.client.create_subconscious_agent(tags=[user_id], name=f"subconscious_agent_user_{user_id}")
            agent.create_learned_context_block(
                label="human", 
                description="Information about the human user you are speaking to", 
                char_limit=10000, 
                value="", 
            )
            agent.create_learned_context_block(
                label="summary", 
                description="A short (1-2 sentences) running summary of the conversation", 
                char_limit=1000, 
                value="", 
            )
 
            print("AGENT CREATED", agent.list_learned_context_blocks())

            print("TAGS", self.letta_client.agents.retrieve(agent_id=agent.agent_id).tags)
            return agent.learn_messages(messages)

    def get_user_memory(self, user_id: str):
        """ Get the memory for a specific user """ 
        agent = self.client.list_subconscious_agents(tags=[user_id])
        if not agent:
            print("NO AGENTS WITH TAGS", user_id)
            return None
        if agent:
            agent = agent[0]
            print("AGENT", agent, agent.id)
            return SubconsciousAgent(agent_id=agent.id, letta_client=self.letta_client).get_learned_context_block("human")
        return None

    def delete_user(self, user_id: str):
        """ Delete a user """ 
        agent = self.client.list_subconscious_agents(tags=[user_id])
        if agent:
            agent = agent[0]
            self.letta_client.agents.delete(agent.id)
            print(f"Deleted agent {agent.id} for user {user_id}")