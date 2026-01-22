"""Unit tests for VideoProcessor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.video_processor import VideoProcessor


class TestVideoProcessor:
    """Test suite for VideoProcessor."""

    def test_initialization(self):
        """Test processor initialization."""
        with patch('app.services.video_processor.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            processor = VideoProcessor()

            assert processor._ffmpeg_path is not None
            assert processor._ffprobe_path is not None

    def test_find_ffmpeg_in_path(self):
        """Test finding FFmpeg in system PATH."""
        with patch('app.services.video_processor.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            processor = VideoProcessor()

            # Should find ffmpeg in PATH
            assert "ffmpeg" in processor._ffmpeg_path

    def test_find_ffmpeg_not_found(self):
        """Test when FFmpeg is not found."""
        with patch('app.services.video_processor.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()

            processor = VideoProcessor()

            # Should return default path
            assert processor._ffmpeg_path == "ffmpeg"

    def test_is_available(self):
        """Test checking if FFmpeg is available."""
        processor = VideoProcessor()

        # This will depend on whether FFmpeg is installed
        # Just ensure the method runs
        result = processor.is_available()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_get_video_info(self):
        """Test getting video information."""
        processor = VideoProcessor()

        # Mock subprocess
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (
                b'{"format": {"duration": "10.0", "size": "1000000", "bit_rate": "800000"}, '
                b'"streams": [{"codec_type": "video", "width": 1920, "height": 1080, '
                b'"r_frame_rate": "30000/1001", "codec_name": "h264"}]}',
                b"",
            )
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            info = await processor.get_video_info("test.mp4")

            assert info["duration"] == 10.0
            assert info["video"]["width"] == 1920
            assert info["video"]["height"] == 1080

    @pytest.mark.asyncio
    async def test_parse_fps(self):
        """Test FPS parsing."""
        processor = VideoProcessor()

        # Test fraction format
        assert processor._parse_fps("30000/1001") == pytest.approx(29.97, rel=0.01)

        # Test integer format
        assert processor._parse_fps("30") == 30.0

        # Test None
        assert processor._parse_fps(None) is None

        # Test invalid
        assert processor._parse_fps("invalid") is None

    @pytest.mark.asyncio
    async def test_concatenate_simple(self):
        """Test simple video concatenation."""
        processor = VideoProcessor()

        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            result = await processor._concatenate_simple(
                ["video1.mp4", "video2.mp4"],
                "output.mp4",
            )

            assert result == "output.mp4"
            mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_resize_video(self):
        """Test video resizing."""
        processor = VideoProcessor()

        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            # Mock get_video_info for aspect ratio calculation
            with patch.object(processor, 'get_video_info') as mock_info:
                mock_info.return_value = {
                    "video": {"width": 1920, "height": 1080}
                }

                result = await processor.resize_video(
                    "input.mp4",
                    "output.mp4",
                    width=1280,
                )

                assert result == "output.mp4"

    @pytest.mark.asyncio
    async def test_resize_video_with_aspect_ratio(self):
        """Test video resizing with aspect ratio."""
        processor = VideoProcessor()

        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            with patch.object(processor, 'get_video_info') as mock_info:
                mock_info.return_value = {
                    "video": {"width": 1920, "height": 1080}
                }

                result = await processor.resize_video(
                    "input.mp4",
                    "output.mp4",
                    aspect_ratio="16:9",
                )

                assert result == "output.mp4"

    @pytest.mark.asyncio
    async def test_trim_video(self):
        """Test video trimming."""
        processor = VideoProcessor()

        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            result = await processor.trim_video(
                "input.mp4",
                "output.mp4",
                start_time=5.0,
                duration=10.0,
            )

            assert result == "output.mp4"

    @pytest.mark.asyncio
    async def test_add_audio(self):
        """Test adding audio to video."""
        processor = VideoProcessor()

        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            result = await processor.add_audio(
                "video.mp4",
                "audio.mp3",
                "output.mp4",
            )

            assert result == "output.mp4"

    @pytest.mark.asyncio
    async def test_remove_audio(self):
        """Test removing audio from video."""
        processor = VideoProcessor()

        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            result = await processor.add_audio(
                "video.mp4",
                None,
                "output.mp4",
            )

            assert result == "output.mp4"

    def test_build_fade_filter(self):
        """Test building fade filter complex."""
        processor = VideoProcessor()

        filter_str = processor._build_fade_filter(3, 0.5)

        assert "fade" in filter_str
        assert "concat" in filter_str

    @pytest.mark.asyncio
    async def test_run_command_success(self):
        """Test running FFmpeg command successfully."""
        processor = VideoProcessor()

        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"output", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            await processor._run_command(["ffmpeg", "-i", "input.mp4", "output.mp4"])

            mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_command_failure(self):
        """Test running FFmpeg command that fails."""
        processor = VideoProcessor()

        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"error output")
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process

            with pytest.raises(RuntimeError):
                await processor._run_command(["ffmpeg", "-i", "input.mp4"])

    @pytest.mark.asyncio
    async def test_run_command_ffmpeg_not_found(self):
        """Test running command when FFmpeg is not found."""
        processor = VideoProcessor()

        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_subprocess.side_effect = FileNotFoundError()

            with pytest.raises(RuntimeError, match="FFmpeg is not installed"):
                await processor._run_command(["ffmpeg", "-i", "input.mp4"])


__all__ = ["TestVideoProcessor"]
