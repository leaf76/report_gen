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

## GitHub Releases

- GitHub Releases now publish Linux `AppImage`, `deb`, and `rpm` artifacts.
- For Linux, prefer the `AppImage` asset if you want a direct download that runs without installing a package.

```bash
chmod +x Report.Generator_<version>_<arch>.AppImage
./Report.Generator_<version>_<arch>.AppImage
```

- Release tags and bundle versions must match. For example, tag `v0.1.7` produces assets with version `0.1.7`.

## Technical Notes

- YAML parsing, aggregation, and Excel export are implemented in Rust commands.
- Frontend uses `@tauri-apps/api` `invoke(...)` instead of HTTP calls.
- Export requires absolute local paths for template and output files.
