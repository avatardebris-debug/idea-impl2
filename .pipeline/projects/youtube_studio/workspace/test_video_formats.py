"""Tests for video format handling in YouTube Studio.

This module provides comprehensive tests for the video format handler,
including format detection, validation, and conversion functionality.
"""

import os
import tempfile
import unittest
from pathlib import Path

from video_formats import (
    VideoFormatHandler,
    FormatFactory,
    create_handler,
    detect_video_format
)
from formats.mp4_handler import MP4Handler
from formats.avi_handler import AVIHandler
from formats.mov_handler import MOVHandler


class TestVideoFormatDetection(unittest.TestCase):
    """Test cases for video format detection."""
    
    def test_detect_mp4_format(self):
        """Test detection of MP4 format."""
        format_name = detect_video_format('/path/to/video.mp4')
        self.assertEqual(format_name, 'mp4')
    
    def test_detect_avi_format(self):
        """Test detection of AVI format."""
        format_name = detect_video_format('/path/to/video.avi')
        self.assertEqual(format_name, 'avi')
    
    def test_detect_mov_format(self):
        """Test detection of MOV format."""
        format_name = detect_video_format('/path/to/video.mov')
        self.assertEqual(format_name, 'mov')
    
    def test_detect_unknown_format(self):
        """Test detection of unsupported format."""
        format_name = detect_video_format('/path/to/video.xyz')
        self.assertIsNone(format_name)
    
    def test_detect_case_insensitive(self):
        """Test case-insensitive format detection."""
        self.assertEqual(detect_video_format('/path/TO/VIDEO.MP4'), 'mp4')
        self.assertEqual(detect_video_format('/path/to/video.Mp4'), 'mp4')
    
    def test_detect_m4v_extension(self):
        """Test detection of m4v extension maps to mp4."""
        self.assertEqual(detect_video_format('/path/to/video.m4v'), 'mp4')
    
    def test_detect_qt_extension(self):
        """Test detection of qt extension maps to mov."""
        self.assertEqual(detect_video_format('/path/to/video.qt'), 'mov')
    
    def test_detect_no_extension(self):
        """Test detection of file with no extension."""
        format_name = detect_video_format('/path/to/video')
        self.assertIsNone(format_name)


class TestFormatFactory(unittest.TestCase):
    """Test cases for the FormatFactory class."""
    
    def test_get_handler_mp4(self):
        """Test getting MP4 handler."""
        handler = create_handler('/path/to/video.mp4')
        self.assertIsInstance(handler, MP4Handler)
        self.assertEqual(handler.file_path, '/path/to/video.mp4')
    
    def test_get_handler_avi(self):
        """Test getting AVI handler."""
        handler = create_handler('/path/to/video.avi')
        self.assertIsInstance(handler, AVIHandler)
        self.assertEqual(handler.file_path, '/path/to/video.avi')
    
    def test_get_handler_mov(self):
        """Test getting MOV handler."""
        handler = create_handler('/path/to/video.mov')
        self.assertIsInstance(handler, MOVHandler)
        self.assertEqual(handler.file_path, '/path/to/video.mov')
    
    def test_get_handler_unknown(self):
        """Test getting handler for unsupported format."""
        handler = create_handler('/path/to/video.xyz')
        self.assertIsNone(handler)
    
    def test_factory_create_mp4(self):
        """Test FormatFactory.create for MP4."""
        handler = FormatFactory.create('/path/to/video.mp4')
        self.assertIsInstance(handler, MP4Handler)
    
    def test_factory_detect(self):
        """Test FormatFactory.detect."""
        format_name = FormatFactory.detect('/path/to/video.mp4')
        self.assertEqual(format_name, 'mp4')
    
    def test_factory_get_supported_formats(self):
        """Test FormatFactory.get_supported_formats."""
        formats = FormatFactory.get_supported_formats()
        self.assertIsInstance(formats, list)
        self.assertIn('mp4', formats)
        self.assertIn('avi', formats)
        self.assertIn('mov', formats)


class TestMP4Handler(unittest.TestCase):
    """Test cases for MP4Handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mp4_handler = MP4Handler('/path/to/video.mp4')
    
    def test_is_valid_extension_mp4(self):
        """Test valid MP4 extension."""
        self.assertTrue(MP4Handler.is_valid_extension('/path/to/video.mp4'))
    
    def test_is_valid_extension_m4v(self):
        """Test valid M4V extension."""
        self.assertTrue(MP4Handler.is_valid_extension('/path/to/video.m4v'))
    
    def test_is_valid_extension_mov(self):
        """Test valid MOV extension (also supported by MP4 handler)."""
        self.assertTrue(MP4Handler.is_valid_extension('/path/to/video.mov'))
    
    def test_is_valid_extension_avi(self):
        """Test invalid extension for MP4 handler."""
        self.assertFalse(MP4Handler.is_valid_extension('/path/to/video.avi'))
    
    def test_validate_file_not_found(self):
        """Test validation of non-existent file."""
        is_valid, message = self.mp4_handler.validate_file()
        self.assertFalse(is_valid)
        self.assertIn('not found', message.lower())
    
    def test_validate_file_too_small(self):
        """Test validation of file that's too small."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            # Write less than MIN_FILE_SIZE bytes
            f.write(b'small')
            temp_path = f.name
        
        try:
            handler = MP4Handler(temp_path)
            is_valid, message = handler.validate_file()
            self.assertFalse(is_valid)
            self.assertIn('too small', message.lower())
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_valid(self):
        """Test validation of a valid file."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            # Write enough bytes to pass size check
            f.write(b'x' * 2048)
            temp_path = f.name
        
        try:
            handler = MP4Handler(temp_path)
            is_valid, message = handler.validate_file()
            self.assertTrue(is_valid)
            self.assertEqual(message, 'File is valid')
        finally:
            os.unlink(temp_path)
    
    def test_get_thumbnail_path(self):
        """Test thumbnail path generation."""
        thumbnail_path = self.mp4_handler.get_thumbnail_path()
        self.assertTrue(thumbnail_path.endswith('.jpg'))
        self.assertIn('video', thumbnail_path)
    
    def test_is_compatible_with_youtube_no_metadata(self):
        """Test YouTube compatibility check without metadata."""
        is_compatible, message = self.mp4_handler.is_compatible_with_youtube()
        self.assertFalse(is_compatible)
        self.assertIn('metadata', message.lower())


class TestAVIHandler(unittest.TestCase):
    """Test cases for AVIHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.avi_handler = AVIHandler('/path/to/video.avi')
    
    def test_is_valid_extension_avi(self):
        """Test valid AVI extension."""
        self.assertTrue(AVIHandler.is_valid_extension('/path/to/video.avi'))
    
    def test_is_valid_extension_mp4(self):
        """Test invalid extension for AVI handler."""
        self.assertFalse(AVIHandler.is_valid_extension('/path/to/video.mp4'))
    
    def test_validate_file_not_found(self):
        """Test validation of non-existent file."""
        is_valid, message = self.avi_handler.validate_file()
        self.assertFalse(is_valid)
        self.assertIn('not found', message.lower())
    
    def test_is_compatible_with_youtube(self):
        """Test that AVI is not compatible with YouTube."""
        is_compatible, message = self.avi_handler.is_compatible_with_youtube()
        self.assertFalse(is_compatible)
        self.assertIn('convert to mp4', message.lower())


class TestMOVHandler(unittest.TestCase):
    """Test cases for MOVHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mov_handler = MOVHandler('/path/to/video.mov')
    
    def test_is_valid_extension_mov(self):
        """Test valid MOV extension."""
        self.assertTrue(MOVHandler.is_valid_extension('/path/to/video.mov'))
    
    def test_is_valid_extension_qt(self):
        """Test valid QT extension."""
        self.assertTrue(MOVHandler.is_valid_extension('/path/to/video.qt'))
    
    def test_is_valid_extension_mp4(self):
        """Test invalid extension for MOV handler."""
        self.assertFalse(MOVHandler.is_valid_extension('/path/to/video.mp4'))
    
    def test_validate_file_not_found(self):
        """Test validation of non-existent file."""
        is_valid, message = self.mov_handler.validate_file()
        self.assertFalse(is_valid)
        self.assertIn('not found', message.lower())
    
    def test_is_compatible_with_youtube(self):
        """Test that MOV is not compatible with YouTube."""
        is_compatible, message = self.mov_handler.is_compatible_with_youtube()
        self.assertFalse(is_compatible)
        self.assertIn('convert to mp4', message.lower())


class TestVideoFormatHandler(unittest.TestCase):
    """Test cases for the VideoFormatHandler class."""
    
    def test_get_handler_mp4(self):
        """Test getting MP4 handler from VideoFormatHandler."""
        handler = VideoFormatHandler('/path/to/video.mp4').get_handler()
        self.assertIsInstance(handler, MP4Handler)
    
    def test_get_handler_avi(self):
        """Test getting AVI handler from VideoFormatHandler."""
        handler = VideoFormatHandler('/path/to/video.avi').get_handler()
        self.assertIsInstance(handler, AVIHandler)
    
    def test_get_handler_mov(self):
        """Test getting MOV handler from VideoFormatHandler."""
        handler = VideoFormatHandler('/path/to/video.mov').get_handler()
        self.assertIsInstance(handler, MOVHandler)
    
    def test_get_handler_unknown(self):
        """Test getting handler for unsupported format."""
        with self.assertRaises(Exception):
            VideoFormatHandler('/path/to/video.xyz').get_handler()
    
    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = VideoFormatHandler.get_supported_formats()
        self.assertIsInstance(formats, list)
        self.assertIn('mp4', formats)
        self.assertIn('avi', formats)
        self.assertIn('mov', formats)
    
    def test_get_thumbnail_path_mp4(self):
        """Test thumbnail path for MP4."""
        handler = VideoFormatHandler('/path/to/video.mp4')
        thumbnail_path = handler.get_thumbnail_path()
        self.assertTrue(thumbnail_path.endswith('.jpg'))


if __name__ == '__main__':
    unittest.main()
