"""Video processing service using FFmpeg."""

import asyncio
import json
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VideoProcessor:
    """
    Video processing service using FFmpeg.

    Handles video composition, concatenation, transcoding, and effects.
    """

    def __init__(self):
        """Initialize video processor."""
        self._ffmpeg_path = self._find_ffmpeg()
        self._ffprobe_path = self._find_ffprobe()

    def _find_ffmpeg(self) -> str:
        """
        Find FFmpeg executable.

        Returns:
            Path to ffmpeg executable
        """
        # Try common locations
        possible_paths = [
            "ffmpeg",  # In PATH
            r"C:\ffmpeg\bin\ffmpeg.exe",  # Windows common
            "/usr/bin/ffmpeg",  # Linux
            "/usr/local/bin/ffmpeg",  # macOS
        ]

        for path in possible_paths:
            try:
                result = subprocess.run(
                    [path, "-version"],
                    capture_output=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    logger.info(f"Found FFmpeg at: {path}")
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        logger.warning("FFmpeg not found, video operations will fail")
        return "ffmpeg"  # Return default, will fail when used

    def _find_ffprobe(self) -> str:
        """
        Find FFprobe executable.

        Returns:
            Path to ffprobe executable
        """
        # Replace ffmpeg with ffprobe in path
        if self._ffmpeg_path == "ffmpeg":
            return "ffprobe"

        path = self._ffmpeg_path.replace("ffmpeg", "ffprobe").replace("FFmpeg", "FFprobe")
        if "ffmpeg.exe" in path.lower():
            path = path.replace("ffmpeg.exe", "ffprobe.exe")
        return path

    async def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get video file information using FFprobe.

        Args:
            video_path: Path to video file

        Returns:
            Dict containing video information
        """
        cmd = [
            self._ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFprobe failed: {stderr.decode()}")
                raise RuntimeError(f"Failed to get video info: {stderr.decode()}")

            info = json.loads(stdout.decode())

            # Extract relevant information
            video_stream = next(
                (s for s in info.get("streams", []) if s.get("codec_type") == "video"),
                None,
            )

            audio_stream = next(
                (s for s in info.get("streams", []) if s.get("codec_type") == "audio"),
                None,
            )

            return {
                "duration": float(info.get("format", {}).get("duration", 0)),
                "size": int(info.get("format", {}).get("size", 0)),
                "bitrate": int(info.get("format", {}).get("bit_rate", 0)),
                "video": {
                    "width": video_stream.get("width") if video_stream else None,
                    "height": video_stream.get("height") if video_stream else None,
                    "fps": self._parse_fps(video_stream.get("r_frame_rate")) if video_stream else None,
                    "codec": video_stream.get("codec_name") if video_stream else None,
                } if video_stream else None,
                "audio": {
                    "codec": audio_stream.get("codec_name") if audio_stream else None,
                    "sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else None,
                    "channels": audio_stream.get("channels") if audio_stream else None,
                } if audio_stream else None,
            }

        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise

    def _parse_fps(self, fps_string: Optional[str]) -> Optional[float]:
        """
        Parse FPS from FFprobe output (e.g., "30000/1001").

        Args:
            fps_string: FPS string from FFprobe

        Returns:
            FPS as float
        """
        if not fps_string:
            return None

        try:
            if "/" in fps_string:
                num, den = fps_string.split("/")
                return float(num) / float(den)
            return float(fps_string)
        except (ValueError, ZeroDivisionError):
            return None

    async def concatenate_videos(
        self,
        video_paths: List[str],
        output_path: str,
        transition_type: str = "cut",
        transition_duration: float = 0.5,
    ) -> str:
        """
        Concatenate multiple videos into one.

        Args:
            video_paths: List of video file paths
            output_path: Path for output video
            transition_type: Type of transition (cut, fade, dissolve)
            transition_duration: Duration of transitions in seconds

        Returns:
            Path to output video
        """
        logger.info(f"Concatenating {len(video_paths)} videos")

        try:
            if transition_type == "cut":
                return await self._concatenate_simple(video_paths, output_path)
            else:
                return await self._concatenate_with_transitions(
                    video_paths,
                    output_path,
                    transition_type,
                    transition_duration,
                )

        except Exception as e:
            logger.error(f"Video concatenation failed: {e}")
            raise

    async def _concatenate_simple(
        self,
        video_paths: List[str],
        output_path: str,
    ) -> str:
        """
        Simple concatenation using FFmpeg concat demuxer.

        Args:
            video_paths: List of video file paths
            output_path: Path for output video

        Returns:
            Path to output video
        """
        # Create concat list file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for video_path in video_paths:
                # Escape paths for FFmpeg
                safe_path = video_path.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")
            list_file = f.name

        try:
            cmd = [
                self._ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c", "copy",
                "-y",
                output_path,
            ]

            await self._run_command(cmd)
            return output_path

        finally:
            # Clean up temp file
            if os.path.exists(list_file):
                os.remove(list_file)

    async def _concatenate_with_transitions(
        self,
        video_paths: List[str],
        output_path: str,
        transition_type: str,
        transition_duration: float,
    ) -> str:
        """
        Concatenate videos with transitions using filter complex.

        Args:
            video_paths: List of video file paths
            output_path: Path for output video
            transition_type: Type of transition
            transition_duration: Duration of transition

        Returns:
            Path to output video
        """
        # For now, implement simple fade transition
        # Full implementation would use xfade filter
        logger.info(f"Applying {transition_type} transitions")

        if transition_type == "fade":
            filter_complex = self._build_fade_filter(
                len(video_paths),
                transition_duration,
            )
        else:
            # Fall back to simple concat for unsupported transitions
            logger.warning(f"Transition {transition_type} not implemented, using cut")
            return await self._concatenate_simple(video_paths, output_path)

        # Build filter complex and inputs
        inputs = []
        for video_path in video_paths:
            inputs.extend(["-i", video_path])

        cmd = [
            self._ffmpeg_path,
            *inputs,
            "-filter_complex", filter_complex,
            "-y",
            output_path,
        ]

        await self._run_command(cmd)
        return output_path

    def _build_fade_filter(
        self,
        num_videos: int,
        duration: float,
    ) -> str:
        """
        Build fade filter complex for FFmpeg.

        Args:
            num_videos: Number of videos
            duration: Fade duration

        Returns:
            Filter complex string
        """
        # Simplified fade implementation
        # Full implementation would be more complex
        filters = []

        for i in range(num_videos):
            # Fade in for first video
            if i == 0:
                filters.append(f"[0:v]fade=t=in:st=0:d={duration}:alpha=1[v0]")
            # Fade out for last video
            elif i == num_videos - 1:
                filters.append(f"[{i}:v]fade=t=out:st=0:d={duration}:alpha=1[v{i}]")
            # Crossfade for middle videos
            else:
                filters.append(f"[{i}:v]fade=t=in:st=0:d={duration}:alpha=1[v{i}]")

        # Concatenate all video streams
        concat_inputs = ",".join([f"v{i}" for i in range(num_videos)])
        filters.append(f"{concat_inputs}concat=n={num_videos}:v=1:a=0[outv]")

        return ";".join(filters)

    async def add_audio(
        self,
        video_path: str,
        audio_path: Optional[str],
        output_path: str,
        audio_volume: float = 1.0,
    ) -> str:
        """
        Add or replace audio in video.

        Args:
            video_path: Path to video file
            audio_path: Path to audio file (None to remove audio)
            output_path: Path for output video
            audio_volume: Audio volume multiplier

        Returns:
            Path to output video
        """
        if audio_path is None:
            # Remove audio
            cmd = [
                self._ffmpeg_path,
                "-i", video_path,
                "-c:v", "copy",
                "-an",
                "-y",
                output_path,
            ]
        else:
            # Add/mix audio
            cmd = [
                self._ffmpeg_path,
                "-i", video_path,
                "-i", audio_path,
                "-filter_complex",
                f"[1:a]volume={audio_volume}[a1];[0:a][a1]amix=inputs=2:duration=first",
                "-c:v", "copy",
                "-y",
                output_path,
            ]

        await self._run_command(cmd)
        return output_path

    async def resize_video(
        self,
        video_path: str,
        output_path: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
    ) -> str:
        """
        Resize video.

        Args:
            video_path: Path to video file
            output_path: Path for output video
            width: Target width (None to keep original)
            height: Target height (None to keep original)
            aspect_ratio: Aspect ratio (e.g., "16:9", "9:16")

        Returns:
            Path to output video
        """
        if aspect_ratio:
            # Calculate dimensions based on aspect ratio
            info = await self.get_video_info(video_path)
            orig_width = info["video"]["width"]
            orig_height = info["video"]["height"]

            ar_width, ar_height = map(int, aspect_ratio.split(":"))

            # Calculate target dimensions
            if width:
                height = int(width * ar_height / ar_width)
            elif height:
                width = int(height * ar_width / ar_height)
            else:
                # Use original dimensions
                target_ar = orig_width / orig_height
                desired_ar = ar_width / ar_height

                if target_ar > desired_ar:
                    # Width is limiting factor
                    width = orig_width
                    height = int(width * ar_height / ar_width)
                else:
                    # Height is limiting factor
                    height = orig_height
                    width = int(height * ar_width / ar_height)

        # Build scale filter
        if width and height:
            scale_filter = f"scale={width}:{height}"
        elif width:
            scale_filter = f"scale={width}:-1"
        elif height:
            scale_filter = f"scale=-1:{height}"
        else:
            # No resize needed
            return video_path

        cmd = [
            self._ffmpeg_path,
            "-i", video_path,
            "-vf", scale_filter,
            "-c:a", "copy",
            "-y",
            output_path,
        ]

        await self._run_command(cmd)
        return output_path

    async def trim_video(
        self,
        video_path: str,
        output_path: str,
        start_time: float,
        duration: Optional[float] = None,
    ) -> str:
        """
        Trim video to specified time range.

        Args:
            video_path: Path to video file
            output_path: Path for output video
            start_time: Start time in seconds
            duration: Duration in seconds (None to end of video)

        Returns:
            Path to output video
        """
        cmd = [
            self._ffmpeg_path,
            "-ss", str(start_time),
            "-i", video_path,
        ]

        if duration:
            cmd.extend(["-t", str(duration)])

        cmd.extend([
            "-c", "copy",
            "-y",
            output_path,
        ])

        await self._run_command(cmd)
        return output_path

    async def _run_command(self, cmd: List[str]) -> None:
        """
        Run FFmpeg command asynchronously.

        Args:
            cmd: Command and arguments

        Raises:
            RuntimeError: If command fails
        """
        logger.debug(f"Running FFmpeg command: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"FFmpeg command failed: {error_msg}")
                raise RuntimeError(f"FFmpeg failed: {error_msg}")

            logger.debug("FFmpeg command completed successfully")

        except FileNotFoundError:
            logger.error("FFmpeg not found")
            raise RuntimeError("FFmpeg is not installed or not in PATH")
        except Exception as e:
            logger.error(f"Error running FFmpeg command: {e}")
            raise

    def is_available(self) -> bool:
        """
        Check if FFmpeg is available.

        Returns:
            True if FFmpeg is found
        """
        try:
            result = subprocess.run(
                [self._ffmpeg_path, "-version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


# Global video processor instance
video_processor = VideoProcessor()


__all__ = ["VideoProcessor", "video_processor"]
