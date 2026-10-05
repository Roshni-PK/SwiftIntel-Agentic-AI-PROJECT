import React, { useState, useEffect, useRef } from 'react';
import {
  CaseDetail,
  InvestigationState,
  WorkflowEvent,
  ReportResponse,
  Evidence
} from '../types';
import { api } from '../services/api';
import { WorkflowGraph } from '../components/WorkflowGraph';
import { EventLogStream } from '../components/EventLogStream';
import { TimelineView } from '../components/TimelineView';
import { HypothesesPanel } from '../components/HypothesesPanel';
import { EvidenceCard } from '../components/EvidenceCard';
import { HumanReviewModal } from '../components/HumanReviewModal';
import {
  Play,
  RotateCcw,
  UserCheck,
  FileText,
  Clock,
  HelpCircle,
  Database,
  Terminal,
  AlertTriangle,
  ArrowLeft,
  Share2,
  Sparkles,
  CheckCircle2
} from 'lucide-react';

interface InvestigationWorkspaceProps {
  caseId: string;
  onBack: () => void;
}

export const InvestigationWorkspace: React.FC<InvestigationWorkspaceProps> = ({
  caseId,
  onBack
}) => {
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [state, setState] = useState<InvestigationState | null>(null);
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [activeTab, setActiveTab] = useState<'timeline' | 'hypotheses' | 'evidence' | 'logs' | 'report'>('timeline');
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [customEvidence, setCustomEvidence] = useState<Evidence[]>([]);
  const [showEvidenceForm, setShowEvidenceForm] = useState(false);
  const [uploadName, setUploadName] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const pollingRef = useRef<number | null>(null);

  const loadCaseAndState = async () => {
    try {
      const [caseData, stateData, eventsData] = await Promise.all([
        api.getCase(caseId),
        api.getInvestigationState(caseId),
        api.getWorkflowEvents(caseId)
      ]);
      setCaseDetail(caseData);
      setState(stateData);
      setEvents(eventsData);
      setCustomEvidence(await api.getCaseEvidence(caseId));

      // Check if report exists
      if (caseData.has_report) {
        try {
          const reportData = await api.getReport(caseId);
          setReport(reportData);
        } catch {
          // ignore if not ready
        }
      }

      if (caseData.status === 'investigating') {
        setIsInvestigating(true);
      } else {
        setIsInvestigating(false);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load case workspace');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCaseAndState();
  }, [caseId]);

  // Polling loop when investigation is running
  useEffect(() => {
    if (isInvestigating) {
      pollingRef.current = window.setInterval(async () => {
        try {
          const [eventsData, stateData, caseData] = await Promise.all([
            api.getWorkflowEvents(caseId),
            api.getInvestigationState(caseId),
            api.getCase(caseId)
          ]);
          setEvents(eventsData);
          setState(stateData);
          setCaseDetail(caseData);

          if (caseData.status !== 'investigating') {
            setIsInvestigating(false);
            if (caseData.has_report) {
              const rep = await api.getReport(caseId);
              setReport(rep);
            }
          }
        } catch (e) {
          setError(e instanceof Error ? `Live update failed: ${e.message}` : 'Live update failed. Refresh the workspace to try again.');
        }
      }, 1500);
    } else if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [isInvestigating, caseId]);

  const handleStartInvestigation = async () => {
    try {
      setError(null);
      setIsInvestigating(true);
      await api.startInvestigation(caseId, false);
      await loadCaseAndState();
    } catch (err: any) {
      setIsInvestigating(false);
      setError(err.message || 'Failed to start investigation');
    }
  };

  const handleHumanReviewSubmit = async (reviewData: {
    decision: 'approved' | 'changes_requested';
    reviewer_name: string;
    feedback: string;
  }) => {
    await api.submitReview(caseId, reviewData);
    if (reviewData.decision === 'changes_requested') {
      // Resume investigation with feedback
      await api.resumeInvestigation(caseId, reviewData.feedback);
      setIsInvestigating(true);
    }
    await loadCaseAndState();
  };

  const handleSelectRecordId = async (recordId: string) => {
    try {
      const rec = await api.getEvidenceDetail(recordId);
      setSelectedEvidence(rec);
      setActiveTab('evidence');
    } catch {
      setActiveTab('evidence');
    }
  };

  if (!caseDetail) {
    return (
      <div className="page-container">
        {isLoading ? <div className="panel loading-state">Loading investigation…</div> : <div className="notice notice-error"><AlertTriangle size={18} /><p>{error || 'This investigation could not be loaded.'}</p></div>}
      </div>
    );
  }

  const currentNode = state?.current_node || (isInvestigating ? 'planner' : 'not_started');

  return (
    <div className="investigation-workspace max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-in fade-in">
      {/* Top Navigation & Status Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="flex items-center space-x-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-950 px-2.5 py-0.5 rounded border border-indigo-800">
                {caseDetail.id}
              </span>
              <span className="text-xs font-medium text-slate-400">{caseDetail.category}</span>
              <span className={`priority-pill priority-${(caseDetail.priority || 'Medium').toLowerCase()}`}>{caseDetail.priority || 'Medium'} priority</span>
              <span className={`status-pill status-pill-${caseDetail.status}`}>
                {caseDetail.status === 'pending' ? 'Draft' : caseDetail.status === 'investigating' ? 'In progress' : caseDetail.status === 'awaiting_review' ? 'Needs review' : caseDetail.status === 'completed' ? 'Completed' : 'Reopened'}
              </span>
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight mt-1">{caseDetail.title}</h1>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center workspace-actions space-x-3 shrink-0">
          {caseDetail.has_report && (
            <button
              onClick={() => setActiveTab('report')}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-all flex items-center space-x-1.5"
            >
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              <span>View Report</span>
            </button>
          )}

          <button
            onClick={() => setIsReviewModalOpen(true)}
            disabled={!caseDetail.has_report || isInvestigating || caseDetail.status === 'completed'}
            title={!caseDetail.has_report ? 'Run the investigation to prepare a report for review' : undefined}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-all flex items-center space-x-1.5 disabled:opacity-50"
          >
            <UserCheck className="w-3.5 h-3.5 text-pink-400" />
            <span>{caseDetail.status === 'completed' ? 'Reviewed' : 'Review findings'}</span>
          </button>

          <button
            onClick={handleStartInvestigation}
            disabled={isInvestigating}
            className={`px-4 py-2 rounded-xl text-xs font-semibold text-white shadow-lg transition-all flex items-center space-x-2 active:scale-95 ${
              isInvestigating
                ? 'bg-indigo-600/50 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-600/30'
            }`}
          >
            {isInvestigating ? (
              <>
                <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                <span>Investigating...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{state?.current_node === 'reporter' ? 'Run investigation again' : 'Start investigation'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-300 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Incident Context Card */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-sm">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
          What was reported
        </h3>
        <p className="text-xs text-slate-300 font-sans leading-relaxed">
          {caseDetail.description}
        </p>
        {caseDetail.objective && <div className="workspace-intake-detail"><strong>Investigation goal</strong><p>{caseDetail.objective}</p></div>}
        {caseDetail.additional_context && <div className="workspace-intake-detail"><strong>Additional context</strong><p>{caseDetail.additional_context}</p></div>}

        {caseDetail.last_review && (
          <div className="mt-3 p-3 rounded-xl bg-indigo-950/30 border border-indigo-900/40 text-xs">
            <span className="font-semibold text-indigo-300 block mb-0.5">
              Latest human review: {caseDetail.last_review.decision === 'approved' ? 'Approved' : 'Changes requested'} by {caseDetail.last_review.reviewer_name}
            </span>
            <p className="text-slate-300 italic">"{caseDetail.last_review.feedback}"</p>
          </div>
        )}
      </div>

      {/* Graphical Workflow Nodes */}
      <section className="panel investigation-evidence">
        <div className="investigation-evidence-heading">
          <div><h2>Investigation Evidence</h2><p>Use available evidence below, or add your own evidence file for this investigation.</p></div>
          <button className="button-primary" onClick={() => setShowEvidenceForm(true)}><span>＋ Add Evidence</span></button>
        </div>
        <h3>Available Evidence</h3>
        <p className="evidence-source-note">Preloaded evidence in the shared repository is searched during the investigation.</p>
        <div className="evidence-source-list">System access logs · Email records · Transaction records · Employee records · Internal messages · Policy documents</div>
        <h3>Custom Evidence <span className="user-added-badge">User Added</span></h3>
        {customEvidence.length ? <div className="custom-evidence-list">{customEvidence.map((ev) => <article key={ev.record_id}>
          <div><strong>{ev.title}</strong><span>{ev.file_name} · Added {ev.added_at ? new Date(ev.added_at).toLocaleString() : 'recently'}</span>{ev.metadata?.description && <p>{ev.metadata.description}</p>}</div>
          <button className="button-secondary remove-evidence" onClick={async () => { try { await api.deleteCaseEvidence(caseId, ev.record_id); setCustomEvidence(await api.getCaseEvidence(caseId)); } catch (e) { setError(e instanceof Error ? e.message : 'Could not remove evidence.'); } }}>Remove</button>
        </article>)}</div> : <p className="evidence-source-note">No custom evidence added yet.</p>}
      </section>
      {showEvidenceForm && <div className="modal-backdrop" role="presentation"><form className="panel evidence-modal upload-form" onSubmit={async (event) => {
        event.preventDefault(); if (!uploadFile) return;
        setUploading(true); setError(null);
        try { await api.addCaseEvidence(caseId, uploadName, uploadDescription, uploadFile); setCustomEvidence(await api.getCaseEvidence(caseId)); setShowEvidenceForm(false); setUploadName(''); setUploadDescription(''); setUploadFile(null); }
        catch (e) { setError(e instanceof Error ? e.message : 'Could not add this evidence.'); }
        finally { setUploading(false); }
      }}>
        <header><div><p className="eyebrow">INVESTIGATION EVIDENCE</p><h2>Add Evidence</h2></div><button type="button" className="icon-button" onClick={() => setShowEvidenceForm(false)} aria-label="Close">×</button></header>
        <div className="evidence-modal-content upload-fields">
          <p>Add searchable evidence for <strong>{caseDetail.title}</strong>. Supported formats: TXT, CSV, JSON, LOG, and MD. Maximum file size: 5 MB. PDF is not supported.</p>
          <label>Evidence / log name<input required maxLength={255} value={uploadName} onChange={e => setUploadName(e.target.value)} placeholder="Server Access Log - September 28" /></label>
          <label>Description (optional)<textarea rows={3} value={uploadDescription} onChange={e => setUploadDescription(e.target.value)} placeholder="Where this evidence came from" /></label>
          <label>Evidence file<input required type="file" accept=".txt,.csv,.json,.log,.md,text/plain,text/csv,application/json" onChange={e => setUploadFile(e.target.files?.[0] || null)} /></label>
          {uploadFile && <div className="selected-upload"><span><strong>{uploadFile.name}</strong><small>{uploadFile.name.split('.').pop()?.toUpperCase()} · {(uploadFile.size / 1024).toFixed(1)} KB</small></span><button type="button" className="button-secondary" onClick={() => setUploadFile(null)}>Remove</button></div>}
        </div>
        <footer><button type="button" className="button-secondary" onClick={() => setShowEvidenceForm(false)}>Cancel</button><button className="button-primary" disabled={uploading || !uploadFile}>{uploading ? 'Adding…' : 'Add Evidence'}</button></footer>
      </form></div>}

      {/* Graphical Workflow Nodes */}
      <WorkflowGraph
        currentNode={currentNode}
        criticDecision={state?.critic_decision}
        retryCount={state?.retry_count || 0}
        maxRetries={state?.max_retries || 2}
        humanReviewStatus={state?.human_review_status || 'pending'}
        pipelineComplete={caseDetail.has_report && !isInvestigating}
      />

      {/* Investigation Workbench: Left Tabs + Right Event Log Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Tabbed Content (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          {/* Tabs Header */}
          <div className="flex items-center workspace-tabs space-x-1 border-b border-slate-800 bg-slate-950 p-1.5 rounded-xl border">
            {[
              { id: 'timeline', label: 'Timeline', icon: Clock, count: state?.event_timeline?.length || 0 },
              { id: 'hypotheses', label: 'Possible explanations', icon: HelpCircle, count: state?.hypotheses?.length || 0 },
              { id: 'evidence', label: 'Evidence', icon: Database, count: state?.retrieved_evidence?.length || 0 },
              { id: 'report', label: 'Report', icon: FileText, badge: caseDetail.has_report ? 'Ready' : null }
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-slate-800 text-indigo-400 border border-slate-700 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                  {tab.count !== undefined && tab.count > 0 && (
                    <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-900 text-slate-300 font-mono">
                      {tab.count}
                    </span>
                  )}
                  {tab.badge && (
                    <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-950 text-emerald-300 font-mono border border-emerald-800">
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Tab Content Display */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 min-h-[460px]">
            {activeTab === 'timeline' && (
              <TimelineView
                events={state?.event_timeline || []}
                onSelectRecord={handleSelectRecordId}
              />
            )}

            {activeTab === 'hypotheses' && (
              <HypothesesPanel
                hypotheses={state?.hypotheses || []}
                evidenceGaps={state?.evidence_gaps || []}
                onSelectRecord={handleSelectRecordId}
              />
            )}

            {activeTab === 'evidence' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800">
                  <span>Records found ({state?.retrieved_evidence?.length || 0})</span>
                  <span>Open a record to see its source details</span>
                </div>

                {state?.retrieved_evidence && state.retrieved_evidence.length > 0 ? (
                  <div className="grid grid-cols-1 gap-3">
                    {state.retrieved_evidence.map((ev) => (
                      <EvidenceCard
                        key={ev.record_id}
                        evidence={ev}
                        highlightId={selectedEvidence?.record_id}
                        onOpenDetail={(rec) => setSelectedEvidence(rec)}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-16 text-slate-500 text-xs">
                    <Database className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                    <p>No evidence retrieved yet.</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'report' && (
              <div className="space-y-4">
                {report ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3 report-header">
                      <div>
                        <h3 className="text-base font-bold text-white">{report.title}</h3>
                        <p className="text-xs text-slate-400">Prepared {new Date(report.created_at).toLocaleString()}</p>
                      </div>
                      <div className="flex flex-wrap gap-2 report-downloads">
                        <a className="button-secondary" href={api.getReportDownloadUrl(caseId, 'markdown')} download><FileText size={14} />Download Markdown</a>
                        <a className="button-secondary" href={api.getReportDownloadUrl(caseId, 'text')} download><FileText size={14} />Download text</a>
                      </div>
                    </div>
                    <div className="report-meta-grid"><div><span>Priority</span><strong>{report.report_json.priority || caseDetail.priority}</strong></div><div><span>Status</span><strong>{report.report_json.status || 'Awaiting human review'}</strong></div><div><span>Evidence strength</span><strong>{report.report_json.evidence_strength || 'Inconclusive'}</strong></div></div>
                    <p className="text-sm text-slate-700 leading-relaxed">{report.report_json.incident_summary || report.summary}</p>
                    <div className="notice notice-info"><AlertTriangle size={17} /><p>AI-generated investigative findings require human review. The report does not independently establish wrongdoing.</p></div>
                    <section className="report-section"><h4>What happened</h4><p>{report.report_json.what_happened || caseDetail.description}</p>{report.report_json.investigation_goal && <p><strong>Investigation goal:</strong> {report.report_json.investigation_goal}</p>}</section>
                    {report.report_json.key_evidence?.length ? <section className="report-section"><h4>Key evidence</h4><ul>{report.report_json.key_evidence.map((record) => <li key={record.record_id}><strong>{record.title}</strong><p>{record.content}</p><details className="evidence-technical"><summary>Technical details</summary><span>Source record: {record.record_id}{record.timestamp ? ` · ${new Date(record.timestamp).toLocaleString()}` : ''}</span></details></li>)}</ul></section> : null}
                    {report.report_json.key_findings?.length > 0 && <section className="report-section"><h4>Key findings</h4><ul>{report.report_json.key_findings.map((finding, index) => <li key={index}>{finding}</li>)}</ul></section>}
                    {(report.report_json.supporting_evidence?.length > 0 || report.report_json.contradictory_evidence?.length > 0) && <section className="report-section"><h4>Evidence referenced</h4>{report.report_json.supporting_evidence?.length > 0 && <p><strong>Supporting records:</strong> {report.report_json.supporting_evidence.join(', ')}</p>}{report.report_json.contradictory_evidence?.length > 0 && <p><strong>Contradicting records:</strong> {report.report_json.contradictory_evidence.join(', ')}</p>}</section>}
                    {report.report_json.competing_hypotheses?.length > 0 && <section className="report-section"><h4>Alternative explanations</h4>{report.report_json.competing_hypotheses.map((hypothesis) => <article key={hypothesis.id}><strong>{hypothesis.title}</strong><span className={`status-pill status-pill-${hypothesis.status}`}>{hypothesis.status}</span><p>{hypothesis.description}</p></article>)}</section>}
                    {report.report_json.uncertainty_declaration && <section className="report-section report-caveat"><h4>Uncertainty and limitations</h4><p>{report.report_json.uncertainty_declaration}</p></section>}
                    {report.report_json.unresolved_questions?.length > 0 && <section className="report-section"><h4>Open questions</h4><ul>{report.report_json.unresolved_questions.map((question, index) => <li key={index}>{question}</li>)}</ul></section>}
                    {report.report_json.recommendations?.length > 0 && <section className="report-section"><h4>Suggested next steps</h4><ul>{report.report_json.recommendations.map((item, index) => <li key={index}>{item}</li>)}</ul></section>}
                    <details className="report-technical"><summary>View complete report text</summary><pre>{report.markdown_content}</pre></details>
                  </div>
                ) : (
                  <div className="text-center py-16 text-slate-500 text-xs">
                    <FileText className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                    <p>No report is available yet. Start the investigation to search records and prepare findings for human review.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Live Event Audit Log Stream (1 col) */}
        <div className="lg:col-span-1">
          <EventLogStream events={events} isInvestigating={isInvestigating} />
        </div>
      </div>

      {/* Human Review Modal */}
      <HumanReviewModal
        isOpen={isReviewModalOpen}
        caseId={caseId}
        caseTitle={caseDetail.title}
        onClose={() => setIsReviewModalOpen(false)}
        onSubmit={handleHumanReviewSubmit}
      />
    </div>
  );
};
