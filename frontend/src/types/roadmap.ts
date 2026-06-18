export interface RoadmapTask {
  id: string;
  week_id: string;
  task_text: string;
  category: string;
  time_estimate: number;
  is_completed: boolean;
  sort_order: number;
  created_at: string;
}

export interface RoadmapWeek {
  id: string;
  roadmap_id: string;
  week_number: number;
  title: string;
  description: string | null;
  sort_order: number;
  tasks: RoadmapTask[];
  created_at: string;
}

export interface Roadmap {
  id: string;
  goal_id: string | null;
  title: string;
  description: string | null;
  is_active: boolean;
  weeks_count: number;
  weeks: RoadmapWeek[];
  created_at: string;
  updated_at: string;
}

export interface RoadmapTaskResponse extends RoadmapTask {}

export interface RoadmapWeekResponse extends RoadmapWeek {}

export interface RoadmapResponse extends Roadmap {}

export interface RoadmapWeekCreate {
  roadmap_id: string;
  week_number: number;
  title: string;
  description: string;
}

export interface RoadmapWeekUpdate {
  week_number?: number;
  title?: string;
  description?: string;
  sort_order?: number;
}

export interface RoadmapTaskCreate {
  task_text: string;
  category?: string;
  time_estimate?: number;
}

export interface RoadmapTaskUpdate {
  task_text?: string;
  category?: string;
  time_estimate?: number;
  is_completed?: boolean;
  sort_order?: number;
}

export interface ReorderRequest {
  items: { id: string; sort_order: number }[];
}
