/**
 * UI Manager Module
 * Orchestrates components and global UI state
 */
import { State } from "./state.js";
import { CONFIG } from "../config.js";
import { BookCard } from "../components/BookCard.js";

export const UI = {
  elements: {
    searchInput: document.getElementById("search-input"),
    searchBtn: document.getElementById("search-btn"),
    resultsGrid: document.getElementById("results"),
    loader: document.getElementById("loader"),
    filterNexus: document.getElementById("provider-nexus"),
    toggleIcon: document.getElementById("toggle-icon"),
    activeSourceName: document.getElementById("active-source-name"),
    typeBookBtn: document.getElementById("type-book"),
    typeAuthorBtn: document.getElementById("type-author"),
  },

  setLoading(isLoading) {
    State.isLoading = isLoading;
    this.elements.loader.style.display = isLoading ? "block" : "none";
    if (isLoading) this.elements.resultsGrid.innerHTML = "";
  },

  updateSearchType(type) {
    State.currentSearchType = type;
    this.elements.typeBookBtn.classList.toggle("active", type === "book");
    this.elements.typeAuthorBtn.classList.toggle("active", type === "author");
    this.elements.searchInput.placeholder =
      type === "book"
        ? CONFIG.UI.SEARCH_TITLE_PLACEHOLDER
        : CONFIG.UI.SEARCH_AUTHOR_PLACEHOLDER;
  },

  updateProvider(prov) {
    State.currentProvider = prov;
    CONFIG.PROVIDERS.forEach((p) => {
      const el = document.getElementById(`prov-${p}`);
      if (el) el.classList.toggle("active", p === prov);
    });
    this.elements.activeSourceName.innerText =
      prov.toUpperCase() === "ALL" ? "ALL_SOURCES" : prov.toUpperCase();
  },

  toggleFilters() {
    const isVisible = this.elements.filterNexus.classList.toggle("visible");
    this.elements.toggleIcon.innerText = isVisible ? "-" : "+";
  },

  renderResults(results, actions) {
    this.elements.resultsGrid.innerHTML = "";

    if (results.length === 0) {
      this.elements.resultsGrid.innerHTML =
        '<div class="empty-nexus">NO DATA FRAGMENTS FOUND_</div>';
      return;
    }

    results.forEach((book) => {
      const card = BookCard.render(
        book,
        actions?.onDownloadRaw || (() => console.warn("DOWNLOAD_RAW_NOT_IMPLEMENTED")),
        actions?.onOpenFlow || (() => console.warn("OPEN_FLOW_NOT_IMPLEMENTED")),
      );
      this.elements.resultsGrid.appendChild(card);
    });
  },

  showError(error) {
    console.error("CRITICAL_SYSTEM_ERROR:", error);
    this.setLoading(false);
    this.elements.resultsGrid.innerHTML =
      '<div class="empty-nexus">CONNECTION_INTERRUPTED_</div>';
  },
};
