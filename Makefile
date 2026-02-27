.PHONY: frontend-dev frontend-build desktop-dev desktop-build rust-test rust-fmt-check clean

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

desktop-dev:
	cd frontend && npm run tauri:dev

desktop-build:
	cd frontend && npm run tauri:build

rust-test:
	cd frontend/src-tauri && cargo test -- --nocapture

rust-fmt-check:
	cd frontend/src-tauri && cargo fmt --check

clean:
	rm -rf frontend/dist frontend/src-tauri/target
