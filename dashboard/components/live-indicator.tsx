'use client';

import { useEffect, useState } from 'react';

interface LiveIndicatorProps {
  isUpdating?: boolean;
  lastUpdateTime?: Date;
}

export function LiveIndicator({ isUpdating = false, lastUpdateTime }: LiveIndicatorProps) {
  const [timeSinceUpdate, setTimeSinceUpdate] = useState('now');

  useEffect(() => {
    if (!lastUpdateTime) return;

    const updateTimeString = () => {
      const now = new Date();
      const diffMs = now.getTime() - lastUpdateTime.getTime();
      const diffSeconds = Math.floor(diffMs / 1000);
      const diffMinutes = Math.floor(diffSeconds / 60);

      if (diffSeconds < 60) {
        setTimeSinceUpdate(`${diffSeconds}s ago`);
      } else if (diffMinutes < 60) {
        setTimeSinceUpdate(`${diffMinutes}m ago`);
      } else {
        setTimeSinceUpdate('over an hour ago');
      }
    };

    updateTimeString();
    const interval = setInterval(updateTimeString, 1000);
    return () => clearInterval(interval);
  }, [lastUpdateTime]);

  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${isUpdating ? 'animate-pulse' : ''} ${isUpdating ? 'bg-green-400' : 'bg-slate-500'}`} />
      <span className="text-xs text-slate-400">
        {isUpdating ? 'Updating' : 'Updated'} {timeSinceUpdate}
      </span>
    </div>
  );
}
