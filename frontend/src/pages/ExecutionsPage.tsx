import React from "react";

import ExecutionTable from "../components/ExecutionTable";
import type { ExecutionRow } from "../types";

type ExecutionsPageProps = {
  hasParsedData: boolean;
  selectedBaseName: string | null;
  executions: ExecutionRow[];
  selectedExecutionId: string | null;
  onSelectExecution: (execution: ExecutionRow) => void;
  loading: boolean;
  error: string | null;
  hasSelectedExecution: boolean;
  onGoImport: () => void;
  onGoGroups: () => void;
  onGoDetails: () => void;
};

export default function ExecutionsPage(props: ExecutionsPageProps): React.ReactElement {
  const {
    hasParsedData,
    selectedBaseName,
    executions,
    selectedExecutionId,
    onSelectExecution,
    loading,
    error,
    hasSelectedExecution,
    onGoImport,
    onGoGroups,
    onGoDetails
  } = props;

  if (!hasParsedData) {
    return (
      <section className="route-page">
        <div className="empty-state-card">
          <h2>No parsed data yet</h2>
          <p>Import summaries before opening the execution page.</p>
          <button type="button" className="button button-primary" onClick={onGoImport}>
            Go to Import
          </button>
        </div>
      </section>
    );
  }

  if (!selectedBaseName) {
    return (
      <section className="route-page">
        <div className="empty-state-card">
          <h2>No group selected</h2>
          <p>Select a grouped result first, then return here to inspect executions.</p>
          <button type="button" className="button button-primary" onClick={onGoGroups}>
            Go to Groups
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="route-page">
      <div className="route-page-header">
        <div>
          <p className="eyebrow route-eyebrow">Page</p>
          <h2>Executions</h2>
          <p className="subtle-text">
            Current group: <strong>{selectedBaseName}</strong>
          </p>
        </div>
        <button
          type="button"
          className="button"
          onClick={onGoDetails}
          disabled={!hasSelectedExecution}
        >
          Open Details
        </button>
      </div>
      <ExecutionTable
        executions={executions}
        selectedExecutionId={selectedExecutionId}
        onSelect={onSelectExecution}
        loading={loading}
        error={error}
      />
    </section>
  );
}
