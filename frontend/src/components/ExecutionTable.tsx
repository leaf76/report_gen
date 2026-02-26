import React from "react";

import type { ExecutionRow } from "../types";

type ExecutionTableProps = {
  executions: ExecutionRow[];
  selectedExecutionId: string | null;
  onSelect: (execution: ExecutionRow) => void;
  loading: boolean;
  error: string | null;
  showTitle?: boolean;
  className?: string;
};

function normalizeResult(result: string): string {
  const normalized = result.toUpperCase();
  if (normalized === "PASS") {
    return "pass";
  }
  if (normalized === "FAIL") {
    return "fail";
  }
  if (normalized === "ERROR") {
    return "error";
  }
  if (normalized === "SKIP") {
    return "skip";
  }
  return "unknown";
}

function badgeClass(result: string): string {
  const normalized = normalizeResult(result);
  return `badge-${normalized}`;
}

function formatTimestamp(timestampMs: number | null): string {
  if (timestampMs === null) {
    return "-";
  }
  const date = new Date(timestampMs);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }
  return `${date.toISOString().replace("T", " ").replace("Z", " UTC")}`;
}

export default function ExecutionTable(props: ExecutionTableProps): React.ReactElement {
  const { executions, selectedExecutionId, onSelect, loading, error, showTitle = true, className } =
    props;
  const sectionClassName = ["panel", className].filter(Boolean).join(" ");

  const onRowKeyDown = (
    event: React.KeyboardEvent<HTMLTableRowElement>,
    execution: ExecutionRow
  ): void => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect(execution);
    }
  };

  return (
    <section className={sectionClassName}>
      {showTitle ? (
        <div className="panel-title-row">
          <h2>Executions</h2>
          <span className="file-count-badge">{loading ? "-" : executions.length}</span>
        </div>
      ) : null}
      {loading ? <p className="subtle-text">Loading executions...</p> : null}
      {error ? <p className="error-text">{error}</p> : null}
      {!loading && !error && executions.length === 0 ? (
        <p className="subtle-text">Select a test group to inspect executions.</p>
      ) : null}
      {!loading && !error && executions.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Iteration</th>
                <th>Result</th>
                <th>Begin</th>
                <th>End</th>
              </tr>
            </thead>
            <tbody>
              {executions.map((execution) => {
                const selected = selectedExecutionId === execution.execution_id;
                const normalizedResult = normalizeResult(execution.result);
                const rowClass = [selected ? "is-selected" : "", `is-${normalizedResult}`]
                  .filter(Boolean)
                  .join(" ");
                return (
                  <tr
                    key={execution.execution_id}
                    className={rowClass}
                    onClick={() => onSelect(execution)}
                    onKeyDown={(event) => onRowKeyDown(event, execution)}
                    tabIndex={0}
                    aria-selected={selected}
                  >
                    <td>{execution.iteration ?? "-"}</td>
                    <td>
                      <span className={`badge ${badgeClass(execution.result)}`}>
                        {execution.result}
                      </span>
                    </td>
                    <td>{formatTimestamp(execution.begin_time)}</td>
                    <td>{formatTimestamp(execution.end_time)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
