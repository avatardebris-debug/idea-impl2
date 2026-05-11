import React from 'react';
import YouTubeChannel from '../components/YouTubeChannel';

const YouTubePage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">YouTube Integration</h1>
        <p className="text-gray-500 mt-1">
          Connect your YouTube channel to sync and manage videos.
        </p>
      </div>
      <YouTubeChannel />
    </div>
  );
};

export default YouTubePage;
