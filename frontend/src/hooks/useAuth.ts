import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { useAuthStore } from "../store/authStore";

export function useAuth(requireAuth = true) {
  const navigate = useNavigate();
  const { user, isLoading, isAuthenticated, login, register, logout, loadUser } =
    useAuthStore();

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    if (!isLoading && requireAuth && !isAuthenticated) {
      navigate("/login");
    }
  }, [isLoading, isAuthenticated, requireAuth, navigate]);

  return { user, isLoading, isAuthenticated, login, register, logout };
}
