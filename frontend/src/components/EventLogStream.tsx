import React, { useState } from 'react';
import { WorkflowEvent } from '../types';
import { ChevronDown, ChevronRight, Activity, Clock } from 'lucide-react';

interface EventLogStreamProps {
  events: WorkflowEvent[];
  isInvestigating?: boolean;
}

export const EventLogStream: React.FC<EventLogStreamProps> = ({ events, isInvestigating }) => {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const getNodeColor = (node: string) => {
    switch (node.toLowerCase()) {
      case 'planner':
        return 'text-sky-400 bg-sky-950/60 border-sky-800/80';
      case 'retriever':
        return 'text-emerald-400 bg-emerald-950/60 border-emerald-800/80';
      case 'analyst':
        return 'text-violet-400 bg-violet-950/60 border-violet-800/80';
      case 'critic':
        return 'text-amber-400 bg-amber-950/60 border-amber-800/80';
      case 'reporter':
        return 'text-indigo-400 bg-indigo-950/60 border-indigo-800/80';
      case 'human_review':
        return 'text-pink-400 bg-pink-950/60 border-pink-800/80';
      default:
        return 'text-slate-400 bg-slate-800 border-slate-700';
    }
  };

  const nodeLabels: Record<string, string> = {
    planner: 'Planning', retriever: 'Record search', analyst: 'Analysis', critic: 'Evidence check', reporter: 'Report',
    human_review: 'Human review', workflow_engine: 'Investigation'
  };
  const nodeLabel = (node: string) => nodeLabels[node.toLowerCase()] || node.replace(/_/g, ' ');

  return (
    <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden flex flex-col h-full shadow-lg">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800 bg-slate-950 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-slate-200">Investigation progress</h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
            {events.length} updates
          </span>
        </div>

        {isInvestigating && (
          <div className="flex items-center space-x-2 text-xs text-indigo-400">
            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></span>
            <span>Investigation in progress…</span>
          </div>
        )}
      </div>

      {/* Events List */}
      <div className="p-4 space-y-3 overflow-y-auto max-h-[480px] text-sm">
        {events.length === 0 ? (
          <div className="text-center py-10 text-slate-500">
            <Activity className="w-8 h-8 mx-auto mb-2 text-slate-600 opacity-60" />
            <p>No updates yet. Start the investigation to review available evidence.</p>
          </div>
        ) : (
          events.map((ev, idx) => {
            const isExpanded = expandedId === (ev.id || idx);
            const hasDetails = Boolean(ev.message || (ev.details && Object.keys(ev.details).length > 0));
            const timeStr = new Date(ev.timestamp).toLocaleTimeString();
            const activityText: Record<string, string> = {
              planner: 'Planning the next investigation step…',
              retriever: 'Searching the available evidence…',
              analyst: 'Reviewing evidence and identifying possible explanations…',
              critic: 'Checking whether the available evidence is sufficient…',
              reporter: 'Preparing the investigation report…',
              human_review: 'A reviewer has updated this investigation.'
            };

            return (
              <div
                key={ev.id || idx}
                className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 hover:border-slate-700 transition-all"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                    <span className={`px-2 py-0.5 rounded border uppercase text-[10px] font-bold ${getNodeColor(ev.node)}`}>
                      {nodeLabel(ev.node)}
                    </span>
                    <span className="text-slate-500 text-[11px] flex items-center space-x-1">
                      <Clock className="w-3 h-3 inline" />
                      <span>{timeStr}</span>
                    </span>
                  </div>

                  {hasDetails && (
                    <button
                      onClick={() => toggleExpand(ev.id || idx)}
                      className="text-slate-400 hover:text-slate-200 flex items-center space-x-1 text-[11px] bg-slate-900 px-2 py-0.5 rounded border border-slate-800"
                    >
                      <span>{isExpanded ? 'Hide details' : 'Technical details'}</span>
                      {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                    </button>
                  )}
                </div>

                <p className="text-slate-300 mt-2 font-sans text-sm leading-relaxed">{activityText[ev.node.toLowerCase()] || 'Investigation progress was updated.'}</p>

                {isExpanded && hasDetails && (
                  <div className="mt-3 p-3 rounded bg-slate-900 border border-slate-800 overflow-x-auto text-[11px] text-indigo-300">
                    <p className="font-sans text-slate-300 mb-2">{ev.message}</p><pre>{JSON.stringify(ev.details, null, 2)}</pre>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
