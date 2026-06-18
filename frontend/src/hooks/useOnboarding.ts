import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { useGoalStore } from "../store/goalStore";

export function useOnboarding() {
  const navigate = useNavigate();
  const { goal, isLoading, fetchActiveGoal } = useGoalStore();

  useEffect(() => {
    fetchActiveGoal();
  }, [fetchActiveGoal]);

  useEffect(() => {
    if (!isLoading && !goal) {
      navigate("/onboarding");
    }
  }, [isLoading, goal, navigate]);

  return { goal, isLoading };
}
