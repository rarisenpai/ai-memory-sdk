from typing import List, Dict, Any, Optional
import time 
import os
from letta_client import Letta
from prompt_formatter import format_messages
from schemas import MessageCreate

class Memory: 
    """ A memory SDK for Letta """

    def __init__(self, 
        letta_api_key: Optional[str] = None,
    ):
        if letta_api_key is None:
            letta_api_key = os.getenv("LETTA_API_KEY")
        self.letta_client = Letta(token=letta_api_key)

    def _create_sleeptime_agent(self, name: str, tags: List[str]): 
        """ Create a subconscious agent that learns over time """ 
        agent_state = self.letta_client.agents.create(
            name=name,
            model="openai/gpt-4.1",
            agent_type="sleeptime_agent",
            initial_message_sequence=[], 
            tags=tags
        )
        return agent_state.id

    def _get_matching_agent(self, tags: List[str]): 
        """ Get an agent with matching tags """ 
        agents = self.letta_client.agents.list(tags=tags, match_all_tags=True)
        if agents:
            return agents[0]
        return None

    def _create_context_block(self, agent_id: str, label: str, description: str, char_limit: int = 10000, value: str = ""):
        """ Create a context block """ 
        block = self.letta_client.blocks.create(
            label=label,
            description=description,
            limit=char_limit,
            value=value,
        )
        self.letta_client.agents.blocks.attach(agent_id=agent_id, block_id=block.id)
        return block.id

    def _list_context_blocks(self, agent_id: str):
        """ List all context blocks for an agent """ 
        return self.letta_client.agents.blocks.list(agent_id=agent_id)

    def _delete_context_block(self, agent_id: str, block_id: str):
        """ Delete a context block """ 
        self.letta_client.agents.blocks.detach(agent_id=agent_id, block_id=block_id)
        self.letta_client.blocks.delete(block_id=block_id)

    def _delete_agent(self, agent_id: str):
        """ Delete an agent """ 
        self.letta_client.agents.delete(agent_id=agent_id)

    def _learn_messages(self, agent_id: str, messages: List[Dict[str, Any]]):
        """ Learn messages """ 
        formatted_messages = format_messages([MessageCreate(**msg) for msg in messages])
        print("FORMATTED MESSAGES", formatted_messages)
        print("AGENT ID", agent_id)
        letta_run = self.letta_client.agents.messages.create_async(
            agent_id=agent_id,
            messages=formatted_messages
        )
        return letta_run.id

    def _format_block(self, block): 
        """ Format a block for a prompt """ 
        return f"<{block.label} description=\"{block.description}\">{block.value}</{block.label}>"

    def _get_run_status(self, run_id: str):
        """ Get the status of a run """ 

        run = self.letta_client.runs.retrieve(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        return run.status

    def wait_for_run(self, run_id: str):
        """ Wait for a run to complete """ 
        while self._get_run_status(run_id) != "completed":
            time.sleep(1)

    def initialize_user_memory(self, 
        user_id: str, 
        user_context_block_prompt: str = "Details about the human user you are speaking to.",
        user_context_block_char_limit: int = 10000,
        user_context_block_value: str = "",
        summary_block_prompt: str = "A short (1-2 sentences) running summary of the conversation.",
        summary_block_char_limit: int = 1000,
        reset: bool = False # whether to reset existing memory
    ): 
        """ Initialize a user's memory """ 

        # check if agent aleady exists
        agent = self._get_matching_agent(tags=[user_id])
        if agent:
            if reset:
                self._delete_agent(agent.id)
            else:
                raise ValueError(f"Agent {agent.id} already exists for user {user_id}. Cannot re-initialize memory unless deleted.")
        
        # create the agent 
        agent_id = self._create_sleeptime_agent(name=f"subconscious_agent_user_{user_id}", tags=[user_id])
        
        # create context blocks
        self._create_context_block(agent_id=agent_id, label="human", description=user_context_block_prompt, char_limit=user_context_block_char_limit, value=user_context_block_value)
        self._create_context_block(agent_id=agent_id, label="summary", description=summary_block_prompt, char_limit=summary_block_char_limit, value="")
        return agent_id
            
    def add_messages(self, user_id: str, messages: List[Dict[str, Any]]): 
        """ Add messages corresponding to a specific user """
        agent = self._get_matching_agent(tags=[user_id])
        if agent:
            agent_id = agent.id
        else:
            agent_id = self.initialize_user_memory(user_id)

        return self._learn_messages(agent_id, messages)

    def add_files(self, files: List[Dict[str, Any]]):
        """ Learn about files """ 
        raise NotImplementedError

    def get_user_memory(self, user_id: str, prompt_formatted: bool = False):
        """ Get the memory for a specific user """ 
        agent = self._get_matching_agent(tags=[user_id])
        if agent:
            block = self.letta_client.agents.blocks.retrieve(agent.id, "human")
            if prompt_formatted: 
                return self._format_block(block)
            return block.value
        return None


    def get_summary(self, user_id: str, prompt_formatted: bool = False):
        """ Get the summary for a specific user """ 
        agent = self._get_matching_agent(tags=[user_id])
        if agent:
            block = self.letta_client.agents.blocks.retrieve(agent.id, "summary")
            if prompt_formatted: 
                return f"<conversation_summary>{block.value}</conversation_summary>"
            return block.value
        return None

    def delete_user(self, user_id: str):
        """ Delete a user """ 
        agent = self._get_matching_agent(tags=[user_id])
        if agent:
            # deleting the agent also deleted associated messages/blocks
            self.letta_client.agents.delete(agent.id)
            print(f"Deleted agent {agent.id} for user {user_id}")