/**
 * Application Constants & Configuration
 * Relocated to JS root for better reliability in module imports
 */
export const CONFIG = {
  ENDPOINTS: {
    SEARCH: "/api/v1/books/search",
    DOWNLOAD_RAW: "/api/v1/books/download_raw",
    DOWNLOAD_FLOW: "/api/v1/books/download",
  },
  PROVIDERS: ["all", "gutenberg", "wikisource", "openlibrary"],
  DEFAULT_AUTH_PLACEHOLDER: "UNKNOWN_ENTITY",
  UI: {
    SEARCH_TITLE_PLACEHOLDER: "INIT_ARCHIVE_SEARCH('TITLE')",
    SEARCH_AUTHOR_PLACEHOLDER: "INIT_ARCHIVE_SEARCH('AUTHOR')",
  },
};
