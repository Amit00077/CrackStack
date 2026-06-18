import type { Goal, GoalCreate, GoalUpdate } from "../types/goal";
import { client } from "./client";

export const goalsApi = {
  getActiveGoal: () =>
    client.get<Goal>("/goals/active").then((r) => r.data),

  createGoal: (data: GoalCreate) =>
    client.post<Goal>("/goals", data).then((r) => r.data),

  updateGoal: (id: string, data: GoalUpdate) =>
    client.put<Goal>(`/goals/${id}`, data).then((r) => r.data),

  deleteGoal: (id: string) =>
    client.delete(`/goals/${id}`).then((r) => r.data),
};
