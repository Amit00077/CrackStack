import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { tasksApi } from "../api/tasks";
import type { DailyTask } from "../types/task";

export function useTodayTasks() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["todayTasks"],
    queryFn: tasksApi.getTodayTasks,
    staleTime: 30000,
    refetchInterval: 60000,
    refetchOnWindowFocus: true,
  });

  return {
    tasks: (data?.tasks || []) as DailyTask[],
    completionPct: data?.completion_pct ?? 0,
    doneCount: data?.done_count ?? 0,
    totalCount: data?.total_count ?? 0,
    currentWeek: data?.current_week ?? null,
    message: data?.message ?? null,
    isLoading,
    isError,
  };
}

export function useGenerateWeekTasks() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (weekId: string) => tasksApi.generateWeekTasks(weekId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todayTasks"] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}
