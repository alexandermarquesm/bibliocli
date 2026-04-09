/**
 * Component: ButtonGlitch
 * Implements granular horizontal slicing glitch
 */
import { random } from "../utils/random.js";

export const ButtonGlitch = {
  getStripHTML(top, stripHeight) {
    const duration = random(5, 10);
    const name = `glitch-${duration}`;
    const delay = random(0, 2);

    return `
      <div 
        class="btn-glitch-strip" 
        style="
          --glitch-x-1: ${random(-50, 50)}px;
          --glitch-hue-1: ${random(-50, 50)}deg;
          --glitch-x-2: ${random(-50, 50)}px;
          --glitch-hue-2: ${random(-50, 50)}deg;
          top: ${top}px;
          height: ${stripHeight}px; 
          animation-name: ${name};
          animation-duration: ${duration * 1000}ms; 
          animation-delay: ${delay}s;
        "
      >
        <div class="strip-content" style="transform: translateY(-${top}px);">
            <span>EXECUTE</span>
        </div>
      </div>`;
  },

  generate(height) {
    let i = 0;
    const html = [];

    while (true) {
      const stripHeight = random(4, 12);

      if (i + stripHeight < height) {
        html.push(this.getStripHTML(i, stripHeight));
      } else {
        html.push(this.getStripHTML(i, height - i));
        break;
      }
      i = i + stripHeight;
    }

    return html.join("");
  },

  init(buttonId) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;

    // Cache busting - remove old layer if exists
    const oldLayer = btn.querySelector(".btn-glitch-strips-layer");
    if (oldLayer) oldLayer.remove();

    // Build the dynamic strips
    const layer = document.createElement("div");
    layer.className = "btn-glitch-strips-layer";
    layer.innerHTML = this.generate(56);
    btn.appendChild(layer);
  },
};
