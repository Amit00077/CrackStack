import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { tasksApi } from "../api/tasks";
import { Button } from "../components/ui/Button";
import { TaskItem } from "../components/tasks/TaskItem";
import { Skeleton } from "../components/ui/Skeleton";
import type { DailyTask, DailyTaskCreate } from "../types/task";

type FilterMode = "all" | "today" | "week";

const categoryOptions = [
  "study",
  "practice",
  "review",
  "project",
  "reading",
];

function MiniCalendar({ selected }: { selected: string }) {
  const today = new Date();
  const days: { date: string; day: number; isToday: boolean; isSelected: boolean; completed: boolean }[] = [];

  for (let i = -3; i <= 3; i++) {
    const d = new Date(today);
    d.setDate(d.getDate() + i);
    const dateStr = d.toISOString().split("T")[0];
    days.push({
      date: dateStr,
      day: d.getDate(),
      isToday: i === 0,
      isSelected: dateStr === selected,
      completed: Math.random() > 0.5,
    });
  }

  return (
    <div className="flex gap-2">
      {days.map((d) => (
        <div
          key={d.date}
          className={`flex flex-col items-center rounded-xl p-2.5 min-w-[52px] transition-all duration-200 ${
            d.isSelected
              ? "bg-primary-50 ring-2 ring-primary-500 shadow-sm shadow-primary-500/10"
              : d.isToday
              ? "bg-surface-100"
              : "bg-white border border-surface-100"
          }`}
        >
          <span className={`text-[11px] font-semibold uppercase tracking-wider ${
            d.isSelected ? "text-primary-600" : "text-surface-400"
          }`}>
            {new Date(d.date).toLocaleDateString("en", { weekday: "short" })}
          </span>
          <span className={`text-sm font-bold mt-0.5 ${
            d.isSelected ? "text-primary-700" : "text-surface-900"
          }`}>{d.day}</span>
          <div
            className={`mt-1.5 h-2 w-2 rounded-full ${
              d.completed ? "bg-emerald-500" : "bg-surface-200"
            }`}
          />
        </div>
      ))}
    </div>
  );
}

export function DailyTasks() {
  const queryClient = useQueryClient();
  const today = new Date().toISOString().split("T")[0];
  const [filter, setFilter] = useState<FilterMode>("today");
  const [showAdd, setShowAdd] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newCategory, setNewCategory] = useState("study");
  const [newDuration, setNewDuration] = useState(30);

  const { data: tasks, isLoading, error } = useQuery<DailyTask[]>({
    queryKey: ["tasks", filter],
    queryFn: async () => {
      if (filter === "today") {
        const res = await tasksApi.getTodayTasks();
        return res.tasks;
      }
      const end = new Date();
      const start = new Date();
      if (filter === "week") {
        start.setDate(start.getDate() - start.getDay());
        end.setDate(start.getDate() + 6);
      } else {
        start.setDate(start.getDate() - 30);
      }
      return tasksApi.getTasks(
        start.toISOString().split("T")[0],
        end.toISOString().split("T")[0],
      );
    },
  });

  const assignMutation = useMutation({
    mutationFn: () => tasksApi.assignTasks(),
  });

  useEffect(() => {
    if (tasks && tasks.length === 0 && filter === "today" && !isLoading && !error) {
      assignMutation.mutate(undefined, {
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ["tasks", filter] });
        },
      });
    }
  }, [tasks, filter, isLoading, error]);

  const toggleMutation = useMutation({
    mutationFn: (id: string) => tasksApi.toggleTask(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ["tasks", filter] });
      const prev = queryClient.getQueryData<DailyTask[]>(["tasks", filter]);
      if (prev) {
        queryClient.setQueryData(
          ["tasks", filter],
          prev.map((t) =>
            t.id === id ? { ...t, is_done: !t.is_done } : t,
          ),
        );
      }
      return { prev };
    },
    onError: (_err, _vars, context) => {
      if (context?.prev) {
        queryClient.setQueryData(["tasks", filter], context.prev);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks", filter] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: tasksApi.deleteTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks", filter] });
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: DailyTaskCreate) => tasksApi.createTask(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks", filter] });
      setShowAdd(false);
      setNewTitle("");
    },
  });

  const taskList = tasks || [];
  const completedCount = taskList.filter((t) => t.is_done).length;

  const handleAdd = () => {
    if (!newTitle.trim()) return;
    createMutation.mutate({
      task_text: newTitle.trim(),
      assigned_date: today,
      category: newCategory,
      time_estimate: newDuration,
    });
  };

  const filters: { key: FilterMode; label: string }[] = [
    { key: "today", label: "Today" },
    { key: "week", label: "This Week" },
    { key: "all", label: "All" },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="section-title">Daily Tasks</h2>
          <p className="section-subtitle">{today}</p>
        </div>
        <div className="flex items-center gap-2">
          {taskList.length > 0 && (
            <span className="text-sm text-surface-500">
              {completedCount}/{taskList.length} completed
            </span>
          )}
          <Button size="sm" onClick={() => setShowAdd(true)}>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Task
          </Button>
        </div>
      </div>

      <MiniCalendar selected={today} />

      <div className="flex gap-2">
        {filters.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-200 ${
              filter === f.key
                ? "bg-gradient-primary text-white shadow-md shadow-primary-500/20"
                : "bg-surface-100 text-surface-600 hover:bg-surface-200"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="flex items-center gap-2.5 rounded-xl bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700">
          <svg className="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Failed to load tasks. Please try again.</span>
        </div>
      )}

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
                {categoryOptions.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
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

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="rect" height={64} />
          ))}
        </div>
      ) : taskList.length === 0 ? (
        <div className="empty-state animate-fade-in">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-primary shadow-lg shadow-primary-500/20 mb-5">
            <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </div>
          <h3 className="mb-2 text-xl font-bold text-surface-900">No tasks yet</h3>
          <p className="text-sm text-surface-500">
            Add your first task to get started
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {taskList.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              onToggle={(id) => toggleMutation.mutate(id)}
              onDelete={(id) => deleteMutation.mutate(id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
