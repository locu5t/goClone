package appconfig

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type Config struct {
	DefaultURL          string      `json:"default_url"`
	DefaultOutputFolder string      `json:"default_output_folder"`
	DefaultInputFolder  string      `json:"default_input_folder"`
	Flags               FlagsConfig `json:"flags"`
}

type FlagsConfig struct {
	Open                 *bool   `json:"open"`
	Serve                *bool   `json:"serve"`
	ServePort            *int    `json:"serve_port"`
	UserAgent            *string `json:"user_agent"`
	ProxyString          *string `json:"proxy_string"`
	Cookies              *bool   `json:"cookie"`
	CookieHeader         *string `json:"cookie_header"`
	Robots               *bool   `json:"robots"`
	BrowserEndpoint      *string `json:"browser_endpoint"`
	AssetsRoot           *string `json:"assets_root"`
	MaxConcurrentWorkers *int    `json:"max_concurrent_downloads"`
	MaxDownloadMB        *int    `json:"max_download_mb"`
	HTTPTimeoutSeconds   *int    `json:"http_timeout_seconds"`
	Verbose              *bool   `json:"verbose"`
}

func Load(configPath string) (Config, string, error) {
	if strings.TrimSpace(configPath) == "" {
		for _, candidate := range DefaultPaths() {
			if _, err := os.Stat(candidate); err == nil {
				configPath = candidate
				break
			}
		}
	}
	if strings.TrimSpace(configPath) == "" {
		return Config{}, "", nil
	}

	body, err := os.ReadFile(configPath)
	if err != nil {
		return Config{}, "", err
	}

	var cfg Config
	if err := json.Unmarshal(body, &cfg); err != nil {
		return Config{}, "", fmt.Errorf("parse config %q: %w", configPath, err)
	}
	return cfg, configPath, nil
}

func DefaultPaths() []string {
	paths := []string{filepath.Join(".", "goclone.json")}
	home, err := os.UserHomeDir()
	if err == nil {
		paths = append(paths, filepath.Join(home, ".goclone.json"))
	}
	return paths
}

func ResolveTargetArgs(args []string, cfg Config, inputFolder string) ([]string, error) {
	if len(args) > 0 {
		return args, nil
	}
	if strings.TrimSpace(cfg.DefaultURL) != "" {
		return []string{strings.TrimSpace(cfg.DefaultURL)}, nil
	}
	if strings.TrimSpace(inputFolder) == "" {
		return args, nil
	}
	file := filepath.Join(inputFolder, "urls.txt")
	fh, err := os.Open(file)
	if err != nil {
		return args, nil
	}
	defer fh.Close()

	scanner := bufio.NewScanner(fh)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line != "" && !strings.HasPrefix(line, "#") {
			return []string{line}, nil
		}
	}
	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("read %s: %w", file, err)
	}
	return args, nil
}
