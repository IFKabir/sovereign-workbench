import sqlite3
import hashlib
import json
import threading
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from shared_schemas.models import AuditBlock

class AuditLedger:
    """SHA-256 hash-chained SQLite audit ledger."""
    
    def __init__(self, db_path: str = 'audit_ledger.db'):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_db()
        
    def init_db(self) -> None:
        """Initialize the database and create the genesis block if necessary."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        block_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        prev_hash TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        action TEXT NOT NULL,
                        query TEXT NOT NULL,
                        models_called TEXT NOT NULL,
                        token_count INTEGER,
                        status TEXT NOT NULL,
                        payload_hash TEXT NOT NULL,
                        combined_sha256 TEXT NOT NULL UNIQUE
                    )
                ''')
                
                # Check if genesis block exists
                cursor.execute('SELECT COUNT(*) FROM audit_logs')
                if cursor.fetchone()[0] == 0:
                    genesis_hash = '0' * 64
                    timestamp = datetime.now(timezone.utc).isoformat()
                    payload_hash = self._compute_payload_hash(
                        "system", "system", "genesis", "genesis", "[]", "success", timestamp
                    )
                    combined_hash = self._compute_chain_hash(genesis_hash, payload_hash)
                    
                    cursor.execute('''
                        INSERT INTO audit_logs (
                            block_id, timestamp, prev_hash, user_id, role, action, query, 
                            models_called, token_count, status, payload_hash, combined_sha256
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        0, timestamp, genesis_hash, "system", "system", "genesis", "genesis",
                        "[]", 0, "success", payload_hash, combined_hash
                    ))
                conn.commit()

    def _compute_payload_hash(self, user_id: str, role: str, query: str, action: str, 
                              models_called: str, status: str, timestamp: str) -> str:
        """Compute SHA-256 of concatenated fields."""
        payload = f"{user_id}|{role}|{query}|{action}|{models_called}|{status}|{timestamp}"
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def _compute_chain_hash(self, prev_hash: str, payload_hash: str) -> str:
        """Compute SHA-256 of prev_hash + payload_hash."""
        return hashlib.sha256(f"{prev_hash}{payload_hash}".encode('utf-8')).hexdigest()

    def append_log(self, user_id: str, role: str, query: str, action: str, 
                   models_called: List[str], token_count: Optional[int], status: str) -> AuditBlock:
        """Append a new log to the audit chain."""
        timestamp = datetime.now(timezone.utc).isoformat()
        models_called_json = json.dumps(models_called)
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get the last block's combined hash to use as prev_hash
                cursor.execute('SELECT combined_sha256 FROM audit_logs ORDER BY block_id DESC LIMIT 1')
                result = cursor.fetchone()
                if not result:
                    raise RuntimeError("Ledger is missing genesis block.")
                prev_hash = result[0]
                
                payload_hash = self._compute_payload_hash(
                    user_id, role, query, action, models_called_json, status, timestamp
                )
                combined_hash = self._compute_chain_hash(prev_hash, payload_hash)
                
                cursor.execute('''
                    INSERT INTO audit_logs (
                        timestamp, prev_hash, user_id, role, action, query, 
                        models_called, token_count, status, payload_hash, combined_sha256
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp, prev_hash, user_id, role, action, query, 
                    models_called_json, token_count, status, payload_hash, combined_hash
                ))
                
                block_id = cursor.lastrowid
                conn.commit()
                
        return AuditBlock(
            block_id=block_id,
            timestamp=datetime.fromisoformat(timestamp),
            prev_hash=prev_hash,
            user_id=user_id,
            role=role,
            action=action,
            query=query,
            models_called=models_called,
            token_count=token_count,
            status=status,
            payload_hash=payload_hash,
            combined_sha256=combined_hash
        )

    def verify_chain_integrity(self) -> Tuple[bool, str]:
        """Verify the integrity of the entire audit chain."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT block_id, timestamp, prev_hash, user_id, role, action, query, 
                           models_called, status, payload_hash, combined_sha256 
                    FROM audit_logs ORDER BY block_id ASC
                ''')
                rows = cursor.fetchall()
                
        if not rows:
            return False, "Ledger is empty"
            
        expected_prev_hash = '0' * 64
        
        for row in rows:
            (block_id, timestamp, prev_hash, user_id, role, action, query, 
             models_called_json, status, stored_payload_hash, stored_combined_hash) = row
            
            if prev_hash != expected_prev_hash:
                return False, f"Broken chain at block {block_id}: expected prev_hash {expected_prev_hash}, got {prev_hash}"
                
            recomputed_payload_hash = self._compute_payload_hash(
                user_id, role, query, action, models_called_json, status, timestamp
            )
            
            if recomputed_payload_hash != stored_payload_hash:
                return False, f"Payload tampering detected at block {block_id}"
                
            recomputed_combined_hash = self._compute_chain_hash(prev_hash, recomputed_payload_hash)
            
            if recomputed_combined_hash != stored_combined_hash:
                return False, f"Chain hash tampering detected at block {block_id}"
                
            expected_prev_hash = recomputed_combined_hash
            
        return True, f"Chain integrity verified: {len(rows)} blocks"

    def _row_to_block(self, row: tuple) -> AuditBlock:
        return AuditBlock(
            block_id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            prev_hash=row[2],
            user_id=row[3],
            role=row[4],
            action=row[5],
            query=row[6],
            models_called=json.loads(row[7]),
            token_count=row[8],
            status=row[9],
            payload_hash=row[10],
            combined_sha256=row[11]
        )

    def get_block(self, block_id: int) -> Optional[AuditBlock]:
        """Get a specific block by ID."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM audit_logs WHERE block_id = ?', (block_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_block(row)
        return None

    def get_recent_blocks(self, limit: int = 50) -> List[AuditBlock]:
        """Get the most recent blocks."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM audit_logs ORDER BY block_id DESC LIMIT ?', (limit,))
                rows = cursor.fetchall()
                return [self._row_to_block(row) for row in rows]

    def get_blocks_by_user(self, user_id: str) -> List[AuditBlock]:
        """Get blocks associated with a specific user."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM audit_logs WHERE user_id = ? ORDER BY block_id ASC', (user_id,))
                rows = cursor.fetchall()
                return [self._row_to_block(row) for row in rows]
                
    def get_chain_length(self) -> int:
        """Get the total number of blocks in the chain."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM audit_logs')
                return cursor.fetchone()[0]
