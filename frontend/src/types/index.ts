export interface Evidence {
  record_id: string;
  case_id?: string;
  source_type: 'email' | 'access_log' | 'employee_record' | 'transaction' | 'internal_message' | 'meeting_note' | 'policy' | 'custom';
  title: string;
  timestamp?: string;
  content: string;
  metadata?: Record<string, any>;
  relevance_score?: number;
  file_name?: string;
  added_at?: string;
  custom?: boolean;
}

export interface TimelineEvent {
  timestamp: string;
  event: string;
  source_records: string[];
  category: string;
  verified?: boolean;
  details?: string;
}

export interface Hypothesis {
  id: string;
  title: string;
  description: string;
  status: 'active' | 'supported' | 'challenged' | 'refuted';
  confidence_rationale: string;
  supporting_evidence: string[];
  contradictory_evidence: string[];
}

export interface WorkflowEvent {
  id: number;
  case_id: string;
  timestamp: string;
  node: string;
  event_type: string;
  message: string;
  details: Record<string, any>;
}

export interface HumanReview {
  id?: number;
  case_id: string;
  decision: 'approved' | 'changes_requested';
  reviewer_name: string;
  feedback: string;
  created_at?: string;
}

export interface StructuredReport {
  case_id: string;
  title: string;
  incident_summary: string;
  investigation?: string;
  priority?: string;
  status?: string;
  investigation_goal?: string;
  additional_context?: string;
  what_happened?: string;
  evidence_strength?: 'Strongly supported' | 'Moderately supported' | 'Limited evidence' | 'Inconclusive';
  key_evidence?: Array<{ record_id: string; title: string; source_type?: string; timestamp?: string; content: string }>;
  timeline: TimelineEvent[];
  key_findings: string[];
  competing_hypotheses: Hypothesis[];
  supporting_evidence: string[];
  contradictory_evidence: string[];
  unresolved_questions: string[];
  recommendations: string[];
  uncertainty_declaration?: string | null;
  human_review_status: string;
  generated_at?: string;
}

export interface ReportResponse {
  id: number;
  case_id: string;
  title: string;
  summary: string;
  report_json: StructuredReport;
  markdown_content: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CaseDetail {
  id: string;
  title: string;
  description: string;
  category: string;
  priority: 'Low' | 'Medium' | 'High';
  objective?: string | null;
  additional_context?: string | null;
  status: 'pending' | 'investigating' | 'awaiting_review' | 'completed' | 'reopened';
  mode: string;
  created_at: string;
  updated_at: string;
  has_report: boolean;
  workflow_step_count: number;
  retrieved_evidence_count: number;
  last_review?: HumanReview | null;
}

export interface SyntheticTemplate {
  id: string;
  title: string;
  category: string;
  incident_description: string;
  ground_truth: {
    primary_responsible_party: string;
    role: string;
    method: string;
    verdict_type: string;
    policy_violation: string;
  };
}

export interface InvestigationState {
  case_id: string;
  title: string;
  incident_description: string;
  current_node: string;
  questions_to_investigate: string[];
  planned_queries: string[];
  queries_attempted: string[];
  retrieved_evidence: Evidence[];
  event_timeline: TimelineEvent[];
  hypotheses: Hypothesis[];
  supporting_evidence: Record<string, string[]>;
  contradictory_evidence: Record<string, string[]>;
  evidence_gaps: string[];
  critic_decision?: string;
  critic_feedback?: string;
  retry_count: number;
  max_retries: number;
  final_report?: StructuredReport | null;
  markdown_report?: string | null;
  human_review_status: string;
  human_feedback?: string | null;
}

export interface BenchmarkMetrics {
  basic_rag: {
    ground_truth_alignment: number;
    citation_accuracy: number;
    policy_retrieval_rate: number;
    contradiction_detection_rate: number;
  };
  agentic_rag: {
    ground_truth_alignment: number;
    citation_accuracy: number;
    policy_retrieval_rate: number;
    contradiction_detection_rate: number;
  };
}

export interface BenchmarkReport {
  benchmark_timestamp: string;
  total_cases_evaluated: number;
  aggregate_metrics: BenchmarkMetrics;
  case_details: BenchmarkCaseResult[];
}

export interface BenchmarkCaseMetrics {
  evidence_count: number;
  policy_captured: boolean;
  citation_accuracy_pct: number;
  contradiction_detected: boolean;
  ambiguity_handled_honestly: boolean;
  ground_truth_alignment_pct: number;
  latency_seconds: number;
  summary: string;
  has_uncertainty_declaration?: boolean;
}

export interface BenchmarkCaseResult {
  case_id: string;
  title: string;
  ground_truth_verdict: string;
  basic_rag: BenchmarkCaseMetrics;
  agentic_rag: BenchmarkCaseMetrics;
}

export interface AppSettings {
  project_name: string;
  version: string;
  llm_provider: string;
  model_name: string;
  api_key_configured: boolean;
  demo_mode_active: boolean;
  database_url: string;
  chroma_persist_dir: string;
  max_critic_retries: number;
}

export interface AuthUser {
  id: number;
  full_name: string;
  email: string;
}
