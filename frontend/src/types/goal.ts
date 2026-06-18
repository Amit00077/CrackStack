export interface Goal {
  id: string;
  user_id: string;
  goal_text: string;
  target_company: string;
  target_role: string;
  duration_months: number;
  daily_study_hours: number;
  skill_level: "beginner" | "intermediate" | "advanced";
  weak_areas: string[];
  start_date: string;
  target_date: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface GoalCreate {
  goal_text: string;
  target_company: string;
  target_role: string;
  duration_months: number;
  daily_study_hours: number;
  skill_level: string;
  weak_areas: string[];
  start_date: string;
}

export interface GoalUpdate {
  goal_text?: string;
  target_company?: string;
  target_role?: string;
  duration_months?: number;
  daily_study_hours?: number;
  skill_level?: string;
  weak_areas?: string[];
}
