/**
 * Data Formatting Utilities
 */
import { CONFIG } from "../config.js";

export const Formatter = {
  /**
   * Formats author names from "Last, First" to "First Last"
   */
  authorName(rawName) {
    if (!rawName) return CONFIG.DEFAULT_AUTH_PLACEHOLDER;

    if (rawName.includes(",")) {
      const parts = rawName.split(",");
      return `${parts[1].trim()} ${parts[0].trim()}`;
    }

    return rawName;
  },

  /**
   * Normalizes source names for CSS class usage
   */
  sourceToClass(source) {
    if (source.toLowerCase().includes("gutenberg")) return "gutenberg";
    if (source.toLowerCase().includes("openlibrary")) return "openlibrary";
    return "wikisource";
  },
};
