import os
import queue
import socket
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).resolve().parent.parent
DIST_EXE = ROOT / "dist" / "goclone.exe"
DIST_BIN = ROOT / "dist" / "goclone"


class GoCloneUI:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("goClone UI")
        self.proc: subprocess.Popen[str] | None = None
        self.preview_proc: subprocess.Popen[str] | None = None
        self.log_queue: queue.Queue[str] = queue.Queue()

        self.url_var = tk.StringVar(value="https://example.com")
        self.output_var = tk.StringVar(value=str(Path.home() / "goclone-output"))
        self.user_agent_var = tk.StringVar(value="goclone")
        self.proxy_var = tk.StringVar()
        self.browser_endpoint_var = tk.StringVar()
        self.cookie_header_var = tk.StringVar()
        self.assets_root_var = tk.StringVar(value="assets")
        self.max_download_mb_var = tk.StringVar(value="50")
        self.max_concurrent_var = tk.StringVar(value="8")
        self.http_timeout_var = tk.StringVar(value="20")
        self.serve_port_var = tk.StringVar(value="8088")

        self.preview_port_var = tk.StringVar(value="8090")
        self.preview_source_dir_var = tk.StringVar()
        self.preview_url_var = tk.StringVar(value="Preview URL: not running")

        self.open_var = tk.BooleanVar(value=False)
        self.serve_var = tk.BooleanVar(value=False)
        self.cookie_var = tk.BooleanVar(value=False)
        self.robots_var = tk.BooleanVar(value=False)
        self.verbose_var = tk.BooleanVar(value=True)

        self._build_widgets()
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)
        self._poll_logs()

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self.master, padding=12)
        frame.grid(sticky="nsew")

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        notebook = ttk.Notebook(frame)
        notebook.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)

        clone_tab = ttk.Frame(notebook, padding=10)
        existing_tab = ttk.Frame(notebook, padding=10)
        notebook.add(clone_tab, text="Clone Website")
        notebook.add(existing_tab, text="Load Existing Clone")

        self._build_clone_tab(clone_tab)
        self._build_existing_clone_tab(existing_tab)

        self.log = tk.Text(frame, height=14, wrap="word")
        self.log.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        frame.rowconfigure(1, weight=1)

    def _build_clone_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        row = 0
        self._add_entry(parent, row, "URL", self.url_var)
        row += 1
        self._add_output_selector(parent, row)
        row += 1
        self._add_entry(parent, row, "User-Agent", self.user_agent_var)
        row += 1
        self._add_entry(parent, row, "Proxy String", self.proxy_var)
        row += 1
        self._add_entry(parent, row, "Browser Endpoint", self.browser_endpoint_var)
        row += 1
        self._add_entry(parent, row, "Cookie Header", self.cookie_header_var)
        row += 1
        self._add_entry(parent, row, "Assets Root", self.assets_root_var)
        row += 1

        numbers = ttk.Frame(parent)
        numbers.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        numbers.columnconfigure((1, 3, 5, 7), weight=1)
        self._add_small_entry(numbers, 0, "Serve Port", self.serve_port_var)
        self._add_small_entry(numbers, 2, "Max MB", self.max_download_mb_var)
        self._add_small_entry(numbers, 4, "Max Concurrent", self.max_concurrent_var)
        self._add_small_entry(numbers, 6, "HTTP Timeout", self.http_timeout_var)
        row += 1

        checks = ttk.Frame(parent)
        checks.grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 8))
        for txt, var in [
            ("Open", self.open_var),
            ("Serve", self.serve_var),
            ("Cookie", self.cookie_var),
            ("Robots", self.robots_var),
            ("Verbose", self.verbose_var),
        ]:
            ttk.Checkbutton(checks, text=txt, variable=var).pack(side=tk.LEFT, padx=(0, 12))
        row += 1

        buttons = ttk.Frame(parent)
        buttons.grid(row=row, column=0, columnspan=3, sticky="ew")
        ttk.Button(buttons, text="Start Clone", command=self.start_clone).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Stop Clone", command=self.stop_clone).pack(side=tk.LEFT, padx=(8, 0))

    def _build_existing_clone_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)

        ttk.Label(
            parent,
            text="Use this screen to load and preview a previously cloned website directory.",
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(parent, text="Cloned Site Directory").grid(row=1, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(parent, textvariable=self.preview_source_dir_var).grid(row=1, column=1, sticky="ew", pady=(0, 4))
        ttk.Button(parent, text="Browse", command=self.browse_existing_clone).grid(row=1, column=2, sticky="e", pady=(0, 4))

        preview = ttk.LabelFrame(parent, text="Preview", padding=8)
        preview.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 8))
        preview.columnconfigure(5, weight=1)

        ttk.Label(preview, text="Preview Port").grid(row=0, column=0, sticky="w")
        ttk.Entry(preview, textvariable=self.preview_port_var, width=8).grid(row=0, column=1, sticky="w", padx=(6, 10))
        ttk.Button(preview, text="Run Preview", command=self.start_preview_from_selected_dir).grid(row=0, column=2, sticky="w")
        ttk.Button(preview, text="Stop Preview", command=self.stop_preview).grid(row=0, column=3, sticky="w", padx=(8, 0))
        ttk.Button(preview, text="Open in Browser", command=self.open_preview_url).grid(row=0, column=4, sticky="w", padx=(8, 0))
        ttk.Label(preview, textvariable=self.preview_url_var).grid(row=1, column=0, columnspan=6, sticky="w", pady=(8, 0))

        actions = ttk.Frame(parent)
        actions.grid(row=3, column=0, columnspan=3, sticky="w")
        ttk.Button(actions, text="Use Derived Clone Folder", command=self.start_preview).pack(side=tk.LEFT)

    def _add_entry(self, parent: ttk.Frame, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, columnspan=2, sticky="ew", pady=(0, 4))

    def _add_small_entry(self, parent: ttk.Frame, col: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=0, column=col, sticky="w", padx=(0, 4))
        ttk.Entry(parent, textvariable=var, width=8).grid(row=0, column=col + 1, sticky="ew", padx=(0, 8))

    def _add_output_selector(self, parent: ttk.Frame, row: int) -> None:
        ttk.Label(parent, text="Output Directory").grid(row=row, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(parent, textvariable=self.output_var).grid(row=row, column=1, sticky="ew", pady=(0, 4))
        ttk.Button(parent, text="Browse", command=self.browse_output).grid(row=row, column=2, sticky="e", pady=(0, 4))

    def browse_output(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.output_var.get() or str(Path.home()))
        if selected:
            self.output_var.set(selected)

    def browse_existing_clone(self) -> None:
        initial_dir = self.preview_source_dir_var.get() or self.output_var.get() or str(Path.home())
        selected = filedialog.askdirectory(initialdir=initial_dir)
        if selected:
            self.preview_source_dir_var.set(selected)

    def _binary_path(self) -> Path:
        if os.name == "nt":
            return DIST_EXE
        return DIST_BIN if DIST_BIN.exists() else DIST_EXE

    def start_clone(self) -> None:
        if self.proc and self.proc.poll() is None:
            messagebox.showinfo("goClone", "Clone is already running.")
            return

        binary = self._binary_path()
        if not binary.exists():
            messagebox.showerror("goClone", f"Binary not found: {binary}\nBuild it first (run.bat or go build).")
            return

        url = self.url_var.get().strip()
        out_dir = Path(self.output_var.get().strip())
        if not url:
            messagebox.showerror("goClone", "URL is required.")
            return

        out_dir.mkdir(parents=True, exist_ok=True)
        args = self._build_args(url)

        self.log.delete("1.0", tk.END)
        self._append_log(f"Running in {out_dir}\n{binary} {' '.join(args)}\n\n")

        self.proc = subprocess.Popen(
            [str(binary), *args],
            cwd=out_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        threading.Thread(target=self._capture_output, daemon=True).start()

    def _build_args(self, url: str) -> list[str]:
        args = [url, "--user_agent", self.user_agent_var.get(), "--assets_root", self.assets_root_var.get()]

        args.extend(["--servePort", self.serve_port_var.get()])
        args.extend(["--max_download_mb", self.max_download_mb_var.get()])
        args.extend(["--max_concurrent_downloads", self.max_concurrent_var.get()])
        args.extend(["--http_timeout_seconds", self.http_timeout_var.get()])

        if self.proxy_var.get().strip():
            args.extend(["--proxy_string", self.proxy_var.get().strip()])
        if self.browser_endpoint_var.get().strip():
            args.extend(["--browser_endpoint", self.browser_endpoint_var.get().strip()])
        if self.cookie_header_var.get().strip():
            args.extend(["--cookie_header", self.cookie_header_var.get().strip()])

        if self.open_var.get():
            args.append("--open")
        if self.serve_var.get():
            args.append("--serve")
        if self.cookie_var.get():
            args.append("--cookie")
        if self.robots_var.get():
            args.append("--robots")
        if self.verbose_var.get():
            args.append("--verbose")

        return args

    def stop_clone(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self._append_log("\nStopped by user.\n")

    def _project_dir(self) -> Path:
        url = self.url_var.get().strip().replace("https://", "").replace("http://", "")
        host = url.split("/")[0].strip()
        return Path(self.output_var.get().strip()) / host

    def start_preview_from_selected_dir(self) -> None:
        selected_dir = Path(self.preview_source_dir_var.get().strip())
        self._start_preview(selected_dir)

    def start_preview(self) -> None:
        self._start_preview(self._project_dir())

    def _start_preview(self, project_dir: Path) -> None:
        if self.preview_proc and self.preview_proc.poll() is None:
            messagebox.showinfo("goClone", "Preview server is already running.")
            return

        if not str(project_dir).strip():
            messagebox.showerror("goClone", "Select a cloned site directory first.")
            return

        if not project_dir.exists() or not project_dir.is_dir():
            messagebox.showerror("goClone", f"Cloned project not found: {project_dir}")
            return

        port = self.preview_port_var.get().strip()
        if not port.isdigit():
            messagebox.showerror("goClone", "Preview port must be numeric.")
            return

        if self._port_in_use(int(port)):
            messagebox.showerror("goClone", f"Port {port} is already in use.")
            return

        self.preview_proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", port],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        threading.Thread(target=self._capture_preview_output, daemon=True).start()

        preview_url = f"http://127.0.0.1:{port}/"
        self.preview_url_var.set(f"Preview URL: {preview_url}")
        self._append_log(f"\nPreview started from {project_dir} at {preview_url}\n")

    def stop_preview(self) -> None:
        if self.preview_proc and self.preview_proc.poll() is None:
            self.preview_proc.terminate()
            self._append_log("Preview stopped by user.\n")
        self.preview_url_var.set("Preview URL: not running")

    def open_preview_url(self) -> None:
        if not (self.preview_proc and self.preview_proc.poll() is None):
            messagebox.showinfo("goClone", "Start preview first.")
            return
        preview_url = self.preview_url_var.get().replace("Preview URL: ", "").strip()
        if preview_url and preview_url != "not running":
            webbrowser.open(preview_url)

    def _capture_preview_output(self) -> None:
        if not self.preview_proc or not self.preview_proc.stdout:
            return
        for line in self.preview_proc.stdout:
            self.log_queue.put(f"[preview] {line}")
        code = self.preview_proc.wait()
        self.log_queue.put(f"[preview] Process exited with code {code}.\n")

    def _port_in_use(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            return s.connect_ex(("127.0.0.1", port)) == 0

    def _on_close(self) -> None:
        self.stop_clone()
        self.stop_preview()
        self.master.destroy()

    def _capture_output(self) -> None:
        if not self.proc or not self.proc.stdout:
            return
        for line in self.proc.stdout:
            self.log_queue.put(line)
        code = self.proc.wait()
        self.log_queue.put(f"\nProcess exited with code {code}.\n")

    def _poll_logs(self) -> None:
        while True:
            try:
                line = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self._append_log(line)
        self.master.after(100, self._poll_logs)

    def _append_log(self, text: str) -> None:
        self.log.insert(tk.END, text)
        self.log.see(tk.END)


def main() -> None:
    root = tk.Tk()
    root.geometry("980x620")
    GoCloneUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
