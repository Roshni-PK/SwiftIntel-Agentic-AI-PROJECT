import React from 'react';
import {
  Compass,
  Database,
  Brain,
  Sparkles,
  FileCheck,
  UserCheck,
  ArrowRight,
  RotateCcw,
  CheckCircle2,
  Clock
} from 'lucide-react';

interface WorkflowGraphProps {
  currentNode: string;
  criticDecision?: string;
  retryCount?: number;
  maxRetries?: number;
  humanReviewStatus?: string;
  pipelineComplete?: boolean;
}

export const WorkflowGraph: React.FC<WorkflowGraphProps> = ({
  currentNode,
  criticDecision,
  retryCount = 0,
  maxRetries = 2,
  humanReviewStatus = 'pending',
  pipelineComplete = false
}) => {
  const nodes = [
    {
      id: 'planner',
      name: 'Plan searches',
      subtitle: 'Set questions to investigate',
      icon: Compass
    },
    {
      id: 'retriever',
      name: 'Find records',
      subtitle: 'Search available evidence',
      icon: Database
    },
    {
      id: 'analyst',
      name: 'Analyze records',
      subtitle: 'Build a timeline and consider explanations',
      icon: Brain
    },
    {
      id: 'critic',
      name: 'Check evidence',
      subtitle: 'Identify gaps and contradictions',
      icon: Sparkles
    },
    {
      id: 'reporter',
      name: 'Prepare report',
      subtitle: 'Summarize findings and limits',
      icon: FileCheck
    }
  ];

  const getNodeStatus = (nodeId: string) => {
    if (pipelineComplete || currentNode === 'completed') return 'completed';
    // Current active node
    if (currentNode === nodeId) return 'active';

    // Sequence index
    const nodeOrder = ['planner', 'retriever', 'analyst', 'critic', 'reporter'];
    const currentIndex = nodeOrder.indexOf(currentNode);
    const nodeIndex = nodeOrder.indexOf(nodeId);

    if (currentIndex > nodeIndex) return 'completed';
    return 'pending';
  };

  return (
    <div className="w-full p-5 rounded-xl bg-slate-900/90 border border-slate-800 shadow-xl overflow-x-auto">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse"></span>
          <h3 className="text-sm font-semibold tracking-wider text-slate-300">
            Investigation progress
          </h3>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          {retryCount > 0 && (
            <div className="flex items-center space-x-1 px-2.5 py-1 rounded bg-amber-950/60 text-amber-300 border border-amber-800">
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Additional search: {retryCount} of {maxRetries}</span>
            </div>
          )}

          {criticDecision && (
            <div className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
              <span className="text-slate-400">Evidence check:</span>
              <span className="font-semibold text-indigo-400">{criticDecision === 'RETRIEVE_MORE' ? 'Searching again' : criticDecision === 'NEEDS_HUMAN_REVIEW' ? 'Human review needed' : 'Complete'}</span>
            </div>
          )}
        </div>
      </div>
      <p className="workflow-loop-note">The evidence check can send the process back to search when it finds gaps. {humanReviewStatus === 'approved' ? 'An investigator has approved this report.' : humanReviewStatus === 'changes_requested' ? 'An investigator requested changes to this report.' : 'An investigator reviews the report after it is prepared.'}</p>

      {/* Nodes visual flow */}
      <div className="flex items-center min-w-[800px] justify-between py-2 workflow-nodes">
        {nodes.map((node, index) => {
          const Icon = node.icon;
          const status = getNodeStatus(node.id);

          let nodeStyle = 'bg-slate-950 border-slate-800 text-slate-500';
          let iconStyle = 'bg-slate-900 text-slate-500 border-slate-800';

          if (status === 'active') {
            nodeStyle = 'bg-indigo-950/50 border-indigo-500 text-indigo-200 ring-2 ring-indigo-500/20 shadow-lg shadow-indigo-500/10';
            iconStyle = 'bg-indigo-600 text-white border-indigo-400 animate-pulse';
          } else if (status === 'completed') {
            nodeStyle = 'bg-slate-900 border-emerald-500/40 text-slate-200';
            iconStyle = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
          }

          return (
            <React.Fragment key={node.id}>
              {/* Node Card */}
              <div className={`relative flex flex-col items-center text-center p-3 rounded-xl border transition-all w-36 workflow-node ${nodeStyle}`}>
                {/* Node Status Badge */}
                <div className="absolute -top-2.5 right-2">
                  {status === 'completed' && <CheckCircle2 className="w-4 h-4 text-emerald-400 bg-slate-950 rounded-full" />}
                  {status === 'active' && <Clock className="w-4 h-4 text-indigo-400 bg-slate-950 rounded-full animate-spin" />}
                </div>

                <div className={`w-10 h-10 rounded-lg flex items-center justify-center border mb-2 transition-all ${iconStyle}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <h4 className="text-xs font-semibold leading-tight line-clamp-1">{node.name}</h4>
                <p className="text-[10px] text-slate-400 mt-1 leading-snug line-clamp-2">{node.subtitle}</p>
              </div>

              {/* Edge Arrow / Conditional Loop indicator */}
              {index < nodes.length - 1 && (
                <div className="flex flex-col items-center px-1 workflow-edge">
                  {node.id === 'critic' && retryCount > 0 ? (
                    <div className="flex flex-col items-center text-[10px] text-amber-400 font-mono">
                      <RotateCcw className="w-4 h-4 mb-0.5 text-amber-400 animate-spin" />
                      <span>Search again</span>
                    </div>
                  ) : (
                    <ArrowRight className={`w-4 h-4 flow-arrow ${status === 'completed' ? 'text-indigo-400' : 'text-slate-700'}`} />
                  )}
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
