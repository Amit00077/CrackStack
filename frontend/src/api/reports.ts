import type { WeeklyReport, ReportGenerateResponse, PaginatedReportsResponse } from "../types/report";
import { client } from "./client";

export const reportsApi = {
  generate: () =>
    client.post<ReportGenerateResponse>("/reports/generate").then((r) => r.data),

  getLatestReport: () =>
    client.get<WeeklyReport>("/reports/latest").then((r) => r.data),

  getCurrent: () =>
    client.get<WeeklyReport>("/reports/current").then((r) => r.data),

  getHistory: (page = 1, limit = 10) =>
    client
      .get<PaginatedReportsResponse>(`/reports/history?page=${page}&limit=${limit}`)
      .then((r) => r.data),
};