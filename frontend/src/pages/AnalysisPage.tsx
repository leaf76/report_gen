import React, { useEffect, useRef } from "react";
import { createPortal } from "react-dom";

import ExecutionTable from "../components/ExecutionTable";
import GroupTable from "../components/GroupTable";
import type { GroupSortKey, GroupSortState } from "../components/GroupTable";
import type { ExecutionRow, GroupRow } from "../types";

type GroupFilterMode = "all" | "problem";

type AnalysisPageProps = {
  hasParsedData: boolean;
  rows: GroupRow[];
  selectedBaseName: string | null;
  onSelectBaseName: (baseName: string) => void;
  groupLoading: boolean;
  searchTerm: string;
  onSearchTermChange: (value: string) => void;
  filterMode: GroupFilterMode;
  onFilterModeChange: (mode: GroupFilterMode) => void;
  sortState: GroupSortState;
  onToggleSort: (key: GroupSortKey) => void;
  executions: ExecutionRow[];
  selectedExecutionId: string | null;
  onSelectExecution: (execution: ExecutionRow) => void;
  executionLoading: boolean;
  executionError: string | null;
  selectedExecution: ExecutionRow | null;
  isExecutionModalOpen: boolean;
  onCloseExecutionModal: () => void;
  onGoImport: () => void;
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

export default function AnalysisPage(props: AnalysisPageProps): React.ReactElement {
  const {
    hasParsedData,
    rows,
    selectedBaseName,
    onSelectBaseName,
    groupLoading,
    searchTerm,
    onSearchTermChange,
    filterMode,
    onFilterModeChange,
    sortState,
    onToggleSort,
    executions,
    selectedExecutionId,
    onSelectExecution,
    executionLoading,
    executionError,
    selectedExecution,
    isExecutionModalOpen,
    onCloseExecutionModal,
    onGoImport
  } = props;
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const previousActiveElementRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isExecutionModalOpen || typeof document === "undefined") {
      return;
    }

    previousActiveElementRef.current =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.requestAnimationFrame(() => {
      closeButtonRef.current?.focus();
    });

    const onKeyDown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        onCloseExecutionModal();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = originalOverflow;
      previousActiveElementRef.current?.focus();
    };
  }, [isExecutionModalOpen, onCloseExecutionModal]);

  if (!hasParsedData) {
    return (
      <section className="route-page">
        <div className="empty-state-card">
          <h2>No parsed data yet</h2>
          <p>Import at least one summary file before opening analysis.</p>
          <button type="button" className="button button-primary" onClick={onGoImport}>
            Go to Import
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="route-page analysis-page">
      <div className="route-page-header">
        <div>
          <p className="eyebrow route-eyebrow">Page</p>
          <h2>Analysis</h2>
          <p className="subtle-text">
            Review grouped results, executions, and details in one workspace.
          </p>
        </div>
      </div>

      <div className="analysis-layout">
        <aside className="analysis-groups-pane">
          <GroupTable
            rows={rows}
            selectedBaseName={selectedBaseName}
            onSelect={onSelectBaseName}
            loading={groupLoading}
            searchTerm={searchTerm}
            onSearchTermChange={onSearchTermChange}
            filterMode={filterMode}
            onFilterModeChange={onFilterModeChange}
            sortState={sortState}
            onToggleSort={onToggleSort}
          />
        </aside>
      </div>

      {isExecutionModalOpen && typeof document !== "undefined"
        ? createPortal(
            <>
              <button
                type="button"
                className="analysis-modal-backdrop"
                aria-label="Close executions modal"
                onClick={onCloseExecutionModal}
              />
              <section
                className="analysis-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="analysis-modal-title"
              >
                <header className="analysis-modal-header">
                  <div>
                    <p className="analysis-modal-eyebrow">Execution Explorer</p>
                    <h3 id="analysis-modal-title">
                      {selectedBaseName ? `Group: ${selectedBaseName}` : "Executions"}
                    </h3>
                  </div>
                  <button
                    ref={closeButtonRef}
                    type="button"
                    className="button analysis-modal-close-button"
                    onClick={onCloseExecutionModal}
                  >
                    Close
                  </button>
                </header>
                <div className="analysis-modal-body">
                  <div className="analysis-modal-column">
                    <section className="panel analysis-execution-toolbar">
                      <div className="analysis-execution-toolbar-copy">
                        <h3>Executions</h3>
                        {selectedBaseName ? (
                          <p className="subtle-text">
                            Current group: <strong>{selectedBaseName}</strong>
                          </p>
                        ) : (
                          <p className="subtle-text">Select a grouped result to load executions.</p>
                        )}
                      </div>
                      <div className="analysis-execution-toolbar-meta">
                        <span className="file-count-badge">{executionLoading ? "-" : executions.length}</span>
                      </div>
                    </section>

                    <ExecutionTable
                      executions={executions}
                      selectedExecutionId={selectedExecutionId}
                      onSelect={onSelectExecution}
                      loading={executionLoading}
                      error={executionError}
                      showTitle={false}
                      className="analysis-execution-table-panel analysis-modal-section"
                    />
                  </div>

                  <section className="panel analysis-selected-pane analysis-modal-section">
                    <div className="panel-title-row">
                      <h2>Selected Execution</h2>
                    </div>
                    {!selectedExecution ? (
                      <p className="subtle-text analysis-selection-empty">
                        Select an execution row to preview key fields.
                      </p>
                    ) : (
                      <div className="execution-preview-grid">
                        <article className="execution-preview-item execution-preview-item-wide">
                          <p className="execution-preview-label">Raw Name</p>
                          <p className="execution-preview-value">{selectedExecution.raw_name}</p>
                        </article>
                        <article className="execution-preview-item">
                          <p className="execution-preview-label">Result</p>
                          <p className="execution-preview-value">
                            <span className={`badge ${resultClass(selectedExecution.result)}`}>
                              {selectedExecution.result}
                            </span>
                          </p>
                        </article>
                        <article className="execution-preview-item">
                          <p className="execution-preview-label">Iteration</p>
                          <p className="execution-preview-value execution-preview-value-mono">
                            {selectedExecution.iteration ?? "-"}
                          </p>
                        </article>
                        <article className="execution-preview-item">
                          <p className="execution-preview-label">Begin</p>
                          <p className="execution-preview-value execution-preview-value-mono">
                            {formatTimestamp(selectedExecution.begin_time)}
                          </p>
                        </article>
                        <article className="execution-preview-item">
                          <p className="execution-preview-label">End</p>
                          <p className="execution-preview-value execution-preview-value-mono">
                            {formatTimestamp(selectedExecution.end_time)}
                          </p>
                        </article>
                        <article className="execution-preview-item">
                          <p className="execution-preview-label">Detail Rows</p>
                          <p className="execution-preview-value execution-preview-value-mono">
                            {selectedExecution.details.length}
                          </p>
                        </article>
                        <article className="execution-preview-item execution-preview-item-wide">
                          <p className="execution-preview-label">Details</p>
                          {selectedExecution.details.length === 0 ? (
                            <p className="subtle-text execution-preview-empty">
                              No detail records for this execution.
                            </p>
                          ) : (
                            <div className="execution-preview-detail-list">
                              <ol>
                                {selectedExecution.details.map((detail, index) => (
                                  <li
                                    key={`${selectedExecution.execution_id}-${index}`}
                                  >
                                    {detail}
                                  </li>
                                ))}
                              </ol>
                            </div>
                          )}
                        </article>
                      </div>
                    )}
                  </section>
                </div>
              </section>
            </>,
            document.body
          )
        : null}
    </section>
  );
}
