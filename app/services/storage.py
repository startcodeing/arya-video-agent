"""Storage service for file operations."""

import os
from pathlib import Path
from typing import Optional

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StorageService:
    """Storage service for managing file uploads and downloads."""

    def __init__(self):
        """Initialize storage service."""
        self.provider = settings.STORAGE_PROVIDER
        self.local_path = Path(settings.LOCAL_STORAGE_PATH)

        # Ensure local storage directory exists
        if self.provider == "local":
            self.local_path.mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        file_path: str,
        content: bytes,
        content_type: str = None
    ) -> str:
        """
        Upload file to storage.

        Args:
            file_path: Path where file should be stored
            content: File content as bytes
            content_type: MIME type of the file

        Returns:
            Public URL of the uploaded file
        """
        if self.provider == "local":
            return await self._upload_local(file_path, content)
        else:
            raise ValueError(f"Storage provider {self.provider} not implemented yet")

    async def _upload_local(
        self,
        file_path: str,
        content: bytes
    ) -> str:
        """
        Upload file to local storage.

        Args:
            file_path: Path where file should be stored
            content: File content as bytes

        Returns:
            Public URL of the uploaded file
        """
        try:
            # Create full file path
            full_path = self.local_path / file_path

            # Create directory if it doesn't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(full_path, "wb") as f:
                f.write(content)

            # Return URL (relative path for local storage)
            logger.info(f"File uploaded to local storage: {full_path}")
            return f"/storage/{file_path}"

        except Exception as e:
            logger.error(f"Error uploading file to local storage: {e}")
            raise

    async def download(self, file_path: str) -> bytes:
        """
        Download file from storage.

        Args:
            file_path: Path of the file to download

        Returns:
            File content as bytes
        """
        if self.provider == "local":
            return await self._download_local(file_path)
        else:
            raise ValueError(f"Storage provider {self.provider} not implemented yet")

    async def _download_local(self, file_path: str) -> bytes:
        """
        Download file from local storage.

        Args:
            file_path: Path of the file to download

        Returns:
            File content as bytes
        """
        try:
            full_path = self.local_path / file_path

            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {full_path}")

            with open(full_path, "rb") as f:
                content = f.read()

            logger.info(f"File downloaded from local storage: {full_path}")
            return content

        except Exception as e:
            logger.error(f"Error downloading file from local storage: {e}")
            raise

    async def get_signed_url(
        self,
        storage_key: str,
        ttl: int = 3600
    ) -> str:
        """
        Get signed URL for file access.

        For local storage, returns the file path directly.
        For cloud storage, would generate a temporary signed URL.

        Args:
            storage_key: Storage key of the file
            ttl: Time to live in seconds (not used for local storage)

        Returns:
            URL to access the file
        """
        if self.provider == "local":
            # For local storage, just return the path
            return f"/storage/{storage_key}"
        else:
            raise ValueError(f"Storage provider {self.provider} not implemented yet")

    async def delete(self, file_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_path: Path of the file to delete

        Returns:
            True if successful, False otherwise
        """
        if self.provider == "local":
            return await self._delete_local(file_path)
        else:
            raise ValueError(f"Storage provider {self.provider} not implemented yet")

    async def _delete_local(self, file_path: str) -> bool:
        """
        Delete file from local storage.

        Args:
            file_path: Path of the file to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self.local_path / file_path

            if full_path.exists():
                full_path.unlink()
                logger.info(f"File deleted from local storage: {full_path}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting file from local storage: {e}")
            return False

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            file_path: Path of the file to check

        Returns:
            True if file exists, False otherwise
        """
        if self.provider == "local":
            full_path = self.local_path / file_path
            return full_path.exists()
        else:
            raise ValueError(f"Storage provider {self.provider} not implemented yet")

    def get_absolute_path(self, file_path: str) -> str:
        """
        Get absolute file system path.

        Args:
            file_path: Relative file path

        Returns:
            Absolute file system path
        """
        return str(self.local_path / file_path)


__all__ = ["StorageService"]
