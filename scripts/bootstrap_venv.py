import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv"
REQ = ROOT / "requirements.txt"


def venv_python() -> Path:
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def main() -> int:
    if not VENV.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])

    python_bin = venv_python()
    subprocess.check_call([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"])
    if REQ.exists() and REQ.stat().st_size > 0:
        subprocess.check_call([str(python_bin), "-m", "pip", "install", "-r", str(REQ)])

    print(f"venv ready: {python_bin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
