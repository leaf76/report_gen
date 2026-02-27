import React from "react";

import type { ExecutionRow } from "../types";

type DetailPanelProps = {
  selectedExecution: ExecutionRow | null;
  latencyAverages: Record<string, number>;
  showTitle?: boolean;
  className?: string;
};

function renderSpongeProperties(properties: Record<string, unknown>): React.ReactElement {
  const keys = Object.keys(properties);
  if (keys.length === 0) {
    return <p className="subtle-text">No sponge properties for this execution.</p>;
  }
  return (
    <ul className="kv-list">
      {keys.sort().map((key) => (
        <li key={key}>
          <strong>{key}</strong>: {String(properties[key])}
        </li>
      ))}
    </ul>
  );
}

function renderLatency(latencyAverages: Record<string, number>): React.ReactElement {
  const keys = Object.keys(latencyAverages);
  if (keys.length === 0) {
    return <p className="subtle-text">No latency metrics in current group.</p>;
  }
  return (
    <ul className="kv-list">
      {keys.sort().map((key) => (
        <li key={key}>
          <strong>{key}</strong>: {latencyAverages[key].toFixed(3)}
        </li>
      ))}
    </ul>
  );
}

export default function DetailPanel(props: DetailPanelProps): React.ReactElement {
  const { selectedExecution, latencyAverages, showTitle = true, className } = props;
  const sectionClassName = ["panel", className].filter(Boolean).join(" ");

  return (
    <section className={sectionClassName}>
      {showTitle ? (
        <div className="panel-title-row">
          <h2>Details</h2>
        </div>
      ) : null}
      <div className="detail-content-grid">
        <section className="detail-section-card">
          <h3>Group Latency Averages</h3>
          {renderLatency(latencyAverages)}
        </section>
        <section className="detail-section-card">
          <h3>Execution Detail</h3>
          {!selectedExecution ? (
            <p className="subtle-text">Select an execution to view details.</p>
          ) : (
            <div className="execution-detail">
              <p>
                <strong>Test:</strong> {selectedExecution.raw_name}
              </p>
              <p>
                <strong>Result:</strong> {selectedExecution.result}
              </p>
              <p>
                <strong>Details:</strong>
              </p>
              {selectedExecution.details.length > 0 ? (
                <div className="detail-list-wrap">
                  <ol>
                    {selectedExecution.details.map((detail, index) => (
                      <li key={`${selectedExecution.raw_name}-${index}`}>{detail}</li>
                    ))}
                  </ol>
                </div>
              ) : (
                <p className="subtle-text">No detail records for this execution.</p>
              )}
              <h4 className="detail-subtitle">Sponge Properties</h4>
              <div className="detail-properties-wrap">
                {renderSpongeProperties(selectedExecution.sponge_properties)}
              </div>
            </div>
          )}
        </section>
      </div>
    </section>
  );
}
