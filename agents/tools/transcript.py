"""
agents/tools/transcript.py
Fetch transcripts from YouTube URLs or transcribe local MP4/audio files.

Two public functions:
    fetch_youtube_transcript(url: str) -> str
    transcribe_local_video(file_path: str) -> str
"""

import re
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


def _extract_video_id(url: str) -> str:
    """Extract YouTube video ID from any YouTube URL format."""
    patterns = [
        r"(?:v=)([A-Za-z0-9_\-]{11})",       # ?v=ID
        r"(?:youtu\.be/)([A-Za-z0-9_\-]{11})",  # youtu.be/ID
        r"(?:shorts/)([A-Za-z0-9_\-]{11})",     # /shorts/ID
        r"(?:embed/)([A-Za-z0-9_\-]{11})",      # /embed/ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def fetch_youtube_transcript(url: str) -> str:
    """
    Fetch the full transcript from a YouTube video URL.

    Args:
        url: Any YouTube URL (watch?v=, youtu.be/, /shorts/, /embed/)

    Returns:
        Plain text transcript as a single string.

    Raises:
        ValueError: If the URL is invalid or has no transcript available.
        ImportError: If youtube-transcript-api is not installed.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api import (
            TranscriptsDisabled,
            NoTranscriptFound,
            VideoUnavailable,
        )
    except ImportError:
        raise ImportError(
            "youtube-transcript-api is not installed. "
            "Run: pip install youtube-transcript-api==1.2.4"
        )

    video_id = _extract_video_id(url)
    logger.info(f"Fetching transcript for video ID: {video_id}")

    try:
        # v1.2.4: instance-based API
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        try:
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
        except NoTranscriptFound:
            transcript = transcript_list.find_transcript(['ar'])
        fetched = transcript.fetch()
    except TranscriptsDisabled:
        raise ValueError(f"Transcripts are disabled for video: {video_id}")
    except NoTranscriptFound:
        raise ValueError(
            f"No transcript found for video: {video_id}. "
            "Try a video with auto-generated captions enabled."
        )
    except VideoUnavailable:
        raise ValueError(f"Video unavailable: {video_id}")

    # Join all segments — each snippet has .text attribute in v1.2.4
    segments = list(fetched)
    if segments and hasattr(segments[0], 'text'):
        full_text = " ".join(s.text for s in segments)
    else:
        # fallback for dict-style segments
        full_text = " ".join(s.get('text', '') for s in segments)

    full_text = re.sub(r"\s+", " ", full_text).strip()

    logger.info(f"Transcript fetched: {len(full_text)} characters")
    return full_text


def transcribe_local_video(file_path: str) -> str:
    """
    Transcribe a local MP4, WAV, or audio file using Faster-Whisper.
    Runs fully locally — $0 cost.

    Args:
        file_path: Absolute path to the local video/audio file.

    Returns:
        Plain text transcription as a single string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ImportError: If faster-whisper is not installed.
    """
    import os

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ImportError(
            "faster-whisper is not installed. "
            "Run: pip install faster-whisper"
        )

    logger.info(f"Loading Faster-Whisper model (medium, CPU, int8)...")
    model = WhisperModel("medium", device="cpu", compute_type="int8")

    logger.info(f"Transcribing: {file_path}")
    segments, info = model.transcribe(
        file_path,
        beam_size=5,
        language="en",
        vad_filter=True,  # filter out silence
    )

    full_text = " ".join(segment.text for segment in segments)
    full_text = re.sub(r"\s+", " ", full_text).strip()

    logger.info(
        f"Transcription complete: {len(full_text)} chars, "
        f"detected language: {info.language} ({info.language_probability:.0%})"
    )
    return full_text
