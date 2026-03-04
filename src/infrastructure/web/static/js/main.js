/**
 * BiblioCLI - Main Application Entry Point
 * Controller Layer
 */
import { State } from "./modules/state.js";
import { API } from "./modules/api.js";
import { UI } from "./modules/ui.js";
import { ButtonGlitch } from "./components/ButtonGlitch.js";

const App = {
  init() {
    this.bindEvents();
    ButtonGlitch.init("search-btn");
  },

  bindEvents() {
    // Standard Search
    UI.elements.searchBtn.addEventListener("click", () => this.handleSearch());
    UI.elements.searchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") this.handleSearch();
    });

    // Toggle Filters
    const toggleBtn = document.getElementById("filter-toggle-btn");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", (e) => {
        e.preventDefault();
        UI.toggleFilters();
      });
    }

    // Modern Event Binding for Search HUD (No more onclick in HTML)
    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".hud-btn");
      if (!btn) return;

      const id = btn.id;
      if (id.startsWith("type-")) {
        const type = id.replace("type-", "");
        UI.updateSearchType(type);
      } else if (id.startsWith("prov-")) {
        const prov = id.replace("prov-", "");
        UI.updateProvider(prov);
      }
    });
  },

  async handleSearch() {
    const query = UI.elements.searchInput.value.trim();
    if (!query) return;

    UI.setLoading(true);

    try {
      const results = await API.search(
        query,
        State.currentSearchType,
        State.currentProvider,
      );
      UI.renderResults(
        results,
        (url) => this.handleDownloadRaw(url),
        (url) => this.handleOpenFlow(url),
      );
      UI.setLoading(false);
    } catch (error) {
      UI.showError(error);
    }
  },

  handleDownloadRaw(url) {
    window.location.href = API.getDownloadRawUrl(url);
  },

  handleOpenFlow(url) {
    window.open(API.getDownloadFlowUrl(url), "_blank");
  },
};

// Start the Protocol
document.addEventListener("DOMContentLoaded", () => App.init());
