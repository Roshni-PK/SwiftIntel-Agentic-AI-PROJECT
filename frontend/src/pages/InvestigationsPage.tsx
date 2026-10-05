import React, { useState, useEffect } from 'react';
import { CaseDetail, SyntheticTemplate } from '../types';
import { api } from '../services/api';
import {
  Plus,
  Play,
  RotateCcw,
  Trash2,
  FolderOpen,
  Filter,
  CheckCircle2,
  Clock,
  Sparkles,
  AlertCircle
} from 'lucide-react';

const statusLabels: Record<CaseDetail['status'], string> = {
  pending: 'Draft', investigating: 'In progress', awaiting_review: 'Needs review', completed: 'Completed', reopened: 'Reopened'
};

interface InvestigationsPageProps {
  onOpenCase: (caseId: string) => void;
  selectedTemplate?: SyntheticTemplate | null;
  onClearTemplate?: () => void;
}

export const InvestigationsPage: React.FC<InvestigationsPageProps> = ({
  onOpenCase,
  selectedTemplate,
  onClearTemplate
}) => {
  const [cases, setCases] = useState<CaseDetail[]>([]);
  const [templates, setTemplates] = useState<SyntheticTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New Case Form State
  const [formId, setFormId] = useState('');
  const [formTitle, setFormTitle] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formCategory, setFormCategory] = useState('Security');
  const [formObjective, setFormObjective] = useState('');
  const [formPriority, setFormPriority] = useState<'Low' | 'Medium' | 'High'>('Medium');
  const [formContext, setFormContext] = useState('');

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [casesData, templatesData] = await Promise.all([
        api.getCases(),
        api.getSyntheticTemplates()
      ]);
      setCases(casesData);
      setTemplates(templatesData);
    } catch (err: any) {
      setError(err.message || 'Failed to load cases');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // When a template is pre-selected
  useEffect(() => {
    if (selectedTemplate) {
      setFormId('');
      setFormTitle(selectedTemplate.title);
      setFormDescription(selectedTemplate.incident_description);
      setFormCategory(templateArea(selectedTemplate.category));
      setIsCreating(true);
      if (onClearTemplate) onClearTemplate();
    }
  }, [selectedTemplate]);

  const handleSelectTemplate = (tpl: SyntheticTemplate) => {
    setFormId('');
    setFormTitle(tpl.title);
    setFormDescription(tpl.incident_description);
    setFormCategory(templateArea(tpl.category));
    setIsCreating(true);
  };

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTitle.trim()) { setError('Please enter an investigation name.'); return; }
    if (!formDescription.trim()) { setError('Please describe what happened.'); return; }
    if (!formObjective.trim()) { setError('Please describe what you are trying to find out.'); return; }

    try {
      setError(null);
      const created = await api.createCase({
        id: formId.trim() || undefined,
        title: formTitle.trim(),
        description: formDescription.trim(),
        category: formCategory,
        objective: formObjective.trim(),
        priority: formPriority,
        additional_context: formContext.trim() || undefined
      });
      await api.startInvestigation(created.id, false);
      setIsCreating(false);
      setFormId('');
      setFormTitle('');
      setFormDescription('');
      setFormObjective(''); setFormContext(''); setFormPriority('Medium');
      await loadData();
      onOpenCase(created.id);
    } catch (err: any) {
      setError(err.message || 'Failed to create case');
    }
  };

  const templateArea = (category: string): string => {
    const value = category.toLowerCase();
    if (value.includes('financial') || value.includes('fraud')) return 'Finance';
    if (value.includes('infrastructure') || value.includes('outage')) return 'Infrastructure';
    if (value.includes('intellectual') || value.includes('theft')) return 'Data / IP';
    return 'Security';
  };

  const handleReopen = async (caseId: string) => {
    try {
      await api.reopenCase(caseId);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to reopen case');
    }
  };

  const handleDelete = async (caseId: string) => {
    if (!window.confirm(`Are you sure you want to delete case ${caseId}?`)) return;
    try {
      await api.deleteCase(caseId);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to delete case');
    }
  };

  const filteredCases = cases.filter((c) => {
    if (filterStatus === 'all') return true;
    return c.status === filterStatus;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-in fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <p className="eyebrow">CASE MANAGEMENT</p>
          <h1 className="text-2xl font-bold text-white tracking-tight">Investigations</h1>
          <p className="text-xs text-slate-400 mt-1">
            Organize incident reviews and follow each case through human review.
          </p>
        </div>

        <button
          onClick={() => setIsCreating(!isCreating)}
          className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-md transition-all flex items-center space-x-2 self-start active:scale-95"
        >
          <Plus className="w-4 h-4" />
          <span>{isCreating ? 'Close form' : 'New investigation'}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Investigation intake */}
      {isCreating && <section className="panel intake-panel">
        <header className="intake-heading"><div><p className="eyebrow">NEW INVESTIGATION</p><h2>Investigation intake</h2><p>Share what happened and what you need to learn. You can review evidence after starting.</p></div><div className="template-picker"><label htmlFor="example-case">Use a fictional example</label><select id="example-case" value="" onChange={e => { const tpl = templates.find(item => item.id === e.target.value); if (tpl) handleSelectTemplate(tpl); }}><option value="">Choose an example…</option>{templates.map(t => <option key={t.id} value={t.id}>{t.title}</option>)}</select></div></header>
        <form onSubmit={handleCreateCase} className="intake-form">
          <section><h3>Investigation details</h3><label>Investigation name<input value={formTitle} onChange={e => setFormTitle(e.target.value)} maxLength={255} placeholder="Suspicious Employee Access" /></label><small>Choose a short name that helps your team identify this case.</small></section>
          <section><h3>Incident description</h3><label>What happened?<textarea rows={4} value={formDescription} onChange={e => setFormDescription(e.target.value)} placeholder="Describe what was noticed, when it happened, and any systems or people involved." /></label></section>
          <section><h3>Investigation goal</h3><label>What are you trying to find out?<textarea rows={3} value={formObjective} onChange={e => setFormObjective(e.target.value)} placeholder="For example: determine whether the account access was authorized." /></label></section>
          <section className="intake-classification"><div><h3>Classification</h3><label>Investigation area<select value={formCategory} onChange={e => setFormCategory(e.target.value)}><option>Security</option><option>Finance</option><option>Employee Activity</option><option>Data / IP</option><option>Infrastructure</option><option>Other</option></select></label></div><div><h3>Priority</h3><label>Priority<select value={formPriority} onChange={e => setFormPriority(e.target.value as 'Low' | 'Medium' | 'High')}><option>Low</option><option>Medium</option><option>High</option></select></label><small>Default priority is Medium.</small></div></section>
          <section><h3>Additional context <span>(optional)</span></h3><label>Anything else the investigator should know?<textarea rows={3} value={formContext} onChange={e => setFormContext(e.target.value)} placeholder="Relevant dates, known constraints, or other useful context." /></label></section>
          <details className="intake-advanced"><summary>Optional case ID</summary><label>Case ID<input value={formId} onChange={e => setFormId(e.target.value)} placeholder="Leave blank to assign automatically" /></label></details>
          <div className="intake-actions"><button type="button" className="button-secondary" onClick={() => setIsCreating(false)}>Cancel</button><button type="submit" className="button-primary"><Play size={15} />Start Investigation</button></div>
        </form>
      </section>}
      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-3 text-xs">
        <Filter className="w-3.5 h-3.5 text-slate-400" />
        <span className="text-slate-400 mr-2">Show:</span>
        {['all', 'pending', 'investigating', 'awaiting_review', 'completed', 'reopened'].map((st) => (
          <button
            key={st}
            onClick={() => setFilterStatus(st)}
            className={`px-3 py-1 rounded-lg capitalize font-medium transition-all ${
              filterStatus === st
                ? 'bg-slate-800 text-indigo-400 border border-slate-700'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {st === 'all' ? 'All cases' : statusLabels[st as CaseDetail['status']]}
          </button>
        ))}
      </div>

      {/* Cases List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {isLoading ? (
          <div className="col-span-full py-16 text-center text-slate-500 text-xs font-mono">
            Loading investigation cases...
          </div>
        ) : filteredCases.length === 0 ? (
          <div className="col-span-full py-16 text-center text-slate-500 bg-slate-900/40 rounded-2xl border border-slate-800">
            <FolderOpen className="w-10 h-10 mx-auto mb-2 text-slate-600" />
            <p className="text-sm text-slate-400">No cases match the selected filter.</p>
          </div>
        ) : (
          filteredCases.map((c) => (
            <div
              key={c.id}
              className="p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between group shadow-lg"
            >
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <span className="text-xs font-mono font-bold text-indigo-300 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                    {c.id}
                  </span>
                  <span className={`status-pill status-pill-${c.status}`}>
                    {statusLabels[c.status]}
                  </span>
                </div>

                <span className={`priority-pill priority-${(c.priority || 'Medium').toLowerCase()}`}>{c.priority || 'Medium'} priority</span>

                <h3 className="text-base font-semibold text-white group-hover:text-indigo-300 transition-colors line-clamp-1">
                  {c.title}
                </h3>

                <p className="text-xs text-slate-400 mt-2 line-clamp-3 leading-relaxed">
                  {c.description}
                </p>

                {/* Metadata Pills */}
                <div className="mt-4 flex items-center space-x-3 text-[11px] font-mono text-slate-400">
                  <span>{c.retrieved_evidence_count} records reviewed</span>
                </div>
              </div>

              {/* Card Actions */}
              <div className="mt-5 pt-3.5 border-t border-slate-800/80 flex items-center justify-between">
                <button
                  onClick={() => handleDelete(c.id)}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                  title="Delete case"
                >
                  <Trash2 className="w-4 h-4" />
                </button>

                <div className="flex items-center space-x-2">
                  {c.status === 'completed' && (
                    <button
                      onClick={() => handleReopen(c.id)}
                      className="px-2.5 py-1.5 rounded-lg text-xs text-amber-400 hover:bg-slate-800 border border-slate-800 transition-colors flex items-center space-x-1"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Reopen</span>
                    </button>
                  )}

                  <button
                    onClick={() => onOpenCase(c.id)}
                    className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all active:scale-95 flex items-center space-x-1.5"
                  >
                    <span>Open case</span>
                    <Play className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
