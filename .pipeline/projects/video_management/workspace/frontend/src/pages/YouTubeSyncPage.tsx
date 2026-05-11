import React from 'react';
import YouTubeSync from '../components/YouTubeSync';

const YouTubeSyncPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Sync Videos</h1>
        <p className="text-gray-500 mt-1">
          Pull all videos from your connected YouTube channel.
        </p>
      </div>
      <YouTubeSync />
    </div>
  );
};

export default YouTubeSyncPage;
