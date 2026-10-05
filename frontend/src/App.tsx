import { useEffect, useState } from 'react';
import { api } from './services/api';
import type { AppSettings, AuthUser, BenchmarkCaseResult, BenchmarkReport, SyntheticTemplate } from './types';
import { Navbar } from './components/Navbar';
import { OverviewDashboard } from './pages/OverviewDashboard';
import { InvestigationsPage } from './pages/InvestigationsPage';
import { InvestigationWorkspace } from './pages/InvestigationWorkspace';
import { EvidenceVaultPage } from './pages/EvidenceVaultPage';
import { AuthPage } from './pages/AuthPage';
import { AlertCircle, Play, RefreshCw, Save } from 'lucide-react';

const metricLabels: Array<{ key: keyof BenchmarkReport['aggregate_metrics']['basic_rag']; label: string; help: string }> = [
  { key: 'ground_truth_alignment', label: 'Finding alignment', help: 'How closely the investigation summary matches the expected scenario outcome.' },
  { key: 'citation_accuracy', label: 'Source accuracy', help: 'How often cited source records exist in the fictional evidence set.' },
  { key: 'policy_retrieval_rate', label: 'Relevant policy found', help: 'How often the expected policy record was found.' },
  { key: 'contradiction_detection_rate', label: 'Conflicting evidence found', help: 'How often the investigation recognized conflicting records.' }
];

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<SyntheticTemplate | null>(null);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [settingsError, setSettingsError] = useState('');
  const [provider, setProvider] = useState('demo');
  const [model, setModel] = useState('demo-engine');
  const [apiKey, setApiKey] = useState('');
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsSaved, setSettingsSaved] = useState(false);
  const [benchmark, setBenchmark] = useState<BenchmarkReport | null>(null);
  const [benchmarkError, setBenchmarkError] = useState('');
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);

  useEffect(() => {
    api.getCurrentUser().then(setAuthUser).catch(() => setAuthUser(null)).finally(() => setAuthChecking(false));
  }, []);

  useEffect(() => {
    if (!authUser) return;
    api.getSettings().then((value) => {
      setSettings(value);
      setProvider(value.llm_provider);
      setModel(value.model_name);
    }).catch((error: Error) => setSettingsError(error.message));
  }, [authUser]);

  useEffect(() => {
    if (!authUser || activeTab !== 'evaluation' || benchmark) return;
    setBenchmarkLoading(true);
    api.getBenchmark().then(setBenchmark).catch((error: Error) => setBenchmarkError(error.message)).finally(() => setBenchmarkLoading(false));
  }, [activeTab, benchmark, authUser]);

  const openCase = (caseId: string) => { setActiveCaseId(caseId); setActiveTab('workspace'); };
  const startNewInvestigation = () => { setSelectedTemplate(null); setActiveTab('investigations'); };
  const logout = async () => {
    try { await api.logout(); } finally { setAuthUser(null); setActiveTab('dashboard'); setActiveCaseId(null); setBenchmark(null); }
  };
  const runBenchmark = async () => {
    setBenchmarkLoading(true); setBenchmarkError('');
    try { setBenchmark(await api.runBenchmark()); }
    catch (error) { setBenchmarkError(error instanceof Error ? error.message : 'Evaluation could not be completed.'); }
    finally { setBenchmarkLoading(false); }
  };
  const saveSettings = async (event: React.FormEvent) => {
    event.preventDefault(); setSettingsSaving(true); setSettingsError(''); setSettingsSaved(false);
    try {
      const updated = await api.updateSettings({ llm_provider: provider, model_name: model, ...(apiKey ? { api_key: apiKey } : {}) });
      setSettings(updated); setApiKey(''); setSettingsSaved(true);
    } catch (error) { setSettingsError(error instanceof Error ? error.message : 'Settings could not be saved.'); }
    finally { setSettingsSaving(false); }
  };

  if (authChecking) return <main className="auth-screen"><div className="panel loading-state">Loading your account…</div></main>;
  if (!authUser) return <AuthPage onAuthenticated={setAuthUser} />;

  return <div className="app-shell">
    <Navbar activeTab={activeTab} setActiveTab={setActiveTab} onNewInvestigation={startNewInvestigation} isDemoMode={settings?.demo_mode_active ?? true} userName={authUser.full_name} onLogout={logout} />
    <main className="app-main">
      {activeTab === 'dashboard' && <OverviewDashboard onOpenCase={openCase} onNewInvestigation={startNewInvestigation} onSelectTemplate={(template) => { setSelectedTemplate(template); setActiveTab('investigations'); }} onNavigateTab={setActiveTab} />}
      {activeTab === 'investigations' && <InvestigationsPage onOpenCase={openCase} selectedTemplate={selectedTemplate} onClearTemplate={() => setSelectedTemplate(null)} />}
      {activeTab === 'workspace' && activeCaseId && <InvestigationWorkspace caseId={activeCaseId} onBack={() => setActiveTab('investigations')} />}
      {activeTab === 'evidence' && <EvidenceVaultPage currentCaseId={activeCaseId} />}
      {activeTab === 'evaluation' && <section className="page-container">
        <div className="page-heading-row"><div><p className="eyebrow">SYSTEM QUALITY</p><h1>Evaluation</h1><p className="page-description">Compare the existing search and investigation approaches on the project’s fictional test cases.</p></div><button className="button-primary" onClick={runBenchmark} disabled={benchmarkLoading}>{benchmarkLoading ? <RefreshCw className="spin" size={16} /> : <Play size={16} />}{benchmarkLoading ? 'Running evaluation…' : 'Run evaluation'}</button></div>
        <div className="notice notice-info"><AlertCircle size={18} /><p>These results come from a small synthetic benchmark. Some measures use scenario-specific rules and do not indicate real-world investigation accuracy.</p></div>
        {benchmarkError && <div className="notice notice-error"><AlertCircle size={18} /><p>{benchmarkError}</p></div>}
        {benchmarkLoading && !benchmark && <div className="panel loading-state"><RefreshCw className="spin" size={20} />Loading the latest evaluation…</div>}
        {benchmark && <>
          <div className="panel evaluation-meta"><div><strong>{benchmark.total_cases_evaluated}</strong><span>synthetic scenarios evaluated</span></div><span>Last run {new Date(benchmark.benchmark_timestamp).toLocaleString()}</span></div>
          <div className="evaluation-grid"><div className="evaluation-labels"><div className="metric-spacer" /><div className="evaluation-column"><span className="method-dot basic" />Standard search</div><div className="evaluation-column"><span className="method-dot agentic" />AI-assisted investigation</div></div>
            {metricLabels.map((metric) => <div className="evaluation-row" key={metric.key}><div className="metric-name"><strong>{metric.label}</strong><small>{metric.help}</small></div><div className="score-cell"><strong>{benchmark.aggregate_metrics.basic_rag[metric.key]}%</strong><div className="score-track"><span style={{ width: `${benchmark.aggregate_metrics.basic_rag[metric.key]}%` }} /></div></div><div className="score-cell"><strong>{benchmark.aggregate_metrics.agentic_rag[metric.key]}%</strong><div className="score-track agentic"><span style={{ width: `${benchmark.aggregate_metrics.agentic_rag[metric.key]}%` }} /></div></div></div>)}
          </div>
          <details className="panel case-results"><summary>View scenario results</summary><div className="case-results-list">{benchmark.case_details.map((item: BenchmarkCaseResult) => <article key={item.case_id}><div><strong>{item.title}</strong><small>{item.case_id} · {item.ground_truth_verdict === 'insufficient_evidence' ? 'Insufficient evidence scenario' : 'Synthetic scenario'}</small></div><details><summary>Compare summaries</summary><p><b>Standard search:</b> {item.basic_rag.summary}</p><p><b>AI-assisted investigation:</b> {item.agentic_rag.summary}</p></details></article>)}</div></details>
        </>}
      </section>}
      {activeTab === 'settings' && <section className="page-container settings-page">
        <div className="page-heading-row"><div><p className="eyebrow">PREFERENCES</p><h1>Settings</h1><p className="page-description">Choose how the investigation assistant generates analysis.</p></div></div>
        {settingsError && <div className="notice notice-error"><AlertCircle size={18} /><p>{settingsError}</p></div>}
        {!settings && !settingsError && <div className="panel loading-state">Loading settings…</div>}
        {settings && <form onSubmit={saveSettings} className="panel settings-form">
          <div className="settings-section"><div><h2>AI service</h2><p>Choose which service helps prepare investigation analysis.</p></div><div className="settings-fields"><label>Service<select value={provider} onChange={(e) => setProvider(e.target.value)}><option value="demo">Demo (offline)</option><option value="openai">OpenAI</option><option value="groq">Groq</option></select><small>Demo mode works offline with fictional records. OpenAI and Groq require an access key.</small></label><label>Model option<input value={model} onChange={(e) => setModel(e.target.value)} placeholder="Enter model name" required /></label><label>Service access key<input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder={settings.api_key_configured ? 'Configured · leave blank to keep current key' : 'Needed for a connected service'} autoComplete="new-password" /><small>Only a key you enter is sent. The saved key is never shown.</small></label></div></div>
          <div className="settings-section"><div><h2>Current status</h2><p>Current service and review settings.</p></div><div className="settings-summary"><div><span>Mode</span><strong>{settings.demo_mode_active ? 'Demo' : 'Connected service'}</strong></div><div><span>Service</span><strong>{settings.llm_provider}</strong></div><div><span>Additional evidence searches</span><strong>{settings.max_critic_retries}</strong><small>How many times the investigation can search again when key information is missing.</small></div></div></div>
          <div className="form-footer">{settingsSaved && <span className="success-message">Settings saved successfully.</span>}<button className="button-primary" type="submit" disabled={settingsSaving}>{settingsSaving ? <RefreshCw className="spin" size={16} /> : <Save size={16} />}{settingsSaving ? 'Saving…' : 'Save settings'}</button></div>
        </form>}
      </section>}
      {activeTab === 'workspace' && !activeCaseId && <div className="page-container empty-state"><h2>No investigation selected</h2><p>Choose an investigation to view its evidence and findings.</p><button className="button-primary" onClick={() => setActiveTab('investigations')}>View investigations</button></div>}
    </main>
  </div>;
}
