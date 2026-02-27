import React from "react";

import DetailPanel from "../components/DetailPanel";
import type { ExecutionRow } from "../types";

type DetailsPageProps = {
  hasParsedData: boolean;
  selectedExecution: ExecutionRow | null;
  latencyAverages: Record<string, number>;
  onGoImport: () => void;
  onGoExecutions: () => void;
};

export default function DetailsPage(props: DetailsPageProps): React.ReactElement {
  const { hasParsedData, selectedExecution, latencyAverages, onGoImport, onGoExecutions } = props;

  if (!hasParsedData) {
    return (
      <section className="route-page">
        <div className="empty-state-card">
          <h2>No parsed data yet</h2>
          <p>Import summaries before opening the details page.</p>
          <button type="button" className="button button-primary" onClick={onGoImport}>
            Go to Import
          </button>
        </div>
      </section>
    );
  }

  if (!selectedExecution) {
    return (
      <section className="route-page">
        <div className="empty-state-card">
          <h2>No execution selected</h2>
          <p>Select an execution record first, then open details.</p>
          <button type="button" className="button button-primary" onClick={onGoExecutions}>
            Go to Executions
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
          <h2>Details</h2>
          <p className="subtle-text">
            Selected execution: <strong>{selectedExecution.raw_name}</strong>
          </p>
        </div>
      </div>
      <DetailPanel selectedExecution={selectedExecution} latencyAverages={latencyAverages} />
    </section>
  );
}
