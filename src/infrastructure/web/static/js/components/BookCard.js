/**
 * Component: BookCard
 * Renders a single book result card
 */
import { Formatter } from "../utils/formatter.js";

export const BookCard = {
  render(book, onDownloadRaw, onOpenFlow) {
    const sourceClass = Formatter.sourceToClass(book.source);
    const author = Formatter.authorName(book.author);

    const card = document.createElement("div");
    card.className = `card-nexus ${sourceClass}`;

    card.innerHTML = `
            <div class="card-source">${book.source.toUpperCase()}</div>
            <div class="card-title">${book.title.toUpperCase()}</div>
            <div class="card-meta">
                <div class="meta-quantum"><strong>AUTH//</strong> ${author}</div>
                <div class="meta-quantum"><strong>LANG//</strong> ${book.language.toUpperCase()}</div>
                ${book.year ? `<div class="meta-quantum"><strong>DATE//</strong> ${book.year}</div>` : ""}
            </div>
            <div class="actions">
                <button class="btn-core download-raw">
                    Access Full Fragment (.txt)
                </button>
                <div class="btn-aux open-flow">PROTOCOL: .TXT</div>
            </div>
        `;

    // Modern Event Delegation within the component
    card
      .querySelector(".download-raw")
      .addEventListener("click", () => onDownloadRaw(book.link));
    card
      .querySelector(".open-flow")
      .addEventListener("click", () => onOpenFlow(book.link));

    return card;
  },
};
