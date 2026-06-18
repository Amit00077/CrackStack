import { create } from "zustand";

import { goalsApi } from "../api/goals";
import type { Goal, GoalCreate } from "../types/goal";

interface GoalState {
  goal: Goal | null;
  isLoading: boolean;

  fetchActiveGoal: () => Promise<void>;
  createGoal: (data: GoalCreate) => Promise<Goal>;
  clearGoal: () => void;
}

export const useGoalStore = create<GoalState>((set) => ({
  goal: null,
  isLoading: true,

  fetchActiveGoal: async () => {
    try {
      const goal = await goalsApi.getActiveGoal();
      set({ goal, isLoading: false });
    } catch {
      set({ goal: null, isLoading: false });
    }
  },

  createGoal: async (data) => {
    const goal = await goalsApi.createGoal(data);
    set({ goal, isLoading: false });
    return goal;
  },

  clearGoal: () => set({ goal: null, isLoading: false }),
}));
