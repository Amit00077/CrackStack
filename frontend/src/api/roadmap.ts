import type { RoadmapResponse, RoadmapWeekResponse, RoadmapWeekCreate, RoadmapWeekUpdate, RoadmapTaskCreate, RoadmapTaskUpdate, ReorderRequest } from "../types/roadmap";
import { client } from "./client";

export const roadmapApi = {
  generate: (goalId: string) =>
    client.post<RoadmapResponse>("/roadmap/generate", { goal_id: goalId }).then((r) => r.data),

  getActive: () =>
    client.get<RoadmapResponse>("/roadmap").then((r) => r.data),

  createWeek: (data: RoadmapWeekCreate) =>
    client.post<RoadmapWeekResponse>("/roadmap/weeks", data).then((r) => r.data),

  updateWeek: (weekId: string, data: RoadmapWeekUpdate) =>
    client.put<RoadmapWeekResponse>(`/roadmap/weeks/${weekId}`, data).then((r) => r.data),

  deleteWeek: (weekId: string) =>
    client.delete(`/roadmap/weeks/${weekId}`).then((r) => r.data),

  reorderWeeks: (data: ReorderRequest) =>
    client.patch("/roadmap/weeks/reorder", data).then((r) => r.data),

  createTask: (weekId: string, data: RoadmapTaskCreate) =>
    client.post(`/roadmap/weeks/${weekId}/tasks`, data).then((r) => r.data),

  updateTask: (taskId: string, data: RoadmapTaskUpdate) =>
    client.put(`/roadmap/tasks/${taskId}`, data).then((r) => r.data),

  deleteTask: (taskId: string) =>
    client.delete(`/roadmap/tasks/${taskId}`).then((r) => r.data),

  deleteRoadmap: () =>
    client.delete("/roadmap").then((r) => r.data),
};
