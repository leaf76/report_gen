export type ResultTotals = {
  total: number;
  by_result: Record<string, number>;
};

export type GroupRow = {
  base_name: string;
  total: number;
  by_result: Record<string, number>;
  latest_result: string;
  group_result: string;
  failure_count: number;
  error_rate: number;
  latency_averages: Record<string, number>;
};

export type ParseSummaryResponse = {
  summary_id: string;
  requested_tests: string[];
  imported_summaries: ImportedSummaryInfo[];
  group_rows: GroupRow[];
  totals: ResultTotals;
};

export type ImportedSummaryInfo = {
  name: string;
  controller_info: unknown | null;
};

export type SummaryInput = {
  name: string;
  content: string;
};

export type ExecutionRow = {
  execution_id: string;
  raw_name: string;
  base_name: string;
  iteration: number | null;
  result: string;
  details: string[];
  sponge_properties: Record<string, unknown>;
  begin_time: number | null;
  end_time: number | null;
};

export type GroupExecutionsResponse = {
  base_name: string;
  latency_averages: Record<string, number>;
  executions: ExecutionRow[];
};

export type ProblemTestsResponse = {
  tests: string[];
};
