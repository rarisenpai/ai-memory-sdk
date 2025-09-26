from typing import List, Dict, Any, Optional
import time 
import os
import asyncio
from letta_client import Letta, AsyncLetta
from prompt_formatter import format_messages
from schemas import MessageCreate

class Memory: 
    """ A memory SDK for Letta

    Adds a general "context" model while keeping user-specific helpers.
    One context maps to one Letta agent; multiple labeled blocks (e.g. "human",
    "summary", "preferences") can be attached to that context.
    """

    def __init__(self, 
        api_key: Optional[str] = None,
        context_id: Optional[str] = None,
    ):
        if api_key is None:
            api_key = os.getenv("LETTA_API_KEY")
        self.letta_client = Letta(token=api_key)
        self.async_letta_client = AsyncLetta(token=api_key)
        # Optional default context for instance-scoped operations
        self.context_id = context_id

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

    def _context_tags(self, context_id: str) -> List[str]:
        """Standardize tags for a context. Include both a namespaced and raw tag for compatibility."""
        return [f"ctx:{context_id}", context_id]

    def _get_agent_for_context(self, context_id: str):
        """Find an agent for a given context. Tries both new and legacy tag styles."""
        # Prefer the namespaced tag
        agent = self._get_matching_agent(tags=[f"ctx:{context_id}"])
        if agent:
            return agent
        # Fallback to legacy behavior that used raw tag only
        return self._get_matching_agent(tags=[context_id])


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

    def _ensure_context(self, context_id: str) -> str:
        """Ensure a context exists and return its agent id."""
        agent = self._get_agent_for_context(context_id)
        if agent:
            return agent.id
        # Create a new agent for this context with both tags for compatibility
        agent_id = self._create_sleeptime_agent(name=f"subconscious_agent_ctx_{context_id}", tags=self._context_tags(context_id))
        # Attach a single archival memory (workaround / anchor)
        self.letta_client.agents.passages.create(
            agent_id=agent_id,
            text=f"Initialized memory for context {context_id}",
        )
        return agent_id

    def _get_effective_context(self, context_id: Optional[str]) -> str:
        """Resolve the effective context id, preferring the instance default if not provided."""
        cid = context_id or self.context_id
        if not cid:
            raise ValueError("No context_id provided and instance is not bound to a context. "
                             "Pass context_id=... or initialize Memory(context_id=...).")
        return cid

    def _find_block_by_label(self, agent_id: str, label: str):
        """Find a block object attached to an agent by label, or return None."""
        blocks = self._list_context_blocks(agent_id)
        for b in blocks:
            b_label = getattr(b, "label", None)
            if b_label is None and isinstance(b, dict):
                b_label = b.get("label")
            if b_label == label:
                return b
        return None

    def _block_id(self, block_obj: Any) -> Optional[str]:
        """Get id from a block object that may be a model or dict."""
        if block_obj is None:
            return None
        bid = getattr(block_obj, "id", None)
        if bid is None and isinstance(block_obj, dict):
            bid = block_obj.get("id")
        return bid

    async def _learn_messages(
        self, 
        agent_id: str, 
        messages: List[Dict[str, Any]], 
        skip_vector_storage: bool,
    ):
        """ Learn messages asynchronously """ 
        formatted_messages = format_messages([MessageCreate(**msg) for msg in messages])
        letta_run = self.letta_client.agents.messages.create_async(
            agent_id=agent_id,
            messages=formatted_messages
        )

        # insert into archival in parallel
        if not skip_vector_storage:
            tasks = [
                self.async_letta_client.agents.passages.create(
                    agent_id=agent_id,
                    text=message["content"],
                    tags=[message["role"]],
                )
                for message in messages
            ]
            await asyncio.gather(*tasks)

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

    # ===== General Context API =====

    def initialize_context(self, context_id: str, reset: bool = False) -> str:
        """Initialize a context (agent). If it exists and reset is False, raise; otherwise recreate.

        Returns the agent id for the context.
        """
        agent = self._get_agent_for_context(context_id)
        if agent:
            if reset:
                self._delete_agent(agent.id)
            else:
                raise ValueError(
                    f"Agent {agent.id} already exists for context {context_id}. "
                    f"Cannot re-initialize unless reset=True."
                )
        return self._ensure_context(context_id)

    def list_blocks(self, context_id: Optional[str] = None):
        """List all blocks for a context. If instance is bound, context_id may be omitted."""
        cid = self._get_effective_context(context_id)
        agent = self._get_agent_for_context(cid)
        if not agent:
            return []
        return self._list_context_blocks(agent.id)

    def initialize_memory(
        self,
        label: str,
        description: str,
        value: str = "",
        char_limit: int = 10000,
        reset: bool = False,
        context_id: Optional[str] = None,
    ) -> str:
        """Create (or optionally reset) a labeled block within a context.

        If the block exists and reset=False, this is a no-op and returns the existing block id.
        """
        cid = self._get_effective_context(context_id)
        agent_id = self._ensure_context(cid)

        existing = self._find_block_by_label(agent_id, label)
        if existing and reset:
            self._delete_context_block(agent_id, self._block_id(existing))
            existing = None

        if existing:
            return self._block_id(existing)

        return self._create_context_block(
            agent_id=agent_id,
            label=label,
            description=description,
            char_limit=char_limit,
            value=value,
        )

    def get_memory(
        self,
        label: str,
        prompt_formatted: bool = False,
        context_id: Optional[str] = None,
    ) -> Optional[str]:
        """Retrieve a labeled block from a context. Returns None if missing."""
        cid = self._get_effective_context(context_id)
        agent = self._get_agent_for_context(cid)
        if not agent:
            return None
        block = self._find_block_by_label(agent.id, label)
        if not block:
            return None
        if prompt_formatted:
            return self._format_block(block)
        value = getattr(block, "value", None)
        if value is None and isinstance(block, dict):
            value = block.get("value")
        return value

    def delete_block(self, label: str, context_id: Optional[str] = None):
        """Delete a labeled block from a context if it exists."""
        cid = self._get_effective_context(context_id)
        agent = self._get_agent_for_context(cid)
        if not agent:
            return
        block = self._find_block_by_label(agent.id, label)
        if block:
            self._delete_context_block(agent.id, self._block_id(block))

    def add_messages_for_context(
        self,
        context_id: str,
        messages: List[Dict[str, Any]],
        skip_vector_storage: bool = True,
    ) -> str:
        """Add messages to a specific context (generalized API)."""
        agent = self._get_agent_for_context(context_id)
        if agent:
            agent_id = agent.id
        else:
            agent_id = self._ensure_context(context_id)
        return asyncio.run(self._learn_messages(agent_id, messages, skip_vector_storage=skip_vector_storage))

    def add_messages_here(self, messages: List[Dict[str, Any]], skip_vector_storage: bool = True) -> str:
        """Add messages using the instance's bound context_id."""
        cid = self._get_effective_context(None)
        return self.add_messages_for_context(cid, messages, skip_vector_storage=skip_vector_storage)

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

        # attach a single archival memory (workaround)
        self.letta_client.agents.passages.create(
            agent_id=agent_id,
            text=f"Initialized memory for user {user_id}",
        )
        return agent_id
            
    def add_messages(self, user_or_messages, messages: Optional[List[Dict[str, Any]]] = None, skip_vector_storage: bool = True): 
        """Add messages.

        Two modes:
        - Legacy user mode: add_messages(user_id: str, messages: List[...], skip_vector_storage=True)
        - Context-bound mode: add_messages(messages: List[...], skip_vector_storage=True) when this instance
          was constructed with a context_id.
        """
        # If first arg is a string, treat as legacy user mode
        if isinstance(user_or_messages, str):
            user_id = user_or_messages
            if messages is None:
                raise ValueError("messages must be provided when calling add_messages(user_id, messages, ...)" )
            agent = self._get_matching_agent(tags=[user_id])
            if agent:
                agent_id = agent.id
            else:
                agent_id = self.initialize_user_memory(user_id)
            return asyncio.run(self._learn_messages(agent_id, messages, skip_vector_storage=skip_vector_storage))

        # Otherwise, treat first arg as the messages list and use the bound context
        inferred_messages = user_or_messages
        if not isinstance(inferred_messages, list):
            raise ValueError("First argument must be a user_id (str) or a messages list (List[Dict]).")
        cid = self._get_effective_context(None)
        return self.add_messages_for_context(cid, inferred_messages, skip_vector_storage=skip_vector_storage)

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

    def get_memory_agent_id(self, user_id: str):
        """ Get the agent ID for a specific user """ 
        agent = self._get_matching_agent(tags=[user_id])
        if agent:
            return agent.id
        return None

    def delete_user(self, user_id: str):
        """ Delete a user """ 
        agent = self._get_matching_agent(tags=[user_id])
        if agent:
            # deleting the agent also deleted associated messages/blocks
            self.letta_client.agents.delete(agent.id)
            print(f"Deleted agent {agent.id} for user {user_id}")

    def search(self, user_id: str, query: str):
        """ Search for stored user messages """ 
        agent = self._get_matching_agent(tags=[user_id])
        if agent:
            response = self.letta_client.agents.passages.search(agent_id=agent.id, query=query, tags=["user"])
            return [result.content for result in response.results]
