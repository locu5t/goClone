import argparse
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SRC_DIRS = [ROOT / "cmd", ROOT / "pkg"]


def newest_go_mtime() -> float:
    mt = 0.0
    for base in SRC_DIRS:
        for path in base.rglob("*.go"):
            mt = max(mt, path.stat().st_mtime)
    return mt


def needs_build(binary: Path) -> bool:
    if not binary.exists():
        return True
    return newest_go_mtime() > binary.stat().st_mtime


def main() -> int:
    parser = argparse.ArgumentParser(description="Build goclone binary into dist/")
    parser.add_argument("--windows", action="store_true", help="Build Windows executable")
    args = parser.parse_args()

    DIST.mkdir(exist_ok=True)

    env = os.environ.copy()
    if args.windows:
        env["GOOS"] = "windows"
        env["GOARCH"] = env.get("GOARCH", "amd64")
        binary = DIST / "goclone.exe"
    else:
        binary = DIST / ("goclone.exe" if os.name == "nt" else "goclone")

    if not needs_build(binary):
        print(f"Up to date: {binary}")
        return 0

    cmd = ["go", "build", "-o", str(binary), "./cmd"]
    print("Building:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT, env=env)
    print(f"Built: {binary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
