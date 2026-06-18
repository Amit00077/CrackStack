import { useState } from "react";
import type { RoadmapWeek, RoadmapTask } from "../../types/roadmap";
import { ProgressBar } from "../ui/ProgressBar";
import { Button } from "../ui/Button";

interface WeekCardProps {
  week: RoadmapWeek;
  onToggleTask: (taskId: string, completed: boolean) => void;
  onEditTask: (taskId: string, task_text: string) => void;
  onDeleteTask: (taskId: string) => void;
  onCreateTask: (task_text: string) => void;
  onGenerateDailyTasks?: (weekId: string) => void;
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  isFirst?: boolean;
  isLast?: boolean;
}

const statusBadge = (tasks: RoadmapTask[]) => {
  const total = tasks.length;
  if (total === 0) return { label: "Empty", color: "badge bg-surface-100 text-surface-600" };
  const done = tasks.filter((t) => t.is_completed).length;
  if (done === total) return { label: "Done", color: "badge-success" };
  if (done > 0) return { label: "In Progress", color: "badge-warning" };
  return { label: "Pending", color: "badge-primary" };
};

export function WeekCard({
  week,
  onToggleTask,
  onEditTask,
  onDeleteTask,
  onCreateTask,
  onGenerateDailyTasks,
  onMoveUp,
  onMoveDown,
  isFirst,
  isLast,
}: WeekCardProps) {
  const [open, setOpen] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [newTaskText, setNewTaskText] = useState("");

  const badge = statusBadge(week.tasks);
  const doneCount = week.tasks.filter((t) => t.is_completed).length;
  const percentage = week.tasks.length > 0 ? (doneCount / week.tasks.length) * 100 : 0;

  const startEdit = (task: RoadmapTask) => {
    setEditingId(task.id);
    setEditText(task.task_text);
  };

  const saveEdit = (taskId: string) => {
    if (editText.trim()) {
      onEditTask(taskId, editText.trim());
    }
    setEditingId(null);
  };

  return (
    <div className="card overflow-hidden transition-all duration-300 hover:shadow-elevated">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-3 p-4 sm:p-5 text-left group"
      >
        <div className={`flex h-7 w-7 items-center justify-center rounded-lg transition-all duration-200 ${open ? "bg-primary-50 text-primary-600" : "bg-surface-100 text-surface-400 group-hover:bg-surface-200"}`}>
          <svg
            className={`h-4 w-4 transition-transform duration-200 ${open ? "rotate-90" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-bold text-surface-900">
              Week {week.week_number}
            </span>
            {week.title && (
              <span className="text-sm text-surface-500 truncate">- {week.title}</span>
            )}
            <span className={`ml-auto ${badge.color}`}>{badge.label}</span>
          </div>
          {week.tasks.length > 0 && (
            <div className="mt-2.5 max-w-md">
              <ProgressBar percentage={percentage} size="sm" color={percentage === 100 ? "green" : "primary"} />
            </div>
          )}
        </div>
        <div className="flex gap-1 flex-shrink-0">
          {onGenerateDailyTasks && week.tasks.length > 0 && (
            <Button
              size="sm"
              variant="outline"
              onClick={(e) => { e.stopPropagation(); onGenerateDailyTasks(week.id); }}
              title="Generate daily tasks for this week"
              className="gap-1"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
              <span className="hidden sm:inline">Generate Tasks</span>
            </Button>
          )}
          {onMoveUp && !isFirst && (
            <button
              onClick={(e) => { e.stopPropagation(); onMoveUp(); }}
              className="flex h-7 w-7 items-center justify-center rounded-lg text-surface-400 hover:bg-surface-100 hover:text-surface-600 transition-all"
              title="Move up"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
            </button>
          )}
          {onMoveDown && !isLast && (
            <button
              onClick={(e) => { e.stopPropagation(); onMoveDown(); }}
              className="flex h-7 w-7 items-center justify-center rounded-lg text-surface-400 hover:bg-surface-100 hover:text-surface-600 transition-all"
              title="Move down"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          )}
        </div>
      </button>

      {open && (
        <div className="border-t border-surface-100 px-4 sm:px-5 pb-4 sm:pb-5 animate-fade-in">
          {week.description && (
            <p className="py-3 text-sm text-surface-500">{week.description}</p>
          )}
          <div className="flex gap-2 pt-3">
            <input
              value={newTaskText}
              onChange={(e) => setNewTaskText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && newTaskText.trim()) {
                  onCreateTask(newTaskText.trim());
                  setNewTaskText("");
                }
              }}
              placeholder="Add a task..."
              className="flex-1 rounded-xl border border-surface-200 bg-surface-50 px-3 py-2 text-sm placeholder-surface-400 focus:border-primary-300 focus:ring-2 focus:ring-primary-500/20 focus:outline-none transition-all"
            />
            <button
              onClick={() => {
                if (newTaskText.trim()) {
                  onCreateTask(newTaskText.trim());
                  setNewTaskText("");
                }
              }}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary-600 text-white hover:bg-primary-700 transition-all"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>
          {(week.tasks.length > 0 ? (
            <div className="space-y-2 pt-3">
              {week.tasks.map((task) => (
                <div
                  key={task.id}
                  className="group flex items-center gap-3 rounded-xl border border-surface-100 p-3 hover:border-surface-200 hover:shadow-sm transition-all duration-200"
                >
                  <button
                    onClick={() => onToggleTask(task.id, !task.is_completed)}
                    className={`flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-lg border-2 transition-all duration-200 ${
                      task.is_completed
                        ? "border-emerald-500 bg-emerald-500 text-white shadow-sm shadow-emerald-500/20"
                        : "border-surface-300 group-hover:border-primary-400"
                    }`}
                  >
                    {task.is_completed && (
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </button>

                  {editingId === task.id ? (
                    <input
                      autoFocus
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      onBlur={() => saveEdit(task.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") saveEdit(task.id);
                        if (e.key === "Escape") setEditingId(null);
                      }}
                      className="flex-1 rounded-xl border border-primary-300 bg-primary-50 px-3 py-1.5 text-sm focus:outline-none"
                    />
                  ) : (
                    <span
                      className={`flex-1 text-sm font-medium ${
                        task.is_completed
                          ? "text-surface-400 line-through"
                          : "text-surface-700"
                      }`}
                    >
                      {task.task_text}
                    </span>
                  )}

                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    <button
                      onClick={() => startEdit(task)}
                      className="flex h-7 w-7 items-center justify-center rounded-lg text-surface-400 hover:bg-surface-100 hover:text-primary-600 transition-all"
                      title="Edit"
                    >
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => onDeleteTask(task.id)}
                      className="flex h-7 w-7 items-center justify-center rounded-lg text-surface-400 hover:bg-rose-50 hover:text-rose-500 transition-all"
                      title="Delete"
                    >
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="py-6 text-center text-sm text-surface-400">No tasks yet</p>
          ))}
        </div>
      )}
    </div>
  );
}
