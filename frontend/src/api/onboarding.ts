import { client } from "./client";

export interface OnboardingQuestion {
  id: string;
  question: string;
  type: "text" | "select" | "multi-select" | "radio" | "number" | "date";
  required: boolean;
  options?: string[];
  placeholder?: string;
}

export interface OnboardingQuestionsResponse {
  onboarding_complete: boolean;
  questions: OnboardingQuestion[];
  session_id?: string;
}

export interface CreateOnboardingRequest {
  goal: string;
  skill_level: "beginner" | "intermediate" | "advanced";
  daily_study_hours: number;
  target_date: string;
  notes?: string;
}

export const onboardingApi = {
  create: (data: CreateOnboardingRequest) =>
    client
      .post<{ phases: { title: string; weeks: any[] }[] }>(
        "/onboarding/complete",
        data,
      )
      .then((r) => r.data),
};
