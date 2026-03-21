"""
Credential Store API for Google Workspace MCP.

This module provides a standardized interface for credential storage and retrieval,
supporting multiple backends configurable via environment variables.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime

from google.oauth2.credentials import Credentials

from auth.config import get_credentials_directory, get_legacy_credentials_directory
from auth.security_io import atomic_write_json, ensure_secure_directory

logger = logging.getLogger(__name__)


class CredentialStore(ABC):
    """Abstract base class for credential storage."""

    @abstractmethod
    def get_credential(self, user_email: str) -> Credentials | None:
        """Get credentials for a user by email."""
        pass

    @abstractmethod
    def store_credential(self, user_email: str, credentials: Credentials) -> bool:
        """Store credentials for a user."""
        pass

    @abstractmethod
    def delete_credential(self, user_email: str) -> bool:
        """Delete credentials for a user."""
        pass

    @abstractmethod
    def list_users(self) -> list[str]:
        """List all users with stored credentials."""
        pass


class LocalDirectoryCredentialStore(CredentialStore):
    """Credential store that uses local JSON files for storage."""

    def __init__(self, base_dir: str | None = None):
        self.legacy_base_dir: str | None = None
        if base_dir is None:
            env_dir = os.getenv("GOOGLE_MCP_CREDENTIALS_DIR")
            if env_dir:
                base_dir = env_dir
            else:
                # Use centralized config directory from auth.config,
                # which respects WORKSPACE_MCP_CONFIG_DIR env var.
                base_dir = os.path.join(get_credentials_directory(), "credentials")
                legacy_base_dir = os.path.join(get_legacy_credentials_directory(), "credentials")
                if os.path.abspath(legacy_base_dir) != os.path.abspath(base_dir):
                    self.legacy_base_dir = legacy_base_dir

        self.base_dir: str = base_dir
        logger.info(f"LocalJsonCredentialStore initialized with base_dir: {base_dir}")

    @staticmethod
    def _normalize_client_key(client_key: str | None) -> str | None:
        if client_key is None:
            return None
        normalized = str(client_key).strip().lower()
        if not normalized:
            return None
        return normalized.replace("/", "_").replace("\\", "_")

    def _get_client_credentials_dir(self, client_key: str | None) -> str:
        normalized_client_key = self._normalize_client_key(client_key)
        if not normalized_client_key:
            return self.base_dir
        return os.path.join(self.base_dir, normalized_client_key)

    def _get_credential_path(self, user_email: str, client_key: str | None = None) -> str:
        """Get the file path for a user's credentials."""
        target_dir = self._get_client_credentials_dir(client_key)
        dir_existed = os.path.exists(target_dir)
        ensure_secure_directory(target_dir)
        if not dir_existed:
            logger.info(f"Created credentials directory: {target_dir}")
        return os.path.join(target_dir, f"{user_email}.json")

    @staticmethod
    def _load_credentials_from_path(user_email: str, creds_path: str) -> Credentials | None:
        """Load credentials from a specific JSON path."""
        try:
            with open(creds_path) as f:
                creds_data = json.load(f)

            expiry = None
            if creds_data.get("expiry"):
                try:
                    expiry = datetime.fromisoformat(creds_data["expiry"])
                    if expiry.tzinfo is not None:
                        expiry = expiry.replace(tzinfo=None)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse expiry time for {user_email}: {e}")

            credentials = Credentials(
                token=creds_data.get("token"),
                refresh_token=creds_data.get("refresh_token"),
                token_uri=creds_data.get("token_uri"),
                client_id=creds_data.get("client_id"),
                client_secret=creds_data.get("client_secret"),
                scopes=creds_data.get("scopes"),
                expiry=expiry,
            )

            logger.debug(f"Loaded credentials for {user_email} from {creds_path}")
            return credentials
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading credentials for {user_email} from {creds_path}: {e}")
            return None

    def get_credential(self, user_email: str) -> Credentials | None:
        """Get credentials from local JSON file."""
        creds_path = self._get_credential_path(user_email)

        if os.path.exists(creds_path):
            return self._load_credentials_from_path(user_email, creds_path)

        if self.legacy_base_dir:
            legacy_path = os.path.join(self.legacy_base_dir, f"{user_email}.json")
            if os.path.exists(legacy_path):
                logger.warning(
                    "Loaded credentials from legacy path %s. Migrate to %s or set WORKSPACE_MCP_CONFIG_DIR.",
                    legacy_path,
                    self.base_dir,
                )
                return self._load_credentials_from_path(user_email, legacy_path)

        logger.debug(f"No credential file found for {user_email} at {creds_path}")
        return None

    def get_credential_for_client(self, client_key: str, user_email: str) -> Credentials | None:
        """Get credentials for a specific OAuth client+user combination."""
        client_path = self._get_credential_path(user_email, client_key=client_key)
        if os.path.exists(client_path):
            return self._load_credentials_from_path(user_email, client_path)

        # Read-through migration fallback from legacy flat per-email storage.
        legacy_flat_path = self._get_credential_path(user_email, client_key=None)
        if os.path.exists(legacy_flat_path):
            credentials = self._load_credentials_from_path(user_email, legacy_flat_path)
            if credentials:
                logger.warning(
                    "Loaded legacy flat credentials for %s while resolving client '%s'. "
                    "Migrating to client-scoped storage.",
                    user_email,
                    client_key,
                )
                self.store_credential_for_client(client_key, user_email, credentials)
                return credentials

        if self.legacy_base_dir:
            legacy_path = os.path.join(self.legacy_base_dir, f"{user_email}.json")
            if os.path.exists(legacy_path):
                logger.warning(
                    "Loaded credentials from legacy path %s for client '%s'. "
                    "Migrate to %s or set WORKSPACE_MCP_CONFIG_DIR.",
                    legacy_path,
                    client_key,
                    self.base_dir,
                )
                credentials = self._load_credentials_from_path(user_email, legacy_path)
                if credentials:
                    self.store_credential_for_client(client_key, user_email, credentials)
                return credentials

        logger.debug("No credential file found for %s under client '%s'", user_email, client_key)
        return None

    def store_credential(self, user_email: str, credentials: Credentials) -> bool:
        """Store credentials to local JSON file."""
        creds_path = self._get_credential_path(user_email)

        creds_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }

        try:
            atomic_write_json(creds_path, creds_data)
            logger.info(f"Stored credentials for {user_email} to {creds_path}")
            return True
        except OSError as e:
            logger.error(f"Error storing credentials for {user_email} to {creds_path}: {e}")
            return False

    def store_credential_for_client(self, client_key: str, user_email: str, credentials: Credentials) -> bool:
        """Store credentials in client-scoped storage."""
        creds_path = self._get_credential_path(user_email, client_key=client_key)
        creds_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }
        try:
            atomic_write_json(creds_path, creds_data)
            logger.info("Stored credentials for %s in client '%s' at %s", user_email, client_key, creds_path)
            return True
        except OSError as e:
            logger.error("Error storing client-scoped credentials for %s to %s: %s", user_email, creds_path, e)
            return False

    def delete_credential(self, user_email: str) -> bool:
        """Delete credential file for a user."""
        creds_path = self._get_credential_path(user_email)
        legacy_path = os.path.join(self.legacy_base_dir, f"{user_email}.json") if self.legacy_base_dir else None

        try:
            deleted = False
            if os.path.exists(creds_path):
                os.remove(creds_path)
                logger.info(f"Deleted credentials for {user_email} from {creds_path}")
                deleted = True
            if legacy_path and os.path.exists(legacy_path):
                os.remove(legacy_path)
                logger.info(f"Deleted credentials for {user_email} from legacy path {legacy_path}")
                deleted = True

            if not deleted:
                logger.debug(f"No credential file to delete for {user_email} at {creds_path}")
            return True
        except OSError as e:
            logger.error(f"Error deleting credentials for {user_email} from {creds_path}: {e}")
            return False

    def delete_credential_for_client(self, client_key: str, user_email: str) -> bool:
        """Delete client-scoped credential file for a user."""
        client_path = self._get_credential_path(user_email, client_key=client_key)
        try:
            if os.path.exists(client_path):
                os.remove(client_path)
                logger.info("Deleted credentials for %s from client '%s' at %s", user_email, client_key, client_path)
            return True
        except OSError as e:
            logger.error("Error deleting client-scoped credentials for %s from %s: %s", user_email, client_path, e)
            return False

    def list_users(self) -> list[str]:
        """List all users with credential files."""
        users: set[str] = set()
        paths_to_check = [self.base_dir]
        if os.path.exists(self.base_dir):
            for item in os.listdir(self.base_dir):
                potential_client_dir = os.path.join(self.base_dir, item)
                if os.path.isdir(potential_client_dir):
                    paths_to_check.append(potential_client_dir)
        if self.legacy_base_dir:
            paths_to_check.append(self.legacy_base_dir)

        for path in paths_to_check:
            if not os.path.exists(path):
                continue
            try:
                for filename in os.listdir(path):
                    if filename.endswith(".json"):
                        users.add(filename[:-5])
            except OSError as e:
                logger.error(f"Error listing credential files in {path}: {e}")

        logger.debug(f"Found {len(users)} users across credential directories")
        return sorted(users)

    def list_users_for_client(self, client_key: str) -> list[str]:
        """List users for a specific client key."""
        users: set[str] = set()
        path = self._get_client_credentials_dir(client_key)
        if not os.path.exists(path):
            return []

        try:
            for filename in os.listdir(path):
                if filename.endswith(".json"):
                    users.add(filename[:-5])
        except OSError as e:
            logger.error("Error listing client credential files in %s: %s", path, e)
        return sorted(users)


_credential_store: CredentialStore | None = None


def get_credential_store() -> CredentialStore:
    """Get the global credential store instance."""
    global _credential_store

    if _credential_store is None:
        _credential_store = LocalDirectoryCredentialStore()
        logger.info(f"Initialized credential store: {type(_credential_store).__name__}")

    return _credential_store


def set_credential_store(store: CredentialStore) -> None:
    """Set the global credential store instance (for testing)."""
    global _credential_store
    _credential_store = store
    logger.info(f"Set credential store: {type(store).__name__}")
