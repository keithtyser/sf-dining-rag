"""
Enhanced conversation management module with persistence and context handling.
"""

import json
import time
import uuid
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import os
from pathlib import Path
from src.api.models import Message, Conversation, ConversationMetadata

@dataclass
class Message:
    """Enhanced message class with metadata"""
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Conversation:
    """Enhanced conversation class with metadata and persistence"""
    id: str
    storage_dir: Optional[Path] = None
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    max_messages: int = 50
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a message with metadata to the conversation"""
        self.messages.append(Message(
            role=role,
            content=content,
            metadata=metadata or {}
        ))
        self.last_updated = time.time()
        self._prune_history()
        self.save()
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get formatted messages for the OpenAI API"""
        messages = self.messages[-limit:] if limit else self.messages
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    def get_context_window(self, window_size: int = 5) -> List[Dict[str, str]]:
        """Get the most recent context window of messages"""
        return self.get_messages(limit=window_size)
    
    def _prune_history(self) -> None:
        """Prune conversation history if it exceeds max_messages"""
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary for storage"""
        try:
            return {
                "id": self.id,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp,
                        "metadata": {
                            k: str(v) if not isinstance(v, (str, int, float, bool, dict, list)) else v
                            for k, v in msg.metadata.items()
                        }
                    }
                    for msg in self.messages
                ],
                "metadata": {
                    k: str(v) if not isinstance(v, (str, int, float, bool, dict, list)) else v
                    for k, v in self.metadata.items()
                },
                "max_messages": self.max_messages,
                "created_at": self.created_at,
                "last_updated": self.last_updated
            }
        except Exception as e:
            print(f"Error serializing conversation {self.id}: {e}")
            # Return a minimal serializable version
            return {
                "id": self.id,
                "messages": [],
                "metadata": {},
                "max_messages": self.max_messages,
                "created_at": self.created_at,
                "last_updated": self.last_updated
            }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], storage_dir: Optional[Path] = None) -> 'Conversation':
        """Create conversation instance from dictionary"""
        conv = cls(
            id=data["id"],
            storage_dir=storage_dir,
            metadata=data.get("metadata", {}),
            max_messages=data.get("max_messages", 50)
        )
        conv.created_at = data.get("created_at", time.time())
        conv.last_updated = data.get("last_updated", time.time())
        
        # Restore messages
        for msg_data in data.get("messages", []):
            msg = Message(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=msg_data.get("timestamp", time.time()),
                metadata=msg_data.get("metadata", {})
            )
            conv.messages.append(msg)
        
        return conv
    
    def save(self) -> None:
        """Save conversation to disk"""
        if not self.storage_dir:
            print(f"Warning: No storage directory set for conversation {self.id}")
            return
            
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = self.storage_dir.absolute() / f"{self.id}.json"
            print(f"Saving conversation {self.id} to {file_path}")
            with open(file_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            print(f"Successfully saved conversation {self.id}")
        except Exception as e:
            print(f"Error saving conversation {self.id}: {e}")

class ConversationManager:
    """Manages multiple conversations with persistence"""
    def __init__(self, storage_dir: str = "conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.conversations: Dict[str, Conversation] = {}
        self._load_conversations()
    
    def _load_conversations(self) -> None:
        """Load all conversations from disk"""
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    conv = Conversation.from_dict(data, storage_dir=self.storage_dir)
                    self.conversations[conv.id] = conv
            except Exception as e:
                print(f"Error loading conversation {file_path}: {e}")
    
    def _save_conversation(self, conversation: Conversation) -> None:
        """Save conversation to disk"""
        if not conversation.storage_dir:
            print(f"Warning: No storage directory set for conversation {conversation.id}")
            return
            
        try:
            conversation.storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = conversation.storage_dir.absolute() / f"{conversation.id}.json"
            print(f"Saving conversation {conversation.id} to {file_path}")
            with open(file_path, "w") as f:
                json.dump(conversation.to_dict(), f, indent=2)
            print(f"Successfully saved conversation {conversation.id}")
        except Exception as e:
            print(f"Error saving conversation {conversation.id}: {e}")
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def add_message(self, conversation_id: str, role: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a message to a conversation"""
        conv = self.get_conversation(conversation_id)
        if conv:
            conv.storage_dir = self.storage_dir  # Ensure storage directory is set
            conv.add_message(role, content, metadata)
    
    def get_recent_conversations(self, limit: int = 10) -> List[Conversation]:
        """Get most recent conversations"""
        sorted_convs = sorted(
            self.conversations.values(),
            key=lambda x: x.last_updated,
            reverse=True
        )
        return sorted_convs[:limit]
    
    def cleanup_old_conversations(self, days_old: int = 30) -> None:
        """Remove conversations older than specified days"""
        cutoff = datetime.now() - timedelta(days=days_old)
        to_remove = []
        
        for conv_id, conv in self.conversations.items():
            if conv.last_updated < cutoff:
                to_remove.append(conv_id)
                # Remove file
                file_path = self.storage_dir / f"{conv_id}.json"
                if file_path.exists():
                    file_path.unlink()
        
        # Remove from memory
        for conv_id in to_remove:
            del self.conversations[conv_id]

async def get_conversation_history(conversation_id: Optional[str]) -> List[Dict[str, Any]]:
    """Get conversation history for a given conversation ID"""
    if not conversation_id:
        return []
        
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        return []
        
    return [
        {
            "role": msg.role,
            "content": msg.content
        }
        for msg in conversation.messages
    ]

async def save_conversation(conversation_id: Optional[str], query: str, response: str):
    """Save a conversation message and response"""
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        now = time.time()
        metadata = {
            "created_at": now,
            "last_updated": now,
            "message_count": 0,
            "metadata": {}
        }
        conversation = Conversation(
            id=conversation_id,
            storage_dir=conversation_manager.storage_dir,
            messages=[],
            metadata=metadata
        )
        conversation_manager.conversations[conversation_id] = conversation
    
    # Add user message
    conversation.messages.append(Message(
        role="user",
        content=query,
        timestamp=time.time(),
        metadata={"type": "user_message"}
    ))
    
    # Add assistant response
    conversation.messages.append(Message(
        role="assistant",
        content=response,
        timestamp=time.time(),
        metadata={"type": "assistant_response"}
    ))
    
    # Update conversation metadata
    conversation.metadata["last_updated"] = time.time()
    conversation.metadata["message_count"] = len(conversation.messages)
    
    # Save conversation
    conversation_manager._save_conversation(conversation)

# Initialize global conversation manager
conversation_manager = ConversationManager() 