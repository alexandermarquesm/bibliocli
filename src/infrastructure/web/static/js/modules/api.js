/**
 * API Communication Module
 * Uses centralized config for endpoints
 */
import { CONFIG } from "../config.js";

export const API = {
  async search(query, type, provider) {
    const url = `${CONFIG.ENDPOINTS.SEARCH}?query=${encodeURIComponent(query)}&search_type=${type}&provider_name=${provider}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  },

  getDownloadRawUrl(url) {
    return `${CONFIG.ENDPOINTS.DOWNLOAD_RAW}?url=${encodeURIComponent(url)}`;
  },

  getDownloadFlowUrl(url) {
    return `${CONFIG.ENDPOINTS.DOWNLOAD_FLOW}?url=${encodeURIComponent(url)}`;
  },
};
