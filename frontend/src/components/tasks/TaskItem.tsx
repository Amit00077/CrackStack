import type { DailyTask } from "../../types/task";

interface TaskItemProps {
  task: DailyTask;
  onToggle: (id: string, completed: boolean) => void;
  onDelete: (id: string) => void;
  onEdit?: (task: DailyTask) => void;
}

const categoryColors: Record<string, string> = {
  study: "bg-primary-50 text-primary-700 border-primary-200",
  practice: "bg-purple-50 text-purple-700 border-purple-200",
  review: "bg-amber-50 text-amber-700 border-amber-200",
  project: "bg-emerald-50 text-emerald-700 border-emerald-200",
  reading: "bg-indigo-50 text-indigo-700 border-indigo-200",
};

export function TaskItem({ task, onToggle, onDelete, onEdit }: TaskItemProps) {
  const catColor =
    categoryColors[task.category || ""] || "bg-surface-100 text-surface-700 border-surface-200";

  return (
    <div
      className={`group flex items-center gap-3 rounded-2xl border p-4 transition-all duration-200 ${
        task.is_done
          ? "border-emerald-200 bg-emerald-50/50"
          : "border-surface-100 bg-white hover:border-surface-200 hover:shadow-sm"
      }`}
    >
      <button
        onClick={() => onToggle(task.id, !task.is_done)}
        className={`flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-lg border-2 transition-all duration-200 ${
          task.is_done
            ? "border-emerald-500 bg-emerald-500 text-white shadow-sm shadow-emerald-500/20"
            : "border-surface-300 hover:border-primary-400"
        }`}
      >
        {task.is_done && (
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        )}
      </button>
      <div className="flex-1 min-w-0">
        <p
          className={`text-sm font-medium truncate ${
            task.is_done
              ? "text-surface-400 line-through"
              : "text-surface-900"
          }`}
        >
          {task.task_text}
        </p>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className={`rounded-xl border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider ${catColor}`}>
          {task.category}
        </span>
        {task.time_estimate > 0 && (
          <span className="flex items-center gap-1 text-xs text-surface-400">
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {task.time_estimate}m
          </span>
        )}
        {onEdit && (
          <button
            onClick={() => onEdit(task)}
            className="flex h-8 w-8 items-center justify-center rounded-xl text-surface-400 opacity-0 group-hover:opacity-100 hover:bg-primary-50 hover:text-primary-500 transition-all duration-200"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
        )}
        <button
          onClick={() => onDelete(task.id)}
          className="flex h-8 w-8 items-center justify-center rounded-xl text-surface-400 opacity-0 group-hover:opacity-100 hover:bg-rose-50 hover:text-rose-500 transition-all duration-200"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  );
}
