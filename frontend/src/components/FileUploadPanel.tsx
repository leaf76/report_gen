import React from "react";

type ImportedFile = {
  name: string;
  contentHash: string;
  controllerInfo: unknown | null;
};

type FileUploadPanelProps = {
  importedFiles: ImportedFile[];
  onImport: (files: File[]) => void;
  onClearImport: () => void;
  isParsing: boolean;
  parseError: string | null;
  infoMessage: string | null;
};

type KeyValueEntry = {
  key: string;
  value: string;
};

type ControllerDeviceView = {
  id: string;
  serial: string;
  model: string;
  version: string;
  restEntries: KeyValueEntry[];
};

type ControllerInfoView = {
  devices: ControllerDeviceView[];
  fallbackText: string | null;
  isMissing: boolean;
};

type NormalizedImportedFile = ImportedFile & {
  view: ControllerInfoView;
};

const SERIAL_KEYS = new Set(["serial", "serialnumber", "sn", "deviceserial"]);
const MODEL_KEYS = new Set(["model", "devicemodel", "productname", "product"]);
const VERSION_KEYS = new Set([
  "version",
  "firmwareversion",
  "buildversion",
  "buildid",
  "buildversionincremental"
]);
const BUILD_INFO_KEYS = new Set(["buildinfo", "build"]);
const USER_ADDED_KEYS = new Set(["useraddedinfo", "userinfo", "meta"]);

function normalizeKey(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function keyLabel(value: string): string {
  const normalized = value.replace(/[_-]+/g, " ").trim();
  if (!normalized) {
    return "Unknown";
  }
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "N/A";
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function findValueByAliases(
  record: Record<string, unknown>,
  aliases: Set<string>
): unknown | undefined {
  for (const [key, value] of Object.entries(record)) {
    if (aliases.has(normalizeKey(key))) {
      return value;
    }
  }
  return undefined;
}

function getNestedRecordByAliases(
  record: Record<string, unknown>,
  aliases: Set<string>
): Record<string, unknown> | null {
  const nestedValue = findValueByAliases(record, aliases);
  if (isRecord(nestedValue)) {
    return nestedValue;
  }
  return null;
}

function getVersion(record: Record<string, unknown>): string {
  const directVersion = findValueByAliases(record, VERSION_KEYS);
  if (directVersion !== undefined) {
    return formatValue(directVersion);
  }

  const buildInfo = getNestedRecordByAliases(record, BUILD_INFO_KEYS);
  if (!buildInfo) {
    return "N/A";
  }

  const incremental = findValueByAliases(buildInfo, new Set(["buildversionincremental"]));
  if (incremental !== undefined) {
    return formatValue(incremental);
  }

  const buildId = findValueByAliases(buildInfo, new Set(["buildid"]));
  if (buildId !== undefined) {
    return formatValue(buildId);
  }

  const sdk = findValueByAliases(buildInfo, new Set(["buildversionsdk", "sdk"]));
  if (sdk !== undefined) {
    return `SDK ${formatValue(sdk)}`;
  }

  return "N/A";
}

function collectRestEntries(record: Record<string, unknown>): KeyValueEntry[] {
  const entries: KeyValueEntry[] = [];
  const excludedKeys = new Set<string>();

  for (const key of Object.keys(record)) {
    const normalized = normalizeKey(key);
    if (SERIAL_KEYS.has(normalized) || MODEL_KEYS.has(normalized) || VERSION_KEYS.has(normalized)) {
      excludedKeys.add(key);
    }
  }

  const buildInfo = getNestedRecordByAliases(record, BUILD_INFO_KEYS);
  if (buildInfo) {
    const buildId = findValueByAliases(buildInfo, new Set(["buildid"]));
    if (buildId !== undefined) {
      entries.push({ key: "Build ID", value: formatValue(buildId) });
    }
    const sdk = findValueByAliases(buildInfo, new Set(["buildversionsdk", "sdk"]));
    if (sdk !== undefined) {
      entries.push({ key: "SDK", value: formatValue(sdk) });
    }
    const product = findValueByAliases(buildInfo, new Set(["productname", "buildproduct"]));
    if (product !== undefined) {
      entries.push({ key: "Product", value: formatValue(product) });
    }
  }

  const userAdded = getNestedRecordByAliases(record, USER_ADDED_KEYS);
  if (userAdded) {
    const sassDevice = findValueByAliases(userAdded, new Set(["sassdevice"]));
    if (sassDevice !== undefined) {
      entries.push({ key: "SASS Device", value: formatValue(sassDevice) });
    }
    const phoneNumber = findValueByAliases(userAdded, new Set(["phonenumber"]));
    if (phoneNumber !== undefined) {
      entries.push({ key: "Phone Number", value: formatValue(phoneNumber) });
    }
    const testLea = findValueByAliases(userAdded, new Set(["testlea"]));
    if (testLea !== undefined) {
      entries.push({ key: "Test LEA", value: formatValue(testLea) });
    }
  }

  for (const [key, value] of Object.entries(record)) {
    if (excludedKeys.has(key)) {
      continue;
    }
    const normalized = normalizeKey(key);
    if (BUILD_INFO_KEYS.has(normalized) || USER_ADDED_KEYS.has(normalized)) {
      continue;
    }
    entries.push({
      key: keyLabel(key),
      value: formatValue(value)
    });
  }

  const deduped = new Map<string, KeyValueEntry>();
  for (const entry of entries) {
    const dedupeKey = `${entry.key}|${entry.value}`;
    if (!deduped.has(dedupeKey)) {
      deduped.set(dedupeKey, entry);
    }
  }

  return Array.from(deduped.values());
}

function buildDeviceView(record: Record<string, unknown>, index: number): ControllerDeviceView {
  const serialValue = findValueByAliases(record, SERIAL_KEYS);
  const modelValue = findValueByAliases(record, MODEL_KEYS);
  const serial = formatValue(serialValue);
  const model = formatValue(modelValue);
  const version = getVersion(record);

  return {
    id: `${index}-${serial}-${model}-${version}`,
    serial,
    model,
    version,
    restEntries: collectRestEntries(record)
  };
}

function normalizeControllerInfo(controllerInfo: unknown): ControllerInfoView {
  if (controllerInfo === null || controllerInfo === undefined) {
    return { devices: [], fallbackText: null, isMissing: true };
  }

  if (Array.isArray(controllerInfo)) {
    const deviceRecords = controllerInfo.filter(isRecord);
    if (deviceRecords.length > 0) {
      return {
        devices: deviceRecords.map((record, index) => buildDeviceView(record, index)),
        fallbackText: null,
        isMissing: false
      };
    }
    return { devices: [], fallbackText: formatValue(controllerInfo), isMissing: false };
  }

  if (isRecord(controllerInfo)) {
    return {
      devices: [buildDeviceView(controllerInfo, 0)],
      fallbackText: null,
      isMissing: false
    };
  }

  return { devices: [], fallbackText: formatValue(controllerInfo), isMissing: false };
}

export default function FileUploadPanel(props: FileUploadPanelProps): React.ReactElement {
  const { importedFiles, onImport, onClearImport, isParsing, parseError, infoMessage } = props;

  const normalizedFiles = React.useMemo<NormalizedImportedFile[]>(
    () =>
      importedFiles.map((file) => ({
        ...file,
        view: normalizeControllerInfo(file.controllerInfo)
      })),
    [importedFiles]
  );

  const overview = React.useMemo(() => {
    const uniqueControllers = new Set<string>();
    const serialVersions = new Map<string, Set<string>>();
    let missingFiles = 0;

    for (const file of normalizedFiles) {
      if (file.view.isMissing) {
        missingFiles += 1;
      }
      for (const device of file.view.devices) {
        const serialKey = device.serial !== "N/A" ? device.serial : `${device.model}|${device.version}`;
        uniqueControllers.add(serialKey);

        if (device.serial === "N/A") {
          continue;
        }
        if (!serialVersions.has(device.serial)) {
          serialVersions.set(device.serial, new Set<string>());
        }
        serialVersions.get(device.serial)?.add(`${device.model}|${device.version}`);
      }
    }

    const conflictCount = Array.from(serialVersions.values()).filter((values) => values.size > 1).length;

    return {
      uniqueControllerCount: uniqueControllers.size,
      missingFiles,
      conflictCount
    };
  }, [normalizedFiles]);

  const onInputChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
    const selected = event.target.files ? Array.from(event.target.files) : [];
    if (selected.length > 0) {
      onImport(selected);
    }
    event.target.value = "";
  };

  return (
    <section className="panel upload-panel">
      <div className="panel-title-row">
        <h2>Input Summaries</h2>
        <div className="panel-actions">
          <button
            type="button"
            className="button"
            onClick={onClearImport}
            disabled={isParsing || importedFiles.length === 0}
          >
            Clear Imports
          </button>
        </div>
      </div>
      <div className="upload-zones">
        <div className={`upload-zone upload-zone-import ${isParsing ? "is-busy" : ""}`}>
          <p className="upload-zone-title">Import Zone</p>
          <label className="file-input-label file-dropzone">
            <span className="dropzone-main">Choose one or more Mobly summary YAML files</span>
            <span className="dropzone-sub">Parsing starts automatically and appends to current results.</span>
            <input
              type="file"
              accept=".yaml,.yml"
              multiple
              onChange={onInputChange}
              disabled={isParsing}
            />
          </label>
          {isParsing ? <p className="subtle-text">Parsing selected files...</p> : null}
        </div>

        <div className="upload-zone upload-zone-list">
          <div className="upload-zone-list-header">
            <p className="upload-zone-title">Imported Files</p>
            <span className="file-count-badge">{normalizedFiles.length}</span>
          </div>
          {normalizedFiles.length > 0 ? (
            <>
              <section className="controller-overview" aria-label="Controller overview">
                <article className="controller-overview-card">
                  <p className="controller-overview-label">Unique Controllers</p>
                  <strong className="controller-overview-value">{overview.uniqueControllerCount}</strong>
                </article>
                <article className="controller-overview-card">
                  <p className="controller-overview-label">Missing Controller Info</p>
                  <strong className="controller-overview-value">{overview.missingFiles}</strong>
                </article>
                <article className="controller-overview-card">
                  <p className="controller-overview-label">Potential Conflicts</p>
                  <strong className="controller-overview-value">{overview.conflictCount}</strong>
                </article>
              </section>

              <ul className="file-list">
                {normalizedFiles.map((file) => (
                  <li key={file.contentHash}>
                    <div className="imported-file-header">
                      <p className="imported-file-name">{file.name}</p>
                      <span
                        className={`controller-state-badge ${file.view.isMissing ? "missing" : "complete"}`}
                      >
                        {file.view.isMissing ? "Missing" : "Complete"}
                      </span>
                    </div>
                    <div className="imported-file-controller">
                      <p className="imported-file-controller-title">Controller Info</p>
                      {file.view.devices.length > 0 ? (
                        <div className="controller-device-list">
                          {file.view.devices.map((device, index) => (
                            <article key={device.id} className="controller-device-card">
                              <p className="controller-device-title">Device {index + 1}</p>
                              <div className="controller-chip-row">
                                <span className="controller-chip">
                                  <span className="controller-chip-key">Serial</span>
                                  <span className="controller-chip-value">{device.serial}</span>
                                </span>
                                <span className="controller-chip">
                                  <span className="controller-chip-key">Model</span>
                                  <span className="controller-chip-value">{device.model}</span>
                                </span>
                                <span className="controller-chip">
                                  <span className="controller-chip-key">Version</span>
                                  <span className="controller-chip-value">{device.version}</span>
                                </span>
                              </div>
                              {device.restEntries.length > 0 ? (
                                <details className="controller-more">
                                  <summary>More</summary>
                                  <dl className="controller-info-kv-list">
                                    {device.restEntries.map((entry) => (
                                      <div
                                        key={`${device.id}-${entry.key}-${entry.value}`}
                                        className="controller-info-kv-row"
                                      >
                                        <dt>{entry.key}</dt>
                                        <dd>{entry.value}</dd>
                                      </div>
                                    ))}
                                  </dl>
                                </details>
                              ) : null}
                            </article>
                          ))}
                        </div>
                      ) : file.view.fallbackText ? (
                        <p className="subtle-text">{file.view.fallbackText}</p>
                      ) : (
                        <p className="subtle-text">N/A</p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="subtle-text">No files imported yet.</p>
          )}
        </div>
      </div>

      {infoMessage ? <p className="success-text">{infoMessage}</p> : null}
      {parseError ? <p className="error-text">{parseError}</p> : null}
    </section>
  );
}
