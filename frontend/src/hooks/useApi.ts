import { useQuery, useMutation, type UseQueryOptions, type UseMutationOptions } from "@tanstack/react-query";
import type { AxiosError } from "axios";

import type { ErrorResponse } from "../types/common";

export function useApiQuery<T>(
  key: string[],
  fn: () => Promise<T>,
  options?: Omit<UseQueryOptions<T, AxiosError<ErrorResponse>>, "queryKey" | "queryFn">,
) {
  return useQuery<T, AxiosError<ErrorResponse>>({
    queryKey: key,
    queryFn: fn,
    ...options,
  });
}

export function useApiMutation<TData, TVariables>(
  fn: (vars: TVariables) => Promise<TData>,
  options?: Omit<
    UseMutationOptions<TData, AxiosError<ErrorResponse>, TVariables>,
    "mutationFn"
  >,
) {
  return useMutation<TData, AxiosError<ErrorResponse>, TVariables>({
    mutationFn: fn,
    ...options,
  });
}
