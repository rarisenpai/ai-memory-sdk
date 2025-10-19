from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from ..models import (
    InitializeUserRequest,
    InitializeUserResponse,
    InitializeWithBlocksRequest,
    InitializeWithBlocksResponse,
    AddConversationRequest,
    AddConversationResponse,
    ContextResponse,
    SummaryResponse,
    SearchResult,
    FullContextResponse,
    DeleteResponse,
    AgentIdResponse,
    CreateIdentityRequest,
    CreateIdentityResponse,
    IdentityInfoResponse,
    ListAgentsByIdentityResponse,
)
from ..memory_service import MemoryService
import os
from dotenv import load_dotenv
load_dotenv()

router = APIRouter(prefix="/memory", tags=["memory"])

# Initialize memory service
memory_service = MemoryService(
    api_key=os.getenv("LETTA_API_KEY"),
    base_url=os.getenv("LETTA_BASE_URL")
)


@router.post("/identity", response_model=CreateIdentityResponse)
async def create_identity(request: CreateIdentityRequest):
    """
    Create a new identity
    
    Use this to create identities for different entity types:
    - user: Individual users
    - org: Organizations or companies
    - other: Bots, systems, teams, or custom types
    """
    result = memory_service.create_identity(
        identifier_key=request.identifier_key,
        name=request.name,
        identity_type=request.identity_type
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    
    return result


@router.get("/identity/{identifier_key}", response_model=IdentityInfoResponse)
async def get_identity_info(identifier_key: str):
    """Get identity information"""
    result = memory_service.get_identity_info(identifier_key=identifier_key)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Identity not found"))
    
    return result


@router.get("/identity/{identifier_key}/agents", response_model=ListAgentsByIdentityResponse)
async def list_agents_by_identity(identifier_key: str):
    """List all agents associated with an identity"""
    result = memory_service.list_agents_by_identity(identifier_key=identifier_key)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to list agents"))
    
    return result


@router.post("/initialize", response_model=InitializeUserResponse)
async def initialize_user(request: InitializeUserRequest):
    """
    Initialize memory for a user with default blocks (human, summary)
    
    For custom blocks, use /initialize-with-blocks
    For block management, use Letta API directly
    """
    result = memory_service.initialize_user(
        user_id=request.user_id,
        user_info=request.user_info,
        user_name=request.user_name,
        identity_type=request.identity_type,
        reset=request.reset
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    
    return result


@router.post("/initialize-with-blocks", response_model=InitializeWithBlocksResponse)
async def initialize_with_blocks(request: InitializeWithBlocksRequest):
    """
    Initialize memory with custom blocks and identities
    
    Use this for advanced use cases like:
    - Customer support bots (customer_profile, support_history, policies)
    - Personal assistants (preferences, goals, schedule)
    - Domain experts (knowledge_base, recent_updates, guidelines)
    """
    # Convert Pydantic models to dicts
    blocks = [block.model_dump() for block in request.blocks]
    
    result = memory_service.initialize_with_blocks(
        user_id=request.user_id,
        blocks=blocks,
        user_name=request.user_name,
        identity_type=request.identity_type,
        additional_identity_ids=request.additional_identity_ids,
        reset=request.reset
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    
    return result


@router.post("/add", response_model=AddConversationResponse)
async def add_conversation(request: AddConversationRequest):
    """
    Add conversation messages to memory
    
    The Letta sleeptime agent processes messages and updates memory blocks
    """
    result = memory_service.add_conversation(
        messages=request.messages,
        user_id=request.user_id,
        store_in_archival=request.store_in_archival,
        wait_for_completion=request.wait_for_completion
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    
    return result


@router.get("/context", response_model=FullContextResponse)
async def get_full_context(
    user_id: str = Query(..., description="User identifier"),
    query: Optional[str] = Query(None, description="Optional query to search for relevant memories"),
    max_results: int = Query(3, description="Number of search results to include"),
    include_summary: bool = Query(True, description="Include conversation summary")
):
    """
    Get comprehensive context for injecting into LLM system prompts
    
    Returns user context, summary, and relevant memories from semantic search
    """
    result = memory_service.get_full_context(
        current_query=query,
        user_id=user_id,
        max_search_results=max_results,
        include_summary=include_summary
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Context not found"))
    
    return result


@router.get("/user-context", response_model=ContextResponse)
async def get_user_context(
    user_id: str = Query(..., description="User identifier"),
    format: str = Query("xml", description="Format: 'xml' or 'raw'")
):
    """Get user memory block only"""
    result = memory_service.get_user_context(user_id=user_id, format=format)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "User context not found"))
    
    return result


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    user_id: str = Query(..., description="User identifier"),
    format: str = Query("xml", description="Format: 'xml' or 'raw'")
):
    """Get conversation summary block only"""
    result = memory_service.get_summary(user_id=user_id, format=format)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Summary not found"))
    
    return result


@router.get("/search", response_model=SearchResult)
async def search_memories(
    user_id: str = Query(..., description="User identifier"),
    query: str = Query(..., description="Search query"),
    max_results: int = Query(5, description="Maximum number of results"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by (e.g., 'user,assistant')")
):
    """
    Semantic search over conversation history
    
    Requires archival storage enabled when adding messages
    """
    tags_list = None
    if tags:
        tags_list = [t.strip() for t in tags.split(',')]
    
    result = memory_service.search_memories(
        query=query,
        user_id=user_id,
        max_results=max_results,
        tags=tags_list
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Search failed"))
    
    return result


@router.delete("/user/{user_id}", response_model=DeleteResponse)
async def delete_user(user_id: str):
    """Delete all memory for a user"""
    result = memory_service.delete_user(user_id=user_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Delete failed"))
    
    return result


@router.get("/agent/{user_id}", response_model=AgentIdResponse)
async def get_agent_id(user_id: str):
    """Get Letta agent ID and dashboard URL for a user"""
    result = memory_service.get_agent_id(user_id=user_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Agent not found"))
    
    return result