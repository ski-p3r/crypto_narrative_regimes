'use client';

import { useEffect, useState } from 'react';
import { AlertCircle, Zap, TrendingUp, Link2, Clock, X } from 'lucide-react';

interface StreamEvent {
  id: string;
  type: 'CASCADE' | 'VOLATILITY' | 'REGIME' | 'CORRELATION' | 'FUNDING';
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  title: string;
  description: string;
  timestamp: Date;
  data?: any;
}

interface EventsStreamProps {
  events?: StreamEvent[];
  onEventDismiss?: (eventId: string) => void;
}

export function EventsStream({ events = [], onEventDismiss }: EventsStreamProps) {
  const [displayedEvents, setDisplayedEvents] = useState<StreamEvent[]>([]);

  useEffect(() => {
    setDisplayedEvents(events.slice(0, 5));
  }, [events]);

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'CASCADE':
        return <AlertCircle className="w-4 h-4" />;
      case 'VOLATILITY':
        return <Zap className="w-4 h-4" />;
      case 'REGIME':
        return <TrendingUp className="w-4 h-4" />;
      case 'CORRELATION':
        return <Link2 className="w-4 h-4" />;
      case 'FUNDING':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const getEventColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-500/10 border-red-500/30 text-red-400';
      case 'WARNING':
        return 'bg-orange-500/10 border-orange-500/30 text-orange-400';
      default:
        return 'bg-blue-500/10 border-blue-500/30 text-blue-400';
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-slate-400" />
          <h2 className="text-xl font-bold">Live Events</h2>
          <span className="text-xs bg-green-500/10 text-green-400 px-2 py-1 rounded-full">
            {displayedEvents.length} active
          </span>
        </div>
      </div>

      {displayedEvents.length > 0 ? (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {displayedEvents.map((event) => (
            <div
              key={event.id}
              className={`border rounded-lg p-4 flex items-start gap-3 ${getEventColor(event.severity)}`}
            >
              <div className="pt-1">{getEventIcon(event.type)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-semibold text-sm">{event.title}</h3>
                    <p className="text-xs text-slate-400 mt-1">{event.description}</p>
                  </div>
                  <button
                    onClick={() => onEventDismiss?.(event.id)}
                    className="p-1 hover:bg-slate-700/30 rounded"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
                <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-700/30">
                  <span className="text-xs text-slate-500">
                    {event.timestamp.toLocaleTimeString()}
                  </span>
                  <span className="text-xs font-mono text-slate-500">{event.type}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-slate-400">
          <Clock className="w-12 h-12 mx-auto mb-2 opacity-20" />
          <p>No recent events</p>
          <p className="text-xs mt-1">Events will appear here in real-time</p>
        </div>
      )}
    </div>
  );
}
