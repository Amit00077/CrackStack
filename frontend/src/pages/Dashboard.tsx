import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import type { DashboardData } from "../api/dashboard";
import { dashboardApi } from "../api/dashboard";
import { MetricCard } from "../components/dashboard/MetricCard";
import { ProgressBar } from "../components/ui/ProgressBar";
import { Skeleton } from "../components/ui/Skeleton";
import { useAuthStore } from "../store/authStore";

function ActivityHeatmap({ data }: { data: { activity_heatmap: { date: string; tasks_completed: number; tasks_total: number }[] } }) {
  const levelColors = [
    "bg-surface-100",
    "bg-primary-200",
    "bg-primary-400",
    "bg-primary-600",
  ];

  const getLevel = (completed: number, total: number) => {
    if (total === 0) return 0;
    const ratio = completed / total;
    if (ratio === 1) return 3;
    if (ratio >= 0.5) return 2;
    if (ratio > 0) return 1;
    return 0;
  };

  const days = data.activity_heatmap.map((d) => ({
    date: new Date(d.date),
    level: getLevel(d.tasks_completed, d.tasks_total),
    completed: d.tasks_completed,
    total: d.tasks_total,
  }));

  const weeks: typeof days[] = [];
  for (let i = 0; i < days.length; i += 7) {
    weeks.push(days.slice(i, i + 7));
  }

  return (
    <div className="card p-5 sm:p-6">
      <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-surface-500">Activity (Last 30 Days)</h3>
      <div className="flex gap-1.5">
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-1.5">
            {week.map((day, di) => (
              <div
                key={di}
                className={`h-3.5 w-3.5 rounded-md ${levelColors[day.level]} transition-all duration-200 hover:scale-125 hover:shadow-sm cursor-pointer`}
                title={`${day.date.toLocaleDateString()} - ${day.completed}/${day.total} tasks`}
              />
            ))}
          </div>
        ))}
      </div>
      <div className="mt-4 flex items-center gap-2 text-xs text-surface-400">
        <span>Less</span>
        {levelColors.map((c, i) => (
          <div key={i} className={`h-3 w-3 rounded-md ${c}`} />
        ))}
        <span>More</span>
      </div>
    </div>
  );
}

function TopicCoverage({ data }: { data: DashboardData }) {
  const categories = data.topic_coverage.categories || [];
  const maxCatTotal = Math.max(...categories.map((c) => c.total), 1);

  return (
    <div className="card p-5 sm:p-6">
      <h3 className="mb-5 text-xs font-semibold uppercase tracking-wider text-surface-500">Topic Coverage</h3>
      {categories.length === 0 ? (
        <p className="py-6 text-center text-sm text-surface-400">No tasks completed yet</p>
      ) : (
        <div className="space-y-4">
          {categories.map((c) => {
            const pct = Math.round((c.completed / c.total) * 100);
            return (
              <div key={c.category}>
                <div className="mb-1.5 flex justify-between text-sm">
                  <span className="font-medium capitalize text-surface-700">{c.category}</span>
                  <span className="font-semibold text-surface-500">{c.completed}/{c.total}</span>
                </div>
                <ProgressBar
                  percentage={pct}
                  size="sm"
                  color={pct >= 80 ? "green" : pct >= 40 ? "primary" : "yellow"}
                />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function Dashboard() {
  const user = useAuthStore((s) => s.user);
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: dashboardApi.getDashboard,
  });

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="space-y-2">
          <Skeleton variant="text" width={200} height={32} />
          <Skeleton variant="text" width={300} height={20} />
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} variant="rect" height={130} />
          ))}
        </div>
        <div className="grid gap-5 lg:grid-cols-3">
          <Skeleton variant="rect" height={240} className="lg:col-span-2" />
          <Skeleton variant="rect" height={240} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl bg-rose-50 border border-rose-200 p-10 text-center animate-fade-in">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-100 text-rose-600 mb-4">
          <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <p className="text-lg font-semibold text-rose-700">Failed to load dashboard data.</p>
        <p className="mt-1 text-sm text-rose-500">Please try refreshing the page.</p>
      </div>
    );
  }

  if (!data?.active_goal) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div>
          <h2 className="section-title">Dashboard</h2>
          <p className="section-subtitle">
            Welcome{user?.full_name ? `, ${user.full_name}` : ""}!
          </p>
        </div>
        <div className="empty-state">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-primary shadow-lg shadow-primary-500/20 mb-5">
            <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h3 className="mb-2 text-xl font-bold text-surface-900">
            No goal set yet
          </h3>
          <p className="mb-6 text-sm text-surface-500">
            Set up your preparation goal to get started
          </p>
          <Link
            to="/onboarding"
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-primary px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-primary-500/30 hover:shadow-xl hover:shadow-primary-500/40 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Start Onboarding
          </Link>
        </div>
      </div>
    );
  }

  const goal = data.active_goal;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="section-title">Dashboard</h2>
        <p className="section-subtitle">
          Welcome back{user?.full_name ? `, ${user.full_name}` : ""}!
        </p>
        {goal && (
          <div className="mt-2 inline-flex items-center gap-2 rounded-xl bg-primary-50 px-3.5 py-1.5 text-sm text-primary-700 border border-primary-100">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="font-medium">{goal.goal_text}</span>
            {goal.target_company && (
              <>
                <span className="text-primary-300">·</span>
                <span>{goal.target_company}</span>
              </>
            )}
            {goal.target_role && (
              <>
                <span className="text-primary-300">·</span>
                <span>{goal.target_role}</span>
              </>
            )}
          </div>
        )}
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Overall Progress"
          value={`${Math.round(data.completion_rate)}%`}
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          }
          trend={{ value: 12, isUp: true }}
          color="primary"
        />
        <MetricCard
          title="Streak"
          value={`${data.streak_days} days`}
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
            </svg>
          }
          color="green"
        />
        <MetricCard
          title="Tasks Completed"
          value={data.total_solved}
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          }
          color="yellow"
        />
        <MetricCard
          title="Avg Study Time"
          value={data.avg_study_time > 60 ? `${(data.avg_study_time / 60).toFixed(1)}h` : `${data.avg_study_time}m`}
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="red"
        />
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-5">
          <div className="card p-5 sm:p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-surface-500">Today's Tasks</h3>
              <Link
                to="/tasks"
                className="inline-flex items-center gap-1 text-xs font-semibold text-primary-600 hover:text-primary-700 transition-colors"
              >
                View all
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
            {data.today_tasks.length === 0 ? (
              <p className="py-6 text-center text-sm text-surface-400">
                No tasks for today
              </p>
            ) : (
              <div className="space-y-2">
                {data.today_tasks.slice(0, 5).map((task) => (
                  <div
                    key={task.id}
                    className="group flex items-center gap-3 rounded-xl border border-surface-100 p-3 hover:border-surface-200 hover:shadow-sm transition-all duration-200"
                  >
                    <div
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
                    </div>
                    <span
                      className={`flex-1 text-sm font-medium ${
                        task.is_completed ? "text-surface-400 line-through" : "text-surface-700"
                      }`}
                    >
                      {task.title}
                    </span>
                    <span className="badge-primary">
                      {task.task_type}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
          <TopicCoverage data={data} />
        </div>
        <div className="space-y-5">
          <ActivityHeatmap data={data} />
        </div>
      </div>
    </div>
  );
}
