"""
VideoProcessor — handles loading and saving video frames.

Supports:
  - Loading frames from video files (via OpenCV)
  - Loading frames from numpy arrays (simulated video data)
  - Saving frames back to video files
  - Frame normalization / denormalization
"""

import os
import numpy as np
import cv2
from typing import List, Optional, Tuple, Union


def _validate_video_path(video_path):
    """Validate a video file path.

    Args:
        video_path: Path to validate.

    Raises:
        TypeError: If video_path is not a string.
        ValueError: If video_path is empty or doesn't exist.
    """
    if not isinstance(video_path, str):
        raise TypeError(f"video_path must be a string, got {type(video_path).__name__}")
    if not video_path.strip():
        raise ValueError("video_path must not be empty")
    if not os.path.exists(video_path):
        raise ValueError(f"Cannot open video file: {video_path}")
    if not cv2.VideoCapture(video_path).isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")


def _validate_frames_array(frames, frame_size=None, channels=None):
    """Validate a frames numpy array.

    Args:
        frames: Array to validate.
        frame_size: Expected (height, width) tuple.
        channels: Expected number of channels.

    Raises:
        TypeError: If frames is not a numpy array.
        ValueError: If frames has wrong number of dimensions or shape.
    """
    if not isinstance(frames, np.ndarray):
        raise TypeError(f"frames must be a numpy array, got {type(frames).__name__}")
    if frames.ndim not in (4, 5):
        raise ValueError(f"frames must be 4D or 5D (batch, frames, h, w, c) or (frames, h, w, c), got {frames.ndim}D")
    if frame_size is not None:
        if frames.ndim == 4:
            h, w = frame_size
            if frames.shape[-3] != h or frames.shape[-2] != w:
                raise ValueError(f"frames spatial dimensions must be {frame_size}, got ({frames.shape[-3]}, {frames.shape[-2]})")
            if frames.shape[-1] != 1 and frames.shape[-1] != 3:
                raise ValueError(f"frames channels must be 1 or 3, got {frames.shape[-1]}")
        elif frames.ndim == 5:
            h, w = frame_size
            if frames.shape[-3] != h or frames.shape[-2] != w:
                raise ValueError(f"frames spatial dimensions must be {frame_size}, got ({frames.shape[-3]}, {frames.shape[-2]})")
            if channels is not None and frames.shape[-1] != channels:
                raise ValueError(f"frames channels must be {channels}, got {frames.shape[-1]}")


class VideoProcessor:
    """Process video frames for GAN training."""

    def __init__(
        self,
        frame_size: Tuple[int, int] = (64, 64),
        num_frames: int = 16,
        channels: int = 3,
        normalize: bool = True,
    ):
        """
        Args:
            frame_size: (height, width) of each frame.
            num_frames: Number of frames per video sample.
            channels: Number of color channels (1=grayscale, 3=RGB).
            normalize: If True, scale pixel values to [-1, 1].
        """
        self.frame_size = frame_size
        self.num_frames = num_frames
        self.channels = channels
        self._normalize_flag = normalize

    def load_video_frames(
        self,
        video_path: str,
        num_frames: Optional[int] = None,
    ) -> np.ndarray:
        """Load frames from a video file.

        Args:
            video_path: Path to the video file.
            num_frames: Override the default number of frames.

        Returns:
            numpy array of shape (num_frames, height, width, channels)
            with pixel values in [0, 255].

        Raises:
            TypeError: If video_path is not a string.
            ValueError: If video_path is empty or cannot be opened.
        """
        _validate_video_path(video_path)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        n_frames = num_frames or self.num_frames
        n_frames = min(n_frames, frame_count)

        step = max(1, frame_count // n_frames)
        frames = []

        for _ in range(n_frames):
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self.frame_size[1], self.frame_size[0]))
            frames.append(frame)

        cap.release()

        if len(frames) == 0:
            raise ValueError(f"No frames extracted from {video_path}")

        return np.array(frames, dtype=np.float32)

    def load_video(self, video_path: str, num_frames: Optional[int] = None) -> np.ndarray:
        """Alias for load_video_frames for convenience.

        Args:
            video_path: Path to the video file.
            num_frames: Override the default number of frames.

        Returns:
            numpy array of shape (num_frames, height, width, channels).
        """
        return self.load_video_frames(video_path, num_frames)

    def save_video_frames(
        self,
        frames: np.ndarray,
        output_path: str,
        fps: float = 10.0,
    ) -> None:
        """Save frames to a video file.

        Args:
            frames: numpy array of shape (num_frames, height, width, channels).
            output_path: Output video file path.
            fps: Frames per second for the output video.

        Raises:
            TypeError: If frames is not a numpy array.
            ValueError: If frames has wrong shape.
            TypeError: If output_path is not a string.
        """
        _validate_frames_array(frames, self.frame_size, self.channels)
        if not isinstance(output_path, str):
            raise TypeError(f"output_path must be a string, got {type(output_path).__name__}")
        if not output_path.strip():
            raise ValueError("output_path must not be empty")
        if frames.ndim == 4:
            frames = frames[0] if frames.shape[0] == 1 else frames

        height, width = self.frame_size
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        if not out.isOpened():
            raise RuntimeError(f"Cannot open video writer for {output_path}")

        for frame in frames:
            frame_uint8 = np.clip(frame, 0, 255).astype(np.uint8)
            frame_bgr = cv2.cvtColor(frame_uint8, cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)

        out.release()

        # Verify the file was written correctly by reopening it
        cap = cv2.VideoCapture(output_path)
        if not cap.isOpened():
            # If mp4v doesn't work, try avi as fallback
            avi_path = output_path.rsplit(".", 1)[0] + ".avi"
            out2 = cv2.VideoWriter(avi_path, cv2.VideoWriter_fourcc(*"XVID"), fps, (width, height))
            if out2.isOpened():
                for frame in frames:
                    frame_uint8 = np.clip(frame, 0, 255).astype(np.uint8)
                    frame_bgr = cv2.cvtColor(frame_uint8, cv2.COLOR_RGB2BGR)
                    out2.write(frame_bgr)
                out2.release()
                # Move avi to mp4 path
                os.replace(avi_path, output_path)
            else:
                raise RuntimeError(f"Cannot write video to {output_path}")
        cap.release()

    def normalize(self, frames: np.ndarray) -> np.ndarray:
        """Normalize frames to [-1, 1].

        Args:
            frames: numpy array with pixel values in [0, 255].

        Returns:
            numpy array with pixel values in [-1, 1].

        Raises:
            TypeError: If frames is not a numpy array.
            ValueError: If frames has incorrect shape or values outside [0, 255].
        """
        if not isinstance(frames, np.ndarray):
            raise TypeError(f"Expected numpy array, got {type(frames).__name__}")
        if frames.ndim != 5:
            raise ValueError(f"Expected 5D array (batch, frames, h, w, c), got {frames.ndim}D")
        h, w = self.frame_size
        if frames.shape[-3] != h or frames.shape[-2] != w:
            raise ValueError(f"frames spatial dimensions must be {self.frame_size}, got ({frames.shape[-3]}, {frames.shape[-2]})")
        if frames.min() < 0 or frames.max() > 255:
            raise ValueError(f"Frame values must be in [0, 255], got min={frames.min()}, max={frames.max()}")
        return (frames / 127.5) - 1.0

    def denormalize(self, frames: np.ndarray) -> np.ndarray:
        """Denormalize frames from [-1, 1] to [0, 255].

        Args:
            frames: numpy array with pixel values in [-1, 1].

        Returns:
            numpy array with pixel values in [0, 255].

        Raises:
            TypeError: If frames is not a numpy array.
            ValueError: If frames has incorrect shape or values outside [-1, 1].
        """
        if not isinstance(frames, np.ndarray):
            raise TypeError(f"Expected numpy array, got {type(frames).__name__}")
        if frames.ndim != 5:
            raise ValueError(f"Expected 5D array (batch, frames, h, w, c), got {frames.ndim}D")
        h, w = self.frame_size
        if frames.shape[-3] != h or frames.shape[-2] != w:
            raise ValueError(f"frames spatial dimensions must be {self.frame_size}, got ({frames.shape[-3]}, {frames.shape[-2]})")
        if frames.min() < -1 or frames.max() > 1:
            raise ValueError(f"Frame values must be in [-1, 1], got min={frames.min()}, max={frames.max()}")
        return ((frames + 1.0) * 127.5).clip(0, 255).astype(np.float32)

    def create_random_video(self, batch_size: int = 1, num_frames: Optional[int] = None, frame_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """Create random video frames for testing.

        Args:
            batch_size: Number of video samples.
            num_frames: Override the default number of frames.
            frame_size: Override (height, width) as a tuple.

        Returns:
            numpy array of shape (batch_size, num_frames, height, width, channels)
            with pixel values in [0, 255] if normalize=False, or [-1, 1] if normalize=True.

        Raises:
            ValueError: If num_frames or frame_size dimensions are negative or zero.
        """
        n_frames = num_frames if num_frames is not None else self.num_frames
        h, w = frame_size if frame_size is not None else self.frame_size
        if n_frames < 0:
            raise ValueError(f"num_frames must be non-negative, got {n_frames}")
        if h <= 0 or w <= 0:
            raise ValueError(f"frame_size dimensions must be positive, got ({h}, {w})")
        frames = np.random.randint(0, 256, size=(batch_size, n_frames, h, w, self.channels)).astype(np.float32)
        if self._normalize_flag:
            frames = (frames / 127.5) - 1.0
        return frames

    def create_constant_video(self, value: float = 128.0, batch_size: int = 1, num_frames: Optional[int] = None, frame_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """Create constant video frames for testing.

        Args:
            value: Constant pixel value. In [0, 255] if normalize=False, or in [-1, 1] if normalize=True.
            batch_size: Number of video samples.
            num_frames: Override the default number of frames.
            frame_size: Override (height, width) as a tuple.

        Returns:
            numpy array of shape (batch_size, num_frames, height, width, channels).

        Raises:
            ValueError: If value is out of valid range, or if num_frames/frame_size are invalid.
        """
        n_frames = num_frames if num_frames is not None else self.num_frames
        h, w = frame_size if frame_size is not None else self.frame_size
        if n_frames < 0:
            raise ValueError(f"num_frames must be non-negative, got {n_frames}")
        if h <= 0 or w <= 0:
            raise ValueError(f"frame_size dimensions must be positive, got ({h}, {w})")
        if self._normalize_flag:
            if value < -1 or value > 1:
                raise ValueError(f"When normalize=True, value must be in [-1, 1], got {value}")
        else:
            if value < 0 or value > 255:
                raise ValueError(f"When normalize=False, value must be in [0, 255], got {value}")
        return np.full((batch_size, n_frames, h, w, self.channels), value, dtype=np.float32)

    def save(
        self,
        frames: np.ndarray,
        output_path: str,
        fps: float = 10.0,
    ) -> None:
        """Alias for save_video_frames."""
        self.save_video_frames(frames, output_path, fps)
