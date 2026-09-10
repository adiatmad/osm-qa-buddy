import os
import re
import subprocess
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from memory import automatic_ram_gb, maximum_manual_ram_gb, total_memory_gb, validate_ram_gb, MIN_RAM_GB

GEOFABRIK_URL = "https://download.geofabrik.de/"
TM_API_BASE = "https://tasking-manager-production-api.hotosm.org/api/v2/projects/"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OSM QA Buddy — 3rd Pass Validation")
        self.geometry("760x600")
        self.minsize(680, 500)

        self.project_id = tk.StringVar()
        self.aoi_path = tk.StringVar()
        self.tasks_path = tk.StringVar()
        self.pbf_path = tk.StringVar()
        self.status = tk.StringVar(value="Enter a HOT TM Project ID to begin.")
        self.progress = tk.DoubleVar(value=0)
        self.ram_mode = tk.StringVar(value="Automatic")
        self.ram_gb = tk.StringVar(value="2")
        self.ram_hint = tk.StringVar(value="Automatic RAM is recommended.")
        self.aoi_url = self.tasks_url = None

        self._build_ui()
        self._update_ram_controls()

    def _build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="OSM QA Buddy", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(root, text="HOT Tasking Manager — 3rd Pass Validation", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 10))

        project = ttk.LabelFrame(root, text="1. HOT TM Project", padding=8)
        project.pack(fill="x")
        row = ttk.Frame(project); row.pack(fill="x")
        ttk.Label(row, text="Project ID:").pack(side="left")
        ttk.Entry(row, textvariable=self.project_id, width=16).pack(side="left", padx=6)
        ttk.Button(row, text="Prepare download links", command=self.prepare_project).pack(side="left")

        links = ttk.LabelFrame(root, text="2. Download source files", padding=8)
        links.pack(fill="x", pady=8)
        ttk.Label(links, text="The app does NOT download these files. Open the links, download the exact files, then select them below.", wraplength=720).pack(anchor="w", pady=(0, 5))
        buttons = ttk.Frame(links); buttons.pack(fill="x")
        self.aoi_button = ttk.Button(buttons, text="HOT TM Boundary (-aoi.geojson)", command=lambda: self.open_link(self.aoi_url), state="disabled")
        self.aoi_button.pack(side="left", padx=(0, 5))
        self.tasks_button = ttk.Button(buttons, text="HOT TM Tasks (-tasks.geojson)", command=lambda: self.open_link(self.tasks_url), state="disabled")
        self.tasks_button.pack(side="left", padx=5)
        ttk.Button(buttons, text="Geofabrik downloads", command=lambda: self.open_link(GEOFABRIK_URL)).pack(side="left", padx=5)

        files = ttk.LabelFrame(root, text="3. Select downloaded files", padding=8)
        files.pack(fill="x")
        self._file_row(files, "Project Boundary", self.aoi_path, 0, "aoi")
        self._file_row(files, "Task Grid", self.tasks_path, 1, "tasks")
        self._file_row(files, "Geofabrik PBF", self.pbf_path, 2, "pbf")

        action = ttk.LabelFrame(root, text="4. Start validation", padding=8)
        action.pack(fill="x", pady=8)
        self.run_button = ttk.Button(action, text="START 3RD PASS VALIDATION", command=self.start_validation, state="disabled")
        self.run_button.pack(anchor="w", ipadx=14, ipady=6)

        advanced = ttk.LabelFrame(action, text="Advanced settings (optional)", padding=6)
        advanced.pack(fill="x", pady=(8, 0))
        ram_row = ttk.Frame(advanced); ram_row.pack(fill="x")
        ttk.Label(ram_row, text="JVM RAM:").pack(side="left")
        self.ram_mode_combo = ttk.Combobox(ram_row, textvariable=self.ram_mode, values=("Automatic", "Manual"), state="readonly", width=12)
        self.ram_mode_combo.pack(side="left", padx=6)
        ttk.Label(ram_row, text="GB:").pack(side="left")
        self.ram_spin = ttk.Spinbox(ram_row, from_=MIN_RAM_GB, to=16, textvariable=self.ram_gb, width=6)
        self.ram_spin.pack(side="left", padx=6)
        self.ram_mode_combo.bind("<<ComboboxSelected>>", lambda _event: self._update_ram_controls())
        ttk.Label(advanced, textvariable=self.ram_hint, wraplength=680).pack(anchor="w", pady=(4, 0))

        checks = ttk.LabelFrame(root, text="5. Validation status / live log", padding=8)
        checks.pack(fill="both", expand=True)
        log_frame = ttk.Frame(checks); log_frame.pack(fill="both", expand=True)
        self.check_text = tk.Text(log_frame, height=8, wrap="none", state="disabled", font=("Consolas", 8))
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.check_text.yview)
        self.check_text.configure(yscrollcommand=scrollbar.set)
        self.check_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        ttk.Label(root, textvariable=self.status).pack(fill="x", pady=(6, 3))
        ttk.Progressbar(root, variable=self.progress, maximum=100).pack(fill="x")

    def _update_ram_controls(self):
        manual = self.ram_mode.get() == "Manual"
        self.ram_spin.configure(state="normal" if manual else "disabled")
        try:
            total_gb = total_memory_gb()
            if manual:
                max_ram = maximum_manual_ram_gb(total_gb)
                self.ram_hint.set(
                    f"Manual override: {MIN_RAM_GB}–{max_ram} GB is allowed on this machine. Automatic is recommended."
                )
                current = int(self.ram_gb.get())
                if current > max_ram:
                    self.ram_gb.set(str(max_ram))
            else:
                auto = automatic_ram_gb(total_gb)
                self.ram_gb.set(str(auto))
                self.ram_hint.set(
                    f"Automatic: about {auto} GB for a machine with {total_gb:.1f} GB physical RAM. Recommended for most users."
                )
        except Exception:
            self.ram_hint.set("RAM will be checked before the QA run.")

    def _file_row(self, parent, label, variable, row, kind):
        ttk.Label(parent, text=label, width=17).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=6, pady=3)
        if kind == "aoi":
            filetypes = [("HOT TM AOI", "*.geojson"), ("All files", "*.*")]
            help_text = "Expected: filename ends with -aoi.geojson (Windows (1) suffix allowed)"
        elif kind == "tasks":
            filetypes = [("HOT TM Tasks", "*.geojson"), ("All files", "*.*")]
            help_text = "Expected: filename ends with -tasks.geojson (Windows (1) suffix allowed)"
        else:
            filetypes = [("OSM PBF", "*.osm.pbf"), ("PBF", "*.pbf"), ("All files", "*.*")]
            help_text = "Expected: filename ends with .osm.pbf (Windows (1) suffix allowed)"
        ttk.Button(parent, text="Browse", command=lambda: self.browse(variable, filetypes)).grid(row=row, column=2, padx=(0, 6), pady=3)
        ttk.Label(parent, text=help_text).grid(row=row, column=3, sticky="w", pady=3)
        parent.columnconfigure(1, weight=1)

    def browse(self, variable, filetypes):
        path = filedialog.askopenfilename(title="Select file", filetypes=filetypes)
        if path:
            variable.set(path)
            self._update_run_state()

    def prepare_project(self):
        project_id = self.project_id.get().strip()
        if not project_id.isdigit():
            messagebox.showerror("Invalid Project ID", "Please enter a numeric HOT TM Project ID.")
            return
        self.aoi_url = f"{TM_API_BASE}{project_id}/queries/aoi/?as_file=true"
        self.tasks_url = f"{TM_API_BASE}{project_id}/tasks/?as_file=true"
        self.aoi_button.configure(state="normal")
        self.tasks_button.configure(state="normal")
        self.status.set("Download the 2 HOT TM GeoJSON files and the matching Geofabrik PBF, then select all 3 files.")
        self.progress.set(20)
        self._set_check_text("OFFICIAL DOWNLOAD LINKS\n\n" + f"Project Boundary (-aoi.geojson):\n{self.aoi_url}\n\n" + f"Task Grid (-tasks.geojson):\n{self.tasks_url}\n\n" + f"Geofabrik downloads:\n{GEOFABRIK_URL}\n")
        self._update_run_state()

    def open_link(self, url):
        if url:
            webbrowser.open(url)

    def _update_run_state(self):
        ready = all(Path(path.get()).is_file() for path in (self.aoi_path, self.tasks_path, self.pbf_path))
        self.run_button.configure(state="normal" if ready else "disabled")
        if ready:
            self.status.set("All 3 files selected. Click START 3RD PASS VALIDATION.")

    def _resolve_ram_for_run(self):
        total_gb = total_memory_gb()
        if self.ram_mode.get() == "Automatic":
            return automatic_ram_gb(total_gb), "automatic"
        value = self.ram_gb.get().strip()
        ok, message = validate_ram_gb(value, total_gb)
        if not ok:
            raise ValueError(message)
        return int(value), "manual"

    def start_validation(self):
        if not self._basic_inputs_ok():
            messagebox.showerror("Input check failed", "Please select the Project Boundary, Task Grid, and Geofabrik PBF files first.")
            return
        try:
            ram_gb, ram_mode = self._resolve_ram_for_run()
        except Exception as exc:
            messagebox.showerror("RAM setting check failed", str(exc))
            return
        self.run_button.configure(state="disabled")
        self.status.set(f"Starting 3rd-pass validation with {ram_gb} GB JVM RAM ({ram_mode})…")
        self.progress.set(30)
        self._set_check_text("STARTING 3RD PASS VALIDATION\n\nLOCAL INPUT CHECKS\n" + self._basic_checks() + f"\n\nJVM RAM: {ram_gb} GB ({ram_mode})\n")
        if not self._filename_patterns_ok():
            self.status.set("Filename check failed.")
            self.progress.set(0)
            self._append_log("\nFAIL: Filename pattern check failed.\n")
            self.run_button.configure(state="normal")
            messagebox.showerror("Wrong file selected", "Expected filenames:\n\nProject Boundary: *-aoi.geojson (or *-aoi(1).geojson, etc.)\nTask Grid: *-tasks.geojson (or *-tasks(1).geojson, etc.)\nGeofabrik: *.osm.pbf (or *.osm(1).pbf, etc.)")
            return
        self.status.set("Docker is running the authoritative pre-flight checks…")
        self.progress.set(40)
        threading.Thread(target=self._docker_worker, args=(ram_gb, ram_mode), daemon=True).start()

    def _basic_checks(self):
        lines = []
        for label, path in (("Project Boundary", self.aoi_path.get()), ("Task Grid", self.tasks_path.get()), ("Geofabrik PBF", self.pbf_path.get())):
            p = Path(path)
            lines.append(f"PASS: {label} exists: {p.name}" if p.is_file() else f"FAIL: {label} missing: {path}")
        return "\n".join(lines)

    def _basic_inputs_ok(self):
        return all(Path(path.get()).is_file() for path in (self.aoi_path, self.tasks_path, self.pbf_path))

    def _filename_patterns_ok(self):
        patterns = (
            (self.aoi_path.get(), r"-aoi(?:\s*\(\d+\))?\.geojson$"),
            (self.tasks_path.get(), r"-tasks(?:\s*\(\d+\))?\.geojson$"),
            (self.pbf_path.get(), r"\.osm(?:\s*\(\d+\))?\.pbf$"),
        )
        return all(re.search(pattern, os.path.basename(path), flags=re.IGNORECASE) for path, pattern in patterns)

    def _docker_worker(self, ram_gb, ram_mode):
        try:
            repo_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(repo_dir, "osm_qa_buddy_results", f"project_{self.project_id.get().strip()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(output_dir, exist_ok=True)
            mounts = []
            for source, target in ((self.aoi_path.get(), "/data/input/project_aoi.geojson"), (self.tasks_path.get(), "/data/input/project_tasks.geojson"), (self.pbf_path.get(), "/data/input/region.osm.pbf")):
                mounts += ["--mount", f"type=bind,source={os.path.abspath(source)},target={target},readonly"]
            mounts += ["--mount", f"type=bind,source={os.path.abspath(output_dir)},target=/data/output"]
            command = ["docker", "run", "--rm", *mounts, "-e", f"QABOT_PROJECT_ID={self.project_id.get().strip()}", "-e", f"QABOT_JAVA_XMX_GB={ram_gb}", "qabot", "/data/input/region.osm.pbf", "/data/input/project_aoi.geojson", "/data/input/project_tasks.geojson", "/data/output"]
            self.after(0, lambda: self._append_log("\nDOCKER / QA LIVE LOG\n" + "=" * 80 + "\n"))
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=repo_dir)
            log_lines = []
            assert process.stdout is not None
            for raw_line in iter(process.stdout.readline, ""):
                line = raw_line.rstrip("\r\n")
                log_lines.append(line)
                self.after(0, lambda text=line: self._append_log(text + "\n"))
            process.stdout.close()
            returncode = process.wait()
            log_path = os.path.join(output_dir, "qa_run.log")
            Path(log_path).write_text("\n".join(log_lines) + "\n", encoding="utf-8")
            if returncode != 0:
                raise RuntimeError(f"Docker QA failed (exit code {returncode}). Full log saved to:\n{log_path}")
            self.after(0, lambda: self._docker_done(output_dir, log_path))
        except Exception as exc:
            self.after(0, lambda: self._docker_failed(str(exc)))

    def _docker_done(self, output_dir, log_path):
        self.progress.set(100)
        self.status.set("QA completed successfully.")
        self._append_log("\n" + "=" * 80 + "\nQA COMPLETED SUCCESSFULLY\n\nResults:\n" + output_dir + "\n\nFull log:\n" + log_path + "\n")
        messagebox.showinfo("QA complete", "3rd Pass Validation completed.\n\nResults are in:\n" + output_dir)
        report = Path(output_dir, "report.html")
        if report.exists():
            webbrowser.open(report.as_uri())
        self.run_button.configure(state="normal")

    def _docker_failed(self, message):
        self.progress.set(0)
        self.status.set("QA failed before completion.")
        self._append_log("\n" + "=" * 80 + "\nQA FAILED\n" + message + "\n")
        self.run_button.configure(state="normal")
        messagebox.showerror("QA failed", message)

    def _append_log(self, text):
        self.check_text.configure(state="normal")
        self.check_text.insert("end", text)
        self.check_text.see("end")
        self.check_text.configure(state="disabled")

    def _set_check_text(self, text):
        self.check_text.configure(state="normal")
        self.check_text.delete("1.0", "end")
        self.check_text.insert("1.0", text)
        self.check_text.see("end")
        self.check_text.configure(state="disabled")


if __name__ == "__main__":
    App().mainloop()
