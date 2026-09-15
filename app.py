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

from shapely.geometry import shape

GEOFABRIK_URL = "https://download.geofabrik.de/"
TM_API_BASE = "https://tasking-manager-production-api.hotosm.org/api/v2/projects/"
DEFAULT_RAM_GB = "24"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OSM QA Buddy — Task Grid 3rd Pass Validation")
        self.geometry("760x620")
        self.minsize(680, 520)
        self.project_id = tk.StringVar()
        self.tasks_path = tk.StringVar()
        self.pbf_path = tk.StringVar()
        self.ram_gb = tk.StringVar(value=DEFAULT_RAM_GB)
        self.status = tk.StringVar(value="Select the HOT Task Grid GeoJSON and Geofabrik PBF to begin.")
        self.progress = tk.DoubleVar(value=0)
        self.tasks_url = None
        self.last_output_dir = None
        self.last_josm_dataset = None
        self._build_ui()

    def _build_ui(self):
        root = ttk.Frame(self, padding=12); root.pack(fill="both", expand=True)
        ttk.Label(root, text="OSM QA Buddy", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(root, text="HOT Tasking Manager — Task Grid 3rd Pass Validation", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 10))

        project = ttk.LabelFrame(root, text="1. HOT TM Project (optional)", padding=8); project.pack(fill="x")
        row = ttk.Frame(project); row.pack(fill="x")
        ttk.Label(row, text="Project ID:").pack(side="left")
        ttk.Entry(row, textvariable=self.project_id, width=16).pack(side="left", padx=6)
        ttk.Button(row, text="Prepare Task download link", command=self.prepare_project).pack(side="left")
        ttk.Button(row, text="Geofabrik downloads", command=lambda: self.open_link(GEOFABRIK_URL)).pack(side="left", padx=6)
        ttk.Label(project, text="Optional. The Project Boundary is intentionally not requested: the Task Grid is the authoritative QA/extraction geometry.", wraplength=720).pack(anchor="w", pady=(5, 0))

        files = ttk.LabelFrame(root, text="2. Select source files", padding=8); files.pack(fill="x", pady=8)
        self._file_row(files, "HOT Task Grid", self.tasks_path, 0, "tasks")
        self._file_row(files, "Geofabrik PBF", self.pbf_path, 1, "pbf")
        self.preview_button = ttk.Button(files, text="Preview Task Grid", command=self.preview_task_grid, state="disabled")
        self.preview_button.grid(row=2, column=1, sticky="w", padx=6, pady=(6, 2))
        self.task_info = ttk.Label(files, text="No Task Grid selected.")
        self.task_info.grid(row=2, column=2, columnspan=2, sticky="w", pady=(6, 2))
        files.columnconfigure(1, weight=1)

        action = ttk.LabelFrame(root, text="3. Start validation", padding=8); action.pack(fill="x", pady=8)
        ram_row = ttk.Frame(action); ram_row.pack(fill="x", pady=(0, 6))
        ttk.Label(ram_row, text="Java/JOSM RAM (GB):").pack(side="left")
        ttk.Entry(ram_row, textvariable=self.ram_gb, width=10).pack(side="left", padx=6)
        ttk.Label(ram_row, text="Example: 8, 16, 24, 32.").pack(side="left")
        self.run_button = ttk.Button(action, text="START 3RD PASS VALIDATION", command=self.start_validation, state="disabled")
        self.run_button.pack(anchor="w", ipadx=14, ipady=6)
        handoff = ttk.Frame(action); handoff.pack(fill="x", pady=(8, 0))
        self.josm_button = ttk.Button(handoff, text="Open Clipped OSM in JOSM", command=self.open_josm, state="disabled"); self.josm_button.pack(side="left", padx=(0, 5))
        self.folder_button = ttk.Button(handoff, text="Open Results Folder", command=self.open_results_folder, state="disabled"); self.folder_button.pack(side="left", padx=5)
        ttk.Label(action, text="The extracted OSM is created from the union of all Task Grid polygons. Individual task polygons remain unchanged for QA attribution.", wraplength=720).pack(anchor="w", pady=(5, 0))

        checks = ttk.LabelFrame(root, text="4. Validation status / live log", padding=8); checks.pack(fill="both", expand=True)
        log_frame = ttk.Frame(checks); log_frame.pack(fill="both", expand=True)
        self.check_text = tk.Text(log_frame, height=8, wrap="none", state="disabled", font=("Consolas", 8))
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.check_text.yview); self.check_text.configure(yscrollcommand=scrollbar.set)
        self.check_text.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        ttk.Label(root, textvariable=self.status).pack(fill="x", pady=(6, 3)); ttk.Progressbar(root, variable=self.progress, maximum=100).pack(fill="x")

    def _file_row(self, parent, label, variable, row, kind):
        ttk.Label(parent, text=label, width=17).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=6, pady=3)
        if kind == "tasks":
            filetypes = [("GeoJSON", "*.geojson"), ("JSON", "*.json"), ("All files", "*.*")]
            help_text = "HOT TM Task Grid GeoJSON/JSON. All task polygons are retained for attribution."
        else:
            filetypes = [("OSM PBF", "*.osm.pbf"), ("PBF", "*.pbf"), ("All files", "*.*")]
            help_text = "Regional OSM PBF downloaded from Geofabrik."
        ttk.Button(parent, text="Browse", command=lambda: self.browse(variable, filetypes)).grid(row=row, column=2, padx=(0, 6), pady=3)
        ttk.Label(parent, text=help_text).grid(row=row, column=3, sticky="w", pady=3)

    def browse(self, variable, filetypes):
        path = filedialog.askopenfilename(title="Select file", filetypes=filetypes)
        if not path: return
        variable.set(path)
        if variable is self.tasks_path:
            self._update_task_preview_state(); self.preview_task_grid(show_errors=False)
        self._update_run_state()

    def prepare_project(self):
        project_id = self.project_id.get().strip()
        if not project_id.isdigit():
            messagebox.showerror("Invalid Project ID", "Enter a numeric HOT TM Project ID, or leave it blank if you already have the Task Grid file."); return
        self.tasks_url = f"{TM_API_BASE}{project_id}/tasks/?as_file=true"
        self.status.set("Opening the HOT TM Task download link. Save the GeoJSON, then select it below.")
        self.progress.set(10); self._set_check_text("HOT TM TASK GRID DOWNLOAD\n\n" + self.tasks_url + "\n\nProject Boundary is not required for this workflow.\n"); self.open_link(self.tasks_url)

    def open_link(self, url):
        if url: webbrowser.open(url)

    def _valid_ram(self):
        value = self.ram_gb.get().strip(); return value.isdigit() and 1 <= int(value) <= 128

    def _update_task_preview_state(self): self.preview_button.configure(state="normal" if Path(self.tasks_path.get()).is_file() else "disabled")

    def _update_run_state(self):
        ready = Path(self.tasks_path.get()).is_file() and Path(self.pbf_path.get()).is_file() and self._valid_ram()
        self.run_button.configure(state="normal" if ready else "disabled")
        if ready: self.status.set("Task Grid, Geofabrik PBF, and RAM setting are ready. Click START 3RD PASS VALIDATION.")

    def _read_task_features(self):
        data = json.loads(Path(self.tasks_path.get()).read_text(encoding="utf-8"))
        if data.get("type") == "Feature": features = [data]
        elif data.get("type") == "FeatureCollection": features = data.get("features", [])
        elif data.get("type") in ("Polygon", "MultiPolygon"): features = [{"type": "Feature", "properties": {}, "geometry": data}]
        else: raise ValueError("GeoJSON must be a Feature, FeatureCollection, Polygon, or MultiPolygon.")
        if not features: raise ValueError("GeoJSON contains no features.")
        geometries = []
        for feature in features:
            geom = shape(feature.get("geometry"))
            if geom.is_empty or not geom.is_valid or geom.geom_type not in ("Polygon", "MultiPolygon"):
                raise ValueError("Every Task Grid feature must be a valid Polygon or MultiPolygon.")
            geometries.append(geom)
        return features, geometries

    def preview_task_grid(self, show_errors=True):
        try:
            features, geometries = self._read_task_features()
            self.task_info.configure(text=f"{len(features)} task feature(s) — valid Polygon/MultiPolygon geometry")
            self.preview_button.configure(state="normal")
            preview_path = Path(self.tasks_path.get()).with_name("osm_qa_buddy_task_grid_preview.html")
            preview_path.write_text(self._task_preview_html(features, geometries), encoding="utf-8")
            webbrowser.open(preview_path.as_uri()); self.status.set(f"Task Grid preview opened: {len(features)} feature(s).")
        except Exception as exc:
            self.task_info.configure(text="Task Grid validation failed.")
            if show_errors: messagebox.showerror("Task Grid preview failed", str(exc))

    def _task_preview_html(self, features, geometries):
        minx = min(g.bounds[0] for g in geometries); miny = min(g.bounds[1] for g in geometries); maxx = max(g.bounds[2] for g in geometries); maxy = max(g.bounds[3] for g in geometries)
        width, height, pad = 1000, 700, 30; dx = max(maxx - minx, 1e-12); dy = max(maxy - miny, 1e-12); scale = min((width - 2 * pad) / dx, (height - 2 * pad) / dy)
        def project(x, y): return pad + (x - minx) * scale, height - pad - (y - miny) * scale
        def polygon_svg(coords): return "<polygon points=\"" + " ".join(f"{project(x, y)[0]:.2f},{project(x, y)[1]:.2f}" for x, y in coords) + "\" />"
        shapes = []; labels = []
        for index, (feature, geom) in enumerate(zip(features, geometries), start=1):
            parts = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
            for part in parts: shapes.append(polygon_svg(part.exterior.coords))
            props = feature.get("properties") or {}; task_id = props.get("taskId", props.get("task_id", props.get("id", index)))
            cx, cy = project(*geom.centroid.coords[0]); labels.append(f"<text x=\"{cx:.2f}\" y=\"{cy:.2f}\">Task {task_id}</text>")
        return f"""<!doctype html><html><head><meta charset=\"utf-8\"><title>OSM QA Buddy — Task Grid Preview</title><style>body{{font-family:Segoe UI,Arial,sans-serif;margin:0;padding:20px;background:#f5f5f5}}svg{{background:white;border:1px solid #ccc;width:100%;height:auto}}polygon{{fill:#d9edf7;stroke:#1479a6;stroke-width:1.2;fill-opacity:.65}}text{{font-size:11px;text-anchor:middle;dominant-baseline:middle;fill:#222}}.meta{{margin-bottom:12px}}</style></head><body><div class=\"meta\"><h2>HOT Task Grid Preview</h2><div>{len(features)} task feature(s)</div><div>QA/extraction geometry: union of all task polygons</div></div><svg viewBox=\"0 0 {width} {height}\">{''.join(shapes)}{''.join(labels)}</svg></body></html>"""

    def start_validation(self):
        if not self._basic_inputs_ok(): messagebox.showerror("Input check failed", "Select the HOT Task Grid and Geofabrik PBF first."); return
        if not self._valid_ram(): messagebox.showerror("Invalid RAM", "Enter a whole number between 1 and 128 GB."); return
        self.run_button.configure(state="disabled"); self.status.set("Native Windows QA is starting…"); self.progress.set(30)
        self._set_check_text("STARTING 3RD PASS VALIDATION\n\nLOCAL INPUT CHECKS\n" + self._basic_checks() + f"\n\nJava/JOSM RAM: {self.ram_gb.get().strip()} GB\n")
        threading.Thread(target=self._native_worker, daemon=True).start()

    def _basic_checks(self):
        return "\n".join(f"PASS: {label} exists: {Path(path).name}" if Path(path).is_file() else f"FAIL: {label} missing: {path}" for label, path in (("HOT Task Grid", self.tasks_path.get()), ("Geofabrik PBF", self.pbf_path.get())))

    def _basic_inputs_ok(self): return Path(self.tasks_path.get()).is_file() and Path(self.pbf_path.get()).is_file()

    def _native_worker(self):
        try:
            repo_dir = os.path.dirname(os.path.abspath(__file__)); project_id = self.project_id.get().strip(); run_label = project_id if project_id else "local"
            output_dir = os.path.join(repo_dir, "osm_qa_buddy_results", f"project_{run_label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"); os.makedirs(output_dir, exist_ok=True)
            work_dir = os.path.join(output_dir, "work"); os.makedirs(work_dir, exist_ok=True)
            env = os.environ.copy(); env["QABOT_WORK_DIR"] = work_dir
            if project_id: env["QABOT_PROJECT_ID"] = project_id
            else: env.pop("QABOT_PROJECT_ID", None)
            command = [sys.executable, os.path.join(repo_dir, "orchestrator.py"), self.pbf_path.get(), self.tasks_path.get(), output_dir, "--ram-gb", self.ram_gb.get().strip()]
            if project_id: command.extend(["--project-id", project_id])
            self.after(0, lambda: self._append_log("\nNATIVE WINDOWS QA LIVE LOG\n" + "=" * 80 + "\n"))
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=repo_dir, env=env)
            threading.Thread(target=self._monitor_josm_dataset, args=(process, work_dir, output_dir), daemon=True).start()
            log_lines = []; assert process.stdout is not None
            for raw_line in iter(process.stdout.readline, ""):
                line = raw_line.rstrip("\r\n"); log_lines.append(line); self.after(0, lambda text=line: self._append_log(text + "\n"))
            process.stdout.close(); returncode = process.wait(); log_path = os.path.join(output_dir, "qa_run.log")
            Path(log_path).write_text("\n".join(log_lines) + "\n", encoding="utf-8")
            if returncode != 0: raise RuntimeError(f"Native QA failed (exit code {returncode}). Full log saved to:\n{log_path}")
            josm_dataset = self.last_josm_dataset or self._create_josm_dataset(work_dir, output_dir)
            self.after(0, lambda: self._native_done(output_dir, log_path, josm_dataset))
        except Exception as exc: self.after(0, lambda: self._native_failed(str(exc)))

    def _monitor_josm_dataset(self, process, work_dir, output_dir):
        marker = Path(work_dir, "sample.osm.ready.json")
        while process.poll() is None:
            if marker.is_file():
                try:
                    if json.loads(marker.read_text(encoding="utf-8")).get("ready") is True:
                        josm_dataset = self._create_josm_dataset(work_dir, output_dir); self.after(0, lambda path=josm_dataset: self._josm_dataset_ready(output_dir, path)); return
                except (OSError, json.JSONDecodeError, RuntimeError): pass
            threading.Event().wait(1)

    def _create_josm_dataset(self, work_dir, output_dir):
        source = Path(work_dir, "sample.osm")
        if not source.is_file(): raise RuntimeError("The extracted OSM dataset was not found at:\n" + str(source))
        destination = Path(output_dir, f"osm_qa_buddy_josm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.osm"); shutil.copy2(source, destination); return str(destination)

    def _josm_dataset_ready(self, output_dir, josm_dataset):
        self.last_output_dir = output_dir; self.last_josm_dataset = josm_dataset; self.josm_button.configure(state="normal"); self.folder_button.configure(state="normal")
        self.status.set("Clipped OSM is ready. You can open it in JOSM while automated QA continues.")
        self._append_log("\n" + "-" * 80 + "\nJOSM HANDOFF READY\nClipped OSM dataset:\n" + josm_dataset + "\nAutomated QA continues independently.\n" + "-" * 80 + "\n")

    def _find_josm_launcher(self):
        for name in ("josm.exe", "JOSM.exe", "josm"):
            found = shutil.which(name)
            if found: return [found]
        jar = Path(os.path.dirname(os.path.abspath(__file__)), "tools", "josm-19613.jar")
        return ["java", "-Xmx24g", "-jar", str(jar)] if jar.is_file() else None

    def open_josm(self):
        if not self.last_josm_dataset or not Path(self.last_josm_dataset).is_file(): messagebox.showerror("JOSM dataset unavailable", "The JOSM-ready OSM file is not available yet."); return
        launcher = self._find_josm_launcher()
        if not launcher: messagebox.showerror("JOSM not found", "JOSM was not found on PATH and the bundled JOSM jar is unavailable."); return
        try: subprocess.Popen(launcher + [self.last_josm_dataset], cwd=os.path.dirname(self.last_josm_dataset)); self.status.set("JOSM launched with the extracted Task Grid dataset. Automated QA continues in the background.")
        except Exception as exc: messagebox.showerror("Could not launch JOSM", str(exc))

    def open_results_folder(self):
        if self.last_output_dir and Path(self.last_output_dir).is_dir(): os.startfile(self.last_output_dir)

    def _native_done(self, output_dir, log_path, josm_dataset):
        self.last_output_dir = output_dir; self.last_josm_dataset = josm_dataset; self.josm_button.configure(state="normal"); self.folder_button.configure(state="normal"); self.progress.set(100)
        self.status.set("QA completed successfully. Task-level QA results are available.")
        self._append_log("\n" + "=" * 80 + "\nQA COMPLETED SUCCESSFULLY\n\nJOSM-ready dataset:\n" + josm_dataset + "\n\nResults:\n" + output_dir + "\n\nFull log:\n" + log_path + "\n")
        report = Path(output_dir, "report.html")
        if report.exists(): webbrowser.open(report.as_uri())
        self.run_button.configure(state="normal")

    def _native_failed(self, message):
        self.progress.set(0); self.status.set("QA failed before completion."); self._append_log("\n" + "=" * 80 + "\nQA FAILED\n" + message + "\n"); self.run_button.configure(state="normal"); messagebox.showerror("QA failed", message)

    def _append_log(self, text):
        self.check_text.configure(state="normal"); self.check_text.insert("end", text); self.check_text.see("end"); self.check_text.configure(state="disabled")

    def _set_check_text(self, text):
        self.check_text.configure(state="normal"); self.check_text.delete("1.0", "end"); self.check_text.insert("1.0", text); self.check_text.see("end"); self.check_text.configure(state="disabled")


if __name__ == "__main__": App().mainloop()
