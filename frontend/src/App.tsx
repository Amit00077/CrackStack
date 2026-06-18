import { useEffect } from "react";
import { Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/layout/AppLayout";
import { ToastContainer } from "./components/ui/Toast";
import { ChatPage } from "./pages/ChatPage";
import { DailyPage } from "./pages/daily/DailyPage";
import { DailyTasks } from "./pages/DailyTasks";
import { Dashboard } from "./pages/Dashboard";
import { ForgotPassword } from "./pages/ForgotPassword";
import { Login } from "./pages/Login";
import { Notifications } from "./pages/Notifications";
import { Onboarding } from "./pages/Onboarding";
import { Register } from "./pages/Register";
import { Reports } from "./pages/Reports";
import { ResetPassword } from "./pages/ResetPassword";
import { RoadmapPage } from "./pages/RoadmapPage";
import { AdminProviders } from "./pages/AdminProviders";
import { Settings } from "./pages/Settings";
import { useAuthStore } from "./store/authStore";

function App() {
  const loadUser = useAuthStore((s) => s.loadUser);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  return (
    <>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/roadmap" element={<RoadmapPage />} />
          <Route path="/tasks" element={<DailyPage />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/admin/providers" element={<AdminProviders />} />
          <Route path="/notifications" element={<Notifications />} />
        </Route>
      </Routes>
      <ToastContainer />
    </>
  );
}

export default App;
