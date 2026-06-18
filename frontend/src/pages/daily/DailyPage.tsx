import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { tasksApi } from "../../api/tasks";
import { Button } from "../../components/ui/Button";
import { Modal } from "../../components/ui/Modal";
import { Skeleton } from "../../components/ui/Skeleton";
import { TaskItem } from "../../components/tasks/TaskItem";
import { useTodayTasks } from "../../hooks/useTasks";
import type { DailyTask, DailyTaskCreate, DailyTaskUpdate } from "../../types/task";

export function DailyPage() {
  const queryClient = useQueryClient();
  const {
    tasks,
    completionPct,
    doneCount,
    totalCount,
    currentWeek,
    message,
    isLoading,
    isError,
  } = useTodayTasks();

  const [showAdd, setShowAdd] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newCategory, setNewCategory] = useState("study");
  const [newDuration, setNewDuration] = useState(30);

  const [editingTask, setEditingTask] = useState<DailyTask | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editCategory, setEditCategory] = useState("study");
  const [editDuration, setEditDuration] = useState(30);

  const today = new Date().toISOString().split("T")[0];

  const toggleMutation = useMutation({
    mutationFn: (id: string) => tasksApi.toggleTask(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ["todayTasks"] });
      const prev = queryClient.getQueryData<{ tasks: any[] }>(["todayTasks"]);
      if (prev) {
        queryClient.setQueryData(["todayTasks"], {
          ...prev,
          tasks: prev.tasks.map((t) =>
            t.id === id ? { ...t, is_done: !t.is_done } : t,
          ),
        });
      }
      return { prev };
    },
    onError: (_err, _vars, context) => {
      if (context?.prev) {
        queryClient.setQueryData(["todayTasks"], context.prev);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["todayTasks"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: tasksApi.deleteTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todayTasks"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: DailyTaskUpdate }) =>
      tasksApi.updateTask(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todayTasks"] });
      setEditingTask(null);
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: DailyTaskCreate) => tasksApi.createTask(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todayTasks"] });
      setShowAdd(false);
      setNewTitle("");
    },
  });

  const handleAdd = () => {
    if (!newTitle.trim()) return;
    createMutation.mutate({
      task_text: newTitle.trim(),
      assigned_date: today,
      category: newCategory,
      time_estimate: newDuration,
    });
  };

  const handleEdit = (task: DailyTask) => {
    setEditingTask(task);
    setEditTitle(task.task_text);
    setEditCategory(task.category || "study");
    setEditDuration(task.time_estimate);
  };

  const handleSaveEdit = () => {
    if (!editingTask || !editTitle.trim()) return;
    updateMutation.mutate({
      id: editingTask.id,
      data: {
        task_text: editTitle.trim(),
        category: editCategory,
        time_estimate: editDuration,
      },
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-4 animate-fade-in">
        <Skeleton variant="text" width={200} height={28} />
        <Skeleton variant="text" width={150} height={20} />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="rect" height={64} />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center gap-2.5 rounded-xl bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700">
        <svg className="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Failed to load tasks. Please try again.</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="section-title">Daily Goals</h2>
          <p className="section-subtitle">{today}</p>
        </div>
        {currentWeek && (
          <div className="rounded-xl bg-primary-50 border border-primary-100 px-4 py-2 text-sm font-semibold text-primary-700">
            Week {currentWeek.week_number}: {currentWeek.title}
          </div>
        )}
      </div>

      {totalCount > 0 && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-surface-700">
              Progress ({doneCount}/{totalCount})
            </span>
            <span className="text-sm font-bold text-primary-600">
              {Math.round(completionPct)}%
            </span>
          </div>
          <div className="h-2.5 w-full rounded-full bg-surface-100 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-primary transition-all duration-500"
              style={{ width: `${completionPct}%` }}
            />
          </div>
        </div>
      )}

      <div className="flex items-center gap-2">
        <Button size="sm" onClick={() => setShowAdd(true)}>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Custom Task
        </Button>
      </div>

      {showAdd && (
        <div className="card p-5 animate-fade-in-down">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
            <div className="flex-1">
              <label className="label">Task</label>
              <input
                autoFocus
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleAdd();
                  if (e.key === "Escape") setShowAdd(false);
                }}
                className="input-field"
                placeholder="What do you need to do?"
              />
            </div>
            <div className="w-full sm:w-32">
              <label className="label">Category</label>
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="input-field"
              >
                {["study", "practice", "review", "project", "reading"].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div className="w-full sm:w-24">
              <label className="label">Minutes</label>
              <input
                type="number"
                min={5}
                step={5}
                value={newDuration}
                onChange={(e) => setNewDuration(Number(e.target.value))}
                className="input-field"
              />
            </div>
            <Button size="sm" onClick={handleAdd} isLoading={createMutation.isPending}>
              Add
            </Button>
          </div>
        </div>
      )}

      {message && tasks.length === 0 ? (
        <div className="empty-state animate-fade-in">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-primary shadow-lg shadow-primary-500/20 mb-5">
            <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </div>
          <h3 className="mb-2 text-xl font-bold text-surface-900">Rest Day</h3>
          <p className="text-sm text-surface-500 mb-6">
            {message}
          </p>
        </div>
      ) : tasks.length === 0 ? (
        <div className="empty-state animate-fade-in">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-primary shadow-lg shadow-primary-500/20 mb-5">
            <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </div>
          <h3 className="mb-2 text-xl font-bold text-surface-900">No tasks yet</h3>
          <p className="text-sm text-surface-500">
            No tasks scheduled for today
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {tasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              onToggle={(id) => toggleMutation.mutate(id)}
              onDelete={(id) => deleteMutation.mutate(id)}
              onEdit={handleEdit}
            />
          ))}
        </div>
      )}

      <Modal
        open={!!editingTask}
        onClose={() => setEditingTask(null)}
        title="Edit Task"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setEditingTask(null)}>
              Cancel
            </Button>
            <Button onClick={handleSaveEdit} isLoading={updateMutation.isPending}>
              Save
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="label">Task</label>
            <input
              autoFocus
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSaveEdit();
                if (e.key === "Escape") setEditingTask(null);
              }}
              className="input-field"
              placeholder="What do you need to do?"
            />
          </div>
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="label">Category</label>
              <select
                value={editCategory}
                onChange={(e) => setEditCategory(e.target.value)}
                className="input-field"
              >
                {["study", "practice", "review", "project", "reading"].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div className="w-24">
              <label className="label">Minutes</label>
              <input
                type="number"
                min={5}
                step={5}
                value={editDuration}
                onChange={(e) => setEditDuration(Number(e.target.value))}
                className="input-field"
              />
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}
