import { client } from "./client";

export interface DashboardData {
  overall_progress: number;
  current_day: number;
  streak: { current_streak: number; best_streak: number; last_active_date: string | null };
  total_solved: number;
  avg_study_time: number;
  topic_coverage: { completed: number; total: number; categories: { category: string; total: number; completed: number }[] };
  activity_heatmap: { date: string; tasks_completed: number; tasks_total: number; study_time_minutes: number }[];
  today_tasks: { id: string; title: string; is_completed: boolean; task_type: string; duration_minutes?: number }[];
  active_goal: { id: string; goal_text: string; target_company?: string; target_role?: string } | null;
  completion_rate: number;
  streak_days: number;
  total_study_hours: number;
}

export interface StreakData {
  current_streak: number;
  best_streak: number;
  last_active_date: string | null;
}

export const dashboardApi = {
  getDashboard: () =>
    client.get<DashboardData>("/progress/dashboard").then((r) => r.data),

  getStreak: () =>
    client.get<StreakData>("/progress/streak").then((r) => r.data),
};
