import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { goalsApi } from "../api/goals";
import { roadmapApi } from "../api/roadmap";
import { tasksApi } from "../api/tasks";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { ProgressBar } from "../components/ui/ProgressBar";
import { Skeleton } from "../components/ui/Skeleton";
import { WeekCard } from "../components/roadmap/WeekCard";
import { useAuthStore } from "../store/authStore";
import { useGenerateWeekTasks } from "../hooks/useTasks";

export function RoadmapPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const [regenerateOpen, setRegenerateOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [weekFormOpen, setWeekFormOpen] = useState(false);
  const [weekTitle, setWeekTitle] = useState("");
  const [weekDesc, setWeekDesc] = useState("");

  const generateWeekTasksMutation = useGenerateWeekTasks();

  const handleGenerateDailyTasks = async (weekId: string) => {
    try {
      await generateWeekTasksMutation.mutateAsync(weekId);
    } catch {
    }
  };

  const { data: goal, isLoading: goalLoading } = useQuery({
    queryKey: ["active-goal"],
    queryFn: goalsApi.getActiveGoal,
    retry: false,
  });

  const goalId = goal?.id;

  const {
    data: roadmap,
    isLoading: roadmapLoading,
    error: roadmapError,
  } = useQuery({
    queryKey: ["roadmap", goalId],
    queryFn: () => roadmapApi.getActive(),
    enabled: !!goalId,
    retry: false,
  });

  const updateTaskMutation = useMutation({
    mutationFn: ({
      taskId,
      data,
    }: {
      taskId: string;
      data: { is_completed?: boolean; task_text?: string };
    }) => roadmapApi.updateTask(taskId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roadmap", goalId] });
    },
  });

  const weeks = roadmap?.weeks || [];
  const sortedWeeks = [...weeks].sort((a, b) => a.week_number - b.week_number);

  const handleGenerate = async () => {
    if (!goalId) return;
    setIsGenerating(true);
    try {
      await roadmapApi.generate(goalId);
      queryClient.invalidateQueries({ queryKey: ["roadmap", goalId] });
    } catch {
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRegenerate = async () => {
    if (!goalId) return;
    setRegenerateOpen(false);
    setIsGenerating(true);
    try {
      await roadmapApi.generate(goalId);
      queryClient.invalidateQueries({ queryKey: ["roadmap", goalId] });
    } catch {
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDeleteRoadmap = async () => {
    setDeleteOpen(false);
    try {
      await roadmapApi.deleteRoadmap();
      queryClient.invalidateQueries({ queryKey: ["roadmap", goalId] });
      queryClient.invalidateQueries({ queryKey: ["active-goal"] });
      navigate("/onboarding");
    } catch {
    }
  };

  const handleAddWeek = async () => {
    if (!weekTitle.trim() || !roadmap?.id) return;
    try {
      const nextNum = sortedWeeks.length > 0 ? sortedWeeks[sortedWeeks.length - 1].week_number + 1 : 1;
      await roadmapApi.createWeek({
        roadmap_id: roadmap.id,
        week_number: nextNum,
        title: weekTitle.trim(),
        description: weekDesc.trim(),
      });
      queryClient.invalidateQueries({ queryKey: ["roadmap", goalId] });
      setWeekFormOpen(false);
      setWeekTitle("");
      setWeekDesc("");
    } catch {
    }
  };

  const handleMoveWeek = async (weekId: string, direction: "up" | "down") => {
    const idx = sortedWeeks.findIndex((w) => w.id === weekId);
    if (idx === -1) return;
    const swapIdx = direction === "up" ? idx - 1 : idx + 1;
    if (swapIdx < 0 || swapIdx >= sortedWeeks.length) return;
    const currentWeek = sortedWeeks[idx];
    const swapWeek = sortedWeeks[swapIdx];
    try {
      await roadmapApi.updateWeek(currentWeek.id, { week_number: swapWeek.week_number });
      await roadmapApi.updateWeek(swapWeek.id, { week_number: currentWeek.week_number });
      queryClient.invalidateQueries({ queryKey: ["roadmap", goalId] });
    } catch {
    }
  };

  if (goalLoading) {
    return (
      <div className="space-y-4 animate-fade-in">
        <Skeleton variant="text" width={200} height={28} />
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} variant="rect" height={80} />
        ))}
      </div>
    );
  }

  if (!goal) {
    return (
      <div className="empty-state animate-fade-in">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-primary shadow-lg shadow-primary-500/20 mb-5">
          <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
        </div>
        <h2 className="mb-2 text-xl font-bold text-surface-900">No Roadmap Yet</h2>
        <p className="mb-6 text-sm text-surface-500">
          Set up your goal first to generate a roadmap
        </p>
        <Button onClick={() => navigate("/onboarding")}>
          Start Onboarding
        </Button>
      </div>
    );
  }

  const totalTasks = sortedWeeks.reduce((s, w) => s + w.tasks.length, 0);
  const doneTasks = sortedWeeks.reduce((s, w) => s + w.tasks.filter((t) => t.is_completed).length, 0);
  const overallProgress = totalTasks > 0 ? (doneTasks / totalTasks) * 100 : 0;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="section-title">Roadmap</h2>
          <p className="section-subtitle">
            {goal.goal_text} @ {goal.target_company}
          </p>
        </div>
        <div className="flex gap-2">
          {weeks.length > 0 && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDeleteOpen(true)}
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setRegenerateOpen(true)}
                isLoading={isGenerating}
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Regenerate
              </Button>
            </>
          )}
          <Button size="sm" onClick={() => setWeekFormOpen(true)}>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Week
          </Button>
        </div>
      </div>

      {totalTasks > 0 && (
        <div className="card p-5">
          <ProgressBar
            percentage={overallProgress}
            label={`Overall Progress (${doneTasks}/${totalTasks} tasks)`}
            showLabel
            color={overallProgress === 100 ? "green" : "primary"}
          />
        </div>
      )}

      {roadmapLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="rect" height={64} />
          ))}
        </div>
      )}

      {roadmapError && weeks.length === 0 && (
        <div className="empty-state">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-primary shadow-lg shadow-primary-500/20 mb-5">
            <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h3 className="mb-2 text-xl font-bold text-surface-900">Roadmap not generated</h3>
          <p className="mb-6 text-sm text-surface-500">
            Generate a personalized study roadmap based on your goal
          </p>
          <Button onClick={handleGenerate} isLoading={isGenerating}>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Generate Roadmap
          </Button>
        </div>
      )}

      {sortedWeeks.length > 0 && (
        <div className="space-y-3">
          {sortedWeeks.map((week, idx) => (
            <WeekCard
              key={week.id}
              week={week}
              onToggleTask={(taskId, completed) =>
                updateTaskMutation.mutate({ taskId, data: { is_completed: completed } })
              }
              onEditTask={(taskId, task_text) =>
                updateTaskMutation.mutate({ taskId, data: { task_text } })
              }
              onCreateTask={async (task_text) => {
                try {
                  await roadmapApi.createTask(week.id, { task_text });
                  queryClient.invalidateQueries({ queryKey: ["roadmap", goalId] });
                } catch {
                }
              }}
              onDeleteTask={async (taskId) => {
                try {
                  await roadmapApi.deleteTask(taskId);
                  queryClient.invalidateQueries({ queryKey: ["roadmap", goalId] });
                } catch {
                }
              }}
              onGenerateDailyTasks={handleGenerateDailyTasks}
              onMoveUp={
                idx > 0 ? () => handleMoveWeek(week.id, "up") : undefined
              }
              onMoveDown={
                idx < sortedWeeks.length - 1
                  ? () => handleMoveWeek(week.id, "down")
                  : undefined
              }
              isFirst={idx === 0}
              isLast={idx === sortedWeeks.length - 1}
            />
          ))}
        </div>
      )}

      <Modal
        open={regenerateOpen}
        onClose={() => setRegenerateOpen(false)}
        title="Regenerate Roadmap?"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setRegenerateOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleRegenerate}>
              Regenerate
            </Button>
          </>
        }
      >
        <p className="text-sm text-surface-600">
          This will regenerate your entire roadmap. All current progress will be lost.
          Are you sure?
        </p>
      </Modal>

      <Modal
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        title="Delete Roadmap?"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDeleteRoadmap}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-sm text-surface-600">
          This will permanently delete your entire roadmap and all associated progress.
          Your goal will remain but you'll need to generate a new roadmap. Are you sure?
        </p>
      </Modal>

      <Modal
        open={weekFormOpen}
        onClose={() => setWeekFormOpen(false)}
        title="Add Week"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setWeekFormOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddWeek}>Add</Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="label">Title</label>
            <input
              value={weekTitle}
              onChange={(e) => setWeekTitle(e.target.value)}
              className="input-field"
              placeholder="Week title"
              autoFocus
            />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea
              value={weekDesc}
              onChange={(e) => setWeekDesc(e.target.value)}
              className="input-field resize-none"
              placeholder="Optional description"
              rows={3}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
