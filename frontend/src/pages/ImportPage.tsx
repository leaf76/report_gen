import React from "react";

import FileUploadPanel from "../components/FileUploadPanel";

type ImportedFileCard = {
  name: string;
  contentHash: string;
  controllerInfo: unknown | null;
};

type ImportPageProps = {
  importedFiles: ImportedFileCard[];
  onImport: (files: File[]) => void;
  onClearImport: () => void;
  isParsing: boolean;
  parseError: string | null;
  infoMessage: string | null;
  hasParsedData: boolean;
  onGoAnalysis: () => void;
};

export default function ImportPage(props: ImportPageProps): React.ReactElement {
  const {
    importedFiles,
    onImport,
    onClearImport,
    isParsing,
    parseError,
    infoMessage,
    hasParsedData,
    onGoAnalysis
  } = props;

  return (
    <section className="route-page">
      <div className="route-page-header">
        <div>
          <p className="eyebrow route-eyebrow">Page</p>
          <h2>Import</h2>
          <p className="subtle-text">Upload Mobly summaries to start analysis.</p>
        </div>
        <button
          type="button"
          className="button button-primary"
          onClick={onGoAnalysis}
          disabled={!hasParsedData || isParsing}
        >
          Go to Analysis
        </button>
      </div>
      <FileUploadPanel
        importedFiles={importedFiles}
        onImport={onImport}
        onClearImport={onClearImport}
        isParsing={isParsing}
        parseError={parseError}
        infoMessage={infoMessage}
      />
    </section>
  );
}
