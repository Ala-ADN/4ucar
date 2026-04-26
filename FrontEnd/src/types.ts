export type InstitutionType = 'grande_ecole' | 'faculte' | 'preparatoire';
export type HealthStatus = 'good' | 'warning' | 'critical';

export interface AccreditationProgress {
  passingControls: number;
  totalControls: number;
}

export interface DashboardInstitution {
  code: string;
  name: string;
  type: InstitutionType;
  city: string;
  students: number;
  rank: number;
  ucarScore: number;
  scoreDelta: number;
  globalHealth: HealthStatus;
  alertsActive: number;
  domainScores: {
    academic: number;
    sustainability: number;
    governance: number;
    hr: number;
  };
  kpiSnapshot: {
    studentFacultyRatio: number;       // ACA-01
    successRate: number;               // ACA-02
    dropoutRate: number;               // ACA-03
    curriculumCoverage: number;        // ACA-05
    workloadCompliance: number;        // HR-01
    trainingFulfillment: number;       // HR-05
    documentControlCompliance: number; // GOV-01
    auditNCRClosureRate: number;       // GOV-02
    energyPerStudent: number;          // ESG-01
    renewableEnergyRate: number;       // ESG-03
    recyclingRate: number;             // ESG-04
    genderDiversityIndex: number;      // ESG-07
  };
  accreditation: {
    iso9001: AccreditationProgress;
    iso21001: AccreditationProgress;
    uiGreenMetric: AccreditationProgress;
  };
}

export type AlertType = 'THRESHOLD' | 'ANOMALY' | 'DOCUMENT' | 'PREDICTIVE' | 'COMPLIANCE';
export type AlertLevel = 'INFO' | 'WARNING' | 'CRITICAL' | 'PREDICTIVE';

export interface AlertRecord {
  id: string;
  severity: HealthStatus;
  alertType: AlertType;
  level: AlertLevel;
  domain: string;
  institutionCode: string;
  title: string;
  description: string;
  ageLabel: string;
  status: 'pending' | 'in_progress' | 'resolved';
}

export interface NetworkTrendPoint {
  period: string;
  ucarScore: number;
  academic: number;
  sustainability: number;
  governance: number;
  hr: number;
}

export interface FrameworkPosture {
  framework: string;
  passingControls: number;
  totalControls: number;
}
