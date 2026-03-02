import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";

import {
  ApiClientError,
  fetchGroupExecutions,
  fetchProblemTests,
  parseSummaries
} from "./api/client";
import type { GroupSortKey, GroupSortState, SortDirection } from "./components/GroupTable";
import SidebarPanel from "./components/SidebarPanel";
import AnalysisPage from "./pages/AnalysisPage";
import ImportPage from "./pages/ImportPage";
import type {
  ExecutionRow,
  GroupRow,
  GroupExecutionsResponse,
  ParseSummaryResponse,
  SummaryInput
} from "./types";

type GroupFilterMode = "all" | "problem";

type ImportedSummary = SummaryInput & {
  contentHash: string;
};

const textEncoder = new TextEncoder();

function groupSeverityScore(groupResult: string): number {
  const normalized = groupResult.toUpperCase();
  if (normalized === "ERROR") {
    return 4;
  }
  if (normalized === "FAIL") {
    return 3;
  }
  if (normalized === "UNKNOWN") {
    return 2;
  }
  if (normalized === "SKIP") {
    return 1;
  }
  return 0;
}

function getResultCount(row: GroupRow, key: "pass" | "fail" | "error" | "skip"): number {
  if (key === "pass") {
    return row.by_result.PASS ?? 0;
  }
  if (key === "fail") {
    return row.by_result.FAIL ?? 0;
  }
  if (key === "error") {
    return row.by_result.ERROR ?? 0;
  }
  return row.by_result.SKIP ?? 0;
}

function compareByDefaultSort(left: GroupRow, right: GroupRow): number {
  const severityDiff = groupSeverityScore(right.group_result) - groupSeverityScore(left.group_result);
  if (severityDiff !== 0) {
    return severityDiff;
  }

  const errorRateDiff = right.error_rate - left.error_rate;
  if (errorRateDiff !== 0) {
    return errorRateDiff;
  }

  const failureCountDiff = right.failure_count - left.failure_count;
  if (failureCountDiff !== 0) {
    return failureCountDiff;
  }

  return left.base_name.localeCompare(right.base_name);
}

function compareBySortKey(left: GroupRow, right: GroupRow, key: GroupSortKey): number {
  if (key === "base_name") {
    return left.base_name.localeCompare(right.base_name);
  }
  if (key === "total") {
    return left.total - right.total;
  }
  if (key === "error_rate") {
    return left.error_rate - right.error_rate;
  }

  return getResultCount(left, key) - getResultCount(right, key);
}

function toMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.traceId ? `${error.message} (trace: ${error.traceId})` : error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unknown error";
}

async function computeContentHash(content: string): Promise<string> {
  const data = textEncoder.encode(content);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, "0")).join(
    ""
  );
}

function toSummaryInputs(items: ImportedSummary[]): SummaryInput[] {
  return items.map(({ name, content }) => ({ name, content }));
}

function formatImportMessage(importedCount: number, duplicateCount: number): string {
  if (duplicateCount > 0) {
    return `Imported ${importedCount} new file(s); skipped ${duplicateCount} duplicate file(s).`;
  }
  return `Imported ${importedCount} new file(s).`;
}

export default function App(): React.ReactElement {
  const navigate = useNavigate();

  const [importedSummaries, setImportedSummaries] = useState<ImportedSummary[]>([]);
  const [parseData, setParseData] = useState<ParseSummaryResponse | null>(null);
  const [parseLoading, setParseLoading] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [importInfoMessage, setImportInfoMessage] = useState<string | null>(null);

  const [selectedBaseName, setSelectedBaseName] = useState<string | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<ExecutionRow | null>(null);
  const [executionData, setExecutionData] = useState<GroupExecutionsResponse | null>(null);
  const [executionLoading, setExecutionLoading] = useState(false);
  const [executionError, setExecutionError] = useState<string | null>(null);
  const executionRequestSeqRef = useRef(0);

  const [problemSet, setProblemSet] = useState<Set<string>>(new Set());

  const [searchTerm, setSearchTerm] = useState("");
  const [filterMode, setFilterMode] = useState<GroupFilterMode>("all");
  const [sortState, setSortState] = useState<GroupSortState>({
    key: null,
    direction: "desc"
  });
  const [executionModalOpen, setExecutionModalOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    if (typeof window === "undefined") {
      return false;
    }
    return window.innerWidth <= 1080;
  });

  const onImportSummaries = async (selectedFiles: File[]): Promise<void> => {
    if (selectedFiles.length === 0 || parseLoading) {
      return;
    }

    setParseLoading(true);
    setParseError(null);
    setImportInfoMessage(null);

    try {
      const uploaded = await Promise.all(
        selectedFiles.map(async (file) => {
          const content = await file.text();
          const contentHash = await computeContentHash(content);
          return {
            name: file.name,
            content,
            contentHash
          } satisfies ImportedSummary;
        })
      );

      const existingHashes = new Set(importedSummaries.map((item) => item.contentHash));
      const batchHashes = new Set<string>();
      const newSummaries: ImportedSummary[] = [];
      let duplicateCount = 0;

      for (const summary of uploaded) {
        if (existingHashes.has(summary.contentHash) || batchHashes.has(summary.contentHash)) {
          duplicateCount += 1;
          continue;
        }
        batchHashes.add(summary.contentHash);
        newSummaries.push(summary);
      }

      if (newSummaries.length === 0) {
        setImportInfoMessage(`Skipped ${duplicateCount} duplicate file(s).`);
        return;
      }

      const candidateSummaries = [...importedSummaries, ...newSummaries];
      const parsed = await parseSummaries(toSummaryInputs(candidateSummaries));

      setImportedSummaries(candidateSummaries);
      setParseData(parsed);
      setSelectedBaseName(parsed.group_rows[0]?.base_name ?? null);
      setSelectedExecution(null);
      setExecutionData(null);
      setExecutionError(null);
      setExecutionModalOpen(false);
      setFilterMode("all");
      setImportInfoMessage(formatImportMessage(newSummaries.length, duplicateCount));

      try {
        const problems = await fetchProblemTests(parsed.summary_id);
        setProblemSet(new Set(problems.tests));
      } catch (error) {
        setProblemSet(new Set());
        setParseError(`Summaries were parsed, but problem-test refresh failed: ${toMessage(error)}`);
      }
    } catch (error) {
      setParseError(toMessage(error));
    } finally {
      setParseLoading(false);
    }
  };

  const onClearImports = (): void => {
    if (parseLoading) {
      return;
    }

    setImportedSummaries([]);
    setParseData(null);
    setParseError(null);
    setImportInfoMessage(null);
    setSelectedBaseName(null);
    setSelectedExecution(null);
    setExecutionData(null);
    setExecutionError(null);
    setProblemSet(new Set());
    setExecutionModalOpen(false);
    setSearchTerm("");
    setFilterMode("all");
    navigate("/import");
  };

  useEffect(() => {
    const requestSeq = executionRequestSeqRef.current + 1;
    executionRequestSeqRef.current = requestSeq;

    const loadExecutions = async (): Promise<void> => {
      if (!parseData || !selectedBaseName) {
        setExecutionData(null);
        setSelectedExecution(null);
        setExecutionLoading(false);
        setExecutionModalOpen(false);
        return;
      }

      setExecutionLoading(true);
      setExecutionError(null);
      try {
        const details = await fetchGroupExecutions(parseData.summary_id, selectedBaseName);
        if (executionRequestSeqRef.current !== requestSeq) {
          return;
        }
        setExecutionData(details);
        setSelectedExecution(details.executions[0] ?? null);
      } catch (error) {
        if (executionRequestSeqRef.current !== requestSeq) {
          return;
        }
        setExecutionData(null);
        setSelectedExecution(null);
        setExecutionError(toMessage(error));
      } finally {
        if (executionRequestSeqRef.current === requestSeq) {
          setExecutionLoading(false);
        }
      }
    };

    void loadExecutions();
  }, [parseData, selectedBaseName]);

  const filteredRows = useMemo(() => {
    if (!parseData) {
      return [];
    }
    const q = searchTerm.trim().toLowerCase();
    const rows = parseData.group_rows.filter((row) => {
      if (q && !row.base_name.toLowerCase().includes(q)) {
        return false;
      }
      if (filterMode !== "problem") {
        return true;
      }
      if (problemSet.size > 0) {
        return problemSet.has(row.base_name);
      }
      const normalized = row.group_result.toUpperCase();
      return normalized === "FAIL" || normalized === "ERROR";
    });

    rows.sort((left, right) => {
      if (sortState.key === null) {
        return compareByDefaultSort(left, right);
      }

      const directionMultiplier = sortState.direction === "asc" ? 1 : -1;
      const primaryDiff = compareBySortKey(left, right, sortState.key);
      if (primaryDiff !== 0) {
        return primaryDiff * directionMultiplier;
      }
      return left.base_name.localeCompare(right.base_name);
    });

    return rows;
  }, [filterMode, parseData, problemSet, searchTerm, sortState]);

  const totals = parseData?.totals.by_result ?? {};
  const totalCount = parseData?.totals.total ?? 0;
  const failCount = (totals.FAIL ?? 0) + (totals.ERROR ?? 0);
  const requestedTestsCount = parseData?.requested_tests.length ?? 0;
  const groupRows = parseData?.group_rows ?? [];
  const successGroups = groupRows.filter((row) => row.group_result.toUpperCase() === "PASS").length;
  const failedGroups = groupRows.filter((row) => row.group_result.toUpperCase() === "FAIL").length;
  const errorGroups = groupRows.filter((row) => row.group_result.toUpperCase() === "ERROR").length;
  const importedFileCards = useMemo(
    () =>
      importedSummaries.map((item, index) => ({
        name: item.name,
        contentHash: item.contentHash,
        controllerInfo: parseData?.imported_summaries?.[index]?.controller_info ?? null
      })),
    [importedSummaries, parseData]
  );

  const hasParsedData = parseData !== null;
  const handleSelectBaseName = (baseName: string): void => {
    const isSameSelection = selectedBaseName === baseName;
    setSelectedBaseName(baseName);
    setExecutionModalOpen(true);
    if (!isSameSelection) {
      setSelectedExecution(null);
      setExecutionError(null);
    }
  };
  const handleSelectExecution = (execution: ExecutionRow): void => {
    setSelectedExecution(execution);
  };
  const handleCloseExecutionModal = useCallback((): void => {
    setExecutionModalOpen(false);
  }, []);
  const handleToggleSort = useCallback((key: GroupSortKey): void => {
    setSortState((previous) => {
      if (previous.key === key) {
        const nextDirection: SortDirection = previous.direction === "asc" ? "desc" : "asc";
        return { key, direction: nextDirection };
      }
      return {
        key,
        direction: key === "base_name" ? "asc" : "desc"
      };
    });
  }, []);

  return (
    <div className="app-shell">
      <header className="app-bar">
        <div className="app-bar-copy">
          <p className="eyebrow">Mobly Summary Explorer</p>
          <h1>Mobly Report Analyzer</h1>
          <p className="app-bar-hint">
            Parse summaries, focus failures first, and inspect execution details.
          </p>
        </div>
      </header>

      <section className={`workspace-layout ${sidebarCollapsed ? "is-collapsed" : ""}`}>
        <SidebarPanel
          collapsed={sidebarCollapsed}
          loading={parseLoading}
          stats={{
            importedFiles: importedSummaries.length,
            totalExecutions: totalCount,
            requestedTests: requestedTestsCount,
            successGroups,
            failedGroups,
            errorGroups,
            problemExecutions: failCount
          }}
          onToggleCollapse={() => setSidebarCollapsed((previous) => !previous)}
        />

        <main className="workspace-main route-content">
          <Routes>
            <Route path="/" element={<Navigate to="/import" replace />} />
            <Route
              path="/import"
              element={
                <ImportPage
                  importedFiles={importedFileCards}
                  onImport={(selectedFiles) => void onImportSummaries(selectedFiles)}
                  onClearImport={onClearImports}
                  isParsing={parseLoading}
                  parseError={parseError}
                  infoMessage={importInfoMessage}
                  hasParsedData={hasParsedData}
                  onGoAnalysis={() => navigate("/analysis")}
                />
              }
            />
            <Route
              path="/analysis"
              element={
                <AnalysisPage
                  hasParsedData={hasParsedData}
                  rows={filteredRows}
                  selectedBaseName={selectedBaseName}
                  onSelectBaseName={handleSelectBaseName}
                  groupLoading={parseLoading}
                  searchTerm={searchTerm}
                  onSearchTermChange={setSearchTerm}
                  filterMode={filterMode}
                  onFilterModeChange={setFilterMode}
                  sortState={sortState}
                  onToggleSort={handleToggleSort}
                  executions={executionData?.executions ?? []}
                  selectedExecutionId={selectedExecution?.execution_id ?? null}
                  onSelectExecution={handleSelectExecution}
                  executionLoading={executionLoading}
                  executionError={executionError}
                  selectedExecution={selectedExecution}
                  isExecutionModalOpen={executionModalOpen && selectedBaseName !== null}
                  onCloseExecutionModal={handleCloseExecutionModal}
                  onGoImport={() => navigate("/import")}
                />
              }
            />
            <Route path="/groups" element={<Navigate to="/analysis" replace />} />
            <Route path="/executions" element={<Navigate to="/analysis" replace />} />
            <Route path="/details" element={<Navigate to="/analysis" replace />} />
            <Route path="*" element={<Navigate to="/import" replace />} />
          </Routes>
        </main>
      </section>
    </div>
  );
}
