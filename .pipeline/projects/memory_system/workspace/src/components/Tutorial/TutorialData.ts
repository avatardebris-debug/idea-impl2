/**
 * Tutorial data for memory technique tutorials
 */

export interface TutorialStep {
  id: string;
  title: string;
  description: string;
  exercise?: {
    type: 'recall' | 'spatial' | 'story' | 'association';
    instructions: string;
    items?: string[];
    timeLimit?: number;
  };
  tips?: string[];
}

export interface Tutorial {
  id: string;
  title: string;
  description: string;
  duration: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  steps: TutorialStep[];
  prerequisites?: string[];
  learningObjectives: string[];
}

export const TUTORIALS: Tutorial[] = [
  {
    id: 'loci-method-basics',
    title: 'The Loci Method: Basics',
    description: 'Learn the foundation of memory palaces using the loci method',
    duration: '15 minutes',
    difficulty: 'beginner',
    prerequisites: [],
    learningObjectives: [
      'Understand what the loci method is',
      'Create your first memory palace',
      'Place items in locations using visualization',
    ],
    steps: [
      {
        id: 'loci-intro',
        title: 'What is the Loci Method?',
        description: 'The loci method (also called the method of loci) is one of the oldest and most effective memory techniques. It involves associating items you want to remember with specific locations in a familiar place, like your home.',
        tips: [
          'Start with a place you know very well',
          'Use a consistent path through the locations',
          'The more vivid the images, the better you\'ll remember',
        ],
      },
      {
        id: 'loci-create-palace',
        title: 'Creating Your First Memory Palace',
        description: 'Choose a familiar location - your home, office, or a route you walk regularly. Identify 5-10 distinct locations along a clear path.',
        exercise: {
          type: 'spatial',
          instructions: 'Identify 5 locations in your home. Click on each location to mark it as part of your memory palace path.',
          timeLimit: 120,
        },
        tips: [
          'Keep the path logical and sequential',
          'Choose locations that are distinct from each other',
          'Don\'t make the path too long for beginners',
        ],
      },
      {
        id: 'loci-place-items',
        title: 'Placing Items in Your Palace',
        description: 'Now that you have your locations, it\'s time to place items you want to remember. Create vivid, unusual mental images at each location.',
        exercise: {
          type: 'recall',
          instructions: 'Place the following items in your memory palace: Apple, Book, Key, Phone, Watch. Create a vivid image for each.',
          items: ['Apple', 'Book', 'Key', 'Phone', 'Watch'],
          timeLimit: 180,
        },
        tips: [
          'Make images exaggerated and unusual',
          'Engage multiple senses in your visualization',
          'Add movement or action to make images memorable',
        ],
      },
      {
        id: 'loci-practice',
        title: 'Practice Recall',
        description: 'Walk through your memory palace and recall the items you placed. This reinforces the neural pathways.',
        exercise: {
          type: 'recall',
          instructions: 'Walk through your memory palace and recall all 5 items. Try to remember the order.',
          items: ['Apple', 'Book', 'Key', 'Phone', 'Watch'],
          timeLimit: 120,
        },
        tips: [
          'Go through the path in order',
          'If you forget, try to reconstruct the image',
          'Practice makes perfect - repeat daily',
        ],
      },
    ],
  },
  {
    id: 'story-technique',
    title: 'Story-Based Memory Technique',
    description: 'Learn to create coherent stories to remember sequences of items',
    duration: '20 minutes',
    difficulty: 'intermediate',
    prerequisites: ['loci-method-basics'],
    learningObjectives: [
      'Understand how stories aid memory',
      'Create narrative connections between items',
      'Use the Story Builder tool effectively',
    ],
    steps: [
      {
        id: 'story-intro',
        title: 'Why Stories Work',
        description: 'Our brains are wired for stories. When we connect items through a narrative, we create multiple retrieval paths, making recall much easier.',
        tips: [
          'Stories provide context and meaning',
          'Emotional content enhances memory',
          'Unexpected plot twists make stories memorable',
        ],
      },
      {
        id: 'story-create',
        title: 'Building Your Story',
        description: 'Use the Story Builder to create a narrative connecting your items. Start with a beginning, middle, and end.',
        exercise: {
          type: 'story',
          instructions: 'Create a story connecting these items: Key, Apple, Book, Phone, Watch. Make it vivid and memorable.',
          items: ['Key', 'Apple', 'Book', 'Phone', 'Watch'],
          timeLimit: 240,
        },
        tips: [
          'Start with a clear protagonist or perspective',
          'Include sensory details',
          'Add unexpected elements for memorability',
          'Ensure logical flow between items',
        ],
      },
      {
        id: 'story-refine',
        title: 'Refining Your Story',
        description: 'Review and enhance your story. Add more vivid details and ensure smooth transitions between items.',
        exercise: {
          type: 'story',
          instructions: 'Review your story. Add at least 3 more descriptive details to make it more vivid.',
          timeLimit: 180,
        },
        tips: [
          'Add colors, sounds, and textures',
          'Make characters feel real',
          'Ensure each item appears naturally in the story',
        ],
      },
      {
        id: 'story-recall',
        title: 'Story Recall Practice',
        description: 'Read your story and then try to recall the items in order without looking.',
        exercise: {
          type: 'recall',
          instructions: 'Read your story, then recall all 5 items in order.',
          items: ['Key', 'Apple', 'Book', 'Phone', 'Watch'],
          timeLimit: 120,
        },
        tips: [
          'Read the story aloud for better retention',
          'Visualize the story as you recall',
          'Practice recalling without looking at the text',
        ],
      },
    ],
  },
  {
    id: 'association-mastery',
    title: 'Association Mastery',
    description: 'Master the art of creating strong associations for cards and numbers',
    duration: '25 minutes',
    difficulty: 'intermediate',
    prerequisites: ['loci-method-basics'],
    learningObjectives: [
      'Use suit-based associations for cards',
      'Apply number mnemonics effectively',
      'Combine associations for complex items',
    ],
    steps: [
      {
        id: 'assoc-intro',
        title: 'Understanding Associations',
        description: 'Associations link new information to existing knowledge. For cards and numbers, we use visual mnemonics and semantic connections.',
        tips: [
          'Connect to things you already know well',
          'Use visual imagery whenever possible',
          'The more unusual, the more memorable',
        ],
      },
      {
        id: 'assoc-suits',
        title: 'Suit-Based Associations',
        description: 'Each suit has characteristic imagery: Hearts = love/heart, Diamonds = wealth/diamond, Clubs = nature/clover, Spades = tool/spade.',
        exercise: {
          type: 'association',
          instructions: 'For each suit, create a visual association. Use the suggestion engine for help.',
          timeLimit: 180,
        },
        tips: [
          'Hearts: Think of a beating heart or love',
          'Diamonds: Visualize a sparkling gem',
          'Clubs: Imagine a four-leaf clover',
          'Spades: Picture a gardener\'s spade',
        ],
      },
      {
        id: 'assoc-numbers',
        title: 'Number Mnemonics',
        description: 'Use the Major System-inspired approach: 1=candle, 2=swan, 3=heart, 4=boat, 5=hook, 6=elephant, 7=mountain, 8=snowman, 9=balloon, 10=bat.',
        exercise: {
          type: 'association',
          instructions: 'Create visual associations for numbers 1-10 using the shape-based mnemonics.',
          timeLimit: 240,
        },
        tips: [
          '1: A single candle flame',
          '2: A graceful swan',
          '3: A heart shape',
          '4: A boat with a sail',
          '5: A fishing hook',
          '6: An elephant with a trunk',
          '7: A mountain peak',
          '8: A snowman',
          '9: A floating balloon',
          '10: A baseball bat',
        ],
      },
      {
        id: 'assoc-combine',
        title: 'Combining Associations',
        description: 'For number cards, combine the number and suit imagery into a single vivid image.',
        exercise: {
          type: 'association',
          instructions: 'Create combined associations for: 2 of Hearts, 7 of Spades, 5 of Diamonds, 10 of Clubs.',
          timeLimit: 300,
        },
        tips: [
          'Combine both elements seamlessly',
          'Create an action or interaction between elements',
          'Make the combined image unusual and memorable',
        ],
      },
    ],
  },
  {
    id: 'moonwalking-einstein',
    title: 'Moonwalking with Einstein Techniques',
    description: 'Advanced memory palace techniques from the world champion memorizer',
    duration: '30 minutes',
    difficulty: 'advanced',
    prerequisites: ['loci-method-basics', 'story-technique'],
    learningObjectives: [
      'Apply advanced visualization techniques',
      'Use the Memory Palace Dashboard effectively',
      'Optimize item placement for recall',
    ],
    steps: [
      {
        id: 'mwe-intro',
        title: 'The Art of Memory',
        description: 'Joshua Foer\'s "Moonwalking with Einstein" reveals how ordinary people can become memory champions through systematic training.',
        tips: [
          'Memory is a skill, not just a talent',
          'Consistent practice yields results',
          'The techniques work for anyone',
        ],
      },
      {
        id: 'mwe-palace',
        title: 'Advanced Palace Construction',
        description: 'Learn to build larger, more complex memory palaces with multiple rooms and detailed locations.',
        exercise: {
          type: 'spatial',
          instructions: 'Build a memory palace with 3 rooms and 5 locations per room (15 total locations).',
          timeLimit: 300,
        },
        tips: [
          'Use a building or complex route',
          'Ensure each room has distinct characteristics',
          'Maintain a clear path through all locations',
        ],
      },
      {
        id: 'mwe-optimization',
        title: 'Smart Placement',
        description: 'Use the placement optimizer to find optimal room and location assignments for your items.',
        exercise: {
          type: 'spatial',
          instructions: 'Place 15 items using the smart placement recommendations.',
          timeLimit: 240,
        },
        tips: [
          'Consider item characteristics when placing',
          'Use the optimizer suggestions',
          'Group related items logically',
        ],
      },
      {
        id: 'mwe-recall',
        title: 'Advanced Recall Practice',
        description: 'Practice recall under various conditions to build robust memory skills.',
        exercise: {
          type: 'recall',
          instructions: 'Recall all 15 items from your memory palace. Then try recall after a 5-minute distraction.',
          items: Array.from({ length: 15 }, (_, i) => `Item ${i + 1}`),
          timeLimit: 300,
        },
        tips: [
          'Practice in different environments',
          'Add distractions to build resilience',
          'Track your accuracy over time',
        ],
      },
    ],
  },
];

export const getTutorialById = (id: string): Tutorial | undefined => {
  return TUTORIALS.find(t => t.id === id);
};

export const getTutorialSteps = (tutorialId: string): TutorialStep[] => {
  const tutorial = getTutorialById(tutorialId);
  return tutorial?.steps || [];
};

export const getPrerequisites = (tutorialId: string): string[] => {
  const tutorial = getTutorialById(tutorialId);
  return tutorial?.prerequisites || [];
};

export const getLearningObjectives = (tutorialId: string): string[] => {
  const tutorial = getTutorialById(tutorialId);
  return tutorial?.learningObjectives || [];
};

export const getBeginnerTutorials = (): Tutorial[] => {
  return TUTORIALS.filter(t => t.difficulty === 'beginner');
};

export const getIntermediateTutorials = (): Tutorial[] => {
  return TUTORIALS.filter(t => t.difficulty === 'intermediate');
};

export const getAdvancedTutorials = (): Tutorial[] => {
  return TUTORIALS.filter(t => t.difficulty === 'advanced');
};

export default TUTORIALS;
