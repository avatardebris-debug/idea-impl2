import { useState, useEffect } from 'react';
import { api } from '../api';

interface Video {
  id: string;
  title: string;
  description: string;
  file_path: string;
  thumbnail_path: string;
  status: string;
  created_at: string;
}

interface YouTubeUploadProps {
  tableId: string;
  onUploadComplete: () => void;
}

export default function YouTubeUpload({ tableId, onUploadComplete }: YouTubeUploadProps) {
  const [videos, setVideos] = useState<Video[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<string>('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [privacyStatus, setPrivacyStatus] = useState('private');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadVideos();
  }, [tableId]);

  const loadVideos = async () => {
    try {
      const data = await api.videos.list({ page: 1, page_size: 100 });
      setVideos(data.items);
    } catch (err: any) {
      setError(err.message || 'Failed to load videos');
    }
  };

  const handleUpload = async () => {
    if (!selectedVideo) {
      setError('Please select a video');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      setSuccess(null);

      const video = videos.find(v => v.id === selectedVideo);
      if (!video) {
        setError('Selected video not found');
        return;
      }

      const response = await fetch('/api/youtube/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_path: video.file_path,
          title: title || video.title,
          description: description || video.description,
          tags: tags.split(',').map(t => t.trim()).filter(t => t),
          privacy_status: privacyStatus,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess(`Video uploaded successfully! Video ID: ${data.video_id}`);
        onUploadComplete();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Upload failed');
      }
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleSelectVideo = (videoId: string) => {
    setSelectedVideo(videoId);
    const video = videos.find(v => v.id === videoId);
    if (video) {
      setTitle(video.title);
      setDescription(video.description);
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Upload to YouTube</h3>

      {error && (
        <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {success && (
        <div className="p-3 bg-green-100 border border-green-400 text-green-700 rounded">
          {success}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700">Select Video</label>
        <select
          value={selectedVideo}
          onChange={(e) => handleSelectVideo(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        >
          <option value="">Select a video</option>
          {videos.map(video => (
            <option key={video.id} value={video.id}>
              {video.title}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Title</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Tags (comma separated)</label>
        <input
          type="text"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Privacy Status</label>
        <select
          value={privacyStatus}
          onChange={(e) => setPrivacyStatus(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        >
          <option value="private">Private</option>
          <option value="unlisted">Unlisted</option>
          <option value="public">Public</option>
        </select>
      </div>

      <button
        onClick={handleUpload}
        disabled={uploading || !selectedVideo}
        className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:opacity-50"
      >
        {uploading ? 'Uploading...' : 'Upload to YouTube'}
      </button>
    </div>
  );
}
