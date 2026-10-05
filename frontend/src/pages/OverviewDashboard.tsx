import React, { useEffect, useState } from 'react';
import { CaseDetail, SyntheticTemplate } from '../types';
import { api } from '../services/api';
import { ArrowRight, AlertCircle, Plus, FolderSearch, ClipboardCheck, FileText, RefreshCw } from 'lucide-react';

interface OverviewDashboardProps {
  onOpenCase: (caseId: string) => void;
  onNewInvestigation: () => void;
  onSelectTemplate: (template: SyntheticTemplate) => void;
  onNavigateTab: (tab: string) => void;
}

const statusLabel: Record<CaseDetail['status'], string> = {
  pending: 'Draft', investigating: 'In progress', awaiting_review: 'Needs review', completed: 'Completed', reopened: 'Reopened'
};

export const OverviewDashboard: React.FC<OverviewDashboardProps> = ({ onOpenCase, onNewInvestigation, onNavigateTab }) => {
  const [cases, setCases] = useState<CaseDetail[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getCases().then(setCases).catch((err: Error) => setError(err.message || 'Investigations could not be loaded.')).finally(() => setIsLoading(false));
  }, []);

  const needsReview = cases.filter((item) => item.status === 'awaiting_review');
  const inProgress = cases.filter((item) => item.status === 'investigating');
  const recent = cases.slice(0, 5);

  return <div className="overview-page">
    <section className="overview-hero">
      <div><p className="eyebrow">INVESTIGATION WORKSPACE</p><h1>Good work starts with clear evidence.</h1><p>Review reported incidents, trace the supporting records, and keep a human investigator involved in every final assessment.</p></div>
      <button className="button-primary" onClick={onNewInvestigation}><Plus size={17} />Start an investigation</button>
    </section>

    <div className="notice notice-info"><AlertCircle size={18} /><p>SwiftIntel supports investigations. Reports need human review and do not independently establish wrongdoing. Records in this project are synthetic and fictional.</p></div>

    {error && <div className="notice notice-error"><AlertCircle size={18} /><p>{error}</p></div>}

    <section className="overview-status-row" aria-label="Investigation summary">
      <button className="status-summary panel" onClick={() => onNavigateTab('investigations')}><span className="summary-icon in-progress"><FolderSearch size={18} /></span><span><small>In progress</small><strong>{isLoading ? '—' : inProgress.length}</strong></span><ArrowRight size={16} className="summary-arrow" /></button>
      <button className="status-summary panel" onClick={() => onNavigateTab('investigations')}><span className="summary-icon needs-review"><ClipboardCheck size={18} /></span><span><small>Needs review</small><strong>{isLoading ? '—' : needsReview.length}</strong></span><ArrowRight size={16} className="summary-arrow" /></button>
      <button className="status-summary panel" onClick={() => onNavigateTab('investigations')}><span className="summary-icon all-cases"><FileText size={18} /></span><span><small>All investigations</small><strong>{isLoading ? '—' : cases.length}</strong></span><ArrowRight size={16} className="summary-arrow" /></button>
    </section>

    <section className="overview-list panel">
      <div className="section-heading"><div><h2>Recent investigations</h2><p>Open a case to review its timeline, evidence, and current status.</p></div><button className="text-action" onClick={() => onNavigateTab('investigations')}>View all <ArrowRight size={15} /></button></div>
      {isLoading ? <div className="overview-empty"><RefreshCw size={18} className="spin" />Loading investigations…</div> : recent.length === 0 ? <div className="overview-empty"><FolderSearch size={26} /><strong>No investigations yet</strong><span>Start one with a short description of the incident and what you know so far.</span><button className="button-secondary" onClick={onNewInvestigation}><Plus size={15} />Create first investigation</button></div> : <div className="case-list">{recent.map((item) => <button className="case-list-row" key={item.id} onClick={() => onOpenCase(item.id)}><span className={`case-status-dot status-${item.status}`} /><span className="case-list-main"><strong>{item.title}</strong><small>{item.id} <span>·</span> {item.category}</small></span><span className={`priority-pill priority-${(item.priority || 'Medium').toLowerCase()}`}>{item.priority || 'Medium'} priority</span><span className={`status-pill status-pill-${item.status}`}>{statusLabel[item.status]}</span><span className="case-updated">Updated {new Date(item.updated_at).toLocaleDateString()}</span><ArrowRight size={16} className="case-row-arrow" /></button>)}</div>}
    </section>
  </div>;
};
