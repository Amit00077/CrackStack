import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { reportsApi } from "../api/reports";
import { Button } from "../components/ui/Button";
import { ProgressBar } from "../components/ui/ProgressBar";
import { Skeleton } from "../components/ui/Skeleton";
import type { WeeklyReport, PaginatedReportsResponse } from "../types/report";

function GradeCard({ report }: { report: WeeklyReport }) {
  const rate = report.completion_rate;
  const grade = report.letter_grade;

  const gradeConfig: Record<string, { color: string; ring: string }> = {
    A: { color: "text-emerald-600 bg-emerald-50 border-emerald-200", ring: "ring-emerald-500/20" },
    B: { color: "text-primary-600 bg-primary-50 border-primary-200", ring: "ring-primary-500/20" },
    C: { color: "text-amber-600 bg-amber-50 border-amber-200", ring: "ring-amber-500/20" },
    D: { color: "text-orange-600 bg-orange-50 border-orange-200", ring: "ring-orange-500/20" },
    F: { color: "text-rose-600 bg-rose-50 border-rose-200", ring: "ring-rose-500/20" },
  };

  const cfg = gradeConfig[grade] || gradeConfig.F;

  return (
    <div className="card p-6 sm:p-8 text-center">
      <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-surface-500">
        Week {report.week_number} Grade
      </p>
      <p className={`text-7xl font-black tracking-tight ${cfg.color}`}>{grade}</p>
      <div className={`mt-4 inline-flex items-center gap-2 rounded-xl border px-4 py-2 ${cfg.color} ${cfg.ring}`}>
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        <span className="text-sm font-semibold">
          {report.completed_tasks}/{report.total_tasks} tasks completed
        </span>
      </div>
    </div>
  );
}

function ReadinessGauge({ rate }: { rate: number }) {
  const color = rate >= 80 ? "text-emerald-600" : rate >= 50 ? "text-amber-600" : "text-rose-600";

  return (
    <div className="card p-6 text-center">
      <p className="mb-5 text-xs font-semibold uppercase tracking-wider text-surface-500">Readiness Score</p>
      <div className="relative mx-auto flex items-center justify-center h-32 w-32">
        <svg className="h-32 w-32 transform -rotate-90" viewBox="0 0 36 36">
          <circle cx="18" cy="18" r="15.5" fill="none" stroke="#e5e7eb" strokeWidth="3" />
          <circle
            cx="18" cy="18" r="15.5"
            fill="none"
            stroke={rate >= 80 ? "#059669" : rate >= 50 ? "#d97706" : "#e11d48"}
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray={`${(rate / 100) * 97.4} 97.4`}
          />
        </svg>
        <span className={`absolute text-3xl font-black ${color}`}>{Math.round(rate)}%</span>
      </div>
    </div>
  );
}

function ReportCard({ report }: { report: WeeklyReport }) {
  return (
    <div className="space-y-5">
      <GradeCard report={report} />

      <div className="card p-5 sm:p-6">
        <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-surface-500">Completion Rate</h3>
        <ProgressBar
          percentage={report.completion_rate}
          showLabel
          size="lg"
          color={
            report.completion_rate >= 80
              ? "green"
              : report.completion_rate >= 50
              ? "yellow"
              : "red"
          }
        />
      </div>

      <ReadinessGauge rate={report.readiness_score} />

      {report.strengths.length > 0 && (
        <div className="rounded-2xl bg-emerald-50 border border-emerald-200 p-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-emerald-200 text-emerald-700">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-sm font-bold text-emerald-800">Strengths</h3>
          </div>
          <ul className="space-y-1.5">
            {report.strengths.map((s) => (
              <li key={s} className="flex items-center gap-2 text-sm font-medium text-emerald-700">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-200/50 text-[10px]">✓</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {report.improvement_areas.length > 0 && (
        <div className="rounded-2xl bg-rose-50 border border-rose-200 p-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-rose-200 text-rose-700">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h3 className="text-sm font-bold text-rose-800">Improvement Areas</h3>
          </div>
          <ul className="space-y-1.5">
            {report.improvement_areas.map((s) => (
              <li key={s} className="flex items-center gap-2 text-sm font-medium text-rose-700">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-rose-200/50 text-[10px]">○</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="card p-5 sm:p-6">
        <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-surface-500">Recommendations</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          {report.recommendations.map((rec) => (
            <div
              key={rec}
              className="rounded-xl bg-surface-50 border border-surface-200 p-4 hover:border-primary-200 hover:bg-primary-50/30 transition-all duration-200"
            >
              <div className="flex items-center gap-2 mb-1">
                <svg className="h-4 w-4 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <p className="text-sm font-bold text-surface-900">{rec}</p>
              </div>
            </div>
          ))}
          {report.recommendations.length === 0 && (
            <p className="col-span-full text-center text-sm text-surface-400 py-4">
              Great job! Keep up the good work.
            </p>
          )}
        </div>
      </div>

      {report.summary && (
        <div className="card p-5 sm:p-6">
          <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-surface-500">Summary</h3>
          <p className="text-sm text-surface-700 leading-relaxed">{report.summary}</p>
        </div>
      )}
    </div>
  );
}

export function Reports() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"current" | "history">("current");
  const [isGenerating, setIsGenerating] = useState(false);

  const {
    data: latestReport,
    isLoading: latestLoading,
    error: latestError,
  } = useQuery({
    queryKey: ["latest-report"],
    queryFn: reportsApi.getLatestReport,
    retry: false,
  });

  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ["reports-history"],
    queryFn: () => reportsApi.getHistory(1, 20),
    retry: false,
    enabled: tab === "history",
  });

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await reportsApi.generate();
      queryClient.invalidateQueries({ queryKey: ["latest-report"] });
      queryClient.invalidateQueries({ queryKey: ["reports-history"] });
    } catch (err) {
      console.error("Report generation failed:", err);
    } finally {
      setIsGenerating(false);
    }
  };

  const report = latestReport || undefined;
  const historyReports: WeeklyReport[] = historyData?.items || [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="section-title">Reports</h2>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setTab(tab === "current" ? "history" : "current")}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={tab === "current" ? "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" : "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"} />
            </svg>
            {tab === "current" ? "View History" : "Current Report"}
          </Button>
          <Button
            size="sm"
            onClick={handleGenerate}
            isLoading={isGenerating}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Generate New Report
          </Button>
        </div>
      </div>

      {tab === "current" && (
        <>
          {latestLoading && (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} variant="rect" height={160} />
              ))}
            </div>
          )}

          {latestError && (
            <div className="empty-state animate-fade-in">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-primary shadow-lg shadow-primary-500/20 mb-5">
                <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="mb-2 text-xl font-bold text-surface-900">No report yet</h3>
              <p className="mb-6 text-sm text-surface-500">
                Generate your first weekly performance report
              </p>
              <Button onClick={handleGenerate} isLoading={isGenerating}>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Generate Report
              </Button>
            </div>
          )}

          {latestReport && <ReportCard report={latestReport} />}
        </>
      )}

      {tab === "history" && (
        <>
          {historyLoading && (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} variant="rect" height={80} />
              ))}
            </div>
          )}

          {historyData && historyReports.length === 0 && (
            <div className="empty-state">
              <p className="text-sm text-surface-500">No past reports found</p>
            </div>
          )}

          {historyReports.length > 0 && (
            <div className="space-y-3">
              {historyReports.map((report) => (
                <div
                  key={report.id}
                  className="card p-5 hover:shadow-elevated transition-all duration-300"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-surface-900">
                        Week {report.week_number}
                      </p>
                      <p className="text-xs text-surface-500 mt-0.5">
                        {new Date(report.week_start).toLocaleDateString()} -{" "}
                        {new Date(report.week_end).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-xl font-black ${
                        report.completion_rate >= 80 ? "text-emerald-600" : report.completion_rate >= 50 ? "text-amber-600" : "text-rose-600"
                      }`}>
                        {Math.round(report.completion_rate)}%
                      </span>
                      <span className={`text-sm font-bold px-2.5 py-1 rounded-lg ${
                        report.letter_grade === "A" ? "bg-emerald-100 text-emerald-700" :
                        report.letter_grade === "B" ? "bg-primary-100 text-primary-700" :
                        report.letter_grade === "C" ? "bg-amber-100 text-amber-700" :
                        "bg-rose-100 text-rose-700"
                      }`}>
                        {report.letter_grade}
                      </span>
                    </div>
                  </div>
                  <div className="mt-3">
                    <ProgressBar
                      percentage={report.completion_rate}
                      size="sm"
                      color={
                        report.completion_rate >= 80
                          ? "green"
                          : report.completion_rate >= 50
                          ? "yellow"
                          : "red"
                      }
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}