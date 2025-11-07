/**
 * Hover card component for AI Tutor application.
 * 
 * Displays hover tooltips for graph nodes with summary information.
 */

import { HoverPayload } from '../lib/api';

/**
 * Hover card component props.
 */
interface HoverCardProps {
  payload: HoverPayload;
  x: number;
  y: number;
  onClose?: () => void;
}

/**
 * Hover card component.
 */
export function HoverCard({ payload, x, y, onClose }: HoverCardProps) {
  const getMasteryColor = (mastery?: number) => {
    if (mastery === undefined) return 'text-gray-600';
    if (mastery < 0.3) return 'text-red-600';
    if (mastery < 0.7) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getMasteryLabel = (mastery?: number) => {
    if (mastery === undefined) return 'N/A';
    return `${(mastery * 100).toFixed(0)}%`;
  };

  return (
    <div
      className="absolute bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-sm z-50 pointer-events-auto"
      style={{
        left: `${x}px`,
        top: `${y}px`,
        transform: 'translate(-50%, -100%)',
        marginTop: '-10px',
      }}
    >
      {onClose && (
        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      )}
      
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-lg">{payload.title}</h3>
          <span className="text-xs px-2 py-1 bg-gray-200 rounded">
            {payload.type}
          </span>
        </div>

        {payload.type === 'topic' && (
          <>
            {payload.summary && (
              <p className="text-sm text-gray-700">{payload.summary}</p>
            )}
            <div className="text-xs text-gray-600 space-y-1">
              <div>Events: {payload.event_count || 0}</div>
              {payload.last_event_at && (
                <div>
                  Last event: {new Date(payload.last_event_at).toLocaleDateString()}
                </div>
              )}
              {payload.open_questions && payload.open_questions.length > 0 && (
                <div>
                  Open questions: {payload.open_questions.length}
                </div>
              )}
            </div>
          </>
        )}

        {payload.type === 'skill' && (
          <>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-semibold">Mastery:</span>
              <span className={`text-sm font-bold ${getMasteryColor(payload.mastery)}`}>
                {getMasteryLabel(payload.mastery)}
              </span>
            </div>
            <div className="text-xs text-gray-600 space-y-1">
              <div>Evidence: {payload.evidence_count || 0}</div>
              {payload.last_evidence_at && (
                <div>
                  Last evidence: {new Date(payload.last_evidence_at).toLocaleDateString()}
                </div>
              )}
              {payload.topic_id && (
                <div>Topic: {payload.topic_id}</div>
              )}
            </div>
          </>
        )}

        {payload.type === 'event' && (
          <>
            {payload.content && (
              <p className="text-sm text-gray-700 line-clamp-3">{payload.content}</p>
            )}
            <div className="text-xs text-gray-600 space-y-1">
              <div>Type: {payload.event_type}</div>
              <div>Actor: {payload.actor}</div>
              {payload.created_at && (
                <div>
                  Created: {new Date(payload.created_at).toLocaleDateString()}
                </div>
              )}
              {payload.topics && payload.topics.length > 0 && (
                <div>Topics: {payload.topics.length}</div>
              )}
              {payload.skills && payload.skills.length > 0 && (
                <div>Skills: {payload.skills.length}</div>
              )}
            </div>
          </>
        )}

        {payload.event_snippet && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <p className="text-xs text-gray-500 italic">
              "{payload.event_snippet.content.substring(0, 100)}..."
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {new Date(payload.event_snippet.created_at).toLocaleDateString()}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

