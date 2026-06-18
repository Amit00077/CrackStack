export interface DailyTask {
  id: string;
  user_id: string;
  week_id: string | null;
  task_text: string;
  category: string | null;
  time_estimate: number;
  task_date: string;
  is_done: boolean;
  completed_at: string | null;
  source: string;
  sort_order: number;
  created_at: string;
}

export interface DailyTaskCreate {
  task_text: string;
  category?: string;
  time_estimate?: number;
  assigned_date?: string;
}

export interface DailyTaskUpdate {
  task_text?: string;
  category?: string;
  time_estimate?: number;
  sort_order?: number;
}

export interface CurrentWeekInfo {
  week_number: number;
  title: string;
  theme: string;
}

export interface TodayTasksResponse {
  tasks: DailyTask[];
  completion_pct: number;
  done_count: number;
  total_count: number;
  message?: string | null;
  current_week?: CurrentWeekInfo | null;
}

export interface DayGrid {
  date: string;
  day_name: string;
  is_today: boolean;
  tasks: DailyTask[];
}

export interface WeeklyGridResponse {
  week_start: string;
  days: DayGrid[];
}
