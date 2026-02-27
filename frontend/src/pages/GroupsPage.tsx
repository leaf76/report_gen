import React from "react";

import GroupTable from "../components/GroupTable";
import type { GroupRow } from "../types";

type GroupsPageProps = {
  hasParsedData: boolean;
  rows: GroupRow[];
  selectedBaseName: string | null;
  onSelectBaseName: (baseName: string) => void;
  loading: boolean;
  onGoImport: () => void;
  onGoExecutions: () => void;
};

export default function GroupsPage(props: GroupsPageProps): React.ReactElement {
  const {
    hasParsedData,
    rows,
    selectedBaseName,
    onSelectBaseName,
    loading,
    onGoImport,
    onGoExecutions
  } = props;

  if (!hasParsedData) {
    return (
      <section className="route-page">
        <div className="empty-state-card">
          <h2>No parsed data yet</h2>
          <p>Import at least one summary file before viewing grouped results.</p>
          <button type="button" className="button button-primary" onClick={onGoImport}>
            Go to Import
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
          <h2>Grouped Results</h2>
          <p className="subtle-text">Review grouped outcomes and choose a test for execution details.</p>
        </div>
        <button
          type="button"
          className="button"
          onClick={onGoExecutions}
          disabled={!selectedBaseName}
        >
          Open Executions
        </button>
      </div>
      <GroupTable
        rows={rows}
        selectedBaseName={selectedBaseName}
        onSelect={onSelectBaseName}
        loading={loading}
      />
    </section>
  );
}
