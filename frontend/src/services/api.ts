import {
  CaseDetail,
  SyntheticTemplate,
  InvestigationState,
  WorkflowEvent,
  ReportResponse,
  HumanReview,
  Evidence,
  BenchmarkReport,
  AppSettings,
  AuthUser
} from '../types';

const API_BASE = '/api';

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: 'include', ...options });
  if (!res.ok) {
    let errMsg = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const errData = await res.json();
      if (errData && errData.detail) {
        errMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errMsg);
  }
  return res.json();
}

export const api = {
  async getCurrentUser(): Promise<AuthUser> {
    const result = await fetchJson<{ user: AuthUser }>(`${API_BASE}/auth/me`);
    return result.user;
  },

  async register(data: { full_name: string; email: string; password: string; confirm_password: string }): Promise<AuthUser> {
    const result = await fetchJson<{ user: AuthUser }>(`${API_BASE}/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
    return result.user;
  },

  async login(data: { email: string; password: string }): Promise<AuthUser> {
    const result = await fetchJson<{ user: AuthUser }>(`${API_BASE}/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
    return result.user;
  },

  async logout(): Promise<void> {
    await fetchJson(`${API_BASE}/auth/logout`, { method: 'POST' });
  },

  // Cases
  async getCases(): Promise<CaseDetail[]> {
    return fetchJson<CaseDetail[]>(`${API_BASE}/cases`);
  },

  async getSyntheticTemplates(): Promise<SyntheticTemplate[]> {
    return fetchJson<SyntheticTemplate[]>(`${API_BASE}/cases/templates`);
  },

  async createCase(data: { id?: string; title: string; description: string; category?: string; objective?: string; additional_context?: string; priority?: 'Low' | 'Medium' | 'High' }): Promise<CaseDetail> {
    return fetchJson<CaseDetail>(`${API_BASE}/cases`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },

  async getCase(caseId: string): Promise<CaseDetail> {
    return fetchJson<CaseDetail>(`${API_BASE}/cases/${caseId}`);
  },

  async reopenCase(caseId: string): Promise<{ status: string }> {
    return fetchJson<{ status: string }>(`${API_BASE}/cases/${caseId}/reopen`, {
      method: 'POST'
    });
  },

  async deleteCase(caseId: string): Promise<{ status: string }> {
    return fetchJson<{ status: string }>(`${API_BASE}/cases/${caseId}`, {
      method: 'DELETE'
    });
  },

  // Investigation Workflow
  async startInvestigation(caseId: string, runSync: boolean = false): Promise<any> {
    return fetchJson(`${API_BASE}/cases/${caseId}/investigate?run_sync=${runSync}`, {
      method: 'POST'
    });
  },

  async getWorkflowEvents(caseId: string, sinceId: number = 0): Promise<WorkflowEvent[]> {
    return fetchJson<WorkflowEvent[]>(`${API_BASE}/cases/${caseId}/workflow-events?since_id=${sinceId}`);
  },

  async getInvestigationState(caseId: string): Promise<InvestigationState> {
    return fetchJson<InvestigationState>(`${API_BASE}/cases/${caseId}/state`);
  },

  async getReport(caseId: string): Promise<ReportResponse> {
    return fetchJson<ReportResponse>(`${API_BASE}/cases/${caseId}/report`);
  },

  getReportDownloadUrl(caseId: string, format: 'markdown' | 'text'): string {
    return `${API_BASE}/cases/${caseId}/report?export_format=${format}`;
  },

  async submitReview(caseId: string, review: { decision: 'approved' | 'changes_requested'; reviewer_name: string; feedback: string }): Promise<HumanReview> {
    return fetchJson<HumanReview>(`${API_BASE}/cases/${caseId}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(review)
    });
  },

  async resumeInvestigation(caseId: string, feedback?: string): Promise<any> {
    return fetchJson(`${API_BASE}/cases/${caseId}/resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback })
    });
  },

  // Evidence Vault
  async searchEvidence(q?: string, sourceType?: string, caseId?: string): Promise<Evidence[]> {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (sourceType) params.set('source_type', sourceType);
    if (caseId) params.set('case_id', caseId);
    return fetchJson<Evidence[]>(`${API_BASE}/evidence?${params.toString()}`);
  },

  async getEvidenceSourceTypes(): Promise<Record<string, number>> {
    return fetchJson<Record<string, number>>(`${API_BASE}/evidence/source-types`);
  },

  async getEvidenceDetail(recordId: string): Promise<Evidence> {
    return fetchJson<Evidence>(`${API_BASE}/evidence/${recordId}`);
  },

  async getCaseEvidence(caseId: string): Promise<Evidence[]> {
    return fetchJson<Evidence[]>(`${API_BASE}/evidence/cases/${caseId}`);
  },

  async addCaseEvidence(caseId: string, name: string, description: string, file: File): Promise<Evidence> {
    const form = new FormData();
    form.append('name', name); form.append('description', description); form.append('file', file);
    return fetchJson<Evidence>(`${API_BASE}/evidence/cases/${caseId}`, { method: 'POST', body: form });
  },

  async deleteCaseEvidence(caseId: string, recordId: string): Promise<void> {
    await fetchJson(`${API_BASE}/evidence/cases/${caseId}/${recordId}`, { method: 'DELETE' });
  },

  // Evaluation & Benchmark
  async getBenchmark(forceRerun: boolean = false): Promise<BenchmarkReport> {
    return fetchJson<BenchmarkReport>(`${API_BASE}/evaluation/benchmark?force_rerun=${forceRerun}`);
  },

  async runBenchmark(): Promise<BenchmarkReport> {
    return fetchJson<BenchmarkReport>(`${API_BASE}/evaluation/run`, {
      method: 'POST'
    });
  },

  // Settings
  async getSettings(): Promise<AppSettings> {
    return fetchJson<AppSettings>(`${API_BASE}/settings`);
  },

  async updateSettings(data: { llm_provider?: string; model_name?: string; api_key?: string }): Promise<AppSettings> {
    return fetchJson<AppSettings>(`${API_BASE}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }
};
