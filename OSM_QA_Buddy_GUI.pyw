"""Normal Windows desktop frontend for OSM QA Buddy's JOSM GUI bridge.

The GUI is intentionally thin: it owns user interaction and launches the
existing gui_pipeline.py commands. JOSM remains the human validation engine.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

REPO_DIR = Path(__file__).resolve().parent
SESSION_FILE = REPO_DIR / ".gui_session.txt"
RUNS_DIR = REPO_DIR / "gui_runs"


def find_osmium() -> str | None:
    found = shutil.which("osmium")
    if found:
        return found
    candidates = []
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        candidates.append(Path(conda_prefix) / "Library" / "bin" / "osmium.exe")
    user = Path(os.environ.get("USERPROFILE", str(Path.home())))
    candidates.extend(
        [
            user / "anaconda3" / "envs" / "qabot" / "Library" / "bin" / "osmium.exe",
            user / "miniconda3" / "envs" / "qabot" / "Library" / "bin" / "osmium.exe",
        ]
    )
    for path in candidates:
        if path.is_file():
            return str(path)
    return None


def python_ok() -> bool:
    return sys.version_info >= (3, 12)


class QABuddyApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("OSM QA Buddy")
        self.geometry("760x600")
        self.minsize(700, 540)
        self.configure(padx=18, pady=16)

        self.pbf_var = tk.StringVar()
        self.tasks_var = tk.StringVar()
        self.xml_var = tk.StringVar()
        self.output_var = tk.StringVar(value="No run started yet")
        self.status_var = tk.StringVar(value="Ready")
        self.josm_ready = False
        self.latest_run: dict[str, str] = {}

        self._build_style()
        self._build_ui()
        self._load_session()
        self._refresh_status()

    def _build_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10))
        style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8))
        style.configure("Status.TLabel", padding=(8, 6))

    def _build_ui(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text="OSM QA Buddy", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="JOSM GUI Validation Bridge • normal Windows desktop interface",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 14))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        prepare = ttk.Frame(notebook, padding=16)
        validate = ttk.Frame(notebook, padding=16)
        finalize = ttk.Frame(notebook, padding=16)
        about = ttk.Frame(notebook, padding=16)
        notebook.add(prepare, text="1  Prepare")
        notebook.add(validate, text="2  Validate in JOSM")
        notebook.add(finalize, text="3  Finalize")
        notebook.add(about, text="About")
        self.notebook = notebook

        self._build_prepare(prepare)
        self._build_validate(validate)
        self._build_finalize(finalize)
        self._build_about(about)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", pady=(12, 0))
        ttk.Label(bottom, textvariable=self.status_var, style="Status.TLabel", anchor="w").pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(bottom, text="Exit", command=self.destroy).pack(side="right")

    def _path_row(self, parent, label, variable, command, filetypes) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=7)
        ttk.Label(row, text=label, width=16).pack(side="left", anchor="w")
        ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(row, text="Browse…", command=lambda: command(filetypes)).pack(side="right")

    def _build_prepare(self, parent) -> None:
        ttk.Label(parent, text="Start a new QA run", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            parent,
            text="Choose the OSM PBF and Task Grid. QA Buddy will prepare a clipped sample for normal JOSM validation.",
            wraplength=650,
        ).pack(anchor="w", pady=(4, 12))

        self._path_row(parent, "OSM PBF", self.pbf_var, self._choose_pbf, [("OSM PBF", "*.osm.pbf"), ("All files", "*.*")])
        self._path_row(
            parent,
            "Task Grid",
            self.tasks_var,
            self._choose_tasks,
            [("GeoJSON", "*.geojson"), ("JSON", "*.json"), ("All files", "*.*")],
        )

        ttk.Separator(parent).pack(fill="x", pady=16)
        ttk.Button(parent, text="Start QA Run", style="Action.TButton", command=self.start_prepare).pack(anchor="w")

        ttk.Label(parent, text="Current output folder:").pack(anchor="w", pady=(20, 3))
        ttk.Label(parent, textvariable=self.output_var, wraplength=650).pack(anchor="w")

        self.prepare_log = tk.Text(parent, height=12, wrap="word", state="disabled", font=("Consolas", 9))
        self.prepare_log.pack(fill="both", expand=True, pady=(12, 0))

    def _build_validate(self, parent) -> None:
        ttk.Label(parent, text="Validate the prepared sample in JOSM", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            parent,
            text="QA Buddy does not replace JOSM's validator. Open the prepared sample, run Shift+V, then save the Validation errors layer as XML.",
            wraplength=650,
        ).pack(anchor="w", pady=(4, 16))

        self.open_josm_button = ttk.Button(
            parent, text="Open sample.osm in JOSM", style="Action.TButton", command=self.open_sample
        )
        self.open_josm_button.pack(anchor="w")

        steps = (
            "1. In JOSM, run Validator with Shift+V.",
            "2. Review the Validation errors layer as normal.",
            "3. Save the validation results as XML.",
            "4. Return here and use the Finalize tab.",
        )
        box = ttk.LabelFrame(parent, text="Human validation checkpoint", padding=14)
        box.pack(fill="x", pady=20)
        for step in steps:
            ttk.Label(box, text=step).pack(anchor="w", pady=3)

        ttk.Label(parent, text="Prepared sample:").pack(anchor="w")
        self.sample_label = ttk.Label(parent, text="No sample prepared", wraplength=650)
        self.sample_label.pack(anchor="w", pady=(3, 0))

    def _build_finalize(self, parent) -> None:
        ttk.Label(parent, text="Finalize the QA run", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            parent,
            text="Select the XML exported by JOSM. QA Buddy will parse the native findings, attribute them to tasks, and generate the existing outputs.",
            wraplength=650,
        ).pack(anchor="w", pady=(4, 12))

        self._path_row(parent, "JOSM XML", self.xml_var, self._choose_xml, [("XML", "*.xml"), ("All files", "*.*")])
        ttk.Label(parent, text="Run output folder:").pack(anchor="w", pady=(12, 3))
        self.final_output_label = ttk.Label(parent, textvariable=self.output_var, wraplength=650)
        self.final_output_label.pack(anchor="w")

        ttk.Button(parent, text="Finalize QA Run", style="Action.TButton", command=self.start_finalize).pack(
            anchor="w", pady=(16, 10)
        )

        links = ttk.Frame(parent)
        links.pack(fill="x")
        self.report_button = ttk.Button(links, text="Open Report", command=self.open_report, state="disabled")
        self.report_button.pack(side="left", padx=(0, 8))
        self.map_button = ttk.Button(links, text="Open Map", command=self.open_map, state="disabled")
        self.map_button.pack(side="left")

        self.finalize_log = tk.Text(parent, height=14, wrap="word", state="disabled", font=("Consolas", 9))
        self.finalize_log.pack(fill="both", expand=True, pady=(12, 0))

    def _build_about(self, parent) -> None:
        ttk.Label(parent, text="Designed to stay boring", style="Section.TLabel").pack(anchor="w")
        text = (
            "This is a thin Windows frontend, not a replacement QA engine.\n\n"
            "• JOSM remains the validation engine.\n"
            "• gui_pipeline.py remains the workflow backend.\n"
            "• Existing GeoJSON, report, and map outputs are preserved.\n"
            "• No browser, server, database, or Electron layer is required.\n\n"
            "The goal is a normal desktop workflow without the black Command Prompt window."
        )
        ttk.Label(parent, text=text, justify="left", wraplength=650).pack(anchor="w", pady=(8, 20))

        self.dependency_label = ttk.Label(parent, justify="left", wraplength=650)
        self.dependency_label.pack(anchor="w")

    def _choose_pbf(self, filetypes) -> None:
        path = filedialog.askopenfilename(title="Select OSM PBF", filetypes=filetypes)
        if path:
            self.pbf_var.set(path)

    def _choose_tasks(self, filetypes) -> None:
        path = filedialog.askopenfilename(title="Select Task Grid GeoJSON", filetypes=filetypes)
        if path:
            self.tasks_var.set(path)

    def _choose_xml(self, filetypes) -> None:
        initial = self.latest_run.get("output", str(RUNS_DIR))
        path = filedialog.askopenfilename(title="Select JOSM Validation XML", initialdir=initial, filetypes=filetypes)
        if path:
            self.xml_var.set(path)

    def _load_session(self) -> None:
        if not SESSION_FILE.is_file():
            return
        values: dict[str, str] = {}
        for line in SESSION_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key] = value
        self.latest_run = values
        self.tasks_var.set(values.get("tasks", ""))
        self.output_var.set(values.get("output", "No run started yet"))
        sample = Path(values.get("sample", "")) if values.get("sample") else None
        if sample and sample.is_file():
            self.sample_label.config(text=str(sample))
            self.josm_ready = True

    def _save_session(self, tasks: str, output: str, sample: str) -> None:
        SESSION_FILE.write_text(
            f"tasks={tasks}\noutput={output}\nsample={sample}\n",
            encoding="utf-8",
        )
        self.latest_run = {"tasks": tasks, "output": output, "sample": sample}

    def _refresh_status(self) -> None:
        osmium = find_osmium()
        python_text = f"Python {sys.version_info.major}.{sys.version_info.minor}"
        self.dependency_label.config(
            text=(
                f"{python_text}: {'OK' if python_ok() else 'Too old (need 3.12+)'}\n"
                f"Osmium: {'Found' if osmium else 'Not found'}\n"
                f"JOSM: opened through your Windows file association"
            )
        )
        if not python_ok():
            self.status_var.set("Python 3.12+ is required")
        elif not osmium:
            self.status_var.set("Ready — Osmium was not detected yet")
        else:
            self.status_var.set("Ready")

    def _append(self, widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.insert("end", text)
        widget.see("end")
        widget.configure(state="disabled")

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.open_josm_button.config(state=state)

    def _run_pipeline(self, args: list[str], log_widget: tk.Text, on_success) -> None:
        def worker() -> None:
            env = os.environ.copy()
            osmium = find_osmium()
            if osmium:
                osmium_dir = str(Path(osmium).parent)
                env["PATH"] = osmium_dir + os.pathsep + env.get("PATH", "")
            env["QABOT_WORK_DIR"] = str(REPO_DIR / "work")
            cmd = [sys.executable, "-u", "gui_pipeline.py", *args]
            try:
                process = subprocess.Popen(
                    cmd,
                    cwd=str(REPO_DIR),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                assert process.stdout is not None
                for line in process.stdout:
                    self.after(0, self._append, log_widget, line)
                code = process.wait()
                if code == 0:
                    self.after(0, on_success)
                else:
                    self.after(0, lambda: messagebox.showerror("QA Buddy", f"Pipeline failed with exit code {code}."))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("QA Buddy", str(exc)))
            finally:
                self.after(0, lambda: self._set_busy(False))

        self._set_busy(True)
        threading.Thread(target=worker, daemon=True).start()

    def start_prepare(self) -> None:
        if not python_ok():
            messagebox.showerror("Python version", "OSM QA Buddy requires Python 3.12 or newer.")
            return
        pbf = self.pbf_var.get().strip()
        tasks = self.tasks_var.get().strip()
        if not pbf or not Path(pbf).is_file():
            messagebox.showwarning("Input required", "Please select a valid OSM PBF file.")
            return
        if not tasks or not Path(tasks).is_file():
            messagebox.showwarning("Input required", "Please select a valid Task Grid GeoJSON file.")
            return
        if not find_osmium():
            messagebox.showerror(
                "Osmium not found",
                "Osmium was not detected. Install it in the active environment or add osmium.exe to PATH.",
            )
            return

        output = RUNS_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
        output.mkdir(parents=True, exist_ok=True)
        self.output_var.set(str(output))
        self._append(self.prepare_log, f"Starting QA run…\nPBF: {pbf}\nTasks: {tasks}\nOutput: {output}\n\n")

        def success() -> None:
            sample = output / "sample.osm"
            self._save_session(tasks, str(output), str(sample))
            self.sample_label.config(text=str(sample))
            self.josm_ready = True
            self.status_var.set("Prepared — ready for JOSM validation")
            self.notebook.select(1)
            messagebox.showinfo("Ready for JOSM", "The sample is ready. Run JOSM Validator with Shift+V, then save the validation results as XML.")

        self._run_pipeline(["prepare", pbf, tasks, str(output)], self.prepare_log, success)

    def open_sample(self) -> None:
        sample = Path(self.latest_run.get("sample", ""))
        if not sample.is_file():
            messagebox.showwarning("No sample", "Start a new QA run first.")
            return
        try:
            os.startfile(str(sample))  # type: ignore[attr-defined]
            self.status_var.set("Opened sample.osm — validate it in JOSM")
        except OSError as exc:
            messagebox.showerror("Could not open sample", str(exc))

    def start_finalize(self) -> None:
        tasks = self.latest_run.get("tasks", "")
        output = self.latest_run.get("output", "")
        xml = self.xml_var.get().strip()
        if not tasks or not Path(tasks).is_file():
            messagebox.showwarning("No run", "Start a new QA run first, or make sure its Task Grid still exists.")
            return
        if not output or not Path(output).is_dir():
            messagebox.showwarning("No run", "The latest QA run folder could not be found.")
            return
        if not xml or not Path(xml).is_file():
            messagebox.showwarning("XML required", "Select the JOSM Validation errors XML file first.")
            return

        self._append(self.finalize_log, f"Finalizing…\nTasks: {tasks}\nXML: {xml}\nOutput: {output}\n\n")

        def success() -> None:
            self.status_var.set("QA run complete")
            self.report_button.config(state="normal")
            self.map_button.config(state="normal")
            self.notebook.select(2)
            messagebox.showinfo("QA run complete", "QA Buddy finished successfully. The report and map are ready.")

        self._run_pipeline(["finalize", tasks, xml, output], self.finalize_log, success)

    def open_report(self) -> None:
        path = Path(self.latest_run.get("output", "")) / "report.html"
        if path.is_file():
            webbrowser.open(path.as_uri())

    def open_map(self) -> None:
        path = Path(self.latest_run.get("output", "")) / "map.html"
        if path.is_file():
            webbrowser.open(path.as_uri())


if __name__ == "__main__":
    app = QABuddyApp()
    app.mainloop()
