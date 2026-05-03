import React from 'react';

interface RecallAnalyticsProps {
  recallData: any[];
  onRecallComplete?: (data: any) => void;
}

const RecallAnalytics: React.FC<RecallAnalyticsProps> = ({ recallData, onRecallComplete }) => {
  return (
    <div className="recall-analytics">
      <h3>Recall Analytics</h3>
      <div className="recall-data">
        {recallData.length === 0 ? (
          <p className="no-data">No recall data available</p>
        ) : (
          <ul className="recall-list">
            {recallData.map((item, index) => (
              <li key={index} className="recall-item">
                <span className="recall-index">{index + 1}</span>
                <span className="recall-content">{JSON.stringify(item)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      {onRecallComplete && (
        <button onClick={() => onRecallComplete(recallData[recallData.length - 1])}>
          Mark Complete
        </button>
      )}
    </div>
  );
};

export default RecallAnalytics;
