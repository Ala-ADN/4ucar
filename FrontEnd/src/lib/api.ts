/**
 * Typed client for the kpi-service HTTP API.
 *
 * Single base URL — the vite dev server proxies /api/kpi/* to the
 * backend (see vite.config.ts). In production a reverse proxy does
 * the same rewrite, so the same paths work in both environments.
 */

const API_BASE = '/api/kpi';

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: unknown,
  ) {
    super(`${status} ${statusText}`);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      // ignore
    }
    throw new ApiError(res.status, res.statusText, body);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Accreditation domain (Domain H)
// ---------------------------------------------------------------------------

export type AccreditationStatusValue =
  | 'PASSING'
  | 'FAILING'
  | 'NEEDS_EVIDENCE'
  | 'NOT_APPLICABLE';

export type ComplianceLevel = 'COMPLIANT' | 'PARTIAL' | 'NON_COMPLIANT';

export type TestType = 'AUTOMATED_KPI' | 'DOCUMENT_UPLOAD' | 'ATTESTATION';

export type EvidenceStatusValue = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface FrameworkSummary {
  code: string;
  name: string;
  full_name: string;
  version: string | null;
  description: string;
  category: string;
  total_controls: number;
}

export interface TestDescriptor {
  test_id: string;
  test_type: TestType;
  name: string;
  kpi_id: string | null;
  threshold: number | null;
  threshold_comparator: string | null;
  required_template_codes: string[] | null;
}

export interface ControlDescriptor {
  control_id: string;
  clause_ref: string;
  name: string;
  description: string | null;
  weight: number;
  requires_external_survey: boolean;
  tests: TestDescriptor[];
}

export interface FrameworkDetail extends FrameworkSummary {
  controls: ControlDescriptor[];
}

export interface ControlStatus {
  control_id: string;
  clause_ref: string;
  name: string;
  framework_code: string;
  weight: number;
  status: AccreditationStatusValue;
  passing_test_ids: string[];
  failing_test_ids: string[];
  missing_evidence: {
    templates_needed?: { name: string; needed?: number; have?: number }[];
    kpi_inputs_needed?: { kpi_id: string | null; description: string }[];
  };
  not_applicable_reason: string | null;
}

export interface FrameworkPosture {
  framework_code: string;
  framework_name: string;
  institution_code: string;
  period_year: number;
  passing: number;
  failing: number;
  needs_evidence: number;
  not_applicable: number;
  total: number;
  score_pct: number;
  compliance_level: ComplianceLevel;
  controls: ControlStatus[];
}

export interface EvidenceRecord {
  evidence_id: string;
  institution_code: string;
  framework_code: string;
  control_id: string;
  test_id: string;
  template_code: string | null;
  doc_name: string | null;
  period_year: number;
  status: EvidenceStatusValue;
  submitted_at: string;
  approved_at: string | null;
  notes: string | null;
}

export interface EvidencePortfolio {
  framework_code: string;
  institution_code: string;
  period_year: number;
  total_evidence: number;
  approved: number;
  pending: number;
  rejected: number;
  records: EvidenceRecord[];
}

export interface GapItem {
  control_id: string;
  clause_ref: string;
  name: string;
  weight: number;
  status: AccreditationStatusValue;
  priority_score: number;
  missing_test_ids: string[];
  suggested_actions: string[];
}

export interface GapAnalysis {
  framework_code: string;
  institution_code: string;
  period_year: number;
  total_gaps: number;
  gaps: GapItem[];
}

export interface NetworkRow {
  institution_code: string;
  frameworks: Record<
    string,
    {
      score_pct: number;
      compliance_level: ComplianceLevel;
      passing: number;
      total: number;
    }
  >;
}

export interface ApproveEvidencePayload {
  test_id: string;
  doc_name?: string;
  template_code?: string | null;
}

export interface ApproveEvidenceResult {
  message: string;
  evidence: EvidenceRecord;
  updated_control_status: ControlStatus;
}

export const accreditationApi = {
  listFrameworks: () =>
    request<FrameworkSummary[]>('/accreditation/frameworks'),
  getFramework: (code: string) =>
    request<FrameworkDetail>(`/accreditation/frameworks/${encodeURIComponent(code)}`),
  listInstitutions: () =>
    request<string[]>('/accreditation/institutions'),
  network: (period?: number) =>
    request<NetworkRow[]>(
      `/accreditation/network${period ? `?period=${period}` : ''}`,
    ),
  status: (framework: string, institution: string, period?: number) =>
    request<FrameworkPosture>(
      `/accreditation/${encodeURIComponent(framework)}/status/${encodeURIComponent(institution)}${period ? `?period=${period}` : ''}`,
    ),
  evidence: (framework: string, institution: string, period?: number) =>
    request<EvidencePortfolio>(
      `/accreditation/${encodeURIComponent(framework)}/evidence/${encodeURIComponent(institution)}${period ? `?period=${period}` : ''}`,
    ),
  gaps: (framework: string, institution: string, period?: number) =>
    request<GapAnalysis>(
      `/accreditation/${encodeURIComponent(framework)}/gaps/${encodeURIComponent(institution)}${period ? `?period=${period}` : ''}`,
    ),
  approveEvidence: (
    framework: string,
    controlId: string,
    institution: string,
    payload: ApproveEvidencePayload,
  ) =>
    request<ApproveEvidenceResult>(
      `/accreditation/${encodeURIComponent(framework)}/controls/${encodeURIComponent(controlId)}/evidence/${encodeURIComponent(institution)}`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
    ),
};

// ---------------------------------------------------------------------------
// Professors directory + matching (HR / Module 3)
// ---------------------------------------------------------------------------

export interface ProfessorListItem {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  department_code: string | null;
  department_name: string | null;
  rank: string | null;
  primary_specialty: string | null;
  gender: string | null;
  h_index: number | null;
  h_index_updated_at: string | null;
  publications_count: number;
  total_citations: number;
}

export interface ProfessorListResponse {
  total: number;
  items: ProfessorListItem[];
}

export interface ProfessorSpecialization {
  domain: string;
  subdomain: string | null;
  level: string | null;
  verified: boolean;
}

export interface ProfessorPublication {
  title: string;
  journal: string | null;
  year: number | null;
  citation_count: number;
  doi: string | null;
  source: string | null;
}

export interface ProfessorDetail extends ProfessorListItem {
  specializations: ProfessorSpecialization[];
  top_publications: ProfessorPublication[];
}

export interface ProfessorFilters {
  departments: { code: string; name: string; count: number }[];
  ranks: { value: string; count: number }[];
}

export type ProfessorSort =
  | 'h_index_desc'
  | 'h_index_asc'
  | 'name_asc'
  | 'name_desc'
  | 'citations_desc';

export interface ProfessorListQuery {
  search?: string;
  department?: string;
  rank?: string;
  has_h_index?: boolean;
  sort?: ProfessorSort;
  limit?: number;
  offset?: number;
}

export interface MatchScoreBreakdown {
  specialization_similarity: number;
  h_index_normalized: number;
  available_capacity: number;
  student_feedback: number;
  same_institution_priority: number;
}

export interface MatchCandidate {
  professor: ProfessorListItem;
  score: number;
  score_breakdown: MatchScoreBreakdown;
  matched_terms: string[];
}

export interface MatchResponse {
  query: string;
  department_code: string | null;
  total_candidates: number;
  candidates: MatchCandidate[];
}

export interface MatchPayload {
  specialty: string;
  department_code?: string | null;
  max_results?: number;
}

type QueryValue = string | number | boolean | null | undefined;

function toQueryString(params: Record<string, QueryValue> | object): string {
  const usp = new URLSearchParams();
  for (const [k, v] of Object.entries(params as Record<string, QueryValue>)) {
    if (v === undefined || v === null || v === '') continue;
    usp.set(k, String(v));
  }
  const s = usp.toString();
  return s ? `?${s}` : '';
}

export const professorsApi = {
  list: (query: ProfessorListQuery = {}) =>
    request<ProfessorListResponse>(`/professors${toQueryString(query)}`),
  filters: () => request<ProfessorFilters>('/professors/filters'),
  detail: (id: string) =>
    request<ProfessorDetail>(`/professors/${encodeURIComponent(id)}`),
  match: (payload: MatchPayload) =>
    request<MatchResponse>('/professors/match', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

// ---------------------------------------------------------------------------
// Ingestion service — uploads, templates, mass-import portal
// ---------------------------------------------------------------------------

const INGESTION_BASE = '/api/ingestion';

async function ingestionRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${INGESTION_BASE}${path}`, {
    headers: {
      ...(init?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      // ignore
    }
    throw new ApiError(res.status, res.statusText, body);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export type IngestionImportStatus =
  | 'pending'
  | 'extracted'
  | 'mapping_proposed'
  | 'mapping_confirmed'
  | 'validated'
  | 'committed'
  | 'cancelled';

export interface UploadResult {
  import_id: string;
  status: IngestionImportStatus;
  message: string;
}

export interface ImportStatus {
  import_id: string;
  status: IngestionImportStatus;
  domain: string | null;
  period: string | null;
  original_filename: string;
  created_at: string;
  headers?: string[];
  preview?: Record<string, unknown>[];
  total_rows?: number;
}

export interface TemplateSummary {
  id: string;
  code: string;
  name: string;
  description: string | null;
  source_format: string;
  domain: string;
  sheet_name: string | null;
  sample_headers: string[];
  match_count: number;
  last_matched_at: string | null;
  created_at: string;
  field_count: number;
  mapped_field_count: number;
}

export interface TemplateField {
  source_header: string;
  target_field_id: string | null;
  target_field_label: string | null;
  transform_hint: string | null;
  is_required: boolean;
}

export interface TemplateDetail extends TemplateSummary {
  confirmed_mapping: Record<string, string | null>;
  fields: TemplateField[];
  sample_preview: Record<string, unknown>[] | null;
}

export interface MatchSuggestion {
  template: TemplateSummary;
  score: number;
  header_coverage: number;
  matched_headers: string[];
  auto_confirm: boolean;
}

export interface TemplateMatchResponse {
  suggestions: MatchSuggestion[];
  best: MatchSuggestion | null;
}

export interface ApplyTemplateResult {
  import_id: string;
  template_id: string;
  status: IngestionImportStatus;
  confirmed_mapping: Record<string, string | null>;
}

export interface CreateTemplateRequest {
  import_id: string;
  code: string;
  name: string;
  description?: string;
}

export interface CommitResult {
  status: IngestionImportStatus;
  records_committed: number;
  records_quarantined: number;
}

export const ingestionApi = {
  upload: (params: {
    file: File;
    institutionId: string;
    domain: string;
    period: string;
    isHistorical?: boolean;
  }) => {
    const fd = new FormData();
    fd.append('file', params.file);
    fd.append('institution_id', params.institutionId);
    fd.append('domain', params.domain);
    fd.append('period', params.period);
    fd.append('is_historical', String(params.isHistorical ?? false));
    return ingestionRequest<UploadResult>('/upload', {
      method: 'POST',
      body: fd,
    });
  },

  importStatus: (importId: string) =>
    ingestionRequest<ImportStatus>(`/imports/${encodeURIComponent(importId)}/status`),

  matchTemplates: (payload: {
    institution_id: string;
    headers: string[];
    source_format: string;
    domain?: string | null;
  }) =>
    ingestionRequest<TemplateMatchResponse>('/templates/match', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  applyTemplate: (importId: string, templateId: string) =>
    ingestionRequest<ApplyTemplateResult>(
      `/imports/${encodeURIComponent(importId)}/apply-template/${encodeURIComponent(templateId)}`,
      { method: 'POST' },
    ),

  listTemplates: (params: {
    institution_id: string;
    domain?: string;
    source_format?: string;
    include_inactive?: boolean;
  }) => ingestionRequest<TemplateSummary[]>(`/templates${toQueryString(params)}`),

  getTemplate: (templateId: string) =>
    ingestionRequest<TemplateDetail>(`/templates/${encodeURIComponent(templateId)}`),

  createTemplate: (body: CreateTemplateRequest) =>
    ingestionRequest<TemplateDetail>('/templates', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  deleteTemplate: (templateId: string) =>
    ingestionRequest<void>(`/templates/${encodeURIComponent(templateId)}`, {
      method: 'DELETE',
    }),

  commit: (importId: string, overwriteMode: 'overwrite' | 'merge' | 'cancel' = 'merge') =>
    ingestionRequest<CommitResult>(
      `/imports/${encodeURIComponent(importId)}/commit`,
      {
        method: 'POST',
        body: JSON.stringify({ overwrite_mode: overwriteMode }),
      },
    ),

  cancel: (importId: string) =>
    ingestionRequest<{ status: string }>(
      `/imports/${encodeURIComponent(importId)}/cancel`,
      { method: 'POST' },
    ),
};
