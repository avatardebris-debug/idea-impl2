import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { TutorialView } from '../components/TutorialView';
import { getTutorialById } from '../data/tutorials';
import MainLayout from '../layouts/MainLayout';

const Tutorial: React.FC = () => {
  const { tutorialId } = useParams<{ tutorialId: string }>();
  const navigate = useNavigate();

  const handleTutorialComplete = () => {
    // Navigate to home or another page after completion
    navigate('/home');
  };

  if (!tutorialId) {
    return (
      <MainLayout>
        <div className="error-page">
          <h1>Error</h1>
          <p>No tutorial ID provided</p>
          <button onClick={() => navigate('/home')}>Go Home</button>
        </div>
      </MainLayout>
    );
  }

  const tutorial = getTutorialById(tutorialId);

  if (!tutorial) {
    return (
      <MainLayout>
        <div className="error-page">
          <h1>Not Found</h1>
          <p>Tutorial not found</p>
          <button onClick={() => navigate('/home')}>Go Home</button>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <TutorialView tutorialId={tutorialId} onComplete={handleTutorialComplete} />
    </MainLayout>
  );
};

export default Tutorial;
