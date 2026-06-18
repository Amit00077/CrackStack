export interface WeeklyReport {
  id: string;
  user_id: string;
  week_start: string;
  week_end: string;
  week_number: number;
  letter_grade: string;
  completion_rate: number;
  readiness_score: number;
  strengths: string[];
  improvement_areas: string[];
  recommendations: string[];
  verdict: string;
  ai_generated: boolean;
  is_current: boolean;
  created_at: string;
  completed_tasks: number;
  total_tasks: number;
  summary?: string;
  ai_feedback?: string;
}

export interface ReportGenerateResponse {
  message: string;
  report_id: string;
}

export interface PaginatedReportsResponse {
  items: WeeklyReport[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}