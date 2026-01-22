"""Unit tests for StorageService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.storage import StorageService
import tempfile
import os


class TestStorageService:
    """Test suite for StorageService."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def storage_service(self, temp_dir):
        """Create a StorageService instance with temp directory."""
        with patch('app.services.storage.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "local"
            mock_settings.LOCAL_STORAGE_PATH = temp_dir

            service = StorageService()
            yield service

    def test_initialization_local(self, temp_dir):
        """Test initialization with local storage."""
        with patch('app.services.storage.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "local"
            mock_settings.LOCAL_STORAGE_PATH = temp_dir

            service = StorageService()

            assert service.storage_type == "local"
            assert service.base_path == temp_dir

    def test_initialization_creates_directory(self):
        """Test that initialization creates directory if it doesn't exist."""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        test_dir = os.path.join(temp_dir, "test_storage")

        try:
            with patch('app.services.storage.settings') as mock_settings:
                mock_settings.STORAGE_TYPE = "local"
                mock_settings.LOCAL_STORAGE_PATH = test_dir

                # Remove directory if it exists
                if os.path.exists(test_dir):
                    shutil.rmtree(test_dir)

                service = StorageService()

                # Directory should be created
                assert os.path.exists(test_dir)
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_upload_file(self, storage_service, temp_dir):
        """Test uploading a file."""
        content = b"Test file content"
        file_path = "videos/test_video.mp4"

        url = await storage_service.upload(file_path, content)

        # Check URL format
        assert "videos/test_video.mp4" in url or url.endswith("test_video.mp4")

        # Check file was created
        full_path = os.path.join(temp_dir, "videos", "test_video.mp4")
        assert os.path.exists(full_path)

        # Check content
        with open(full_path, "rb") as f:
            assert f.read() == content

    @pytest.mark.asyncio
    async def test_upload_nested_path(self, storage_service, temp_dir):
        """Test uploading to nested directory."""
        content = b"Nested file content"
        file_path = "outputs/2024/01/video.mp4"

        url = await storage_service.upload(file_path, content)

        # Check file was created
        full_path = os.path.join(temp_dir, "outputs", "2024", "01", "video.mp4")
        assert os.path.exists(full_path)

    @pytest.mark.asyncio
    async def test_upload_with_metadata(self, storage_service, temp_dir):
        """Test uploading file with metadata."""
        content = b"File with metadata"
        file_path = "videos/video.mp4"
        metadata = {"duration": 10, "format": "mp4"}

        url = await storage_service.upload(
            file_path,
            content,
            metadata=metadata
        )

        # File should still be uploaded
        full_path = os.path.join(temp_dir, "videos", "video.mp4")
        assert os.path.exists(full_path)

    @pytest.mark.asyncio
    async def test_download_file(self, storage_service, temp_dir):
        """Test downloading a file."""
        # First upload a file
        content = b"Download test content"
        file_path = "videos/test.mp4"
        await storage_service.upload(file_path, content)

        # Then download it
        downloaded = await storage_service.download(file_path)

        assert downloaded == content

    @pytest.mark.asyncio
    async def test_download_nonexistent_file(self, storage_service):
        """Test downloading non-existent file."""
        with pytest.raises(FileNotFoundError):
            await storage_service.download("nonexistent/file.mp4")

    @pytest.mark.asyncio
    async def test_delete_file(self, storage_service, temp_dir):
        """Test deleting a file."""
        # First upload a file
        content = b"Delete test content"
        file_path = "videos/to_delete.mp4"
        await storage_service.upload(file_path, content)

        # Verify file exists
        full_path = os.path.join(temp_dir, "videos", "to_delete.mp4")
        assert os.path.exists(full_path)

        # Delete it
        await storage_service.delete(file_path)

        # Verify file is gone
        assert not os.path.exists(full_path)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, storage_service):
        """Test deleting non-existent file (should not raise error)."""
        # Should not raise an error
        await storage_service.delete("nonexistent/file.mp4")

    @pytest.mark.asyncio
    async def test_get_signed_url(self, storage_service):
        """Test getting signed URL (local storage)."""
        url = await storage_service.get_signed_url("videos/video.mp4", ttl=3600)

        # For local storage, should return file:// URL or similar
        assert "video.mp4" in url

    @pytest.mark.asyncio
    async def test_file_exists(self, storage_service, temp_dir):
        """Test checking if file exists."""
        # Check non-existent file
        exists = await storage_service.file_exists("videos/nonexistent.mp4")
        assert exists is False

        # Upload a file
        content = b"Existence test"
        await storage_service.upload("videos/existing.mp4", content)

        # Check existing file
        exists = await storage_service.file_exists("videos/existing.mp4")
        assert exists is True

    @pytest.mark.asyncio
    async def test_list_files(self, storage_service, temp_dir):
        """Test listing files in a directory."""
        # Upload some files
        await storage_service.upload("videos/video1.mp4", b"content1")
        await storage_service.upload("videos/video2.mp4", b"content2")
        await storage_service.upload("images/image1.png", b"content3")

        # List videos
        videos = await storage_service.list_files("videos")

        assert len(videos) == 2
        assert any("video1.mp4" in f for f in videos)
        assert any("video2.mp4" in f for f in videos)

        # List all files
        all_files = await storage_service.list_files("")
        assert len(all_files) >= 3

    @pytest.mark.asyncio
    async def test_list_files_recursive(self, storage_service):
        """Test listing files recursively."""
        # Upload nested files
        await storage_service.upload("videos/2024/01/video1.mp4", b"content1")
        await storage_service.upload("videos/2024/02/video2.mp4", b"content2")
        await storage_service.upload("videos/2023/12/video3.mp4", b"content3")

        # List recursively
        files = await storage_service.list_files("videos", recursive=True)

        assert len(files) == 3
        assert all("video" in f for f in files)

    @pytest.mark.asyncio
    async def test_get_file_size(self, storage_service):
        """Test getting file size."""
        content = b"Size test content"
        await storage_service.upload("videos/size_test.mp4", content)

        size = await storage_service.get_file_size("videos/size_test.mp4")

        assert size == len(content)

    @pytest.mark.asyncio
    async def test_get_file_size_nonexistent(self, storage_service):
        """Test getting size of non-existent file."""
        with pytest.raises(FileNotFoundError):
            await storage_service.get_file_size("nonexistent/file.mp4")

    def test_generate_storage_key(self, storage_service):
        """Test generating storage key."""
        key = storage_service._generate_storage_key("videos", "video.mp4")

        assert "videos" in key
        assert "video.mp4" in key

    def test_generate_storage_key_with_prefix(self, storage_service):
        """Test generating storage key with custom prefix."""
        key = storage_service._generate_storage_key(
            "videos",
            "video.mp4",
            prefix="outputs"
        )

        assert "outputs" in key
        assert "videos" in key
        assert "video.mp4" in key

    def test_normalize_path(self, storage_service):
        """Test path normalization."""
        # Remove leading slashes
        path1 = storage_service._normalize_path("/videos/video.mp4")
        assert not path1.startswith("/")

        # Remove double slashes
        path2 = storage_service._normalize_path("videos//video.mp4")
        assert "//" not in path2

        # Handle empty path
        path3 = storage_service._normalize_path("")
        assert path3 == ""

    @pytest.mark.asyncio
    async def test_upload_large_file(self, storage_service):
        """Test uploading a large file."""
        # Create 1MB of data
        content = b"x" * (1024 * 1024)

        url = await storage_service.upload("videos/large.mp4", content)

        assert "large.mp4" in url

        # Verify file was created correctly
        downloaded = await storage_service.download("videos/large.mp4")
        assert len(downloaded) == len(content)
        assert downloaded == content

    @pytest.mark.asyncio
    async def test_copy_file(self, storage_service, temp_dir):
        """Test copying a file."""
        content = b"Copy test content"
        await storage_service.upload("videos/original.mp4", content)

        await storage_service.copy(
            "videos/original.mp4",
            "videos/copy.mp4"
        )

        # Verify both files exist
        original_path = os.path.join(temp_dir, "videos", "original.mp4")
        copy_path = os.path.join(temp_dir, "videos", "copy.mp4")

        assert os.path.exists(original_path)
        assert os.path.exists(copy_path)

        # Verify content is the same
        with open(copy_path, "rb") as f:
            assert f.read() == content

    @pytest.mark.asyncio
    async def test_copy_nonexistent_file(self, storage_service):
        """Test copying non-existent file."""
        with pytest.raises(FileNotFoundError):
            await storage_service.copy(
                "nonexistent/source.mp4",
                "videos/destination.mp4"
            )


class TestStorageServiceErrors:
    """Test suite for StorageService error handling."""

    @pytest.mark.asyncio
    async def test_upload_invalid_path(self):
        """Test upload with invalid path."""
        with patch('app.services.storage.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "local"
            mock_settings.LOCAL_STORAGE_PATH = tempfile.gettempdir()

            service = StorageService()

            # Empty path should raise error
            with pytest.raises(ValueError):
                await service.upload("", b"content")

    @pytest.mark.asyncio
    async def test_upload_permission_error(self):
        """Test upload when directory is not writable."""
        # Create a read-only directory
        with tempfile.TemporaryDirectory() as tmpdir:
            readonly_dir = os.path.join(tmpdir, "readonly")
            os.makedirs(readonly_dir)
            os.chmod(readonly_dir, 0o444)

            try:
                with patch('app.services.storage.settings') as mock_settings:
                    mock_settings.STORAGE_TYPE = "local"
                    mock_settings.LOCAL_STORAGE_PATH = readonly_dir

                    service = StorageService()

                    # Should raise permission error
                    with pytest.raises((PermissionError, OSError)):
                        await service.upload("videos/test.mp4", b"content")
            finally:
                # Restore permissions for cleanup
                os.chmod(readonly_dir, 0o755)


__all__ = ["TestStorageService", "TestStorageServiceErrors"]
