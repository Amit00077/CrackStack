import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";

import { onboardingApi } from "../api/onboarding";
import { Button } from "../components/ui/Button";
import { Skeleton } from "../components/ui/Skeleton";

const SKILL_LEVELS = ["Beginner", "Intermediate", "Advanced"] as const;

const DAILY_HOURS = [
  { label: "1–2 Hours", value: 2 },
  { label: "3–4 Hours", value: 4 },
  { label: "5–6 Hours", value: 6 },
  { label: "6+ Hours", value: 8 },
] as const;

const QUICK_DATES = [
  { label: "1 Month", days: 30 },
  { label: "3 Months", days: 90 },
  { label: "6 Months", days: 180 },
  { label: "1 Year", days: 365 },
] as const;

type OnboardingStep = "goal" | "level" | "hours" | "date" | "notes";

interface OnboardingState {
  goal: string;
  skillLevel: string;
  dailyHours: number;
  targetDate: string;
  notes: string;
}

function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-surface-400">
          Step {current} of {total}
        </span>
        <span className="text-xs font-medium text-primary-600">
          {Math.round((current / total) * 100)}%
        </span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-surface-100 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-primary transition-all duration-500 ease-out"
          style={{ width: `${(current / total) * 100}%` }}
        />
      </div>
    </div>
  );
}

export function Onboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState<OnboardingStep>("goal");
  const [form, setForm] = useState<OnboardingState>({
    goal: "",
    skillLevel: "",
    dailyHours: 0,
    targetDate: "",
    notes: "",
  });
  const [error, setError] = useState("");

  const { data: existingGoal, isLoading: checkingGoal } = useQuery({
    queryKey: ["active-goal"],
    queryFn: () =>
      import("../api/goals").then((m) => m.goalsApi.getActiveGoal()),
    retry: false,
  });

  const completeMutation = useMutation({
    mutationFn: () =>
      onboardingApi.create({
        goal: form.goal,
        skill_level: form.skillLevel.toLowerCase() as "beginner" | "intermediate" | "advanced",
        daily_study_hours: form.dailyHours,
        target_date: form.targetDate,
        notes: form.notes || undefined,
      }),
    onSuccess: () => {
      navigate("/roadmap", { replace: true });
    },
    onError: (err: unknown) => {
      const axiosError = err as { response?: { data?: { details?: string; error?: string } } };
      setError(axiosError.response?.data?.details || axiosError.response?.data?.error || "Failed to create roadmap. Please try again.");
    },
  });

  const updateField = (field: keyof OnboardingState, value: string | number) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setError("");
  };

  const goNext = () => {
    const steps: OnboardingStep[] = ["goal", "level", "hours", "date", "notes"];
    const idx = steps.indexOf(step);
    if (idx < steps.length - 1) {
      setStep(steps[idx + 1]);
    }
  };

  const goBack = () => {
    const steps: OnboardingStep[] = ["goal", "level", "hours", "date", "notes"];
    const idx = steps.indexOf(step);
    if (idx > 0) {
      setStep(steps[idx - 1]);
      setError("");
    }
  };

  const validateStep = (): boolean => {
    switch (step) {
      case "goal":
        if (!form.goal.trim()) {
          setError("Please describe what you're preparing for");
          return false;
        }
        return true;
      case "level":
        if (!form.skillLevel) {
          setError("Please select your current level");
          return false;
        }
        return true;
      case "hours":
        if (!form.dailyHours) {
          setError("Please select your available time");
          return false;
        }
        return true;
      case "date":
        if (!form.targetDate) {
          setError("Please select a target date");
          return false;
        }
        return true;
      default:
        return true;
    }
  };

  const handleNext = () => {
    if (!validateStep()) return;
    if (step === "notes") {
      completeMutation.mutate();
    } else {
      goNext();
    }
  };

  if (checkingGoal) {
    return (
      <div className="mx-auto max-w-2xl animate-fade-in">
        <Skeleton variant="rect" height={400} />
      </div>
    );
  }

  if (existingGoal) {
    return (
      <div className="mx-auto max-w-2xl animate-fade-in">
        <div className="card p-8 sm:p-10 text-center">
          <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-100 text-amber-600">
            <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="mb-2 text-xl font-bold text-surface-900">You already have an active goal</h2>
          <p className="mb-6 text-sm text-surface-500">You can view your roadmap or change your goal in settings.</p>
          <div className="flex justify-center gap-3">
            <Button variant="secondary" onClick={() => navigate("/roadmap")}>View Roadmap</Button>
            <Button onClick={() => navigate("/")}>Go to Dashboard</Button>
          </div>
        </div>
      </div>
    );
  }

  const steps: OnboardingStep[] = ["goal", "level", "hours", "date", "notes"];
  const currentStepIndex = steps.indexOf(step);

  return (
    <div className="mx-auto max-w-2xl animate-fade-in">
      <div className="mb-6">
        <h2 className="section-title">Set Up Your Goal</h2>
        <p className="section-subtitle">Tell us about your preparation in a few quick steps</p>
      </div>

      <div className="card p-6 sm:p-8">
        <StepIndicator current={currentStepIndex + 1} total={steps.length} />

        {error && (
          <div className="mb-5 flex items-center gap-2.5 rounded-xl bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700">
            <span>{error}</span>
          </div>
        )}

        {/* Step 1: Goal */}
        {step === "goal" && (
          <div className="animate-fade-in-up">
            <label className="label text-base mb-1">What are you preparing for?</label>
            <p className="text-sm text-surface-500 mb-4">
              Be specific — this helps us create a tailored roadmap
            </p>
            <input
              type="text"
              value={form.goal}
              onChange={(e) => updateField("goal", e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleNext(); }}
              placeholder="e.g., SSC CGL 2027, FAANG SDE Interview, IELTS Band 8"
              className="input-field text-base py-3"
              autoFocus
            />
          </div>
        )}

        {/* Step 2: Skill Level */}
        {step === "level" && (
          <div className="animate-fade-in-up">
            <label className="label text-base mb-1">What's your current level?</label>
            <p className="text-sm text-surface-500 mb-4">This helps us set the right starting point</p>
            <div className="space-y-2.5">
              {SKILL_LEVELS.map((level) => (
                <button
                  key={level}
                  type="button"
                  onClick={() => { updateField("skillLevel", level); }}
                  className={`w-full rounded-xl border-2 px-4 py-3.5 text-sm font-medium text-left transition-all duration-200 ${
                    form.skillLevel === level
                      ? "border-primary-500 bg-primary-50 text-primary-700 shadow-sm shadow-primary-500/10"
                      : "border-surface-200 text-surface-600 hover:border-surface-300 hover:bg-surface-50"
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Daily Hours */}
        {step === "hours" && (
          <div className="animate-fade-in-up">
            <label className="label text-base mb-1">How much time can you invest daily?</label>
            <p className="text-sm text-surface-500 mb-4">Choose the option closest to your availability</p>
            <div className="grid grid-cols-2 gap-3">
              {DAILY_HOURS.map((option) => (
                <button
                  key={option.label}
                  type="button"
                  onClick={() => { updateField("dailyHours", option.value); }}
                  className={`rounded-xl border-2 px-4 py-4 text-sm font-medium text-center transition-all duration-200 ${
                    form.dailyHours === option.value
                      ? "border-primary-500 bg-primary-50 text-primary-700 shadow-sm shadow-primary-500/10"
                      : "border-surface-200 text-surface-600 hover:border-surface-300 hover:bg-surface-50"
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Target Date */}
        {step === "date" && (
          <div className="animate-fade-in-up">
            <label className="label text-base mb-1">What's your target date?</label>
            <p className="text-sm text-surface-500 mb-4">Pick a date or choose a quick option</p>

            <div className="mb-4">
              <input
                type="date"
                value={form.targetDate}
                onChange={(e) => updateField("targetDate", e.target.value)}
                className="input-field text-base py-3"
                autoFocus
              />
            </div>

            <div className="flex flex-wrap gap-2">
              {QUICK_DATES.map((opt) => {
                const d = new Date();
                d.setDate(d.getDate() + opt.days);
                const dateStr = d.toISOString().split("T")[0];
                return (
                  <button
                    key={opt.label}
                    type="button"
                    onClick={() => updateField("targetDate", dateStr)}
                    className={`rounded-lg border-2 px-3.5 py-2 text-xs font-medium transition-all duration-200 ${
                      form.targetDate === dateStr
                        ? "border-primary-500 bg-primary-50 text-primary-700"
                        : "border-surface-200 text-surface-500 hover:border-surface-300 hover:bg-surface-50"
                    }`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Step 5 (Optional): Notes */}
        {step === "notes" && (
          <div className="animate-fade-in-up">
            <label className="label text-base mb-1">
              Anything else you'd like me to know?{" "}
              <span className="text-surface-400 font-normal">(optional)</span>
            </label>
            <p className="text-sm text-surface-500 mb-4">
              Share any additional context that could help personalize your roadmap
            </p>
            <textarea
              value={form.notes}
              onChange={(e) => updateField("notes", e.target.value)}
              placeholder="e.g., I work full-time, I can study only on weekends, Quant is my weak area..."
              className="input-field text-base py-3 min-h-[120px] resize-none"
              autoFocus
            />
          </div>
        )}

        {/* Navigation */}
        <div className="mt-8 pt-6 border-t border-surface-100 flex justify-between">
          <Button variant="outline" onClick={goBack} disabled={step === "goal"}>
            Back
          </Button>
          <Button
            onClick={handleNext}
            isLoading={completeMutation.isPending && step === "notes"}
          >
            {step === "notes" ? "Generate My Roadmap" : "Continue"}
          </Button>
        </div>
      </div>
    </div>
  );
}
