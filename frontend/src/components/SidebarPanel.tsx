import React from "react";
import { NavLink } from "react-router-dom";

type SidebarStats = {
  importedFiles: number;
  totalExecutions: number;
  requestedTests: number;
  successGroups: number;
  failedGroups: number;
  errorGroups: number;
  problemExecutions: number;
};

type SidebarPanelProps = {
  collapsed: boolean;
  loading: boolean;
  stats: SidebarStats;
  onToggleCollapse: () => void;
};

const ROUTE_ITEMS = [
  { to: "/import", label: "Import", short: "I" },
  { to: "/analysis", label: "Analysis", short: "A" }
];

function statValue(value: number, loading: boolean): string {
  if (loading) {
    return "-";
  }
  return value.toString();
}

export default function SidebarPanel(props: SidebarPanelProps): React.ReactElement {
  const { collapsed, loading, stats, onToggleCollapse } = props;

  return (
    <aside className={`panel side-rail ${collapsed ? "is-collapsed" : ""}`} aria-label="Main navigation">
      <div className="side-rail-header">
        {!collapsed ? <h2>Workspace</h2> : null}
        <button
          type="button"
          className="button side-rail-toggle"
          onClick={onToggleCollapse}
          aria-expanded={!collapsed}
          aria-controls="side-rail-content"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? ">" : "<"}
        </button>
      </div>

      <div id="side-rail-content" className="side-rail-content">
        <section className="side-rail-section side-route-section">
          {!collapsed ? <h3>Pages</h3> : null}
          <nav className={`side-route-list ${collapsed ? "compact" : ""}`} aria-label="Application pages">
            {ROUTE_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `side-route-link ${isActive ? "is-active" : ""} ${collapsed ? "compact" : ""}`
                }
                title={item.label}
                aria-label={`Navigate to ${item.label}`}
              >
                <span className="side-route-short">{item.short}</span>
                {!collapsed ? <span className="side-route-label">{item.label}</span> : null}
              </NavLink>
            ))}
          </nav>
        </section>

        {collapsed ? (
          <section className="side-rail-section side-mini-section">
            <span className="side-mini-chip success" title="Success groups">
              S {statValue(stats.successGroups, loading)}
            </span>
            <span className="side-mini-chip failed" title="Failed groups">
              F {statValue(stats.failedGroups, loading)}
            </span>
            <span className="side-mini-chip error" title="Error groups">
              E {statValue(stats.errorGroups, loading)}
            </span>
          </section>
        ) : (
          <section className="side-rail-section">
            <h3>System Health</h3>
            <div className="side-health-grid">
              <article className="side-health-card">
                <p>Imported Files</p>
                <strong>{statValue(stats.importedFiles, loading)}</strong>
              </article>
              <article className="side-health-card">
                <p>Total Executions</p>
                <strong>{statValue(stats.totalExecutions, loading)}</strong>
              </article>
              <article className="side-health-card">
                <p>Fail + Error</p>
                <strong>{statValue(stats.problemExecutions, loading)}</strong>
              </article>
              <article className="side-health-card">
                <p>Requested Tests</p>
                <strong>{statValue(stats.requestedTests, loading)}</strong>
              </article>
              <article className="side-health-card success">
                <p>Success Groups</p>
                <strong>{statValue(stats.successGroups, loading)}</strong>
              </article>
              <article className="side-health-card failed">
                <p>Failed Groups</p>
                <strong>{statValue(stats.failedGroups, loading)}</strong>
              </article>
              <article className="side-health-card error">
                <p>Error Groups</p>
                <strong>{statValue(stats.errorGroups, loading)}</strong>
              </article>
            </div>
          </section>
        )}
      </div>
    </aside>
  );
}
