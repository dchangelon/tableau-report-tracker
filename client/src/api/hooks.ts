import { useQuery, useMutation } from "@tanstack/react-query";
import {
  getHealth,
  getReports,
  getReportById,
  getProjects,
  getRequests,
  getRequestById,
  createRequest,
} from "./client";
import type { CreateRequestPayload } from "../types";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    staleTime: 30 * 1000, // 30 seconds
    retry: 1,
  });
}

export function useReports() {
  return useQuery({
    queryKey: ["reports"],
    queryFn: getReports,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}

export function useReport(id: string) {
  return useQuery({
    queryKey: ["reports", id],
    queryFn: () => getReportById(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: getProjects,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

// Request tracking hooks
export function useRequests(email: string) {
  return useQuery({
    queryKey: ["requests", email],
    queryFn: () => getRequests(email),
    enabled: !!email,
    staleTime: 2 * 60 * 1000, // 2 minutes (requests change more frequently)
    retry: 2,
  });
}

export function useRequest(cardId: string) {
  return useQuery({
    queryKey: ["requests", "detail", cardId],
    queryFn: () => getRequestById(cardId),
    enabled: !!cardId,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

export function useCreateRequest() {
  return useMutation({
    mutationFn: (payload: CreateRequestPayload) => createRequest(payload),
  });
}
