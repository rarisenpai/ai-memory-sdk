from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal


# Identity type options (from Letta API)
IdentityTypeEnum = Literal["user", "org", "other"]


# Base Response Model (must be defined first)
class BaseResponse(BaseModel):
    success: bool
    error: Optional[str] = None


# Block Definition
class BlockDefinition(BaseModel):
    """Definition for a memory block"""
    label: str = Field(..., description="Block identifier (e.g., 'human', 'policies', 'preferences')")
    description: str = Field(..., description="What this block stores and when to update it")
    value: str = Field(default="", description="Initial content")
    char_limit: int = Field(default=10000, description="Maximum characters")


# Identity Request/Response Models
class CreateIdentityRequest(BaseModel):
    """Create a new identity"""
    identifier_key: str = Field(..., description="Unique identifier (e.g., user_id, org_id)")
    name: Optional[str] = Field(None, description="Display name")
    identity_type: IdentityTypeEnum = Field(default="user", description="Type of identity")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "identifier_key": "alice@example.com",
                    "name": "Alice Smith",
                    "identity_type": "user"
                },
                {
                    "identifier_key": "acme_corp",
                    "name": "Acme Corporation",
                    "identity_type": "org"
                },
                {
                    "identifier_key": "support_bot",
                    "name": "Support Bot",
                    "identity_type": "other"
                }
            ]
        }
    }


class CreateIdentityResponse(BaseResponse):
    identity_id: Optional[str] = None
    identifier_key: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None


class IdentityInfoResponse(BaseResponse):
    identity_id: Optional[str] = None
    identifier_key: Optional[str] = None
    name: Optional[str] = None
    identity_type: Optional[str] = None
    agent_ids: List[str] = []
    message: Optional[str] = None


class AgentInfo(BaseModel):
    agent_id: str
    name: str
    tags: List[str] = []


class ListAgentsByIdentityResponse(BaseResponse):
    agents: List[AgentInfo] = []
    count: int = 0


# Initialize User Request/Response Models
class InitializeUserRequest(BaseModel):
    """Initialize memory with default blocks and identity"""
    user_id: str
    user_info: str = ""
    user_name: Optional[str] = None
    identity_type: IdentityTypeEnum = Field(default="user", description="Type of identity")
    reset: bool = False


class InitializeUserResponse(BaseResponse):
    message: Optional[str] = None
    agent_id: Optional[str] = None
    identity_id: Optional[str] = None
    identity_type: Optional[str] = None


# Initialize with Blocks Request/Response Models
class InitializeWithBlocksRequest(BaseModel):
    """Initialize memory with custom blocks and identities"""
    user_id: str
    blocks: List[BlockDefinition]
    user_name: Optional[str] = None
    identity_type: IdentityTypeEnum = Field(default="user", description="Type of primary identity")
    additional_identity_ids: Optional[List[str]] = Field(
        None,
        description="Additional identity IDs to associate (e.g., organization, team)"
    )
    reset: bool = False
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "alice@acme.com",
                    "user_name": "Alice Smith",
                    "identity_type": "user",
                    "additional_identity_ids": ["identity-acme123"],
                    "blocks": [
                        {
                            "label": "human",
                            "description": "User details",
                            "value": "Name: Alice, Role: Engineer"
                        }
                    ]
                }
            ]
        }
    }


class InitializeWithBlocksResponse(BaseResponse):
    message: Optional[str] = None
    agent_id: Optional[str] = None
    identity_id: Optional[str] = None
    identity_type: Optional[str] = None
    identity_ids: Optional[List[str]] = None
    blocks_created: Optional[int] = None


# Add Conversation Request/Response Models
class AddConversationRequest(BaseModel):
    user_id: str
    messages: List[Dict[str, str]] = Field(..., description="List of message objects with 'role' and 'content'")
    store_in_archival: bool = True
    wait_for_completion: bool = True


class AddConversationResponse(BaseResponse):
    run_id: Optional[str] = None
    message: Optional[str] = None
    messages_count: Optional[int] = None


# Context Request/Response Models
class ContextResponse(BaseResponse):
    context: str = ""
    message: Optional[str] = None


class SummaryResponse(BaseResponse):
    summary: str = ""
    message: Optional[str] = None


class SearchResult(BaseModel):
    success: bool
    results: List[str] = []
    count: int = 0
    total_found: Optional[int] = None
    error: Optional[str] = None


class FullContextResponse(BaseResponse):
    user_context: str = ""
    summary: str = ""
    relevant_memories: List[str] = []
    combined_context: str = ""


# Delete and Agent Response Models
class DeleteResponse(BaseResponse):
    message: Optional[str] = None


class AgentIdResponse(BaseResponse):
    agent_id: Optional[str] = None
    dashboard_url: Optional[str] = None
    message: Optional[str] = None


# Health Response Model
class HealthResponse(BaseModel):
    status: str
    service: str