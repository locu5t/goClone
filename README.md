# 🌱 goClone

<a href="https://github.com/shurco/goClone/releases"><img src="https://img.shields.io/github/v/release/shurco/goclone?sort=semver&label=Release&color=651FFF"></a>
<a href="https://goreportcard.com/report/github.com/shurco/goClone"><img src="https://goreportcard.com/badge/github.com/shurco/goClone"></a>
<a href="https://www.codefactor.io/repository/github/shurco/goclone"><img src="https://www.codefactor.io/repository/github/shurco/goclone/badge" alt="CodeFactor" /></a>
<a href="https://github.com/shurco/goClone/actions/workflows/release.yml"><img src="https://github.com/shurco/goClone/actions/workflows/release.yml/badge.svg"></a>
<a href="https://github.com/shurco/goClone/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>


goClone is a powerful utility that enables you to effortlessly download entire websites from the Internet and save them to your local directory. With goClone, you can easily obtain HTML, CSS, JavaScript, images, and other associated files directly from the server and store them on your computer.

One of the standout features of goClone is its ability to accurately preserve the original website's relative link structure. This means that when you open any page of the "mirrored" website in your browser, you can seamlessly navigate through the site by following links just as if you were browsing it online.

goClone empowers you to have offline access to websites, making it convenient for various purposes such as research, archiving, or simply enjoying a website without an internet connection.

So go ahead, give goClone a try and experience the freedom of having your favorite websites at your fingertips, even when you're offline!

![Example](/.github/media/example.gif)

<a name="macos"></a>
## MacOS installing

```shell
$ brew install shurco/tap/goclone
```

Alternately, you can configure the tap and install the package separately:

``` shell
$ brew tap shurco/tap
$ brew install goclone
```


<a name="manual"></a>

## Manual

```bash
# go get :)
go get github.com/shurco/goClone
# change to project directory using your GOPATH
cd $GOPATH/src/github.com/shurco/goClone/cmd
# build and install application
go install
```


<a name="examples"></a>

## Examples

```bash
# goclone <url>
goclone https://domain.com
```

<a name="usage"></a>

## Usage

```
Usage:
  goclone <url> [flags]

Flags:
  -b, --browser_endpoint string        chrome headless browser WS endpoint
  -c, --cookie                         if set true, cookies won't send
      --cookie_header string           raw Cookie header value for authenticated requests
  -h, --help                           help for goclone
      --config string                  path to JSON config file (defaults to ./goclone.json or ~/.goclone.json)
      --input_folder string            directory containing urls.txt used when no URL argument is provided
  -o, --open                           automatically open project in default browser
      --output_folder string           output directory where cloned projects are stored
  -p, --proxy_string string            proxy connection string
  -r, --robots                         disable robots.txt checks
  -s, --serve                          serve the generated files using gofiber
  -P, --servePort int                  serve port number (default 8088)
  -u, --user_agent string              custom User-Agent (default "goclone")
      --assets_root string             root directory for downloaded assets (default "assets")
      --max_concurrent_downloads int   maximum number of concurrent downloads (default 8)
      --max_download_mb int            maximum size of a downloaded asset in MB (default 50)
      --http_timeout_seconds int       HTTP request timeout for asset downloads (seconds) (default 20)
  -v, --verbose                        enable verbose logging
```


## Config file

You can define default values in `goclone.json` (current directory) or `~/.goclone.json`, or pass a custom file with `--config`.

Example:

```json
{
  "default_url": "https://example.com",
  "default_output_folder": "/tmp/goclone",
  "default_input_folder": "/tmp/goclone-input",
  "flags": {
    "open": false,
    "serve": false,
    "serve_port": 8088,
    "user_agent": "goclone",
    "proxy_string": "",
    "cookie": false,
    "cookie_header": "",
    "robots": false,
    "browser_endpoint": "",
    "assets_root": "assets",
    "max_concurrent_downloads": 8,
    "max_download_mb": 50,
    "http_timeout_seconds": 20,
    "verbose": true
  }
}
```

Notes:
- CLI flags still win over config values.
- If URL argument is omitted, `default_url` is used.
- If URL argument and `default_url` are omitted, goClone tries `<default_input_folder>/urls.txt` (or `--input_folder/urls.txt`) and uses the first non-empty, non-comment line.
- `default_output_folder` (or `--output_folder`) changes the working directory before cloning.

## Making JS Rendered Requests

JS Rendered requests can be made using ```-b``` flag. For example start image :  


``` bash
docker run -d -p 9222:9222 --rm --name headless-shell chromedp/headless-shell
```

then run goclone: 

```bash
goclone -b "ws://localhost:9222" https://domain.com
```


## Cloning authenticated pages

For pages that require login (e.g. app dashboards), pass your session cookies as a raw `Cookie` header:

```bash
goclone --cookie_header "sessionid=...; other_cookie=..." https://example.com/app
```

Notes:
- `--cookie_header` is sent on crawler requests and asset downloads.
- Browser profiles (Chrome/Brave) are not read automatically; export/copy the cookies you need and pass them explicitly.
- Be careful not to commit shell history or logs that contain sensitive cookie values.

## JS-rendered pages (browser_endpoint)

To crawl JS-rendered pages, run with a Chrome DevTools endpoint and pass it via `-b/--browser_endpoint`.

Example:

```bash
# Start Chrome headless with DevTools (Docker)
docker run -d -p 9222:9222 --rm --name headless chromedp/headless-shell:stable
# Retrieve full DevTools WS URL (optional)
curl -s http://127.0.0.1:9222/json/version | jq -r .webSocketDebuggerUrl
# Run goclone with rendering
goclone -b ws://127.0.0.1:9222 https://example.com
```

### Linux notes (Docker networking)
If you run Chrome inside Docker on Linux, the container might not be able to reach `http://127.0.0.1:<port>` served on the host. Use one of the following approaches:

- Host networking (simple and recommended for local testing):
  ```bash
  docker rm -f headless || true
  docker run -d --net=host --rm --name headless chromedp/headless-shell:stable
  goclone -b ws://127.0.0.1:9222 http://127.0.0.1:18088
  ```
- Shared Docker network with a server in a container:
  ```bash
  docker network create goclone-net || true
  docker run -d --network goclone-net --name headless chromedp/headless-shell:stable
  docker run -d --network goclone-net --name web -p 18088:18088 your/web:latest
  goclone -b ws://127.0.0.1:9222 http://web:18088
  ```
- Use the host IP address reachable from the container (instead of 127.0.0.1):
  ```bash
  HOST_IP=$(ip route | awk '/default/ {print $3}')
  goclone -b ws://127.0.0.1:9222 http://$HOST_IP:18088
  ```

If rendering produces errors like `ERR_CONNECTION_REFUSED` or `ERR_NAME_NOT_RESOLVED`, adjust Docker networking as above and ensure you pass the full DevTools WebSocket URL from `/json/version` if necessary.


## Windows quick start (Go CLI + Python UI)

### Prerequisites

- Go **1.21+** (with `go` available in PATH)
- Python **3.10+** (with `python` available in PATH)

### One-command run (recommended)

From repo root in `cmd.exe`:

```bat
run.bat
```

`run.bat` will:
1. Create or reuse `.venv`
2. Install Python deps from `requirements.txt`
3. Build `dist\goclone.exe` when missing or stale
4. Launch the Tkinter UI

### Build only (Windows binary)

```bat
python scripts\build_goclone.py --windows
```

This writes `dist\goclone.exe`.

### Python UI usage

The UI (`ui/app.py`) lets you set:
- Target URL
- Output directory (clone is executed with this directory as working directory)
- Core CLI options/flags (`--user_agent`, `--proxy_string`, `--browser_endpoint`, `--assets_root`, `--servePort`, `--max_download_mb`, `--max_concurrent_downloads`, `--http_timeout_seconds`, and boolean flags)

The lower panel streams process logs and final exit code from the Go binary.

The UI also includes a **Preview cloned website** section that can:
- Start a local test server rooted at the cloned host folder
- Show the preview URL
- Open that URL in your default browser so you can test the cloned site like a live web app

### Troubleshooting

- **`python` not found**: install Python 3.10+ and enable "Add python.exe to PATH".
- **`go` not found**: install Go 1.21+ and confirm `go version` works in a new terminal.
- **Tkinter missing** (rare on custom Python builds): reinstall Python with Tk/Tcl support.
- **Binary not found in UI**: run `run.bat` or build manually using the command above.
