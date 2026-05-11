import React, { useState } from 'react';
import { api, YouTubeUploadResponse } from '../api';

type UploadStatus = 'public' | 'private' | 'unlisted';

const YouTubeUploadPage: React.FC = () => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<UploadStatus>('unlisted');
  const [tags, setTags] = useState('');
  const [publishAt, setPublishAt] = useState('');
  const [thumbnailUrl, setThumbnailUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<YouTubeUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Title is required');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      setResult(null);

      const tagList = tags
        ? tags.split(',').map((t) => t.trim()).filter(Boolean)
        : [];

      const data = await api.youtube.uploadVideo({
        title: title.trim(),
        description: description.trim(),
        status,
        tags: tagList.length > 0 ? tagList : undefined,
        publish_at: publishAt || undefined,
        thumbnail_url: thumbnailUrl.trim() || undefined,
      });

      setResult(data);
      if (data.success) {
        setTitle('');
        setDescription('');
        setTags('');
        setPublishAt('');
        setThumbnailUrl('');
      }
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Upload to YouTube</h1>
        <p className="text-gray-500 mt-1">
          Publish a video to your connected YouTube channel.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {result && (
        <div className={`p-4 rounded-lg border ${result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          <p className={`font-medium ${result.success ? 'text-green-700' : 'text-red-700'}`}>
            {result.message}
          </p>
          {result.youtube_video_id && (
            <p className="text-sm text-gray-600 mt-1">
              Video ID: {result.youtube_video_id}
            </p>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Title *
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter video title"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter video description"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Visibility
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as UploadStatus)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="public">Public</option>
              <option value="unlisted">Unlisted</option>
              <option value="private">Private</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Publish Date (optional)
            </label>
            <input
              type="datetime-local"
              value={publishAt}
              onChange={(e) => setPublishAt(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tags (comma-separated)
          </label>
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., tutorial, coding, react"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Thumbnail URL (optional)
          </label>
          <input
            type="url"
            value={thumbnailUrl}
            onChange={(e) => setThumbnailUrl(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="https://example.com/thumbnail.jpg"
          />
        </div>

        <button
          type="submit"
          disabled={uploading}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? 'Uploading...' : 'Upload Video'}
        </button>
      </form>
    </div>
  );
};

export default YouTubeUploadPage;
