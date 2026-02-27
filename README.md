# report_gen (Desktop / Tauri)

`report_gen` is now implemented as a desktop application:
- UI: React + Vite (`frontend/`)
- Desktop runtime: Tauri + Rust (`frontend/src-tauri/`)

Core flow:
1. Load Mobly summary YAML files.
2. Focus FAIL/ERROR test groups quickly.
3. Inspect executions and detail payloads.
4. Export to Excel template directly from desktop.

## Quick Start

### 1) Install frontend + Tauri CLI dependencies

```bash
cd frontend
npm install
```

### 2) Run desktop app in dev mode

```bash
cd frontend
npm run tauri:dev
```

### 3) Build desktop app

```bash
cd frontend
npm run tauri:build
```

## Technical Notes

- YAML parsing, aggregation, and Excel export are implemented in Rust commands.
- Frontend uses `@tauri-apps/api` `invoke(...)` instead of HTTP calls.
- Export requires absolute local paths for template and output files.
