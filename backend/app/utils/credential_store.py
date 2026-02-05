"""
Encrypted credential storage using SQLite + Fernet encryption.

This module provides secure storage for user API credentials with:
- AES-128 encryption via Fernet (from cryptography library)
- SQLite database for persistence across server restarts
- Session-based credential lookup
- Automatic expiration and cleanup

No external database services required - uses local SQLite file.

Usage:
    from app.utils.credential_store import get_credential_store

    store = get_credential_store()
    store.store_credentials(session_id, provider, model, api_key)
    creds = store.get_credentials(session_id)
"""

import os
import sqlite3
import time
from typing import Optional, Dict
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("credential_store")

# Try to import cryptography, but make it optional
try:
    from cryptography.fernet import Fernet, InvalidToken
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    logger.warning("cryptography package not installed - credential encryption disabled")

# Get encryption key from environment (generate with: Fernet.generate_key())
ENCRYPTION_KEY = os.getenv("CREDENTIAL_ENCRYPTION_KEY", "")

# Database path - stored in backend/data directory
DB_PATH = Path(__file__).parent.parent.parent / "data" / "sessions.db"


class CredentialStore:
    """
    Encrypted credential storage using SQLite + Fernet encryption.

    Thread-safe for concurrent access from multiple requests.
    """

    def __init__(self):
        """Initialize the credential store."""
        self.encryption_enabled = False
        self.fernet = None

        if ENCRYPTION_AVAILABLE and ENCRYPTION_KEY:
            try:
                self.fernet = Fernet(ENCRYPTION_KEY.encode())
                self.encryption_enabled = True
                logger.info("Credential encryption enabled")
            except Exception as e:
                logger.warning(f"Invalid encryption key, encryption disabled: {e}")
        elif not ENCRYPTION_AVAILABLE:
            logger.warning("Credential store running without encryption (cryptography not installed)")
        elif not ENCRYPTION_KEY:
            logger.warning("CREDENTIAL_ENCRYPTION_KEY not set - encryption disabled")

        self._init_db()

    def _init_db(self):
        """Initialize SQLite database and create tables."""
        try:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    encrypted_api_key BLOB NOT NULL,
                    azure_endpoint TEXT,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
            ''')
            # Create index for expiration cleanup
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_expires
                ON sessions(expires_at)
            ''')
            conn.commit()
            conn.close()
            logger.info(f"Credential store initialized at {DB_PATH}")
        except Exception as e:
            logger.error(f"Failed to initialize credential database: {e}")
            raise

    def _encrypt(self, data: str) -> bytes:
        """Encrypt data using Fernet if available, otherwise return as bytes."""
        if self.encryption_enabled and self.fernet:
            return self.fernet.encrypt(data.encode())
        # Fallback: base64-like encoding (not secure, but functional)
        return data.encode('utf-8')

    def _decrypt(self, data: bytes) -> str:
        """Decrypt data using Fernet if available, otherwise decode bytes."""
        if self.encryption_enabled and self.fernet:
            try:
                return self.fernet.decrypt(data).decode()
            except InvalidToken:
                logger.error("Failed to decrypt credential - invalid token")
                return ""
        # Fallback: simple decode
        return data.decode('utf-8')

    def store_credentials(
        self,
        session_id: str,
        provider: str,
        model: str,
        api_key: str,
        azure_endpoint: Optional[str] = None,
        ttl_hours: int = 24
    ) -> bool:
        """
        Store encrypted credentials for a session.

        Args:
            session_id: Unique session identifier
            provider: LLM provider (azure, openai, gemini)
            model: Model name
            api_key: API key to encrypt and store
            azure_endpoint: Azure endpoint URL (optional)
            ttl_hours: Time to live in hours (default 24)

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            encrypted_key = self._encrypt(api_key)
            now = time.time()
            expires = now + (ttl_hours * 3600)

            conn = sqlite3.connect(str(DB_PATH))
            conn.execute('''
                INSERT OR REPLACE INTO sessions
                (session_id, provider, model, encrypted_api_key, azure_endpoint, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, provider, model, encrypted_key, azure_endpoint, now, expires))
            conn.commit()
            conn.close()

            logger.info(f"Stored credentials for session {session_id[:8]}... (provider: {provider})")
            return True

        except Exception as e:
            logger.error(f"Failed to store credentials: {e}")
            return False

    def get_credentials(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve and decrypt credentials for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            Dict with provider, model, api_key, azure_endpoint or None if not found/expired
        """
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.execute(
                '''SELECT provider, model, encrypted_api_key, azure_endpoint, expires_at
                   FROM sessions WHERE session_id = ?''',
                (session_id,)
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            provider, model, encrypted_key, azure_endpoint, expires_at = row

            # Check expiration
            if time.time() > expires_at:
                logger.info(f"Session {session_id[:8]}... expired, removing")
                self.delete_session(session_id)
                return None

            api_key = self._decrypt(encrypted_key)
            if not api_key:
                return None

            return {
                'provider': provider,
                'model': model,
                'api_key': api_key,
                'azure_endpoint': azure_endpoint
            }

        except Exception as e:
            logger.error(f"Failed to retrieve credentials: {e}")
            return None

    def get_credential_metadata(self, session_id: str) -> Optional[Dict]:
        """
        Get credential metadata without the actual API key.
        Safe to expose to frontend.

        Args:
            session_id: Unique session identifier

        Returns:
            Dict with provider, model, has_azure_endpoint or None if not found
        """
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.execute(
                '''SELECT provider, model, azure_endpoint, expires_at
                   FROM sessions WHERE session_id = ?''',
                (session_id,)
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            provider, model, azure_endpoint, expires_at = row

            # Check expiration
            if time.time() > expires_at:
                return None

            return {
                'exists': True,
                'provider': provider,
                'model': model,
                'has_azure_endpoint': bool(azure_endpoint)
            }

        except Exception as e:
            logger.error(f"Failed to retrieve credential metadata: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session's credentials.

        Args:
            session_id: Unique session identifier

        Returns:
            True if deleted, False otherwise
        """
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            conn.commit()
            conn.close()
            logger.info(f"Deleted credentials for session {session_id[:8]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    def cleanup_expired(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions removed
        """
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.execute('DELETE FROM sessions WHERE expires_at < ?', (time.time(),))
            count = cursor.rowcount
            conn.commit()
            conn.close()
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

    def get_stats(self) -> Dict:
        """Get credential store statistics."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.execute('SELECT COUNT(*) FROM sessions')
            total = cursor.fetchone()[0]
            cursor = conn.execute('SELECT COUNT(*) FROM sessions WHERE expires_at > ?', (time.time(),))
            active = cursor.fetchone()[0]
            conn.close()
            return {
                'total_sessions': total,
                'active_sessions': active,
                'expired_sessions': total - active,
                'encryption_enabled': self.encryption_enabled
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}


# Singleton instance
_store: Optional[CredentialStore] = None


def get_credential_store() -> CredentialStore:
    """
    Get the singleton credential store instance.

    Returns:
        CredentialStore instance
    """
    global _store
    if _store is None:
        _store = CredentialStore()
    return _store
