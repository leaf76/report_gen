import React from "react";

import type { GroupRow } from "../types";

type GroupFilterMode = "all" | "problem";

type GroupTableProps = {
  rows: GroupRow[];
  selectedBaseName: string | null;
  onSelect: (baseName: string) => void;
  loading: boolean;
  searchTerm: string;
  onSearchTermChange: (value: string) => void;
  filterMode: GroupFilterMode;
  onFilterModeChange: (mode: GroupFilterMode) => void;
};

function resultClass(result: string): string {
  const normalized = result.toUpperCase();
  if (normalized === "PASS") {
    return "badge-pass";
  }
  if (normalized === "FAIL") {
    return "badge-fail";
  }
  if (normalized === "ERROR") {
    return "badge-error";
  }
  if (normalized === "SKIP") {
    return "badge-skip";
  }
  return "badge-unknown";
}

function percent(count: number, total: number): string {
  if (total <= 0) {
    return "0.0%";
  }
  return `${((count / total) * 100).toFixed(1)}%`;
}

export default function GroupTable(props: GroupTableProps): React.ReactElement {
  const {
    rows,
    selectedBaseName,
    onSelect,
    loading,
    searchTerm,
    onSearchTermChange,
    filterMode,
    onFilterModeChange
  } = props;

  const onRowKeyDown = (
    event: React.KeyboardEvent<HTMLTableRowElement>,
    baseName: string
  ): void => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect(baseName);
    }
  };

  const successGroups = rows.filter((row) => row.group_result.toUpperCase() === "PASS").length;
  const failedGroups = rows.filter((row) => row.group_result.toUpperCase() === "FAIL").length;
  const errorGroups = rows.filter((row) => row.group_result.toUpperCase() === "ERROR").length;

  const summaryValue = (value: number): string => {
    if (loading) {
      return "-";
    }
    return value.toString();
  };

  return (
    <section className="panel">
      <div className="panel-title-row">
        <h2>Grouped Results</h2>
        <span className="file-count-badge">{loading ? "-" : rows.length}</span>
      </div>
      <div className="group-table-controls">
        <label className="groups-field-label" htmlFor="analysis-group-search">
          Search grouped tests
        </label>
        <input
          id="analysis-group-search"
          type="text"
          placeholder="Search test name"
          value={searchTerm}
          onChange={(event) => onSearchTermChange(event.target.value)}
          disabled={loading}
        />
        <label className="checkbox-label groups-filter-check">
          <input
            type="checkbox"
            checked={filterMode === "problem"}
            onChange={(event) => onFilterModeChange(event.target.checked ? "problem" : "all")}
            disabled={loading}
          />
          Show FAIL/ERROR only
        </label>
      </div>
      <div className="group-summary-strip">
        <article className="group-summary-card success">
          <p className="group-summary-label">Success</p>
          <strong className="group-summary-value">{summaryValue(successGroups)}</strong>
        </article>
        <article className="group-summary-card failed">
          <p className="group-summary-label">Failed</p>
          <strong className="group-summary-value">{summaryValue(failedGroups)}</strong>
        </article>
        <article className="group-summary-card error">
          <p className="group-summary-label">Error</p>
          <strong className="group-summary-value">{summaryValue(errorGroups)}</strong>
        </article>
      </div>
      {loading ? <p className="subtle-text">Loading groups...</p> : null}
      {!loading && rows.length === 0 ? <p className="subtle-text">No grouped results.</p> : null}
      {!loading && rows.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Test</th>
                <th>Total</th>
                <th>PASS</th>
                <th>FAIL</th>
                <th>ERROR</th>
                <th>SKIP</th>
                <th>Error Rate</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const selected = selectedBaseName === row.base_name;
                const pass = row.by_result.PASS ?? 0;
                const fail = row.by_result.FAIL ?? 0;
                const error = row.by_result.ERROR ?? 0;
                const skip = row.by_result.SKIP ?? 0;
                const knownTotal = pass + fail + error + skip;
                const total = row.total > 0 ? row.total : knownTotal;
                const unknown = Math.max(total - knownTotal, 0);
                const normalizedGroupResult = row.group_result.toUpperCase();
                const rowClassName = [
                  selected ? "is-selected" : "",
                  normalizedGroupResult === "FAIL" ? "is-fail" : "",
                  normalizedGroupResult === "ERROR" ? "is-error" : ""
                ]
                  .filter(Boolean)
                  .join(" ");
                const statusCaption =
                  fail === 0 && error === 0
                    ? `${row.group_result} · No FAIL/ERROR`
                    : `${row.group_result} · ${fail} FAIL / ${error} ERROR`;
                const statusAriaLabel =
                  `PASS ${pass} (${percent(pass, total)}), ` +
                  `FAIL ${fail} (${percent(fail, total)}), ` +
                  `ERROR ${error} (${percent(error, total)}), ` +
                  `SKIP ${skip} (${percent(skip, total)})` +
                  (unknown > 0 ? `, UNKNOWN ${unknown} (${percent(unknown, total)})` : "");

                return (
                  <tr
                    key={row.base_name}
                    className={rowClassName}
                    onClick={() => onSelect(row.base_name)}
                    onKeyDown={(event) => onRowKeyDown(event, row.base_name)}
                    tabIndex={0}
                    aria-selected={selected}
                  >
                    <td>{row.base_name}</td>
                    <td>{row.total}</td>
                    <td>{pass}</td>
                    <td>{fail}</td>
                    <td>{error}</td>
                    <td>{skip}</td>
                    <td>{(row.error_rate * 100).toFixed(1)}%</td>
                    <td className="status-cell">
                      <div className="status-stack">
                        <div className="status-summary">
                          <span className={`badge ${resultClass(row.group_result)}`}>
                            {row.group_result}
                          </span>
                        </div>
                        <div className="status-segment-bar" role="img" aria-label={statusAriaLabel}>
                          {pass > 0 ? (
                            <span
                              className="status-segment status-segment-pass"
                              style={{ width: `${(pass / Math.max(total, 1)) * 100}%` }}
                            />
                          ) : null}
                          {fail > 0 ? (
                            <span
                              className="status-segment status-segment-fail"
                              style={{ width: `${(fail / Math.max(total, 1)) * 100}%` }}
                            />
                          ) : null}
                          {error > 0 ? (
                            <span
                              className="status-segment status-segment-error"
                              style={{ width: `${(error / Math.max(total, 1)) * 100}%` }}
                            />
                          ) : null}
                          {skip > 0 ? (
                            <span
                              className="status-segment status-segment-skip"
                              style={{ width: `${(skip / Math.max(total, 1)) * 100}%` }}
                            />
                          ) : null}
                          {unknown > 0 ? (
                            <span
                              className="status-segment status-segment-unknown"
                              style={{ width: `${(unknown / Math.max(total, 1)) * 100}%` }}
                            />
                          ) : null}
                          {total === 0 ? <span className="status-segment status-segment-empty" /> : null}
                        </div>
                        <p className="status-caption">{statusCaption}</p>
                      </div>
                    </td>
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
