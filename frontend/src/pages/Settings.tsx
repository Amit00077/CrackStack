import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";

import { client } from "../api/client";
import { goalsApi } from "../api/goals";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { useAuthStore } from "../store/authStore";
import { useToast } from "../components/ui/Toast";
import { useQueryClient } from "@tanstack/react-query";

function Toggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!value)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-200 ${
        value ? "bg-gradient-primary shadow-sm shadow-primary-500/20" : "bg-surface-200"
      }`}
    >
      <span
        className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-transform duration-200 ${
          value ? "translate-x-[22px]" : "translate-x-[2px]"
        }`}
      />
    </button>
  );
}

export function Settings() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const toast = useToast();

  const { data: goal } = useQuery({
    queryKey: ["active-goal"],
    queryFn: goalsApi.getActiveGoal,
    retry: false,
  });

  const [displayName, setDisplayName] = useState(user?.full_name || "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || "");
  const [emailNotif, setEmailNotif] = useState(true);
  const [pushNotif, setPushNotif] = useState(true);
  const [dailyReminder, setDailyReminder] = useState(true);
  const [weeklyReport, setWeeklyReport] = useState(false);
  const [timezone, setTimezone] = useState(
    Intl.DateTimeFormat().resolvedOptions().timeZone,
  );
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [deleteModal, setDeleteModal] = useState(false);
  const [editGoalModal, setEditGoalModal] = useState(false);
  const [goalForm, setGoalForm] = useState({
    goal_text: "",
    target_company: "",
    target_role: "",
    duration_months: 3,
    daily_study_hours: 2,
    skill_level: "intermediate",
    weak_areas: [] as string[],
  });

  const updateProfileMutation = useMutation({
    mutationFn: (data: { full_name?: string; avatar_url?: string }) =>
      client.patch("/users/me", data),
    onSuccess: () => {
      toast.success("Profile updated");
      queryClient.invalidateQueries({ queryKey: ["active-goal"] });
    },
    onError: () => toast.error("Failed to update profile"),
  });

  const changePasswordMutation = useMutation({
    mutationFn: (data: { old_password: string; new_password: string }) =>
      client.post("/auth/change-password", data),
    onSuccess: () => {
      toast.success("Password changed");
      setOldPassword("");
      setNewPassword("");
      setConfirmNewPassword("");
    },
    onError: () => toast.error("Failed to change password"),
  });

  const deleteAccountMutation = useMutation({
    mutationFn: () => client.delete("/users/me"),
    onSuccess: () => {
      logout();
      navigate("/login");
    },
    onError: () => toast.error("Failed to delete account"),
  });

  const handleProfileSave = () => {
    updateProfileMutation.mutate({
      full_name: displayName,
      avatar_url: avatarUrl || undefined,
    });
  };

  const handlePasswordChange = () => {
    setPasswordError("");
    if (newPassword !== confirmNewPassword) {
      setPasswordError("Passwords do not match");
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError("Password must be at least 8 characters");
      return;
    }
    changePasswordMutation.mutate({
      old_password: oldPassword,
      new_password: newPassword,
    });
  };

  const updateGoalMutation = useMutation({
    mutationFn: (data: Parameters<typeof goalsApi.updateGoal>[1]) =>
      goalsApi.updateGoal(goal!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["active-goal"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      toast.success("Goal updated");
      setEditGoalModal(false);
    },
    onError: () => toast.error("Failed to update goal"),
  });

  const handleOpenEditGoal = () => {
    if (!goal) return;
    setGoalForm({
      goal_text: goal.goal_text,
      target_company: goal.target_company,
      target_role: goal.target_role,
      duration_months: goal.duration_months,
      daily_study_hours: goal.daily_study_hours,
      skill_level: goal.skill_level,
      weak_areas: [...goal.weak_areas],
    });
    setEditGoalModal(true);
  };

  const handleSaveGoal = () => {
    updateGoalMutation.mutate(goalForm);
  };

  const handleReopenOnboarding = () => {
    navigate("/onboarding");
  };

  const handleRegenerateRoadmap = async () => {
    try {
      await client.post("/goals/regenerate-roadmap");
      toast.success("Roadmap regeneration started");
    } catch {
      toast.error("Failed to regenerate roadmap");
    }
  };

  const SectionCard = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <section className={`card p-5 sm:p-6 ${className}`}>{children}</section>
  );

  const SectionTitle = ({ children }: { children: React.ReactNode }) => (
    <h3 className="mb-5 text-base font-bold text-surface-900 flex items-center gap-2">{children}</h3>
  );

  return (
    <div className="mx-auto max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h2 className="section-title">Settings</h2>
        <p className="section-subtitle">Manage your account and preferences</p>
      </div>

      <SectionCard>
        <SectionTitle>
          <svg className="h-5 w-5 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          Profile
        </SectionTitle>
        <div className="space-y-4">
          <div>
            <label className="label">Display Name</label>
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="input-field"
              placeholder="Your name"
            />
          </div>
          <div>
            <label className="label">Email</label>
            <input
              value={user?.email || ""}
              readOnly
              className="input-field bg-surface-50 text-surface-500 cursor-not-allowed"
            />
          </div>
          <div>
            <label className="label">Avatar URL</label>
            <input
              value={avatarUrl}
              onChange={(e) => setAvatarUrl(e.target.value)}
              className="input-field"
              placeholder="https://example.com/avatar.jpg"
            />
          </div>
          <Button
            onClick={handleProfileSave}
            isLoading={updateProfileMutation.isPending}
            size="sm"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Save Profile
          </Button>
        </div>
      </SectionCard>

      <SectionCard>
        <SectionTitle>
          <svg className="h-5 w-5 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          Notification Preferences
        </SectionTitle>
        <div className="space-y-4">
          {[
            { label: "Email notifications", value: emailNotif, set: setEmailNotif },
            { label: "Push notifications", value: pushNotif, set: setPushNotif },
            { label: "Daily reminder", value: dailyReminder, set: setDailyReminder },
            { label: "Weekly report", value: weeklyReport, set: setWeeklyReport },
          ].map(({ label, value, set }) => (
            <label key={label} className="flex items-center justify-between py-0.5">
              <span className="text-sm font-medium text-surface-700">{label}</span>
              <Toggle value={value} onChange={set} />
            </label>
          ))}
        </div>
      </SectionCard>

      <SectionCard>
        <SectionTitle>
          <svg className="h-5 w-5 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Timezone
        </SectionTitle>
        <select
          value={timezone}
          onChange={(e) => setTimezone(e.target.value)}
          className="input-field"
        >
          {Intl.supportedValuesOf("timeZone").map((tz) => (
            <option key={tz} value={tz}>
              {tz}
            </option>
          ))}
        </select>
      </SectionCard>

      <SectionCard>
        <SectionTitle>
          <svg className="h-5 w-5 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          Change Password
        </SectionTitle>
        {passwordError && (
          <div className="mb-4 flex items-center gap-2.5 rounded-xl bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700">
            <svg className="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{passwordError}</span>
          </div>
        )}
        <div className="space-y-4">
          <div>
            <label className="label">Current Password</label>
            <input
              type="password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              className="input-field"
            />
          </div>
          <div>
            <label className="label">New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="input-field"
              placeholder="At least 8 characters"
            />
          </div>
          <div>
            <label className="label">Confirm New Password</label>
            <input
              type="password"
              value={confirmNewPassword}
              onChange={(e) => setConfirmNewPassword(e.target.value)}
              className="input-field"
            />
          </div>
          <Button
            onClick={handlePasswordChange}
            isLoading={changePasswordMutation.isPending}
            size="sm"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Change Password
          </Button>
        </div>
      </SectionCard>

      {goal && (
        <SectionCard>
          <SectionTitle>
            <svg className="h-5 w-5 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Your Goal
          </SectionTitle>
          <div className="space-y-3">
            <div className="rounded-xl bg-primary-50 border border-primary-100 p-4 space-y-2 text-sm">
              {[
                { label: "Goal", value: goal.goal_text },
                { label: "Company", value: goal.target_company },
                { label: "Role", value: goal.target_role },
                { label: "Duration", value: `${goal.duration_months} months` },
                { label: "Daily Hours", value: `${goal.daily_study_hours} hours` },
                { label: "Level", value: goal.skill_level },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between">
                  <span className="text-primary-600 font-medium">{label}</span>
                  <span className="font-semibold text-primary-900">{value}</span>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleOpenEditGoal}>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Edit Goal
              </Button>
              <Button variant="outline" size="sm" onClick={handleReopenOnboarding}>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Recreate Goal
              </Button>
            </div>
          </div>
        </SectionCard>
      )}

      <SectionCard className="border-rose-200 bg-rose-50/30">
        <SectionTitle>
          <svg className="h-5 w-5 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          Danger Zone
        </SectionTitle>
        <p className="mb-4 text-sm text-surface-500">
          Once you delete your account, there is no going back. Please be certain.
        </p>
        <Button variant="danger" size="sm" onClick={() => setDeleteModal(true)}>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Delete Account
        </Button>
      </SectionCard>

      <Modal
        open={editGoalModal}
        onClose={() => setEditGoalModal(false)}
        title="Edit Goal"
        size="lg"
        footer={
          <>
            <Button variant="ghost" onClick={() => setEditGoalModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveGoal}
              isLoading={updateGoalMutation.isPending}
            >
              Save Changes
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="label">Goal</label>
            <input
              value={goalForm.goal_text}
              onChange={(e) => setGoalForm((f) => ({ ...f, goal_text: e.target.value }))}
              className="input-field"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Company</label>
              <input
                value={goalForm.target_company}
                onChange={(e) => setGoalForm((f) => ({ ...f, target_company: e.target.value }))}
                className="input-field"
              />
            </div>
            <div>
              <label className="label">Role</label>
              <input
                value={goalForm.target_role}
                onChange={(e) => setGoalForm((f) => ({ ...f, target_role: e.target.value }))}
                className="input-field"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Duration (months)</label>
              <select
                value={goalForm.duration_months}
                onChange={(e) => setGoalForm((f) => ({ ...f, duration_months: Number(e.target.value) }))}
                className="input-field"
              >
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>{i + 1} month{i > 0 ? "s" : ""}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Daily Hours</label>
              <select
                value={goalForm.daily_study_hours}
                onChange={(e) => setGoalForm((f) => ({ ...f, daily_study_hours: Number(e.target.value) }))}
                className="input-field"
              >
                {Array.from({ length: 8 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>{i + 1} hour{i > 0 ? "s" : ""}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="label">Skill Level</label>
            <select
              value={goalForm.skill_level}
              onChange={(e) => setGoalForm((f) => ({ ...f, skill_level: e.target.value }))}
              className="input-field"
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
          <div>
            <label className="label">Weak Areas</label>
            <div className="flex flex-wrap gap-2 mt-2">
              {["Data Structures", "Algorithms", "System Design", "Object-Oriented Design", "Database Design", "Networking", "Operating Systems", "Behavioral", "Coding Practice", "Machine Learning", "Frontend Development", "Backend Development"].map((area) => {
                const selected = goalForm.weak_areas.includes(area);
                return (
                  <button
                    key={area}
                    type="button"
                    onClick={() =>
                      setGoalForm((f) => ({
                        ...f,
                        weak_areas: selected
                          ? f.weak_areas.filter((a) => a !== area)
                          : [...f.weak_areas, area],
                      }))
                    }
                    className={`rounded-lg border-2 px-3 py-1.5 text-xs font-medium transition-all ${
                      selected
                        ? "border-primary-500 bg-primary-50 text-primary-700"
                        : "border-surface-200 text-surface-600 hover:border-surface-300"
                    }`}
                  >
                    {area}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </Modal>

      <Modal
        open={deleteModal}
        onClose={() => setDeleteModal(false)}
        title="Delete Account?"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setDeleteModal(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={() => deleteAccountMutation.mutate()}
              isLoading={deleteAccountMutation.isPending}
            >
              Delete
            </Button>
          </>
        }
      >
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-600">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-surface-900 mb-1">Are you absolutely sure?</p>
            <p className="text-sm text-surface-500">
              This will permanently delete your account and all associated data. This action cannot be undone.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
}
