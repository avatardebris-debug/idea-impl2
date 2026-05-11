"""
Tests for video format handlers (MP4, AVI, MOV) and the FormatFactory.

Covers:
- VideoFormatHandler base class (abstract contract)
- MP4Handler, AVIHandler, MOVHandler concrete implementations
- FormatFactory registration and handler resolution
- detect_video_format and create_handler convenience functions
"""

import os
import sys
import tempfile
import pytest

# Ensure the workspace is on the path so we can import the formats package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from formats.base_handler import (
    VideoFormatHandler,
    FormatFactory,
    detect_video_format,
    create_handler,
)
from formats.mp4_handler import MP4Handler, MP4Metadata
from formats.avi_handler import AVIHandler, AVIMetadata
from formats.mov_handler import MOVHandler, MOVMetadata


# ------ helpers ---------------------------------------------------------------

def _write_temp_file(name: str, content: bytes = b"") -> str:
    """Write *content* to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=name.rsplit(".", 1)[-1] if "." in name else "")
    with os.fdopen(fd, "wb") as f:
        f.write(content)
    return path


# ------ VideoFormatHandler – abstract base class ------------------------------

class TestVideoFormatHandlerBase:
    """Tests for the abstract VideoFormatHandler base class."""

    def test_is_abstract(self):
        """Instantiating VideoFormatHandler directly must raise TypeError."""
        with pytest.raises(TypeError):
            VideoFormatHandler("/tmp/fake.mp4")

    def test_subclass_must_implement_validate_integrity(self):
        """A concrete subclass that skips validate_integrity is still abstract."""
        class IncompleteHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["xyz"]
            FORMAT_NAME = "xyz"
            MIME_TYPE = "video/xyz"
            DEFAULT_CODEC = "xyz"

            def get_metadata(self):
                return {}

        with pytest.raises(TypeError):
            IncompleteHandler("/tmp/fake.xyz")

    def test_subclass_must_implement_get_metadata(self):
        """A concrete subclass that skips get_metadata is still abstract."""
        class IncompleteHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["xyz"]
            FORMAT_NAME = "xyz"
            MIME_TYPE = "video/xyz"
            DEFAULT_CODEC = "xyz"

            def validate_integrity(self):
                return True, "ok"

        with pytest.raises(TypeError):
            IncompleteHandler("/tmp/fake.xyz")

    def test_validate_extension_raises_on_mismatch(self):
        """Passing a file with the wrong extension raises ValueError."""
        class TestHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["abc"]
            FORMAT_NAME = "abc"
            MIME_TYPE = "video/abc"
            DEFAULT_CODEC = "abc"

            def validate_integrity(self):
                return True, "ok"

            def get_metadata(self):
                return {}

        with pytest.raises(ValueError, match="Invalid extension"):
            TestHandler("/tmp/fake.xyz")

    def test_validate_extension_accepts_valid(self):
        """No exception when the extension is valid."""
        class TestHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["abc"]
            FORMAT_NAME = "abc"
            MIME_TYPE = "video/abc"
            DEFAULT_CODEC = "abc"

            def validate_integrity(self):
                return True, "ok"

            def get_metadata(self):
                return {}

        # Should not raise
        handler = TestHandler("/tmp/fake.abc")
        assert handler.file_path == "/tmp/fake.abc"

    def test_validate_extension_case_insensitive(self):
        """Extension matching is case-insensitive."""
        class TestHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["abc"]
            FORMAT_NAME = "abc"
            MIME_TYPE = "video/abc"
            DEFAULT_CODEC = "abc"

            def validate_integrity(self):
                return True, "ok"

            def get_metadata(self):
                return {}

        handler = TestHandler("/tmp/fake.ABC")
        assert handler.file_path == "/tmp/fake.ABC"

    def test_is_valid_extension_classmethod(self):
        """is_valid_extension returns bool without raising."""
        class TestHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["abc"]
            FORMAT_NAME = "abc"
            MIME_TYPE = "video/abc"
            DEFAULT_CODEC = "abc"

            def validate_integrity(self):
                return True, "ok"

            def get_metadata(self):
                return {}

        assert TestHandler.is_valid_extension("/tmp/fake.abc") is True
        assert TestHandler.is_valid_extension("/tmp/fake.xyz") is False

    def test_properties_return_class_attributes(self):
        """format, mime_type, default_codec return the class-level values."""
        class TestHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["abc"]
            FORMAT_NAME = "abc"
            MIME_TYPE = "video/abc"
            DEFAULT_CODEC = "abc"

            def validate_integrity(self):
                return True, "ok"

            def get_metadata(self):
                return {}

        handler = TestHandler("/tmp/fake.abc")
        assert handler.format == "abc"
        assert handler.mime_type == "video/abc"
        assert handler.default_codec == "abc"

    def test_convert_raises_not_implemented(self):
        """Base class convert() raises NotImplementedError."""
        class TestHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["abc"]
            FORMAT_NAME = "abc"
            MIME_TYPE = "video/abc"
            DEFAULT_CODEC = "abc"

            def validate_integrity(self):
                return True, "ok"

            def get_metadata(self):
                return {}

        handler = TestHandler("/tmp/fake.abc")
        with pytest.raises(NotImplementedError, match="Subclasses must implement"):
            handler.convert("/tmp/out.abc")

    def test_is_compatible_with_youtube_file_too_large(self):
        """Files > 256 GB are flagged as incompatible."""
        class TestHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["abc"]
            FORMAT_NAME = "abc"
            MIME_TYPE = "video/abc"
            DEFAULT_CODEC = "abc"

            def validate_integrity(self):
                return True, "ok"

            def get_metadata(self):
                return {"file_size_bytes": 257 * 1024**3, "duration_seconds": 100}

        handler = TestHandler("/tmp/fake.abc")
        compatible, msg = handler.is_compatible_with_youtube()
        assert compatible is False
        assert "256GB" in msg

    def test_is_compatible_with_youtube_duration_too_long(self):
        """Videos > 12 hours are flagged as incompatible."""
        class TestHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["abc"]
            FORMAT_NAME = "abc"
            MIME_TYPE = "video/abc"
            DEFAULT_CODEC = "abc"

            def validate_integrity(self):
                return True, "ok"

            def get_metadata(self):
                return {"file_size_bytes": 1000, "duration_seconds": 13 * 3600}

        handler = TestHandler("/tmp/fake.abc")
        compatible, msg = handler.is_compatible_with_youtube()
        assert compatible is False
        assert "12 hours" in msg

    def test_is_compatible_with_youtube_ok(self):
        """Normal files pass YouTube compatibility."""
        class TestHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["abc"]
            FORMAT_NAME = "abc"
            MIME_TYPE = "video/abc"
            DEFAULT_CODEC = "abc"

            def validate_integrity(self):
                return True, "ok"

            def get_metadata(self):
                return {"file_size_bytes": 1000, "duration_seconds": 300}

        handler = TestHandler("/tmp/fake.abc")
        compatible, msg = handler.is_compatible_with_youtube()
        assert compatible is True
        assert "compatible" in msg.lower()

    def test_is_compatible_with_youtube_no_metadata(self):
        """Missing metadata returns False."""
        class TestHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["abc"]
            FORMAT_NAME = "abc"
            MIME_TYPE = "video/abc"
            DEFAULT_CODEC = "abc"

            def validate_integrity(self):
                return True, "ok"

            def get_metadata(self):
                return {}

        handler = TestHandler("/tmp/fake.abc")
        compatible, msg = handler.is_compatible_with_youtube()
        assert compatible is False
        assert "metadata" in msg.lower()


# ------ MP4Handler ------------------------------------------------------------

class TestMP4Handler:
    """Tests for MP4Handler."""

    def test_supported_extensions(self):
        assert "mp4" in [e.lower() for e in MP4Handler.SUPPORTED_EXTENSIONS]

    def test_format_name(self):
        assert MP4Handler.FORMAT_NAME == "mp4"

    def test_mime_type(self):
        assert MP4Handler.MIME_TYPE == "video/mp4"

    def test_default_codec(self):
        assert MP4Handler.DEFAULT_CODEC == "h264"

    def test_initialization(self):
        handler = MP4Handler("/tmp/video.mp4")
        assert handler.file_path == "/tmp/video.mp4"

    def test_initialization_rejects_wrong_ext(self):
        with pytest.raises(ValueError):
            MP4Handler("/tmp/video.avi")

    def test_validate_integrity_returns_tuple(self):
        handler = MP4Handler("/tmp/video.mp4")
        result = handler.validate_integrity()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_get_metadata_returns_dict(self):
        handler = MP4Handler("/tmp/video.mp4")
        metadata = handler.get_metadata()
        assert isinstance(metadata, dict)

    def test_metadata_has_expected_keys(self):
        handler = MP4Handler("/tmp/video.mp4")
        metadata = handler.get_metadata()
        expected_keys = {"format", "duration", "codec", "resolution", "file_size_bytes"}
        assert expected_keys.issubset(set(metadata.keys()))

    def test_convert_raises_not_implemented(self):
        handler = MP4Handler("/tmp/video.mp4")
        with pytest.raises(NotImplementedError):
            handler.convert("/tmp/out.mp4")

    def test_is_compatible_with_youtube(self):
        handler = MP4Handler("/tmp/video.mp4")
        compatible, msg = handler.is_compatible_with_youtube()
        assert isinstance(compatible, bool)
        assert isinstance(msg, str)


# ------ AVIHandler ------------------------------------------------------------

class TestAVIHandler:
    """Tests for AVIHandler."""

    def test_supported_extensions(self):
        assert "avi" in [e.lower() for e in AVIHandler.SUPPORTED_EXTENSIONS]

    def test_format_name(self):
        assert AVIHandler.FORMAT_NAME == "avi"

    def test_mime_type(self):
        assert AVIHandler.MIME_TYPE == "video/x-msvideo"

    def test_default_codec(self):
        assert AVIHandler.DEFAULT_CODEC == "divx"

    def test_initialization(self):
        handler = AVIHandler("/tmp/video.avi")
        assert handler.file_path == "/tmp/video.avi"

    def test_initialization_rejects_wrong_ext(self):
        with pytest.raises(ValueError):
            AVIHandler("/tmp/video.mp4")

    def test_validate_integrity_returns_tuple(self):
        handler = AVIHandler("/tmp/video.avi")
        result = handler.validate_integrity()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_get_metadata_returns_dict(self):
        handler = AVIHandler("/tmp/video.avi")
        metadata = handler.get_metadata()
        assert isinstance(metadata, dict)

    def test_metadata_has_expected_keys(self):
        handler = AVIHandler("/tmp/video.avi")
        metadata = handler.get_metadata()
        expected_keys = {"format", "duration", "codec", "resolution", "file_size_bytes"}
        assert expected_keys.issubset(set(metadata.keys()))

    def test_convert_raises_not_implemented(self):
        handler = AVIHandler("/tmp/video.avi")
        with pytest.raises(NotImplementedError):
            handler.convert("/tmp/out.avi")


# ------ MOVHandler ------------------------------------------------------------

class TestMOVHandler:
    """Tests for MOVHandler."""

    def test_supported_extensions(self):
        assert "mov" in [e.lower() for e in MOVHandler.SUPPORTED_EXTENSIONS]
        assert "qt" in [e.lower() for e in MOVHandler.SUPPORTED_EXTENSIONS]

    def test_format_name(self):
        assert MOVHandler.FORMAT_NAME == "mov"

    def test_mime_type(self):
        assert MOVHandler.MIME_TYPE == "video/quicktime"

    def test_default_codec(self):
        assert MOVHandler.DEFAULT_CODEC == "h264"

    def test_initialization_with_mov(self):
        handler = MOVHandler("/tmp/video.mov")
        assert handler.file_path == "/tmp/video.mov"

    def test_initialization_with_qt(self):
        handler = MOVHandler("/tmp/video.qt")
        assert handler.file_path == "/tmp/video.qt"

    def test_initialization_rejects_wrong_ext(self):
        with pytest.raises(ValueError):
            MOVHandler("/tmp/video.mp4")

    def test_validate_integrity_returns_tuple(self):
        handler = MOVHandler("/tmp/video.mov")
        result = handler.validate_integrity()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_get_metadata_returns_dict(self):
        handler = MOVHandler("/tmp/video.mov")
        metadata = handler.get_metadata()
        assert isinstance(metadata, dict)

    def test_metadata_has_expected_keys(self):
        handler = MOVHandler("/tmp/video.mov")
        metadata = handler.get_metadata()
        expected_keys = {"format", "duration", "codec", "resolution", "file_size_bytes"}
        assert expected_keys.issubset(set(metadata.keys()))

    def test_convert_raises_not_implemented(self):
        handler = MOVHandler("/tmp/video.mov")
        with pytest.raises(NotImplementedError):
            handler.convert("/tmp/out.mov")


# ------ FormatFactory ---------------------------------------------------------

class TestFormatFactory:
    """Tests for FormatFactory."""

    def test_get_handler_mp4(self):
        handler = FormatFactory.get_handler("/tmp/video.mp4")
        assert isinstance(handler, MP4Handler)

    def test_get_handler_avi(self):
        handler = FormatFactory.get_handler("/tmp/video.avi")
        assert isinstance(handler, AVIHandler)

    def test_get_handler_mov(self):
        handler = FormatFactory.get_handler("/tmp/video.mov")
        assert isinstance(handler, MOVHandler)

    def test_get_handler_qt(self):
        handler = FormatFactory.get_handler("/tmp/video.qt")
        assert isinstance(handler, MOVHandler)

    def test_get_handler_unsupported_returns_none(self):
        handler = FormatFactory.get_handler("/tmp/video.xyz")
        assert handler is None

    def test_get_handler_no_extension_returns_none(self):
        handler = FormatFactory.get_handler("/tmp/video")
        assert handler is None

    def test_get_handler_case_insensitive(self):
        handler = FormatFactory.get_handler("/tmp/video.MP4")
        assert isinstance(handler, MP4Handler)

    def test_register_handler(self):
        """Custom handler can be registered and retrieved."""
        class CustomHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["custom"]
            FORMAT_NAME = "custom"
            MIME_TYPE = "video/custom"
            DEFAULT_CODEC = "custom"

            def validate_integrity(self):
                return True, "ok"

            def get_metadata(self):
                return {}

        FormatFactory.register_handler("custom", CustomHandler)
        handler = FormatFactory.get_handler("/tmp/file.custom")
        assert isinstance(handler, CustomHandler)

    def test_get_supported_formats(self):
        formats = FormatFactory.get_supported_formats()
        assert "mp4" in formats
        assert "avi" in formats
        assert "mov" in formats

    def test_get_handler_returns_instance_not_class(self):
        handler = FormatFactory.get_handler("/tmp/video.mp4")
        assert not isinstance(handler, type)  # must be an instance
        assert hasattr(handler, "file_path")


# ------ detect_video_format ---------------------------------------------------

class TestDetectVideoFormat:
    """Tests for the detect_video_format convenience function."""

    def test_detect_mp4(self):
        assert detect_video_format("/tmp/video.mp4") == "mp4"

    def test_detect_avi(self):
        assert detect_video_format("/tmp/video.avi") == "avi"

    def test_detect_mov(self):
        assert detect_video_format("/tmp/video.mov") == "mov"

    def test_detect_qt(self):
        assert detect_video_format("/tmp/video.qt") == "mov"

    def test_detect_m4a(self):
        assert detect_video_format("/tmp/video.m4a") == "mp4"

    def test_detect_m4v(self):
        assert detect_video_format("/tmp/video.m4v") == "mp4"

    def test_detect_unsupported_returns_none(self):
        assert detect_video_format("/tmp/video.xyz") is None

    def test_detect_no_extension_returns_none(self):
        assert detect_video_format("/tmp/video") is None

    def test_detect_case_insensitive(self):
        assert detect_video_format("/tmp/video.MP4") == "mp4"
        assert detect_video_format("/tmp/video.AVI") == "avi"


# ------ create_handler --------------------------------------------------------

class TestCreateHandler:
    """Tests for the create_handler convenience function."""

    def test_create_mp4(self):
        handler = create_handler("/tmp/video.mp4")
        assert isinstance(handler, MP4Handler)

    def test_create_avi(self):
        handler = create_handler("/tmp/video.avi")
        assert isinstance(handler, AVIHandler)

    def test_create_mov(self):
        handler = create_handler("/tmp/video.mov")
        assert isinstance(handler, MOVHandler)

    def test_create_unsupported_returns_none(self):
        handler = create_handler("/tmp/video.xyz")
        assert handler is None

    def test_create_no_extension_returns_none(self):
        handler = create_handler("/tmp/video")
        assert handler is None


# ------ Integration / end-to-end ----------------------------------------------

class TestIntegration:
    """End-to-end integration tests."""

    def test_factory_and_detect_consistent(self):
        """detect_video_format and FormatFactory agree on supported formats."""
        for ext in ["mp4", "avi", "mov", "qt", "m4a", "m4v"]:
            path = f"/tmp/video.{ext}"
            fmt = detect_video_format(path)
            handler = FormatFactory.get_handler(path)
            if fmt is not None:
                assert handler is not None
                assert handler.format == fmt
            else:
                assert handler is None

    def test_handler_properties_consistent(self):
        """Handler properties match class-level constants."""
        for handler_cls in [MP4Handler, AVIHandler, MOVHandler]:
            path = f"/tmp/video.{handler_cls.FORMAT_NAME}"
            handler = handler_cls(path)
            assert handler.format == handler_cls.FORMAT_NAME
            assert handler.mime_type == handler_cls.MIME_TYPE
            assert handler.default_codec == handler_cls.DEFAULT_CODEC

    def test_validate_extension_and_is_valid_extension_agree(self):
        """is_valid_extension and __init__ validation are consistent."""
        for handler_cls in [MP4Handler, AVIHandler, MOVHandler]:
            valid_ext = handler_cls.SUPPORTED_EXTENSIONS[0]
            path_valid = f"/tmp/video.{valid_ext}"
            path_invalid = f"/tmp/video.xyz"

            assert handler_cls.is_valid_extension(path_valid) is True
            assert handler_cls.is_valid_extension(path_invalid) is False

            # Valid path should not raise
            handler_cls(path_valid)

            # Invalid path should raise
            with pytest.raises(ValueError):
                handler_cls(path_invalid)

    def test_youtube_compatibility_boundary_values(self):
        """Test boundary values for YouTube limits."""
        class TestHandler(VideoFormatHandler):
            SUPPORTED_EXTENSIONS = ["abc"]
            FORMAT_NAME = "abc"
            MIME_TYPE = "video/abc"
            DEFAULT_CODEC = "abc"

            def validate_integrity(self):
                return True, "ok"

            def get_metadata(self):
                return self._meta

        # Exactly 256 GB – should be OK
        h = TestHandler("/tmp/fake.abc")
        h._meta = {"file_size_bytes": 256 * 1024**3, "duration_seconds": 100}
        ok, _ = h.is_compatible_with_youtube()
        assert ok is True

        # 1 byte over – should fail
        h._meta = {"file_size_bytes": 256 * 1024**3 + 1, "duration_seconds": 100}
        ok, _ = h.is_compatible_with_youtube()
        assert ok is False

        # Exactly 12 hours – should be OK
        h._meta = {"file_size_bytes": 1000, "duration_seconds": 12 * 3600}
        ok, _ = h.is_compatible_with_youtube()
        assert ok is True

        # 1 second over – should fail
        h._meta = {"file_size_bytes": 1000, "duration_seconds": 12 * 3600 + 1}
        ok, _ = h.is_compatible_with_youtube()
        assert ok is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
