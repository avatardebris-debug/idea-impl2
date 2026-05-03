/**
 * Tutorial data for memory technique tutorials
 */

export type TutorialStepType = 'recall' | 'visualization' | 'association' | 'placement';

export interface TutorialStep {
  id: string;
  title: string;
  description: string;
  exercise?: {
    type: TutorialStepType;
    instructions: string;
    successCriteria: string;
  };
  tips?: string[];
}

export interface Tutorial {
  id: string;
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimatedTime: number; // in minutes
  steps: TutorialStep[];
  prerequisites?: string[];
  learningObjectives: string[];
}

export interface TutorialProgress {
  tutorialId: string;
  completed: boolean;
  currentStep: number;
  lastAccessed: string;
  completionDate?: string;
}

/**
 * Tutorial: Introduction to Memory Palaces
 */
export const MEMORY_PALACE_TUTORIAL: Tutorial = {
  id: 'memory-palace-intro',
  title: 'Introduction to Memory Palaces',
  description: 'Learn the foundational technique of creating and using memory palaces for enhanced recall.',
  difficulty: 'beginner',
  estimatedTime: 15,
  learningObjectives: [
    'Understand the loci method',
    'Create your first memory palace',
    'Place items in specific locations',
    'Recall items using spatial memory',
  ],
  prerequisites: [],
  steps: [
    {
      id: 'step-1',
      title: 'What is a Memory Palace?',
      description: 'A memory palace (or method of loci) is a mnemonic device that uses spatial memory to improve recall. You mentally place items in familiar locations, then "walk through" the palace to retrieve them.',
      tips: [
        'Start with a place you know well - your home, school, or daily route',
        'The more familiar the location, the better your recall will be',
        'Visualize the space in as much detail as possible',
      ],
    },
    {
      id: 'step-2',
      title: 'Choose Your Palace',
      description: 'Select a familiar location to serve as your memory palace. This could be your house, office, or a route you walk regularly.',
      exercise: {
        type: 'visualization',
        instructions: 'Close your eyes and visualize your chosen location. Walk through it mentally, noting specific spots where you can place items.',
        successCriteria: 'You can mentally walk through the location and identify at least 5 distinct placement spots.',
      },
      tips: [
        'Use a clockwise or counter-clockwise path for consistency',
        'Mark clear, distinct locations (doorways, furniture, corners)',
        'Start with 5-10 locations for your first palace',
      ],
    },
    {
      id: 'step-3',
      title: 'Place Items in Your Palace',
      description: 'Now that you have your palace, learn to place items in specific locations. Each item should have a unique, memorable association with its location.',
      exercise: {
        type: 'placement',
        instructions: 'Choose 3 items to memorize. For each item, create a vivid mental image that connects the item to a specific location in your palace.',
        successCriteria: 'You can describe the connection between each item and its location.',
      },
      tips: [
        'Make the images vivid, unusual, and exaggerated',
        'Use all your senses - sight, sound, smell, touch',
        'The more emotional or funny the image, the better you\'ll remember it',
      ],
    },
    {
      id: 'step-4',
      title: 'Recall Items from Your Palace',
      description: 'To recall items, mentally walk through your palace in the same order you placed them. At each location, retrieve the item you placed there.',
      exercise: {
        type: 'recall',
        instructions: 'Walk through your palace mentally and recall all the items you placed. Write down what you remember.',
        successCriteria: 'You can recall at least 80% of the items you placed.',
      },
      tips: [
        'Always walk through in the same order',
        'If you miss an item, revisit that location and strengthen the association',
        'Practice recall multiple times to strengthen the memory',
      ],
    },
  ],
};

/**
 * Tutorial: The Moonwalking with Einstein Technique
 */
export const MOONWALKING_TUTORIAL: Tutorial = {
  id: 'moonwalking-einstein',
  title: 'Moonwalking with Einstein Technique',
  description: 'Learn the advanced memory techniques from Joshua Foer\'s book, including the Major System and memory palace construction.',
  difficulty: 'intermediate',
  estimatedTime: 25,
  learningObjectives: [
    'Master the Major System for numbers',
    'Create vivid memory palaces',
    'Combine techniques for complex memorization',
    'Apply techniques to real-world scenarios',
  ],
  prerequisites: ['memory-palace-intro'],
  steps: [
    {
      id: 'step-1',
      title: 'The Major System',
      description: 'The Major System is a mnemonic technique that converts numbers into consonant sounds, which can then be turned into words and images.',
      exercise: {
        type: 'association',
        instructions: 'Learn the basic Major System mappings: 0=s/z, 1=t/d, 2=n, 3=m, 4=r, 5=l, 6=sh/j/ch, 7=k/g, 8=f/v, 9=p/b. Create words from number sequences.',
        successCriteria: 'You can convert at least 5 number sequences into words.',
      },
      tips: [
        'Vowels and w, h, y are "wildcards" - they don\'t represent numbers',
        'Start with simple 2-3 digit numbers',
        'Practice daily to build fluency',
      ],
    },
    {
      id: 'step-2',
      title: 'Advanced Memory Palace Construction',
      description: 'Learn to build more complex memory palaces with multiple rooms and detailed pathways.',
      exercise: {
        type: 'visualization',
        instructions: 'Create a memory palace with at least 20 distinct locations across 2-3 rooms.',
        successCriteria: 'You can mentally navigate the palace and identify all 20 locations.',
      },
      tips: [
        'Use different floors or rooms for different categories',
        'Create clear boundaries between locations',
        'Practice the path until it\'s automatic',
      ],
    },
    {
      id: 'step-3',
      title: 'Combining Techniques',
      description: 'Learn to combine the Major System with memory palaces to memorize long sequences of numbers.',
      exercise: {
        type: 'recall',
        instructions: 'Memorize a 20-digit number using the Major System and a memory palace. Recall it after 1 hour.',
        successCriteria: 'You can recall the number with 100% accuracy.',
      },
      tips: [
        'Break the number into 2-digit chunks',
        'Convert each chunk to a word',
        'Place each word in a location in your palace',
      ],
    },
  ],
};

/**
 * Tutorial: Speed Memorization Techniques
 */
export const SPEED_MEMORIZATION_TUTORIAL: Tutorial = {
  id: 'speed-memorization',
  title: 'Speed Memorization Techniques',
  description: 'Learn advanced techniques for rapid memorization and recall under time pressure.',
  difficulty: 'advanced',
  estimatedTime: 30,
  learningObjectives: [
    'Master rapid encoding techniques',
    'Optimize recall speed',
    'Handle large volumes of information',
    'Apply techniques in competitive scenarios',
  ],
  prerequisites: ['memory-palace-intro', 'moonwalking-einstein'],
  steps: [
    {
      id: 'step-1',
      title: 'Rapid Encoding',
      description: 'Learn techniques to encode information as quickly as possible while maintaining accuracy.',
      exercise: {
        type: 'recall',
        instructions: 'Practice encoding 50 random words in under 2 minutes using memory palace techniques.',
        successCriteria: 'You can encode all 50 words with at least 90% accuracy.',
      },
      tips: [
        'Use automatic associations',
        'Don\'t overthink the images',
        'Practice under timed conditions',
      ],
    },
    {
      id: 'step-2',
      title: 'Optimized Recall',
      description: 'Learn to recall information faster through optimized pathways and retrieval strategies.',
      exercise: {
        type: 'recall',
        instructions: 'Recall 100 items from your memory palace in under 5 minutes.',
        successCriteria: 'You can recall all 100 items with at least 95% accuracy.',
      },
      tips: [
        'Use consistent pathways',
        'Practice rapid retrieval',
        'Minimize cognitive load',
      ],
    },
  ],
};

/**
 * Tutorial: Advanced Associations
 */
export const ADVANCED_ASSOCIATIONS_TUTORIAL: Tutorial = {
  id: 'advanced-associations',
  title: 'Advanced Association Techniques',
  description: 'Master complex association techniques for linking multiple concepts and ideas.',
  difficulty: 'intermediate',
  estimatedTime: 20,
  learningObjectives: [
    'Create complex associations',
    'Link multiple concepts',
    'Build associative chains',
    'Apply to abstract concepts',
  ],
  prerequisites: ['memory-palace-intro'],
  steps: [
    {
      id: 'step-1',
      title: 'Complex Associations',
      description: 'Learn to create associations between multiple items and concepts.',
      exercise: {
        type: 'association',
        instructions: 'Create a chain of associations linking 10 unrelated concepts.',
        successCriteria: 'You can recall the entire chain in order.',
      },
      tips: [
        'Use vivid imagery',
        'Create logical connections',
        'Practice the chain multiple times',
      ],
    },
  ],
};

/**
 * Tutorial: Card Memorization
 */
export const CARD_MEMORIZATION_TUTORIAL: Tutorial = {
  id: 'card-memorization',
  title: 'Card Memorization Techniques',
  description: 'Learn specialized techniques for memorizing playing cards quickly and accurately.',
  difficulty: 'advanced',
  estimatedTime: 35,
  learningObjectives: [
    'Master card-to-image conversion',
    'Memorize full decks',
    'Recall cards in order',
    'Apply to competitive scenarios',
  ],
  prerequisites: ['memory-palace-intro', 'moonwalking-einstein'],
  steps: [
    {
      id: 'step-1',
      title: 'Card-to-Image System',
      description: 'Learn a system to convert each card into a unique image or person.',
      exercise: {
        type: 'association',
        instructions: 'Create images for all 52 cards using a consistent system.',
        successCriteria: 'You can identify any card from its image.',
      },
      tips: [
        'Use people or characters for each card',
        'Make images distinctive and memorable',
        'Practice until automatic',
      ],
    },
  ],
};

/**
 * Tutorial: Number Memorization
 */
export const NUMBER_MEMORIZATION_TUTORIAL: Tutorial = {
  id: 'number-memorization',
  title: 'Number Memorization Techniques',
  description: 'Master techniques for memorizing long sequences of numbers.',
  difficulty: 'intermediate',
  estimatedTime: 25,
  learningObjectives: [
    'Master the Major System',
    'Memorize long number sequences',
    'Recall numbers with high accuracy',
    'Apply to real-world scenarios',
  ],
  prerequisites: ['memory-palace-intro'],
  steps: [
    {
      id: 'step-1',
      title: 'Major System Mastery',
      description: 'Deep dive into the Major System for converting numbers to words.',
      exercise: {
        type: 'association',
        instructions: 'Convert 10 different 10-digit numbers into memorable words.',
        successCriteria: 'You can convert all 10 numbers accurately.',
      },
      tips: [
        'Practice daily',
        'Build a vocabulary of number-words',
        'Use the Major System consistently',
      ],
    },
  ],
};

/**
 * Tutorial: Mnemonic Techniques
 */
export const MNEMONIC_TUTORIAL: Tutorial = {
  id: 'mnemonic-techniques',
  title: 'Mnemonic Techniques Overview',
  description: 'Learn various mnemonic techniques and when to apply each one.',
  difficulty: 'beginner',
  estimatedTime: 20,
  learningObjectives: [
    'Understand different mnemonic types',
    'Choose the right technique for the task',
    'Apply mnemonics to various scenarios',
    'Build a personal mnemonic toolkit',
  ],
  prerequisites: [],
  steps: [
    {
      id: 'step-1',
      title: 'Types of Mnemonics',
      description: 'Explore different types of mnemonic devices and their applications.',
      exercise: {
        type: 'recall',
        instructions: 'Learn and practice 3 different mnemonic techniques.',
        successCriteria: 'You can explain when to use each technique.',
      },
      tips: [
        'Match the technique to the task',
        'Practice each technique regularly',
        'Build a toolkit of techniques',
      ],
    },
  ],
};

/**
 * All tutorials available
 */
export const tutorials: Tutorial[] = [
  MEMORY_PALACE_TUTORIAL,
  MOONWALKING_TUTORIAL,
  SPEED_MEMORIZATION_TUTORIAL,
  ADVANCED_ASSOCIATIONS_TUTORIAL,
  CARD_MEMORIZATION_TUTORIAL,
  NUMBER_MEMORIZATION_TUTORIAL,
  MNEMONIC_TUTORIAL,
];

/**
 * Get a tutorial by ID
 */
export function getTutorialById(id: string): Tutorial | undefined {
  return tutorials.find((t) => t.id === id);
}

/**
 * Get all tutorials
 */
export function getAllTutorials(): Tutorial[] {
  return tutorials;
}

/**
 * Get tutorials by difficulty
 */
export function getTutorialsByDifficulty(difficulty: string): Tutorial[] {
  return tutorials.filter((t) => t.difficulty === difficulty);
}

/**
 * Get tutorials by prerequisite
 */
export function getTutorialsByPrerequisite(prereqId: string): Tutorial[] {
  return tutorials.filter((t) => t.prerequisites?.includes(prereqId));
}
