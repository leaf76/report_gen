"""Tkinter UI for browsing automation test summaries."""

from __future__ import annotations

import subprocess
import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Dict, Iterable, Optional, Sequence

from . import data_loader, exporter, stats, ui_helpers, view_model
from .layout import compute_exec_tree_widths, compute_group_tree_widths
from .models import TestExecution


class ReportApp:
    """Main application window."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Automation Test Summary Browser")
        self.root.geometry("1100x700")
        self.root.minsize(720, 480)

        self.summary = None
        self.loaded_paths: list[Path] = []
        self.executions_by_base: dict[str, list[TestExecution]] = {}
        self.group_items: Dict[str, view_model.GroupRow] = {}
        self.execution_items: Dict[str, TestExecution] = {}
        self.default_sheet_name = "Single-Point A_BT+B_BT"
        self.default_column = "d"
        self.default_debug_mode = False
        self.fill_report_script: Path | None = self._detect_default_script()
        self.group_rows: list[view_model.GroupRow] = []
        self.group_sort_states: dict[str, bool] = {}
        self.current_group_latency_summary: dict[str, float] = {}

        # Resize/Configure guards to avoid feedback loops (especially on Linux)
        self._group_resize_job = None  # type: Optional[str]
        self._exec_resize_job = None   # type: Optional[str]
        self._topbar_resize_job = None # type: Optional[str]
        self._group_last_widths: dict[str, int] = {}
        self._exec_last_widths: dict[str, int] = {}
        self._last_wraplength: Optional[int] = None

        self._init_style()
        self._create_menu()
        self._build_layout()
        self._configure_exit_handlers()

    def _detect_default_script(self) -> Path | None:
        candidate_dirs: list[Path] = []
        if getattr(sys, "_MEIPASS", None):
            candidate_dirs.append(Path(sys._MEIPASS))
        if getattr(sys, "executable", None):
            candidate_dirs.append(Path(sys.executable).resolve().parent)
        candidate_dirs.append(Path(__file__).resolve().parent.parent)

        for base_dir in candidate_dirs:
            par_candidate = base_dir / "fill_report.par"
            if par_candidate.exists():
                return par_candidate
            py_candidate = base_dir / "fill_report.py"
            if py_candidate.exists():
                return py_candidate
        return None

    def _init_style(self) -> None:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")

    def _create_menu(self) -> None:
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(
            label="Open Summaries...",
            command=self.on_open_summary,
        )
        file_menu.add_command(
            label="Export to Template...",
            command=self.on_export_to_template,
        )
        file_menu.add_command(
            label="Select fill_report script...",
            command=self.on_select_fill_report_script,
        )
        file_menu.add_command(
            label="Copy Problem Tests",
            command=self.on_copy_problem_tests,
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)
        self.menubar = menubar

    def _build_layout(self) -> None:
        control_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        control_frame.pack(fill=tk.X)

        open_button = ttk.Button(
            control_frame, text="Open Summaries...", command=self.on_open_summary
        )
        open_button.grid(row=0, column=0, sticky=tk.W)

        self.file_label = ttk.Label(control_frame, text="No file loaded", wraplength=480)
        self.file_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        self.summary_label = ttk.Label(
            control_frame,
            text="",
            font=("TkDefaultFont", 10, "bold"),
            foreground="#2f4f4f",
        )
        self.summary_label.grid(row=0, column=2, sticky=tk.E)

        control_frame.columnconfigure(1, weight=1)

        main_pane = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_pane)
        right_pane = ttk.Panedwindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(left_frame, weight=2)
        main_pane.add(right_pane, weight=3)

        # Keep references for state restore/save
        self.main_pane = main_pane
        self.right_pane = right_pane

        group_frame = ttk.LabelFrame(left_frame, text="Grouped Results")
        group_frame.pack(fill=tk.BOTH, expand=True)

        right_top = ttk.Frame(right_pane)
        right_bottom = ttk.Frame(right_pane)
        right_pane.add(right_top, weight=2)
        right_pane.add(right_bottom, weight=3)

        execution_frame = ttk.LabelFrame(right_top, text="Executions")
        execution_frame.pack(fill=tk.BOTH, expand=True)

        details_frame = ttk.LabelFrame(right_bottom, text="Details")
        details_frame.pack(fill=tk.BOTH, expand=True)

        self.group_tree = self._create_group_tree(group_frame)
        self.execution_tree = self._create_execution_tree(execution_frame)

        # Responsive behavior bindings
        self._install_responsive_layout(control_frame)

        # Compute initial sizes after widgets are realized
        self.root.after(0, self._update_top_bar_wraplength)
        self.root.after(0, self._auto_size_group_tree)
        self.root.after(0, self._auto_size_execution_tree)
        self.root.after(0, self._restore_layout_state)

        self.details_text = tk.Text(
            details_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=8,
            font=("TkFixedFont", 10),
        )
        detail_scrollbar = ttk.Scrollbar(
            details_frame, orient=tk.VERTICAL, command=self.details_text.yview
        )
        self.details_text.configure(yscrollcommand=detail_scrollbar.set)
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)

    def _create_group_tree(self, parent: ttk.Misc) -> ttk.Treeview:
        columns = (
            "test",
            "total",
            "pass",
            "fail",
            "error",
            "skip",
            "unknown",
            "error_rate",
            "result",
        )
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        headings = {
            "test": "Test",
            "total": "Total",
            "pass": "PASS",
            "fail": "FAIL",
            "error": "ERROR",
            "skip": "SKIP",
            "unknown": "UNKNOWN",
            "error_rate": "Error Rate",
            "result": "Result",
        }
        widths = {
            "test": 260,
            "total": 60,
            "pass": 60,
            "fail": 60,
            "error": 70,
            "skip": 70,
            "unknown": 80,
            "error_rate": 100,
            "result": 100,
        }
        for column in columns:
            tree.heading(
                column,
                text=headings[column],
                command=lambda col=column: self._on_group_heading_click(col),
            )
            anchor = tk.W if column == "test" else tk.CENTER
            tree.column(column, width=widths[column], anchor=anchor, stretch=False)
        tree.grid(row=0, column=0, sticky="nsew")

        vscrollbar = ttk.Scrollbar(
            container, orient=tk.VERTICAL, command=tree.yview
        )
        tree.configure(yscrollcommand=vscrollbar.set)
        vscrollbar.grid(row=0, column=1, sticky="ns")

        hscrollbar = ttk.Scrollbar(
            container, orient=tk.HORIZONTAL, command=tree.xview
        )
        tree.configure(xscrollcommand=hscrollbar.set)
        hscrollbar.grid(row=1, column=0, sticky="ew")

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # Keep reference for responsive sizing
        self._group_container = container
        self._group_tree_base_widths = widths

        # Bind container size changes to auto-size columns (debounced)
        container.bind("<Configure>", self._queue_group_resize)

        tree.bind("<<TreeviewSelect>>", self.on_group_select)
        return tree

    def _create_execution_tree(self, parent: ttk.Misc) -> ttk.Treeview:
        columns = ("iteration", "result", "begin", "end")
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        headings = {
            "iteration": "Iteration",
            "result": "Result",
            "begin": "Begin",
            "end": "End",
        }
        widths = {
            "iteration": 80,
            "result": 80,
            "begin": 200,
            "end": 200,
        }
        for column in columns:
            tree.heading(column, text=headings[column])
            anchor = tk.CENTER if column in {"iteration", "result"} else tk.W
            tree.column(column, width=widths[column], anchor=anchor, stretch=False)
        tree.grid(row=0, column=0, sticky="nsew")

        vscrollbar = ttk.Scrollbar(
            container, orient=tk.VERTICAL, command=tree.yview
        )
        tree.configure(yscrollcommand=vscrollbar.set)
        vscrollbar.grid(row=0, column=1, sticky="ns")

        hscrollbar = ttk.Scrollbar(
            container, orient=tk.HORIZONTAL, command=tree.xview
        )
        tree.configure(xscrollcommand=hscrollbar.set)
        hscrollbar.grid(row=1, column=0, sticky="ew")

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # Keep reference for responsive sizing
        self._exec_container = container
        self._exec_tree_base_widths = widths

        # Bind container size changes to auto-size columns (debounced)
        container.bind("<Configure>", self._queue_exec_resize)

        tree.bind("<<TreeviewSelect>>", self.on_execution_select)
        return tree

    # ----- Responsive helpers -----
    def _install_responsive_layout(self, control_frame: ttk.Frame) -> None:
        # Update wraplength of file label when the top bar changes size (debounced)
        control_frame.bind("<Configure>", self._queue_topbar_resize)

    def _update_top_bar_wraplength(self) -> None:
        try:
            width = self.file_label.winfo_toplevel().winfo_width()
        except Exception:
            return
        # Reserve space for button and summary label; clamp sensible bounds
        available = max(200, width - 420)
        if self._last_wraplength == available:
            return
        self._last_wraplength = available
        self.file_label.configure(wraplength=available)

    def _queue_topbar_resize(self, event: tk.Event) -> None:  # pragma: no cover - UI binding
        if self._topbar_resize_job is not None:
            try:
                self.root.after_cancel(self._topbar_resize_job)
            except Exception:
                pass
        self._topbar_resize_job = self.root.after(50, self._run_topbar_resize)

    def _run_topbar_resize(self) -> None:
        self._topbar_resize_job = None
        self._update_top_bar_wraplength()

    def _auto_size_group_tree(self) -> None:
        if not hasattr(self, "_group_container"):
            return
        container_w = self._group_container.winfo_width() or 0
        if container_w <= 100:
            return
        widths = dict(self._group_tree_base_widths)
        fixed_cols = [
            "total",
            "pass",
            "fail",
            "error",
            "skip",
            "unknown",
            "error_rate",
            "result",
        ]
        new_widths = compute_group_tree_widths(container_w, widths)
        if new_widths == self._group_last_widths:
            return
        self._group_last_widths = dict(new_widths)

        self.group_tree.column("test", width=new_widths["test"])
        for col in fixed_cols:
            self.group_tree.column(col, width=new_widths[col])

    def _auto_size_execution_tree(self) -> None:
        if not hasattr(self, "_exec_container"):
            return
        container_w = self._exec_container.winfo_width() or 0
        if container_w <= 100:
            return
        widths = dict(self._exec_tree_base_widths)
        fixed_cols = ["iteration", "result"]
        new_widths_exec = compute_exec_tree_widths(container_w, widths)
        if new_widths_exec == self._exec_last_widths:
            return
        self._exec_last_widths = dict(new_widths_exec)

        self.execution_tree.column("begin", width=new_widths_exec["begin"])
        self.execution_tree.column("end", width=new_widths_exec["end"])
        for col in fixed_cols:
            self.execution_tree.column(col, width=new_widths_exec[col])

    def _queue_group_resize(self, event: tk.Event) -> None:  # pragma: no cover - UI binding
        if self._group_resize_job is not None:
            try:
                self.root.after_cancel(self._group_resize_job)
            except Exception:
                pass
        self._group_resize_job = self.root.after(50, self._run_group_resize)

    def _run_group_resize(self) -> None:
        self._group_resize_job = None
        self._auto_size_group_tree()

    def _queue_exec_resize(self, event: tk.Event) -> None:  # pragma: no cover - UI binding
        if self._exec_resize_job is not None:
            try:
                self.root.after_cancel(self._exec_resize_job)
            except Exception:
                pass
        self._exec_resize_job = self.root.after(50, self._run_exec_resize)

    def _run_exec_resize(self) -> None:
        self._exec_resize_job = None
        self._auto_size_execution_tree()

    # ----- Persist/restore layout -----
    def _state_file_path(self) -> Path:
        return Path.home() / ".report_gen_ui.json"

    def _configure_exit_handlers(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def on_exit(self) -> None:
        self._on_close()

    def _on_close(self) -> None:
        try:
            self._save_layout_state()
        except Exception:
            pass
        # Ensure the window is destroyed (quit would leave event loop)
        try:
            self.root.destroy()
        except Exception:
            pass

    def _restore_layout_state(self) -> None:
        state_path = self._state_file_path()
        if not state_path.exists():
            return
        try:
            with state_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        # Need realized sizes to compute pixels from ratios
        main_w = max(1, self.main_pane.winfo_width())
        right_h = max(1, self.right_pane.winfo_height())
        if main_w <= 1 or right_h <= 1:
            # Try again shortly if not ready
            self.root.after(50, self._restore_layout_state)
            return

        try:
            m_ratio = float(data.get("main_ratio", 0.4))
            r_ratio = float(data.get("right_ratio", 0.5))
            m_pos = int(max(80, min(main_w - 80, m_ratio * main_w)))
            r_pos = int(max(60, min(right_h - 60, r_ratio * right_h)))
            self.main_pane.sashpos(0, m_pos)
            self.right_pane.sashpos(0, r_pos)
        except Exception:
            pass

    def _save_layout_state(self) -> None:
        try:
            main_w = max(1, self.main_pane.winfo_width())
            right_h = max(1, self.right_pane.winfo_height())
            m_pos = max(1, int(self.main_pane.sashpos(0)))
            r_pos = max(1, int(self.right_pane.sashpos(0)))
            data = {
                "main_ratio": max(0.05, min(0.95, m_pos / main_w)),
                "right_ratio": max(0.1, min(0.9, r_pos / right_h)),
            }
            state_path = self._state_file_path()
            with state_path.open("w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def on_open_summary(self) -> None:
        file_paths = filedialog.askopenfilenames(
            title="Open test summaries",
            filetypes=(("YAML files", "*.yaml *.yml"), ("All files", "*.*")),
        )
        if not file_paths:
            return
        paths = [Path(path) for path in file_paths]
        self.load_summaries(paths)

    def on_select_fill_report_script(self) -> None:
        initial_dir = None
        if self.fill_report_script is not None:
            initial_dir = str(self.fill_report_script.parent)
        script_path = filedialog.askopenfilename(
            title="Select fill_report script",
            filetypes=(
                ("Executable", "*.par *.py"),
                ("All files", "*.*"),
            ),
            initialdir=initial_dir,
        )
        if not script_path:
            return
        path_obj = Path(script_path).expanduser().resolve()
        if not path_obj.exists():
            messagebox.showerror(
                "Invalid script",
                f"File not found:\n{path_obj}",
            )
            return
        self.fill_report_script = path_obj

    def on_copy_problem_tests(self) -> None:
        if not self.group_rows:
            messagebox.showinfo(
                "No data",
                "Please load test summaries before copying problem tests.",
            )
            return

        problem_tests = view_model.collect_problem_tests(self.group_rows)
        if not problem_tests:
            messagebox.showinfo(
                "No issues",
                "All grouped tests are PASS.",
            )
            return

        joined = ",".join(problem_tests)
        self.root.clipboard_clear()
        self.root.clipboard_append(joined)
        self.root.update_idletasks()
        messagebox.showinfo(
            "Copied",
            f"Problem tests copied to clipboard:\n{joined}",
        )

    def _on_group_heading_click(self, column: str) -> None:
        ascending = not self.group_sort_states.get(column, False)
        self.group_sort_states[column] = ascending

        key_func = self._group_sort_key(column)
        if key_func is None:
            return

        self.group_rows.sort(key=key_func, reverse=not ascending)
        self._populate_group_tree(self.group_rows)

    def _group_sort_key(self, column: str):
        if column == "test":
            return lambda row: row.base_name
        if column == "total":
            return lambda row: row.total
        if column in {"pass", "fail", "error", "skip", "unknown"}:
            result_name = column.upper()
            return lambda row: row.by_result.get(result_name, 0)
        if column == "error_rate":
            return lambda row: row.error_rate
        if column == "result":
            order = {"ERROR": 0, "FAIL": 1, "UNKNOWN": 2, "SKIP": 3, "PASS": 4}
            return lambda row: order.get(row.group_result.upper(), 5)
        return None

    def on_export_to_template(self) -> None:
        if not self.loaded_paths:
            messagebox.showinfo(
                "No summaries",
                "Please open at least one test summary before exporting.",
            )
            return

        template_path = filedialog.askopenfilename(
            title="Select report template",
            filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*")),
        )
        if not template_path:
            return

        template_path_obj = Path(template_path)
        default_name = f"{template_path_obj.stem}_output.xlsx"
        save_path = filedialog.asksaveasfilename(
            title="Save filled report as",
            defaultextension=".xlsx",
            initialdir=str(template_path_obj.parent),
            initialfile=default_name,
            filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*")),
        )
        if not save_path:
            return
        output_path = Path(save_path)

        sheet_name = simpledialog.askstring(
            "Sheet Name",
            "Enter the target sheet name:",
            initialvalue=self.default_sheet_name,
            parent=self.root,
        )
        if sheet_name is None or not sheet_name.strip():
            return

        column = simpledialog.askstring(
            "Start Column",
            "Enter the start column (e.g. D):",
            initialvalue=self.default_column,
            parent=self.root,
        )
        if column is None or not column.strip():
            return

        default_button = "yes" if self.default_debug_mode else "no"
        debug_mode = messagebox.askyesno(
            "Debug Mode",
            "Enable debug mode for fill_report?",
            icon=messagebox.QUESTION,
            default=default_button,
        )

        self.default_sheet_name = sheet_name.strip()
        self.default_column = column.strip()
        self.default_debug_mode = debug_mode

        try:
            script_path = self._ensure_script_path()
            if script_path is None:
                return
            prepared_path = exporter.prepare_output_file(
                template_path_obj, output_path
            )
            config = exporter.ExportConfig(
                template_path=prepared_path,
                sheet_name=self.default_sheet_name,
                column=self.default_column,
                debug_mode=self.default_debug_mode,
                script_path=script_path,
            )
            exporter.export_summaries(config, self.loaded_paths)
        except exporter.ExportError as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        except subprocess.CalledProcessError as exc:
            messagebox.showerror(
                "Export failed",
                f"fill_report exited with status {exc.returncode}",
            )
            return

        messagebox.showinfo(
            "Export complete",
            f"Export finished. Output saved to:\n{prepared_path}",
        )

    def _ensure_script_path(self) -> Path | None:
        if self.fill_report_script and self.fill_report_script.exists():
            return self.fill_report_script

        messagebox.showinfo(
            "Script not set",
            "Please select the fill_report script to use (e.g. fill_report.par).",
        )
        self.on_select_fill_report_script()
        if self.fill_report_script and self.fill_report_script.exists():
            return self.fill_report_script
        messagebox.showerror(
            "Export aborted",
            "fill_report script not provided.",
        )
        return None

    def load_summaries(self, paths: Sequence[Path]) -> None:
        if not paths:
            return
        try:
            summary = data_loader.parse_multiple_test_summaries(paths)
        except Exception as exc:  # pragma: no cover - interactive feedback
            messagebox.showerror("Failed to load", str(exc))
            return

        self.summary = summary
        self.loaded_paths = [path for path in paths]
        self.file_label.configure(text=self._format_loaded_paths(self.loaded_paths))
        self.executions_by_base = self._index_executions(summary.executions)
        totals = stats.compute_result_totals(summary.executions)
        self.summary_label.configure(text=ui_helpers.build_overall_summary_text(totals))
        self.group_rows = view_model.build_group_rows(summary.executions)
        self.group_sort_states.clear()
        self._populate_group_tree(self.group_rows)
        self._clear_execution_tree()
        self._set_details("")

    def _format_loaded_paths(self, paths: Sequence[Path]) -> str:
        if len(paths) == 1:
            return str(paths[0])
        joined = "; ".join(str(path) for path in paths[:3])
        if len(paths) > 3:
            joined += f" ... (+{len(paths) - 3} more)"
        return joined

    def _populate_group_tree(self, group_rows: Iterable[view_model.GroupRow]) -> None:
        self.group_tree.delete(*self.group_tree.get_children())
        self.group_items = {}
        self.group_rows = list(group_rows)
        for row in self.group_rows:
            values = ui_helpers.group_row_to_tree_values(row)
            item_id = self.group_tree.insert("", tk.END, iid=row.base_name, values=values)
            self.group_items[item_id] = row

    def _index_executions(self, executions: Iterable[TestExecution]) -> dict[str, list[TestExecution]]:
        indexed: dict[str, list[TestExecution]] = {}
        for execution in executions:
            indexed.setdefault(execution.base_name, []).append(execution)
        for base, items in indexed.items():
            items.sort(
                key=lambda execution: (
                    execution.begin_time or -1,
                    execution.iteration if execution.iteration is not None else -1,
                )
            )
        return indexed

    def _clear_execution_tree(self) -> None:
        self.execution_tree.delete(*self.execution_tree.get_children())
        self.execution_items = {}
        self.current_group_latency_summary = {}

    def on_group_select(self, event: tk.Event) -> None:  # pragma: no cover - UI binding
        selection = self.group_tree.selection()
        if not selection:
            return
        item_id = selection[0]
        row = self.group_items.get(item_id)
        if not row:
            return
        executions = self.executions_by_base.get(row.base_name, [])
        self._populate_execution_tree(row.base_name, executions, row.latency_averages)

    def _populate_execution_tree(
        self,
        base_name: str,
        executions: Iterable[TestExecution],
        latency_summary: Optional[dict[str, float]] = None,
    ) -> None:
        self._clear_execution_tree()
        self.current_group_latency_summary = latency_summary or {}

        for execution in executions:
            values = ui_helpers.build_execution_summary_values(execution)
            item_id = self.execution_tree.insert("", tk.END, values=values)
            self.execution_items[item_id] = execution
        if executions:
            first_item = next(iter(self.execution_tree.get_children()))
            self.execution_tree.selection_set(first_item)
            self.execution_tree.focus(first_item)
            self._show_execution_details(self.execution_items[first_item])
        else:
            summary_text = self._format_group_latency_summary()
            self._set_details(summary_text)

    def on_execution_select(self, event: tk.Event) -> None:  # pragma: no cover - UI binding
        selection = self.execution_tree.selection()
        if not selection:
            return
        item_id = selection[0]
        execution = self.execution_items.get(item_id)
        if execution:
            self._show_execution_details(execution)

    def _show_execution_details(self, execution: TestExecution) -> None:
        detail_text = ui_helpers.format_execution_details(execution)
        prefix = self._format_group_latency_summary()
        if prefix:
            combined = f"{prefix}\n\n{detail_text}"
        else:
            combined = detail_text
        self._set_details(combined)

    def _set_details(self, text: str) -> None:
        self.details_text.configure(state=tk.NORMAL)
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, text)
        self.details_text.configure(state=tk.DISABLED)

    def _format_group_latency_summary(self) -> str:
        if not self.current_group_latency_summary:
            return ""
        lines = ["Group Latency Averages:"]
        for key in sorted(self.current_group_latency_summary):
            value = self.current_group_latency_summary[key]
            lines.append(f"- {key}: {value:.3f}")
        return "\n".join(lines)


def run_app(initial_paths: Optional[Sequence[Path] | Path] = None) -> None:
    root = tk.Tk()
    app = ReportApp(root)
    if initial_paths:
        if isinstance(initial_paths, (list, tuple)):
            app.load_summaries(list(initial_paths))
        else:
            app.load_summaries([initial_paths])
    root.mainloop()


if __name__ == "__main__":  # pragma: no cover - manual launch
    run_app()
