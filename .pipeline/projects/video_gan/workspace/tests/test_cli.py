"""
Tests for VideoGAN CLI.
"""

import sys
import pathlib
import pytest
from unittest.mock import patch, MagicMock

# Add workspace to path
_ws = pathlib.Path(__file__).parent.parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from video_gan.cli import main


class TestCLI:
    """Test CLI commands."""

    @patch('video_gan.cli.VideoGAN')
    @patch('video_gan.cli.VideoProcessor')
    @patch('video_gan.cli.click.echo')
    def test_train_command(self, mock_echo, mock_processor, mock_gan_class):
        """Test the train command."""
        # Mock the VideoGAN class
        mock_gan = MagicMock()
        mock_gan_class.return_value = mock_gan
        
        # Mock the VideoProcessor
        mock_processor_instance = MagicMock()
        mock_processor_instance.create_random_video.return_value = MagicMock()
        mock_processor.return_value = mock_processor_instance
        
        # Mock train_epoch
        mock_gan.train_epoch.return_value = {'d_loss': 0.5, 'g_loss': 0.6}
        
        # Run the train command
        with patch('sys.argv', ['cli', '--epochs', '2', '--batch-size', '4']):
            with patch('video_gan.cli.click.echo'):
                with patch('sys.exit'):
                    main()
        
        # Verify the calls
        mock_gan_class.assert_called_once()
        mock_gan.train_epoch.assert_called()
        mock_processor_instance.create_random_video.assert_called()

    @patch('video_gan.cli.VideoGAN')
    @patch('video_gan.cli.VideoProcessor')
    @patch('video_gan.cli.click.echo')
    def test_generate_command(self, mock_echo, mock_processor, mock_gan_class):
        """Test the generate command."""
        # Mock the VideoGAN class
        mock_gan = MagicMock()
        mock_gan_class.return_value = mock_gan
        
        # Mock the VideoProcessor
        mock_processor_instance = MagicMock()
        mock_processor_instance.create_random_video.return_value = MagicMock()
        mock_processor.return_value = mock_processor_instance
        
        # Mock generate
        mock_gan.generate.return_value = MagicMock()
        
        # Run the generate command
        with patch('sys.argv', ['cli', '--generate', '5']):
            with patch('video_gan.cli.click.echo'):
                with patch('sys.exit'):
                    main()
        
        # Verify the calls
        mock_gan_class.assert_called_once()
        mock_gan.generate.assert_called()
        mock_processor_instance.create_random_video.assert_called()

    @patch('video_gan.cli.VideoGAN')
    @patch('video_gan.cli.VideoProcessor')
    @patch('video_gan.cli.click.echo')
    def test_classify_command(self, mock_echo, mock_processor, mock_gan_class):
        """Test the classify command."""
        # Mock the VideoGAN class
        mock_gan = MagicMock()
        mock_gan_class.return_value = mock_gan
        
        # Mock the VideoProcessor
        mock_processor_instance = MagicMock()
        mock_processor_instance.load_video_frames.return_value = MagicMock()
        mock_processor.return_value = mock_processor_instance
        
        # Mock classify
        mock_gan.classify.return_value = (0.8, 0.2)
        
        # Run the classify command
        with patch('sys.argv', ['cli', '--classify', 'test.mp4']):
            with patch('video_gan.cli.click.echo'):
                with patch('sys.exit'):
                    main()
        
        # Verify the calls
        mock_gan_class.assert_called_once()
        mock_gan.classify.assert_called()
        mock_processor_instance.load_video_frames.assert_called()

    @patch('video_gan.cli.VideoGAN')
    @patch('video_gan.cli.click.echo')
    def test_info_command(self, mock_echo, mock_gan_class):
        """Test the info command."""
        # Mock the VideoGAN class
        mock_gan = MagicMock()
        mock_gan_class.return_value = mock_gan
        
        # Mock the properties
        mock_gan.generator_latent_dim = 128
        mock_gan.generator_num_frames = 16
        mock_gan.generator_frame_size = (64, 64)
        mock_gan.discriminator_input_channels = 3
        mock_gan.discriminator_num_frames = 16
        mock_gan.discriminator_frame_size = (64, 64)
        
        # Run the info command
        with patch('sys.argv', ['cli', '--info']):
            with patch('video_gan.cli.click.echo'):
                with patch('sys.exit'):
                    main()
        
        # Verify the calls
        mock_gan_class.assert_called_once()

    @patch('video_gan.cli.VideoGAN')
    @patch('video_gan.cli.click.echo')
    def test_save_command(self, mock_echo, mock_gan_class):
        """Test the save command."""
        # Mock the VideoGAN class
        mock_gan = MagicMock()
        mock_gan_class.return_value = mock_gan
        
        # Run the save command
        with patch('sys.argv', ['cli', '--save', 'test.pt']):
            with patch('video_gan.cli.click.echo'):
                with patch('sys.exit'):
                    main()
        
        # Verify the calls
        mock_gan_class.assert_called_once()
        mock_gan.save_checkpoint.assert_called()

    @patch('video_gan.cli.VideoGAN')
    @patch('video_gan.cli.click.echo')
    def test_load_command(self, mock_echo, mock_gan_class):
        """Test the load command."""
        # Mock the VideoGAN class
        mock_gan = MagicMock()
        mock_gan_class.return_value = mock_gan
        
        # Run the load command
        with patch('sys.argv', ['cli', '--load', 'test.pt']):
            with patch('video_gan.cli.click.echo'):
                with patch('sys.exit'):
                    main()
        
        # Verify the calls
        mock_gan_class.assert_called_once()
        mock_gan.load_checkpoint.assert_called()
