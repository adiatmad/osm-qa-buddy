import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

GEOFABRIK_URL = "https://download.geofabrik.de/"
TM_API_BASE = "https://tasking-manager-production-api.hotosm.org/api/v2/projects/"
DEFAULT_RAM_GB = "24"


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
        self.ram_gb = tk.StringVar(value=DEFAULT_RAM_GB)
        self.status = tk.StringVar(value="Select the 3 input files to begin. Project ID is optional.")
        self.progress = tk.DoubleVar(value=0)
        self.aoi_url = self.tasks_url = None
        self.last_output_dir = None
        self.last_josm_dataset = None

        self._build_ui()

    def _build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="OSM QA Buddy", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(root, text="HOT Tasking Manager — 3rd Pass Validation", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 10))

        project = ttk.LabelFrame(root, text="1. HOT TM Project (optional)", padding=8)
        project.pack(fill="x")
        row = ttk.Frame(project); row.pack(fill="x")
        ttk.Label(row, text="Project ID:").pack(side="left")
        ttk.Entry(row, textvariable=self.project_id, width=16).pack(side="left", padx=6)
        ttk.Button(row, text="Prepare download links", command=self.prepare_project).pack(side="left")
        ttk.Label(project, text="Optional: enter a numeric HOT TM Project ID only if you want the official download links. It is not required to run QA on local files.", wraplength=720).pack(anchor="w", pady=(5, 0))

        links = ttk.LabelFrame(root, text="2. Download source files", padding=8)
        links.pack(fill="x", pady=8)
        ttk.Label(links, text="The app does NOT download these files. Open the links, download the source files, then select them below.", wraplength=720).pack(anchor="w", pady=(0, 5))
        buttons = ttk.Frame(links); buttons.pack(fill="x")
        self.aoi_button = ttk.Button(buttons, text="HOT TM Boundary", command=lambda: self.open_link(self.aoi_url), state="disabled")
        self.aoi_button.pack(side="left", padx=(0, 5))
        self.tasks_button = ttk.Button(buttons, text="HOT TM Tasks", command=lambda: self.open_link(self.tasks_url), state="disabled")
        self.tasks_button.pack(side="left", padx=5)
        ttk.Button(buttons, text="Geofabrik downloads", command=lambda: self.open_link(GEOFABRIK_URL)).pack(side="left", padx=5)

        files = ttk.LabelFrame(root, text="3. Select downloaded files", padding=8)
        files.pack(fill="x")
        self._file_row(files, "Project Boundary", self.aoi_path, 0, "aoi")
        self._file_row(files, "Task Grid", self.tasks_path, 1, "tasks")
        self._file_row(files, "Geofabrik PBF", self.pbf_path, 2, "pbf")

        action = ttk.LabelFrame(root, text="4. Start validation", padding=8)
        action.pack(fill="x", pady=8)
        ram_row = ttk.Frame(action); ram_row.pack(fill="x", pady=(0, 6))
        ttk.Label(ram_row, text="Java/JOSM RAM (GB):").pack(side="left")
        ttk.Entry(ram_row, textvariable=self.ram_gb, width=10).pack(side="left", padx=6)
        ttk.Label(ram_row, text="Enter a whole number, e.g. 8, 16, 24, 32.").pack(side="left")
        ttk.Label(action, text="RAM is passed directly to Java as -Xmx. Do not allocate more than your computer can spare.", wraplength=720).pack(anchor="w", pady=(0, 6))
        self.run_button = ttk.Button(action, text="START 3RD PASS VALIDATION", command=self.start_validation, state="disabled")
        self.run_button.pack(anchor="w", ipadx=14, ipady=6)
        handoff = ttk.Frame(action); handoff.pack(fill="x", pady=(8, 0))
        self.josm_button = ttk.Button(handoff, text="Open Clipped OSM in JOSM", command=self.open_josm, state="disabled")
        self.josm_button.pack(side="left", padx=(0, 5))
        self.folder_button = ttk.Button(handoff, text="Open Clipped OSM Folder", command=self.open_results_folder, state="disabled")
        self.folder_button.pack(side="left", padx=5)
        ttk.Label(action, text="These buttons become available as soon as the clipped OSM dataset is ready; QA can continue in the background.", wraplength=720).pack(anchor="w", pady=(5, 0))

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

    def _file_row(self, parent, label, variable, row, kind):
        ttk.Label(parent, text=label, width=17).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=6, pady=3)
        if kind == "aoi":
            filetypes = [("GeoJSON", "*.geojson"), ("All files", "*.*")]
            help_text = "Any valid GeoJSON filename; preflight validates the contents."
        elif kind == "tasks":
            filetypes = [("GeoJSON", "*.geojson"), ("All files", "*.*")]
            help_text = "Any valid GeoJSON filename; preflight validates the contents."
        else:
            filetypes = [("OSM PBF", "*.osm.pbf"), ("PBF", "*.pbf"), ("All files", "*.*")]
            help_text = "Any readable OSM PBF filename; preflight validates the file."
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
            messagebox.showerror("Invalid Project ID", "Please enter a numeric HOT TM Project ID, or leave it blank if you already have the source files.")
            return
        self.aoi_url = f"{TM_API_BASE}{project_id}/queries/aoi/?as_file=true"
        self.tasks_url = f"{TM_API_BASE}{project_id}/tasks/?as_file=true"
        self.aoi_button.configure(state="normal")
        self.tasks_button.configure(state="normal")
        self.status.set("Download the HOT TM GeoJSON files and the matching Geofabrik PBF, then select all 3 files.")
        self.progress.set(20)
        self._set_check_text("OFFICIAL DOWNLOAD LINKS\n\n" + f"Project Boundary:\n{self.aoi_url}\n\n" + f"Task Grid:\n{self.tasks_url}\n\n" + f"Geofabrik downloads:\n{GEOFABRIK_URL}\n")
        self._update_run_state()

    def open_link(self, url):
        if url:
            webbrowser.open(url)

    def _valid_ram(self):
        value = self.ram_gb.get().strip()
        return value.isdigit() and 1 <= int(value) <= 128

    def _update_run_state(self):
        ready = all(Path(path.get()).is_file() for path in (self.aoi_path, self.tasks_path, self.pbf_path)) and self._valid_ram()
        self.run_button.configure(state="normal" if ready else "disabled")
        if ready:
            self.status.set("All 3 files selected and RAM setting is valid. Click START 3RD PASS VALIDATION.")

    def start_validation(self):
        if not self._basic_inputs_ok():
            messagebox.showerror("Input check failed", "Please select the Project Boundary, Task Grid, and Geofabrik PBF files first.")
            return
        if not self._valid_ram():
            messagebox.showerror("Invalid RAM", "Enter a whole number between 1 and 128 GB.")
            return
        self.run_button.configure(state="disabled")
        self.status.set("Starting native Windows 3rd-pass validation…")
        self.progress.set(30)
        self._set_check_text("STARTING 3RD PASS VALIDATION\n\nLOCAL INPUT CHECKS\n" + self._basic_checks() + f"\n\nJava/JOSM RAM: {self.ram_gb.get().strip()} GB\n")
        self.status.set("Native Windows QA is running…")
        self.progress.set(40)
        threading.Thread(target=self._native_worker, daemon=True).start()

    def _basic_checks(self):
        lines = []
        for label, path in (("Project Boundary", self.aoi_path.get()), ("Task Grid", self.tasks_path.get()), ("Geofabrik PBF", self.pbf_path.get())):
            p = Path(path)
            lines.append(f"PASS: {label} exists: {p.name}" if p.is_file() else f"FAIL: {label} missing: {path}")
        return "\n".join(lines)

    def _basic_inputs_ok(self):
        return all(Path(path.get()).is_file() for path in (self.aoi_path, self.tasks_path, self.pbf_path))

    def _native_worker(self):
        try:
            repo_dir = os.path.dirname(os.path.abspath(__file__))
            project_id = self.project_id.get().strip()
            run_label = project_id if project_id else "local"
            output_dir = os.path.join(repo_dir, "osm_qa_buddy_results", f"project_{run_label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(output_dir, exist_ok=True)
            work_dir = os.path.join(output_dir, "work")
            os.makedirs(work_dir, exist_ok=True)
            env = os.environ.copy()
            if project_id:
                env["QABOT_PROJECT_ID"] = project_id
            else:
                env.pop("QABOT_PROJECT_ID", None)
            env["QABOT_WORK_DIR"] = work_dir
            command = [sys.executable, os.path.join(repo_dir, "orchestrator.py"), self.pbf_path.get(), self.aoi_path.get(), self.tasks_path.get(), output_dir, "--ram-gb", self.ram_gb.get().strip()]
            if project_id:
                command.extend(["--project-id", project_id])
            self.after(0, lambda: self._append_log("\nNATIVE WINDOWS QA LIVE LOG\n" + "=" * 80 + "\n"))
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=repo_dir, env=env)
            threading.Thread(target=self._monitor_josm_dataset, args=(process, work_dir, output_dir), daemon=True).start()
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
                raise RuntimeError(f"Native QA failed (exit code {returncode}). Full log saved to:\n{log_path}")
            josm_dataset = self.last_josm_dataset
            if not josm_dataset or not Path(josm_dataset).is_file():
                josm_dataset = self._create_josm_dataset(work_dir, output_dir)
            self.after(0, lambda: self._native_done(output_dir, log_path, josm_dataset))
        except Exception as exc:
            message = str(exc)
            self.after(0, lambda: self._native_failed(message))

    def _monitor_josm_dataset(self, process, work_dir, output_dir):
        source = Path(work_dir, "sample.osm")
        while process.poll() is None:
            if source.is_file() and source.stat().st_size > 0:
                previous_size = source.stat().st_size
                time.sleep(2)
                if process.poll() is None and source.is_file() and source.stat().st_size == previous_size:
                    try:
                        josm_dataset = self._create_josm_dataset(work_dir, output_dir)
                    except Exception:
                        time.sleep(1)
                        continue
                    self.after(0, lambda path=josm_dataset: self._josm_dataset_ready(output_dir, path))
                    return
            time.sleep(1)

    def _create_josm_dataset(self, work_dir, output_dir):
        source = Path(work_dir, "sample.osm")
        if not source.is_file():
            raise RuntimeError("The extracted OSM dataset was not found at:\n" + str(source))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination = Path(output_dir, f"osm_qa_buddy_josm_{timestamp}.osm")
        shutil.copy2(source, destination)
        return str(destination)

    def _josm_dataset_ready(self, output_dir, josm_dataset):
        self.last_output_dir = output_dir
        self.last_josm_dataset = josm_dataset
        self.josm_button.configure(state="normal")
        self.folder_button.configure(state="normal")
        self.status.set("Clipped OSM is ready. You can open it in JOSM while automated QA continues.")
        self._append_log("\n" + "-" * 80 + "\nJOSM HANDOFF READY\nClipped OSM dataset:\n" + josm_dataset + "\nYou may now open this dataset in JOSM GUI; automated QA continues independently.\n" + "-" * 80 + "\n")

    def _find_josm_launcher(self):
        for name in ("josm.exe", "JOSM.exe", "josm"):
            found = shutil.which(name)
            if found:
                return [found]
        jar = Path(os.path.dirname(os.path.abspath(__file__)), "tools", "josm-19613.jar")
        if jar.is_file():
            return ["java", "-Xmx24g", "-jar", str(jar)]
        return None

    def open_josm(self):
        if not self.last_josm_dataset or not Path(self.last_josm_dataset).is_file():
            messagebox.showerror("JOSM dataset unavailable", "The JOSM-ready OSM file is not available yet.")
            return
        launcher = self._find_josm_launcher()
        if not launcher:
            messagebox.showerror("JOSM not found", "JOSM was not found on PATH and the bundled JOSM jar is unavailable.")
            return
        try:
            subprocess.Popen(launcher + [self.last_josm_dataset], cwd=os.path.dirname(self.last_josm_dataset))
            self.status.set("JOSM launched with the extracted project dataset. Automated QA continues in the background.")
        except Exception as exc:
            messagebox.showerror("Could not launch JOSM", str(exc))

    def open_results_folder(self):
        if self.last_output_dir and Path(self.last_output_dir).is_dir():
            os.startfile(self.last_output_dir)

    def _native_done(self, output_dir, log_path, josm_dataset):
        self.last_output_dir = output_dir
        self.last_josm_dataset = josm_dataset
        self.josm_button.configure(state="normal")
        self.folder_button.configure(state="normal")
        self.progress.set(100)
        self.status.set("QA completed successfully. JOSM-ready dataset is available.")
        self._append_log("\n" + "=" * 80 + "\nQA COMPLETED SUCCESSFULLY\n\nJOSM-ready dataset:\n" + josm_dataset + "\n\nResults:\n" + output_dir + "\n\nFull log:\n" + log_path + "\n")
        dialog = tk.Toplevel(self)
        dialog.title("QA complete")
        dialog.transient(self)
        dialog.grab_set()
        ttk.Label(dialog, text="3rd Pass Validation completed.", font=("Segoe UI", 11, "bold")).pack(padx=20, pady=(18, 6))
        ttk.Label(dialog, text="A timestamped OSM dataset was prepared earlier and is available for interactive JOSM validation.", wraplength=440).pack(padx=20, pady=(0, 14))
        buttons = ttk.Frame(dialog); buttons.pack(padx=20, pady=(0, 18))
        ttk.Button(buttons, text="Open in JOSM", command=lambda: self.open_josm_and_close(dialog)).pack(side="left", padx=4)
        ttk.Button(buttons, text="Open Results Folder", command=self.open_results_folder).pack(side="left", padx=4)
        ttk.Button(buttons, text="Close", command=dialog.destroy).pack(side="left", padx=4)
        report = Path(output_dir, "report.html")
        if report.exists():
            webbrowser.open(report.as_uri())
        self.run_button.configure(state="normal")

    def open_josm_and_close(self, dialog):
        self.open_josm()
        dialog.destroy()

    def _native_failed(self, message):
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
