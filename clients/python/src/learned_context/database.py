import sqlite3
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel


class Message(BaseModel): 
    """ Represents a message in the conversation """
    id: int
    agent_id: str
    content: str
    processed: bool
    role: Optional[str] = None
    name: Optional[str] = None
    registered_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class File(BaseModel):
    """ Represents a file in the database """
    id: int
    agent_id: str
    file_path: str
    file_hash: str
    size: int
    last_modified: datetime
    processed: bool
    label: str
    description: str
    registered_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


class MessageCreate(BaseModel):
    """ Data for creating a new message """
    content: str
    role: str
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DatabaseStats(BaseModel):
    """ Database statistics for an agent """
    total_messages: int
    processed_messages: int
    unprocessed_messages: int
    total_files: int
    processed_files: int
    unprocessed_files: int


class SubconsciousDatabase:
    """Database handler for SubconsciousAgent storing messages and file metadata."""
    
    def __init__(self, db_path: str = "subconscious.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for registered messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                message_hash TEXT NOT NULL,
                content TEXT NOT NULL,
                role TEXT NOT NULL,
                name TEXT,
                metadata TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE,
                processed_at TIMESTAMP NULL,
                UNIQUE(agent_id, message_hash)
            )
        ''')
        
        # Table for registered files
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                size INTEGER,
                last_modified TIMESTAMP,
                label TEXT NOT NULL,
                description TEXT NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE,
                processed_at TIMESTAMP NULL,
                UNIQUE(agent_id, file_path, file_hash)
            )
        ''')
        
        # Index for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_agent_hash ON messages(agent_id, message_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_agent_processed ON messages(agent_id, processed)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_agent_path ON files(agent_id, file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_agent_processed ON files(agent_id, processed)')
        
        conn.commit()
        conn.close()
    
    def _get_message_hash(self, message: MessageCreate) -> str:
        """Generate a hash for a message to detect duplicates."""
        message_dict = message.model_dump()
        message_str = json.dumps(message_dict, sort_keys=True)
        return hashlib.sha256(message_str.encode()).hexdigest()
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate a hash for a file based on its content."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except FileNotFoundError:
            return ""
    
    def register_messages(self, agent_id: str, messages: List[MessageCreate]) -> int:
        """Register multiple messages for a specific agent. Returns count of newly registered messages."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        registered_count = 0
        for message in messages:
            message_hash = self._get_message_hash(message)
            metadata_json = json.dumps(message.metadata) if message.metadata else None
            
            try:
                cursor.execute('''
                    INSERT INTO messages (agent_id, message_hash, content, role, name, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (agent_id, message_hash, message.content, message.role, message.name, metadata_json))
                registered_count += 1
            except sqlite3.IntegrityError:
                # Message already exists for this agent
                pass
        
        conn.commit()
        conn.close()
        return registered_count
    
    def register_file(self, agent_id: str, file_path: str, label: str, description: str) -> bool:
        """Register a file for a specific agent. Returns True if newly registered, False if already exists."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_hash = self._get_file_hash(file_path)
        file_stats = path.stat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if file already registered with same hash for this agent
        cursor.execute('''
            SELECT id FROM files WHERE agent_id = ? AND file_path = ? AND file_hash = ?
        ''', (agent_id, str(path.absolute()), file_hash))
        
        if cursor.fetchone():
            conn.close()
            return False
        
        # Register new file or update if content changed
        cursor.execute('''
            INSERT OR REPLACE INTO files (agent_id, file_path, file_hash, size, last_modified, label, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (agent_id, str(path.absolute()), file_hash, file_stats.st_size, 
              datetime.fromtimestamp(file_stats.st_mtime), label, description))
        
        conn.commit()
        conn.close()
        return True
    
    def get_unprocessed_messages(self, agent_id: str) -> List[Message]:
        """Get all unprocessed messages for a specific agent."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, agent_id, content, role, name, metadata, registered_at, processed_at 
            FROM messages 
            WHERE agent_id = ? AND processed = FALSE
            ORDER BY registered_at ASC
        ''', (agent_id,))
        
        results = []
        for row in cursor.fetchall():
            metadata = json.loads(row[5]) if row[5] else {}
            message = Message(
                id=row[0],
                agent_id=row[1],
                content=row[2],
                processed=False,
                role=row[3],
                name=row[4],
                registered_at=datetime.fromisoformat(row[6]) if row[6] else None,
                processed_at=datetime.fromisoformat(row[7]) if row[7] else None,
                metadata=metadata
            )
            results.append(message)
        
        conn.close()
        return results
    
    def get_unprocessed_files(self, agent_id: str) -> List[File]:
        """Get all unprocessed files for a specific agent."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, agent_id, file_path, file_hash, size, last_modified, label, description, registered_at, processed_at
            FROM files WHERE agent_id = ? AND processed = FALSE
            ORDER BY registered_at ASC
        ''', (agent_id,))
        
        results = []
        for row in cursor.fetchall():
            file_obj = File(
                id=row[0],
                agent_id=row[1],
                file_path=row[2],
                file_hash=row[3],
                size=row[4],
                last_modified=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                processed=False,
                label=row[6],
                description=row[7],
                registered_at=datetime.fromisoformat(row[8]) if row[8] else None,
                processed_at=datetime.fromisoformat(row[9]) if row[9] else None
            )
            results.append(file_obj)
        
        conn.close()
        return results
    
    def mark_messages_processed(self, message_ids: List[int]):
        """Mark messages as processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        placeholders = ','.join(['?' for _ in message_ids])
        cursor.execute(f'''
            UPDATE messages SET processed = TRUE, processed_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders})
        ''', message_ids)
        
        conn.commit()
        conn.close()
    
    def mark_files_processed(self, file_ids: List[int]):
        """Mark files as processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        placeholders = ','.join(['?' for _ in file_ids])
        cursor.execute(f'''
            UPDATE files SET processed = TRUE, processed_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders})
        ''', file_ids)
        
        conn.commit()
        conn.close()
    
    def reset_processing_status(self, agent_id: str):
        """Reset all items to unprocessed status for a specific agent (for reprocessing)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE messages SET processed = FALSE, processed_at = NULL WHERE agent_id = ?', (agent_id,))
        cursor.execute('UPDATE files SET processed = FALSE, processed_at = NULL WHERE agent_id = ?', (agent_id,))
        
        conn.commit()
        conn.close()
    
    def get_stats(self, agent_id: str) -> DatabaseStats:
        """Get database statistics for a specific agent."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM messages WHERE agent_id = ?', (agent_id,))
        total_messages = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM messages WHERE agent_id = ? AND processed = TRUE', (agent_id,))
        processed_messages = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM files WHERE agent_id = ?', (agent_id,))
        total_files = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM files WHERE agent_id = ? AND processed = TRUE', (agent_id,))
        processed_files = cursor.fetchone()[0]
        
        conn.close()
        
        return DatabaseStats(
            total_messages=total_messages,
            processed_messages=processed_messages,
            unprocessed_messages=total_messages - processed_messages,
            total_files=total_files,
            processed_files=processed_files,
            unprocessed_files=total_files - processed_files
        )