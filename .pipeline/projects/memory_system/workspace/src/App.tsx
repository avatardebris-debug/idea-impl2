import { useState } from 'react';
import { useSpacedRepetition, useReviewQueue, useReviewSession } from './hooks';
import { DifficultyLevel, RecallQuality } from './types/spacedRepetition';

function App() {
  const {
    addItem,
    reviewItem,
    getDueItemsForReview,
    stats,
    schedules,
    difficultyConfigs,
  } = useSpacedRepetition();

  const { queue, estimatedTime } = useReviewQueue();
  const { currentSession, startSession, recordReview, endSession } = useReviewSession();

  const [newItemId, setNewItemId] = useState('');
  const [newItemDifficulty, setNewItemDifficulty] = useState<DifficultyLevel>('medium');
  const [newItemPriority, setNewItemPriority] = useState(3);
  const [newItemReason, setNewItemReason] = useState('');

  const handleAddItem = () => {
    if (!newItemId) return;

    addItem(newItemId, {
      difficulty: newItemDifficulty,
      priority: newItemPriority,
      reason: newItemReason,
    });

    setNewItemId('');
    setNewItemReason('');
  };

  const handleReview = (itemId: string, quality: RecallQuality) => {
    reviewItem(itemId, quality);
  };

  const handleCompleteSession = () => {
    if (!currentSession) return;

    const session = endSession();
    if (session) {
      console.log('Session completed:', session);
    }
  };

  const dueItems = getDueItemsForReview(10);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Memory System</h1>

      <section style={{ marginBottom: '20px' }}>
        <h2>Add New Item</h2>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Item ID"
            value={newItemId}
            onChange={(e) => setNewItemId(e.target.value)}
            style={{ padding: '8px', flex: 1 }}
          />
          <select
            value={newItemDifficulty}
            onChange={(e) => setNewItemDifficulty(e.target.value as DifficultyLevel)}
            style={{ padding: '8px' }}
          >
            <option value="very_easy">Very Easy</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
            <option value="very_hard">Very Hard</option>
          </select>
          <input
            type="number"
            placeholder="Priority (0-10)"
            value={newItemPriority}
            onChange={(e) => setNewItemPriority(parseInt(e.target.value))}
            min="0"
            max="10"
            style={{ padding: '8px', width: '100px' }}
          />
          <input
            type="text"
            placeholder="Reason"
            value={newItemReason}
            onChange={(e) => setNewItemReason(e.target.value)}
            style={{ padding: '8px', flex: 1 }}
          />
          <button onClick={handleAddItem} style={{ padding: '8px 16px' }}>
            Add Item
          </button>
        </div>
      </section>

      <section style={{ marginBottom: '20px' }}>
        <h2>Statistics</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
          <div style={{ padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
            <strong>Total Items</strong>
            <div>{stats.totalItems}</div>
          </div>
          <div style={{ padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
            <strong>Due Today</strong>
            <div>{stats.dueToday}</div>
          </div>
          <div style={{ padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
            <strong>Avg Retention</strong>
            <div>{(stats.averageRetention * 100).toFixed(1)}%</div>
          </div>
          <div style={{ padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
            <strong>Est. Review Time</strong>
            <div>{estimatedTime}s</div>
          </div>
        </div>
      </section>

      <section style={{ marginBottom: '20px' }}>
        <h2>Due for Review ({dueItems.length})</h2>
        {dueItems.length === 0 ? (
          <p>No items due for review.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {dueItems.map((item) => (
              <div
                key={item.itemId}
                style={{
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  backgroundColor: '#fafafa',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <strong>{item.itemId}</strong>
                  <span style={{ color: '#666' }}>Priority: {item.priority}</span>
                </div>
                <div style={{ marginBottom: '5px' }}>
                  <strong>Difficulty:</strong> {item.difficulty}
                </div>
                <div style={{ marginBottom: '5px' }}>
                  <strong>Reason:</strong> {item.reason}
                </div>
                <div style={{ display: 'flex', gap: '5px' }}>
                  <button
                    onClick={() => handleReview(item.itemId, 'again')}
                    style={{ padding: '5px 10px', backgroundColor: '#ff6b6b', color: 'white', border: 'none', borderRadius: '4px' }}
                  >
                    Again
                  </button>
                  <button
                    onClick={() => handleReview(item.itemId, 'hard')}
                    style={{ padding: '5px 10px', backgroundColor: '#ffa502', color: 'white', border: 'none', borderRadius: '4px' }}
                  >
                    Hard
                  </button>
                  <button
                    onClick={() => handleReview(item.itemId, 'good')}
                    style={{ padding: '5px 10px', backgroundColor: '#4ecdc4', color: 'white', border: 'none', borderRadius: '4px' }}
                  >
                    Good
                  </button>
                  <button
                    onClick={() => handleReview(item.itemId, 'easy')}
                    style={{ padding: '5px 10px', backgroundColor: '#45b7d1', color: 'white', border: 'none', borderRadius: '4px' }}
                  >
                    Easy
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section style={{ marginBottom: '20px' }}>
        <h2>Review Session</h2>
        {currentSession ? (
          <div style={{ padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
            <div style={{ marginBottom: '10px' }}>
              <strong>Items Reviewed:</strong> {currentSession.itemsReviewed}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Mastered:</strong> {currentSession.itemsMastered}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Time Spent:</strong> {currentSession.timeSpent}s
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={() => recordReview('again')}
                style={{ padding: '8px 16px', backgroundColor: '#ff6b6b', color: 'white', border: 'none', borderRadius: '4px' }}
              >
                Record Again
              </button>
              <button
                onClick={() => recordReview('hard')}
                style={{ padding: '8px 16px', backgroundColor: '#ffa502', color: 'white', border: 'none', borderRadius: '4px' }}
              >
                Record Hard
              </button>
              <button
                onClick={() => recordReview('good')}
                style={{ padding: '8px 16px', backgroundColor: '#4ecdc4', color: 'white', border: 'none', borderRadius: '4px' }}
              >
                Record Good
              </button>
              <button
                onClick={() => recordReview('easy')}
                style={{ padding: '8px 16px', backgroundColor: '#45b7d1', color: 'white', border: 'none', borderRadius: '4px' }}
              >
                Record Easy
              </button>
              <button
                onClick={handleCompleteSession}
                style={{ padding: '8px 16px', backgroundColor: '#2ecc71', color: 'white', border: 'none', borderRadius: '4px' }}
              >
                Complete Session
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={startSession}
            style={{ padding: '8px 16px', backgroundColor: '#3498db', color: 'white', border: 'none', borderRadius: '4px' }}
          >
            Start Session
          </button>
        )}
      </section>

      <section>
        <h2>All Items</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
          {Object.entries(schedules).map(([itemId, schedule]) => (
            <div
              key={itemId}
              style={{
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                backgroundColor: '#fafafa',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <strong>{itemId}</strong>
                <span style={{ color: '#666' }}>{schedule.status}</span>
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                Next review: {new Date(schedule.scheduledDate).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default App;
