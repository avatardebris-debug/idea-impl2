import { createBrowserRouter, Navigate } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import Home from '../pages/Home';
import CardExercise from '../pages/CardExercise';
import NumberExercise from '../pages/NumberExercise';
import MnemonicExercise from '../pages/MnemonicExercise';
import MemoryPalace from '../pages/MemoryPalace';
import MemoryPalaceIntro from '../pages/MemoryPalaceIntro';
import AdvancedAssociations from '../pages/AdvancedAssociations';
import Moonwalking from '../pages/Moonwalking';
import SpeedMemorization from '../pages/SpeedMemorization';
import TutorialPage from '../pages/TutorialPage';
import Tutorial from '../pages/Tutorial';

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/home" replace />,
      },
      {
        path: 'home',
        element: <Home />,
      },
      {
        path: 'card-exercise',
        element: <CardExercise />,
      },
      {
        path: 'number-exercise',
        element: <NumberExercise />,
      },
      {
        path: 'mnemonic-exercise',
        element: <MnemonicExercise />,
      },
      {
        path: 'memory-palace',
        element: <MemoryPalace />,
      },
      {
        path: 'memory-palace-intro',
        element: <MemoryPalaceIntro />,
      },
      {
        path: 'advanced-associations',
        element: <AdvancedAssociations />,
      },
      {
        path: 'moonwalking',
        element: <Moonwalking />,
      },
      {
        path: 'speed-memorization',
        element: <SpeedMemorization />,
      },
      {
        path: 'tutorial-page',
        element: <TutorialPage />,
      },
      {
        path: 'tutorial',
        element: <Tutorial />,
      },
    ],
  },
]);

export default router;
