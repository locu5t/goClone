package appconfig

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadConfig(t *testing.T) {
	dir := t.TempDir()
	cfgPath := filepath.Join(dir, "goclone.json")
	if err := os.WriteFile(cfgPath, []byte(`{"default_url":"https://example.com","default_output_folder":"/tmp/out","flags":{"verbose":true,"serve_port":9090}}`), 0o600); err != nil {
		t.Fatal(err)
	}

	cfg, used, err := Load(cfgPath)
	if err != nil {
		t.Fatal(err)
	}
	if used != cfgPath {
		t.Fatalf("expected used path %q, got %q", cfgPath, used)
	}
	if cfg.DefaultURL != "https://example.com" {
		t.Fatalf("unexpected URL %q", cfg.DefaultURL)
	}
	if cfg.Flags.ServePort == nil || *cfg.Flags.ServePort != 9090 {
		t.Fatalf("unexpected serve_port")
	}
}

func TestResolveTargetArgs(t *testing.T) {
	args, err := ResolveTargetArgs([]string{}, Config{DefaultURL: "https://example.org"}, "")
	if err != nil {
		t.Fatal(err)
	}
	if len(args) != 1 || args[0] != "https://example.org" {
		t.Fatalf("unexpected args: %#v", args)
	}

	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "urls.txt"), []byte("# one\n\nhttps://from-file.dev\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	args, err = ResolveTargetArgs(nil, Config{}, dir)
	if err != nil {
		t.Fatal(err)
	}
	if len(args) != 1 || args[0] != "https://from-file.dev" {
		t.Fatalf("unexpected args from file: %#v", args)
	}
}
