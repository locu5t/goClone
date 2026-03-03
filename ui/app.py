import os
import queue
import subprocess
import threading
import tkinter as tk
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
        self.log_queue: queue.Queue[str] = queue.Queue()

        self.url_var = tk.StringVar(value="https://example.com")
        self.output_var = tk.StringVar(value=str(Path.home() / "goclone-output"))
        self.user_agent_var = tk.StringVar(value="goclone")
        self.proxy_var = tk.StringVar()
        self.browser_endpoint_var = tk.StringVar()
        self.assets_root_var = tk.StringVar(value="assets")
        self.max_download_mb_var = tk.StringVar(value="50")
        self.max_concurrent_var = tk.StringVar(value="8")
        self.http_timeout_var = tk.StringVar(value="20")
        self.serve_port_var = tk.StringVar(value="8088")

        self.open_var = tk.BooleanVar(value=False)
        self.serve_var = tk.BooleanVar(value=False)
        self.cookie_var = tk.BooleanVar(value=False)
        self.robots_var = tk.BooleanVar(value=False)
        self.verbose_var = tk.BooleanVar(value=True)

        self._build_widgets()
        self._poll_logs()

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self.master, padding=12)
        frame.grid(sticky="nsew")

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        row = 0
        self._add_entry(frame, row, "URL", self.url_var)
        row += 1
        self._add_output_selector(frame, row)
        row += 1
        self._add_entry(frame, row, "User-Agent", self.user_agent_var)
        row += 1
        self._add_entry(frame, row, "Proxy String", self.proxy_var)
        row += 1
        self._add_entry(frame, row, "Browser Endpoint", self.browser_endpoint_var)
        row += 1
        self._add_entry(frame, row, "Assets Root", self.assets_root_var)
        row += 1

        numbers = ttk.Frame(frame)
        numbers.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        numbers.columnconfigure((1, 3, 5, 7), weight=1)
        self._add_small_entry(numbers, 0, "Serve Port", self.serve_port_var)
        self._add_small_entry(numbers, 2, "Max MB", self.max_download_mb_var)
        self._add_small_entry(numbers, 4, "Max Concurrent", self.max_concurrent_var)
        self._add_small_entry(numbers, 6, "HTTP Timeout", self.http_timeout_var)
        row += 1

        checks = ttk.Frame(frame)
        checks.grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 8))
        for txt, var in [
            ("Open", self.open_var),
            ("Serve", self.serve_var),
            ("Disable Cookies", self.cookie_var),
            ("Robots", self.robots_var),
            ("Verbose", self.verbose_var),
        ]:
            ttk.Checkbutton(checks, text=txt, variable=var).pack(side=tk.LEFT, padx=(0, 12))
        row += 1

        buttons = ttk.Frame(frame)
        buttons.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        ttk.Button(buttons, text="Start Clone", command=self.start_clone).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Stop", command=self.stop_clone).pack(side=tk.LEFT, padx=(8, 0))
        row += 1

        self.log = tk.Text(frame, height=18, wrap="word")
        self.log.grid(row=row, column=0, columnspan=3, sticky="nsew")
        frame.rowconfigure(row, weight=1)

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
        if "#" in url and not self.browser_endpoint_var.get().strip():
            self._append_log(
                "Warning: URL contains a fragment (#...). Fragments are client-side only and may cause 404 from the server.\n"
                "Tip: for SPA/login pages, run with --browser_endpoint to use a headless browser renderer.\n\n"
            )
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
