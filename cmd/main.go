package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"

	"github.com/spf13/cobra"

	"github.com/shurco/goClone/pkg/appconfig"
	"github.com/shurco/goClone/pkg/crawler"
)

var (
	gitCommit = "00000000"
	version   = "0.0.1"
	buildDate = "2023-07-07"
)

func main() {
	flags := crawler.Flags{}
	configPath := ""
	outputFolder := ""
	inputFolder := ""

	rootCmd := &cobra.Command{
		Use:     "goclone <url>",
		Short:   "Clone a website with ease!",
		Long:    `Copy websites to your computer! goclone is a utility that allows you to download a website from the Internet to a local directory. Get html, css, js, images, and other files from the server to your computer. goclone arranges the original site's relative link-structure. Simply open a page of the "mirrored" website in your browser, and you can browse the site from link to link, as if you were viewing it online.`,
		Args:    cobra.ArbitraryArgs,
		Version: fmt.Sprintf("%s (%s), %s", version, gitCommit, buildDate),
		Run: func(cmd *cobra.Command, args []string) {
			cfg, usedConfigPath, err := appconfig.Load(configPath)
			if err != nil {
				log.Fatal(err)
			}

			applyConfigDefaults(cmd, &flags, cfg, &outputFolder, &inputFolder)
			resolvedArgs, err := appconfig.ResolveTargetArgs(args, cfg, inputFolder)
			if err != nil {
				log.Fatal(err)
			}

			if strings.TrimSpace(outputFolder) != "" {
				if err := os.MkdirAll(outputFolder, os.ModePerm); err != nil {
					log.Fatal(err)
				}
				if err := os.Chdir(outputFolder); err != nil {
					log.Fatal(err)
				}
			}

			if flags.Verbose && usedConfigPath != "" {
				log.Printf("using config: %s", usedConfigPath)
			}

			if len(resolvedArgs) < 1 {
				if err := cmd.Usage(); err != nil {
					log.Fatal(err)
				}
				return
			}
			ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
			defer stop()
			if err := crawler.CloneSite(ctx, resolvedArgs, flags); err != nil {
				log.Printf("%+v", err)
				os.Exit(1)
			}
		},
	}

	pf := rootCmd.PersistentFlags()
	pf.BoolVarP(&flags.Open, "open", "o", false, "automatically open project in default browser")
	pf.BoolVarP(&flags.Serve, "serve", "s", false, "serve the generated files using gofiber")
	pf.IntVarP(&flags.ServePort, "servePort", "P", 8088, "serve port number")
	pf.StringVarP(&flags.ProxyString, "proxy_string", "p", "", "proxy connection string")
	pf.StringVarP(&flags.UserAgent, "user_agent", "u", "goclone", "custom User-Agent")
	pf.BoolVarP(&flags.Cookies, "cookie", "c", false, "if set true, cookies won't send")
	pf.StringVar(&flags.CookieHeader, "cookie_header", "", "raw Cookie header value for authenticated requests")
	pf.BoolVarP(&flags.Robots, "robots", "r", false, "disable robots.txt checks")
	pf.StringVarP(&flags.BrowserEndpoint, "browser_endpoint", "b", "", "chrome headless browser WS endpoint")
	pf.StringVar(&flags.AssetsRoot, "assets_root", "assets", "root directory for downloaded assets")
	pf.StringVar(&outputFolder, "output_folder", "", "output directory where cloned projects are stored")
	pf.StringVar(&inputFolder, "input_folder", "", "directory containing urls.txt used when no URL argument is provided")
	pf.StringVar(&configPath, "config", "", "path to JSON config file (defaults to ./goclone.json or ~/.goclone.json)")
	pf.IntVar(&flags.MaxConcurrentWorkers, "max_concurrent_downloads", 8, "maximum number of concurrent downloads")
	pf.IntVar(&flags.MaxDownloadMB, "max_download_mb", 50, "maximum size of a downloaded asset in MB")
	pf.IntVar(&flags.HTTPTimeoutSeconds, "http_timeout_seconds", 20, "HTTP request timeout for asset downloads (seconds)")
	pf.BoolVarP(&flags.Verbose, "verbose", "v", false, "enable verbose logging")

	if err := rootCmd.Execute(); err != nil {
		log.Fatal(err)
	}
}

func applyConfigDefaults(cmd *cobra.Command, flags *crawler.Flags, cfg appconfig.Config, outputFolder *string, inputFolder *string) {
	applyBool := func(flagName string, target *bool, src *bool) {
		if src != nil && !cmd.Flags().Changed(flagName) {
			*target = *src
		}
	}
	applyInt := func(flagName string, target *int, src *int) {
		if src != nil && !cmd.Flags().Changed(flagName) {
			*target = *src
		}
	}
	applyString := func(flagName string, target *string, src *string) {
		if src != nil && !cmd.Flags().Changed(flagName) {
			*target = *src
		}
	}

	f := cfg.Flags
	applyBool("open", &flags.Open, f.Open)
	applyBool("serve", &flags.Serve, f.Serve)
	applyInt("servePort", &flags.ServePort, f.ServePort)
	applyString("proxy_string", &flags.ProxyString, f.ProxyString)
	applyString("user_agent", &flags.UserAgent, f.UserAgent)
	applyBool("cookie", &flags.Cookies, f.Cookies)
	applyString("cookie_header", &flags.CookieHeader, f.CookieHeader)
	applyBool("robots", &flags.Robots, f.Robots)
	applyString("browser_endpoint", &flags.BrowserEndpoint, f.BrowserEndpoint)
	applyString("assets_root", &flags.AssetsRoot, f.AssetsRoot)
	applyInt("max_concurrent_downloads", &flags.MaxConcurrentWorkers, f.MaxConcurrentWorkers)
	applyInt("max_download_mb", &flags.MaxDownloadMB, f.MaxDownloadMB)
	applyInt("http_timeout_seconds", &flags.HTTPTimeoutSeconds, f.HTTPTimeoutSeconds)
	applyBool("verbose", &flags.Verbose, f.Verbose)

	if strings.TrimSpace(*outputFolder) == "" {
		*outputFolder = strings.TrimSpace(cfg.DefaultOutputFolder)
	}
	if strings.TrimSpace(*inputFolder) == "" {
		*inputFolder = strings.TrimSpace(cfg.DefaultInputFolder)
	}
}
