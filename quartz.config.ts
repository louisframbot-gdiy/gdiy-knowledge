import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

const config: QuartzConfig = {
  configuration: {
    pageTitle: "GDIY Knowledge",
    pageTitleSuffix: " · GDIY",
    enableSPA: true,
    enablePopovers: true,
    analytics: {
      provider: "plausible",
    },
    locale: "fr-FR",
    baseUrl: "louisframbot-gdiy.github.io/gdiy-knowledge",
    ignorePatterns: [
      "private",
      "templates",
      ".obsidian",
      "_drafts",
      "Newsletter",
    ],
    defaultDateType: "modified",
    theme: {
      fontOrigin: "googleFonts",
      cdnCaching: true,
      typography: {
        header: "Inter",
        body: "Inter",
        code: "IBM Plex Mono",
      },
      colors: {
        lightMode: {
          light: "#ffffff",
          lightgray: "#f0f0f0",
          gray: "#b8b8b8",
          darkgray: "#2a2a2a",
          dark: "#0d0d0d",
          secondary: "#00FFAD",
          tertiary: "#00FFAD",
          highlight: "rgba(0, 255, 173, 0.08)",
          textHighlight: "rgba(0, 255, 173, 0.2)",
        },
        darkMode: {
          light: "#0d0d0d",
          lightgray: "#1a1a1a",
          gray: "#444444",
          darkgray: "#cccccc",
          dark: "#f0f0f0",
          secondary: "#00FFAD",
          tertiary: "#00FFAD",
          highlight: "rgba(0, 255, 173, 0.1)",
          textHighlight: "rgba(0, 255, 173, 0.25)",
        },
      },
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({
        priority: ["frontmatter", "git", "filesystem"],
      }),
      Plugin.SyntaxHighlighting({
        theme: {
          light: "github-light",
          dark: "github-dark",
        },
        keepBackground: false,
      }),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents(),
      Plugin.CrawlLinks({ markdownLinkResolution: "shortest" }),
      Plugin.Description(),
    ],
    filters: [Plugin.RemoveDrafts()],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({
        enableSiteMap: true,
        enableRSS: true,
      }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.Favicon(),
      Plugin.NotFoundPage(),
    ],
  },
}

export default config
