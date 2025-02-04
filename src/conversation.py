"""
Enhanced conversation management module with persistence and context handling.
"""

import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path

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
        return {
            "id": self.id,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                for msg in self.messages
            ],
            "metadata": self.metadata,
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
            return
            
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.storage_dir / f"{self.id}.json"
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

class ConversationManager:
    """Manages multiple conversations with persistence"""
    def __init__(self, storage_dir: str = "data/conversations"):
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
    
    def get_conversation(self, conversation_id: str) -> Conversation:
        """Get or create a conversation"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = Conversation(
                id=conversation_id,
                storage_dir=self.storage_dir
            )
        return self.conversations[conversation_id]
    
    def add_message(self, conversation_id: str, role: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a message to a conversation"""
        conv = self.get_conversation(conversation_id)
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
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        to_remove = []
        
        for conv_id, conv in self.conversations.items():
            if conv.last_updated < cutoff_time:
                to_remove.append(conv_id)
                # Remove file
                file_path = self.storage_dir / f"{conv_id}.json"
                if file_path.exists():
                    file_path.unlink()
        
        # Remove from memory
        for conv_id in to_remove:
            del self.conversations[conv_id] 