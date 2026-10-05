import React, { useState } from 'react';
import { UserCheck, CheckCircle2, RotateCcw, X, AlertCircle } from 'lucide-react';

interface HumanReviewModalProps {
  isOpen: boolean;
  caseId: string;
  caseTitle: string;
  onClose: () => void;
  onSubmit: (data: { decision: 'approved' | 'changes_requested'; reviewer_name: string; feedback: string }) => Promise<void>;
}

export const HumanReviewModal: React.FC<HumanReviewModalProps> = ({
  isOpen,
  caseId,
  caseTitle,
  onClose,
  onSubmit
}) => {
  const [decision, setDecision] = useState<'approved' | 'changes_requested'>('changes_requested');
  const [reviewerName, setReviewerName] = useState('Lead Investigator');
  const [feedback, setFeedback] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedback.trim()) {
      setError('Please provide comments or rationale for your review decision.');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await onSubmit({
        decision,
        reviewer_name: reviewerName.trim() || 'Lead Investigator',
        feedback: feedback.trim()
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to submit review');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in" role="dialog" aria-modal="true" aria-labelledby="review-modal-heading">
      <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 text-indigo-400 flex items-center justify-center border border-indigo-500/30">
              <UserCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 id="review-modal-heading" className="text-sm font-semibold text-white">Review findings</h3>
              <p className="text-xs text-slate-400">Investigation {caseId}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close review"
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800 text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Case Title</label>
            <p className="text-sm text-slate-100 font-medium">{caseTitle}</p>
          </div>

          {/* Decision Selection */}
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-2">Your review</label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setDecision('approved')}
                className={`p-3 rounded-xl border flex flex-col items-center text-center transition-all ${
                  decision === 'approved'
                    ? 'bg-emerald-950/50 border-emerald-500 text-emerald-300 ring-2 ring-emerald-500/20'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <CheckCircle2 className="w-5 h-5 mb-1.5 text-emerald-400" />
                <span className="text-xs font-bold">Approve findings</span>
                <span className="text-[10px] text-slate-400 mt-0.5">Mark this review complete</span>
              </button>

              <button
                type="button"
                onClick={() => setDecision('changes_requested')}
                className={`p-3 rounded-xl border flex flex-col items-center text-center transition-all ${
                  decision === 'changes_requested'
                    ? 'bg-amber-950/50 border-amber-500 text-amber-300 ring-2 ring-amber-500/20'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <RotateCcw className="w-5 h-5 mb-1.5 text-amber-400" />
                <span className="text-xs font-bold">Request more investigation</span>
                <span className="text-[10px] text-slate-400 mt-0.5">Add comments and continue reviewing evidence</span>
              </button>
            </div>
          </div>

          {/* Reviewer Name */}
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Reviewer name</label>
            <input
              type="text"
              value={reviewerName}
              onChange={(e) => setReviewerName(e.target.value)}
              placeholder="Your name"
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-indigo-500 font-sans"
              required
            />
          </div>

          {/* Feedback */}
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Reviewer comments
            </label>
            <textarea
              rows={4}
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder={
                decision === 'approved'
                  ? 'Explain which findings and source records you reviewed.'
                  : 'Describe what is missing, what does not agree, or which records should be examined next.'
              }
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-indigo-500 font-sans leading-relaxed"
              required
            />
          </div>

          {/* Action Buttons */}
          <div className="pt-3 border-t border-slate-800 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`px-5 py-2 rounded-lg text-xs font-semibold text-white shadow-md transition-all ${
                decision === 'approved'
                  ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/25'
                  : 'bg-amber-600 hover:bg-amber-500 shadow-amber-600/25'
              }`}
            >
              {isSubmitting ? 'Submitting…' : decision === 'approved' ? 'Approve findings' : 'Request more investigation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
