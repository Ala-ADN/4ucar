export type InstitutionType = 'grande_ecole' | 'faculte' | 'preparatoire';
export type HealthStatus = 'good' | 'warning' | 'critical';

export interface Institution {
  code: string;
  name: string;
  type: InstitutionType;
  city: string;
  governorate?: string;
  students: number;
  coords: [number, number];
  health: {
    academic: HealthStatus;
    financial: HealthStatus;
    hr: HealthStatus;
    research: HealthStatus;
  };
  global_health: HealthStatus;
  alerts_active?: number;
  ranking_national?: number;
  kpi_snapshot?: {
    taux_reussite: number;
    taux_abandon: number;
    taux_redoublement: number;
    budget_execution: number;
    masse_salariale_pct: number;
    taux_encadrement: number;
    taux_absenteisme: number;
    taux_vacataires: number;
    publications_indexees: number;
    theses_actives: number;
    financements_externes_tnd: number;
    room_occupancy: number;
  };
}

export interface Alert {
  id: string;
  severity: HealthStatus;
  domain: string;
  institution: string;
  time: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'resolved';
}
