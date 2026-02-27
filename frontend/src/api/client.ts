import { invoke } from "@tauri-apps/api/core";

import type {
  GroupExecutionsResponse,
  ParseSummaryResponse,
  ProblemTestsResponse,
  SummaryInput
} from "../types";

type ErrorPayload = {
  error?: string;
  code?: string;
  trace_id?: string;
};

export class ApiClientError extends Error {
  code?: string;
  traceId?: string;

  constructor(message: string, code?: string, traceId?: string) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.traceId = traceId;
  }
}

function parseInvokeError(error: unknown): ApiClientError {
  if (typeof error === "object" && error !== null) {
    const payload = error as ErrorPayload;
    if (payload.error) {
      return new ApiClientError(payload.error, payload.code, payload.trace_id);
    }
  }
  if (error instanceof Error) {
    return new ApiClientError(error.message);
  }
  return new ApiClientError(String(error));
}

async function invokeCommand<T>(command: string, args?: Record<string, unknown>): Promise<T> {
  try {
    return await invoke<T>(command, args);
  } catch (error) {
    throw parseInvokeError(error);
  }
}

export async function parseSummaries(inputs: SummaryInput[]): Promise<ParseSummaryResponse> {
  return invokeCommand<ParseSummaryResponse>("parse_summaries", { inputs });
}

export async function fetchGroupExecutions(
  summaryId: string,
  baseName: string
): Promise<GroupExecutionsResponse> {
  return invokeCommand<GroupExecutionsResponse>("get_group_executions", {
    args: {
      summary_id: summaryId,
      base_name: baseName
    }
  });
}

export async function fetchProblemTests(summaryId: string): Promise<ProblemTestsResponse> {
  return invokeCommand<ProblemTestsResponse>("get_problem_tests", {
    args: {
      summary_id: summaryId
    }
  });
}
