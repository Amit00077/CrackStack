import type { DailyTask, DailyTaskCreate, DailyTaskUpdate, TodayTasksResponse, WeeklyGridResponse } from "../types/task";
import { client } from "./client";

export const tasksApi = {
  assignTasks: () =>
    client.post<DailyTask[]>("/tasks/assign").then((r) => r.data),

  generateWeekTasks: (weekId: string) =>
    client.post<DailyTask[]>(`/tasks/generate-week/${weekId}`).then((r) => r.data),

  getTodayTasks: () =>
    client.get<TodayTasksResponse>("/tasks/today").then((r) => r.data),

  getWeeklyGrid: (weekStart?: string) => {
    const params: Record<string, string> = {};
    if (weekStart) params.week_start = weekStart;
    return client.get<WeeklyGridResponse>("/tasks/weekly-grid", { params }).then((r) => r.data);
  },

  getTasks: (startDate?: string, endDate?: string) => {
    const params: Record<string, string> = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return client.get<DailyTask[]>("/tasks", { params }).then((r) => r.data);
  },

  createTask: (data: DailyTaskCreate) =>
    client.post<DailyTask>("/tasks", data).then((r) => r.data),

  toggleTask: (id: string) =>
    client.patch<DailyTask>(`/tasks/${id}/toggle`).then((r) => r.data),

  updateTask: (id: string, data: DailyTaskUpdate) =>
    client.put<DailyTask>(`/tasks/${id}`, data).then((r) => r.data),

  deleteTask: (id: string) =>
    client.delete(`/tasks/${id}`).then((r) => r.data),
};
