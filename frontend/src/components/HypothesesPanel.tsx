import React from 'react';
import { Hypothesis } from '../types';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  ThumbsUp,
  ThumbsDown,
  AlertOctagon
} from 'lucide-react';

interface HypothesesPanelProps {
  hypotheses: Hypothesis[];
  evidenceGaps?: string[];
  onSelectRecord?: (recordId: string) => void;
}

export const HypothesesPanel: React.FC<HypothesesPanelProps> = ({
  hypotheses,
  evidenceGaps = [],
  onSelectRecord
}) => {
  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'supported':
        return (
          <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-800">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Evidence supports this</span>
          </span>
        );
      case 'refuted':
        return (
          <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-300 border border-rose-800">
            <XCircle className="w-3.5 h-3.5" />
            <span>Evidence conflicts</span>
          </span>
        );
      case 'challenged':
        return (
          <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-300 border border-amber-800">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Still uncertain</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Under consideration</span>
          </span>
        );
    }
  };

  if (!hypotheses || hypotheses.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
        <HelpCircle className="w-8 h-8 mx-auto mb-2 text-slate-600" />
        <p className="text-sm">No possible explanations yet.</p>
        <p className="text-xs text-slate-400 mt-1">Start the investigation to review the available evidence.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hypotheses List */}
      <div className="space-y-4">
        {hypotheses.map((hyp) => (
          <div
            key={hyp.id}
            className={`p-5 rounded-xl border transition-all ${
              hyp.status === 'supported'
                ? 'bg-slate-900/90 border-emerald-800/60 shadow-lg shadow-emerald-950/20'
                : hyp.status === 'refuted'
                ? 'bg-slate-900/70 border-rose-900/40 opacity-90'
                : 'bg-slate-900/80 border-slate-800'
            }`}
          >
            <div className="flex items-start justify-between flex-wrap gap-2">
              <div className="flex items-center space-x-2">
                <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-slate-800 text-slate-300">
                  {hyp.id}
                </span>
                <h4 className="text-base font-semibold text-white">{hyp.title}</h4>
              </div>
              {getStatusBadge(hyp.status)}
            </div>

            <p className="text-sm text-slate-300 mt-2.5 leading-relaxed">{hyp.description}</p>

            {hyp.confidence_rationale && (
              <div className="mt-3 p-3 rounded-lg bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300">
                <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] block mb-1">
                  Why this is suggested
                </span>
                {hyp.confidence_rationale}
              </div>
            )}

            {/* Supporting & Contradictory Evidence Grids */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4 pt-3 border-t border-slate-800">
              {/* Supporting Evidence */}
              <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/40">
                <div className="flex items-center space-x-1.5 text-xs font-semibold text-emerald-400 mb-2">
                  <ThumbsUp className="w-3.5 h-3.5" />
                  <span>Evidence supporting this ({hyp.supporting_evidence?.length || 0})</span>
                </div>
                {hyp.supporting_evidence && hyp.supporting_evidence.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {hyp.supporting_evidence.map((rid) => (
                      <button
                        key={rid}
                        onClick={() => onSelectRecord && onSelectRecord(rid)}
                        className="px-2 py-0.5 rounded text-xs font-mono bg-emerald-900/40 text-emerald-300 border border-emerald-800 hover:bg-emerald-800 hover:text-white transition-colors"
                      >
                        [{rid}]
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No direct supporting records found.</p>
                )}
              </div>

              {/* Contradictory Evidence */}
              <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-900/40">
                <div className="flex items-center space-x-1.5 text-xs font-semibold text-rose-400 mb-2">
                  <ThumbsDown className="w-3.5 h-3.5" />
                  <span>Evidence that conflicts ({hyp.contradictory_evidence?.length || 0})</span>
                </div>
                {hyp.contradictory_evidence && hyp.contradictory_evidence.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {hyp.contradictory_evidence.map((rid) => (
                      <button
                        key={rid}
                        onClick={() => onSelectRecord && onSelectRecord(rid)}
                        className="px-2 py-0.5 rounded text-xs font-mono bg-rose-900/40 text-rose-300 border border-rose-800 hover:bg-rose-800 hover:text-white transition-colors"
                      >
                        [{rid}]
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No contradictory records detected.</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Evidence Gaps Card */}
      {evidenceGaps && evidenceGaps.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-900/50">
          <div className="flex items-center space-x-2 text-amber-300 text-sm font-semibold mb-2">
            <AlertOctagon className="w-4 h-4 text-amber-400" />
            <span>Identified Evidence Gaps & Unknowns</span>
          </div>
          <ul className="list-disc list-inside space-y-1.5 text-xs text-amber-200/80">
            {evidenceGaps.map((gap, i) => (
              <li key={i}>{gap}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
