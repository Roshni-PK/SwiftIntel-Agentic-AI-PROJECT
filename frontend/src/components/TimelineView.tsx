import React from 'react';
import { TimelineEvent } from '../types';
import { Clock, ShieldCheck, Tag } from 'lucide-react';

interface TimelineViewProps {
  events: TimelineEvent[];
  onSelectRecord?: (recordId: string) => void;
}

export const TimelineView: React.FC<TimelineViewProps> = ({ events, onSelectRecord }) => {
  if (!events || events.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
        <Clock className="w-8 h-8 mx-auto mb-2 text-slate-600" />
        <p className="text-sm">No chronological timeline reconstructed yet.</p>
        <p className="text-xs text-slate-400 mt-1">Start the investigation to build a timeline from available records.</p>
      </div>
    );
  }

  return (
    <div className="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
      {events.map((ev, index) => {
        const timeFormatted = ev.timestamp ? new Date(ev.timestamp).toUTCString() : 'Timestamp Unspecified';

        return (
          <div key={index} className="relative group">
            {/* Timeline bullet dot */}
            <div className="absolute -left-[23px] top-1.5 w-3.5 h-3.5 rounded-full bg-slate-950 border-2 border-indigo-500 group-hover:scale-125 transition-transform" />

            {/* Event Card */}
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all shadow-sm">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <span className="text-xs font-mono text-indigo-400 flex items-center space-x-1">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{timeFormatted}</span>
                </span>

                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
                    {ev.category}
                  </span>
                  {ev.verified === true && (
                    <span className="text-[10px] text-emerald-400 flex items-center space-x-0.5">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>Source status confirmed</span>
                    </span>
                  )}
                  {ev.verified === false && <span className="text-[10px] text-amber-500">Not verified</span>}
                </div>
              </div>

              <p className="text-sm text-slate-100 font-medium mt-2 leading-relaxed">{ev.event}</p>

              {/* Source Records Citation Chips */}
              {ev.source_records && ev.source_records.length > 0 && (
                <div className="flex items-center space-x-1.5 mt-3 pt-2.5 border-t border-slate-800/80">
                  <Tag className="w-3 h-3 text-slate-400" />
                  <span className="text-[11px] text-slate-400 mr-1">Traceable Sources:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {ev.source_records.map((rid) => (
                      <button
                        key={rid}
                        onClick={() => onSelectRecord && onSelectRecord(rid)}
                        className="px-2 py-0.5 rounded text-xs font-mono bg-indigo-950/80 text-indigo-300 border border-indigo-800 hover:bg-indigo-900 hover:text-white transition-colors"
                      >
                        [{rid}]
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
