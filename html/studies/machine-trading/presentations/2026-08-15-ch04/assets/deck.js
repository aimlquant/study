(function () {
  "use strict";

  const slides = Array.from(document.querySelectorAll(".slide"));
  const counter = document.getElementById("deckCounter");
  const progress = document.getElementById("progress");
  const toc = document.getElementById("toc");
  const tocItems = document.getElementById("tocItems");
  const tocButton = document.getElementById("tocButton");
  const settingsPanel = document.getElementById("settingsPanel");
  const settingsToggle = document.getElementById("settingsToggle");
  const themeButton = document.getElementById("themeButton");
  let current = 0;
  let touchStart = null;
  let chromeTimer = null;

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function hashIndex() {
    const match = window.location.hash.match(/(?:#\/|#slide-)(\d+)$/);
    return match ? clamp(Number(match[1]) - 1, 0, slides.length - 1) : 0;
  }

  function slideLabel(slide, index) {
    return slide.getAttribute("aria-label") ||
      slide.querySelector("h1")?.textContent.trim() ||
      `슬라이드 ${index + 1}`;
  }

  function updateHash(index) {
    const nextHash = `#/${index + 1}`;
    if (window.location.hash !== nextHash) {
      window.history.replaceState(null, "", nextHash);
    }
  }

  function showSlide(index, options = {}) {
    current = clamp(index, 0, slides.length - 1);
    slides.forEach((slide, slideIndex) => {
      const active = slideIndex === current;
      slide.classList.toggle("is-active", active);
      slide.setAttribute("aria-hidden", String(!active));
    });

    document.querySelectorAll("[data-slide-total]").forEach((node) => {
      node.textContent = String(slides.length);
    });
    document.querySelectorAll("[data-slide-number]").forEach((node) => {
      const owner = node.closest(".slide");
      node.textContent = String(slides.indexOf(owner) + 1).padStart(2, "0");
    });

    counter.textContent = `${current + 1} / ${slides.length}`;
    progress.style.width = `${((current + 1) / slides.length) * 100}%`;
    tocItems.querySelectorAll(".toc-item").forEach((item, itemIndex) => {
      item.classList.toggle("current", itemIndex === current);
      item.setAttribute("aria-current", itemIndex === current ? "page" : "false");
    });
    document.title = `${slideLabel(slides[current], current)} · ${slides[0].querySelector("h1")?.textContent.trim() || "발표자료"}`;
    if (!options.skipHash) updateHash(current);
  }

  function move(delta) {
    showSlide(current + delta);
  }

  function buildToc() {
    slides.forEach((slide, index) => {
      const button = document.createElement("button");
      const number = document.createElement("span");
      const label = document.createElement("span");
      button.type = "button";
      button.className = "toc-item";
      number.textContent = String(index + 1).padStart(2, "0");
      label.textContent = slideLabel(slide, index);
      button.append(number, label);
      button.addEventListener("click", () => {
        showSlide(index);
        setToc(false);
      });
      tocItems.appendChild(button);
    });
  }

  function setToc(open) {
    if (open) setSettings(false);
    toc.classList.toggle("open", open);
    toc.setAttribute("aria-hidden", String(!open));
    tocButton.setAttribute("aria-expanded", String(open));
    if (open) showChrome();
  }

  function setSettings(open) {
    settingsPanel.classList.toggle("is-open", open);
    settingsPanel.setAttribute("aria-hidden", String(!open));
    settingsToggle.setAttribute("aria-expanded", String(open));
    if (open) {
      setToc(false);
      showChrome();
    }
  }

  function savedTheme() {
    try {
      return window.localStorage.getItem("aimlquant-deck-theme");
    } catch (_error) {
      return null;
    }
  }

  function applyTheme(theme) {
    document.documentElement.className = `theme-${theme}`;
    themeButton.textContent = theme === "dark" ? "☾" : "☀";
    themeButton.setAttribute("aria-pressed", String(theme === "dark"));
    themeButton.setAttribute("title", theme === "dark" ? "라이트 모드로 전환" : "나이트 모드로 전환");
    try {
      window.localStorage.setItem("aimlquant-deck-theme", theme);
    } catch (_error) {
      // Local files and private browsing may reject storage. Navigation still works.
    }
  }

  function toggleTheme() {
    applyTheme(document.documentElement.classList.contains("theme-dark") ? "light" : "dark");
  }

  function toggleFullscreen() {
    if (document.fullscreenElement) {
      document.exitFullscreen?.();
    } else {
      document.documentElement.requestFullscreen?.();
    }
  }

  function fitStage() {
    const scale = Math.min(window.innerWidth / 1280, window.innerHeight / 720);
    document.documentElement.style.setProperty("--deck-scale", String(scale));
  }

  function hideChrome() {
    if (!toc.classList.contains("open") && !settingsPanel.classList.contains("is-open")) {
      document.body.classList.add("chrome-hidden");
    }
  }

  function showChrome() {
    document.body.classList.remove("chrome-hidden");
    window.clearTimeout(chromeTimer);
    chromeTimer = window.setTimeout(hideChrome, 2600);
  }

  document.getElementById("prevButton").addEventListener("click", () => move(-1));
  document.getElementById("nextButton").addEventListener("click", () => move(1));
  themeButton.addEventListener("click", toggleTheme);
  document.getElementById("fullscreenButton").addEventListener("click", toggleFullscreen);
  tocButton.addEventListener("click", () => setToc(!toc.classList.contains("open")));
  settingsToggle.addEventListener("click", () => setSettings(!settingsPanel.classList.contains("is-open")));

  document.addEventListener("keydown", (event) => {
    showChrome();
    if (event.key === "Escape") {
      setToc(false);
      setSettings(false);
      return;
    }
    if (event.target.matches("input, textarea, button, a, select, [contenteditable='true']")) return;
    if (["ArrowRight", "PageDown", " "].includes(event.key)) {
      event.preventDefault();
      move(1);
    } else if (["ArrowLeft", "PageUp"].includes(event.key)) {
      event.preventDefault();
      move(-1);
    } else if (event.key === "Home") {
      event.preventDefault();
      showSlide(0);
    } else if (event.key === "End") {
      event.preventDefault();
      showSlide(slides.length - 1);
    } else if (event.key.toLowerCase() === "f") {
      toggleFullscreen();
    } else if (event.key.toLowerCase() === "d") {
      toggleTheme();
    } else if (event.key.toLowerCase() === "m") {
      setToc(!toc.classList.contains("open"));
    }
  });

  document.addEventListener("click", (event) => {
    if (toc.classList.contains("open") && !event.target.closest(".toc, .toc-button")) {
      setToc(false);
    }
    if (settingsPanel.classList.contains("is-open") && !event.target.closest(".deck-settings")) {
      setSettings(false);
    }
  });
  document.addEventListener("mousemove", showChrome);
  document.addEventListener("touchstart", (event) => {
    touchStart = event.touches[0]?.clientX ?? null;
    showChrome();
  }, { passive: true });
  document.addEventListener("touchend", (event) => {
    if (touchStart === null) return;
    const delta = (event.changedTouches[0]?.clientX ?? touchStart) - touchStart;
    if (Math.abs(delta) > 50) move(delta < 0 ? 1 : -1);
    touchStart = null;
  }, { passive: true });
  window.addEventListener("hashchange", () => showSlide(hashIndex(), { skipHash: true }));
  window.addEventListener("resize", fitStage);
  window.addEventListener("beforeprint", () => document.body.classList.remove("chrome-hidden"));

  // ===== Syntax highlighting =====
  // report.js 와 같은 토크나이저다. 외부 의존성을 싣지 않는 템플릿이라 CDN
  // 하이라이터를 쓸 수 없다. MATLAB 은 작은따옴표를 문자열과 전치에 함께 쓰므로
  // 바로 앞 글자가 식별자·닫는 괄호·점이면 전치로 본다.
  const SYNTAX_GRAMMARS = {
    python: {
      comment: "#",
      quotes: "'\"",
      transposeQuote: false,
      keywords: " and as assert async await break class continue def del elif else" +
        " except finally for from global if import in is lambda nonlocal not or" +
        " pass raise return try while with yield ",
      literals: " True False None ",
    },
    matlab: {
      comment: "%",
      quotes: "'\"",
      transposeQuote: true,
      keywords: " break case catch continue else elseif end for function global" +
        " if otherwise persistent return switch try while ",
      literals: " true false NaN Inf ",
    },
    bash: {
      comment: "#",
      quotes: "'\"",
      transposeQuote: false,
      keywords: " case cd do done elif else esac export fi for function if in" +
        " local return then while ",
      literals: "",
    },
  };

  const escapeCode = (text) => text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  function tokenizeCode(source, grammar) {
    let out = "";
    let index = 0;
    const length = source.length;
    let previous = "";

    const emit = (cls, text) => {
      out += `<span class="tok-${cls}">${escapeCode(text)}</span>`;
    };

    while (index < length) {
      const ch = source.charAt(index);

      if (ch === "\n") {
        out += "\n";
        previous = "";
        index += 1;
        continue;
      }

      if (ch === grammar.comment) {
        let lineEnd = source.indexOf("\n", index);
        if (lineEnd < 0) lineEnd = length;
        emit("com", source.slice(index, lineEnd));
        index = lineEnd;
        continue;
      }

      if (grammar.quotes.indexOf(ch) >= 0) {
        const isTranspose = grammar.transposeQuote && ch === "'" &&
          /[A-Za-z0-9_)\]}.]/.test(previous);
        if (!isTranspose) {
          let cursor = index + 1;
          while (cursor < length && source.charAt(cursor) !== ch &&
                 source.charAt(cursor) !== "\n") {
            if (!grammar.transposeQuote && source.charAt(cursor) === "\\") cursor += 1;
            cursor += 1;
          }
          if (cursor < length && source.charAt(cursor) === ch) cursor += 1;
          emit("str", source.slice(index, cursor));
          index = cursor;
          previous = "'";
          continue;
        }
      }

      if (ch >= "0" && ch <= "9" && !/[A-Za-z0-9_.]/.test(previous)) {
        const number = /^[0-9][0-9_]*(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/
          .exec(source.slice(index))[0];
        emit("num", number);
        index += number.length;
        previous = "0";
        continue;
      }

      if (/[A-Za-z_]/.test(ch)) {
        const word = /^[A-Za-z_][A-Za-z0-9_]*/.exec(source.slice(index))[0];
        let cls = "";
        if (grammar.keywords.indexOf(` ${word} `) >= 0) cls = "kw";
        else if (grammar.literals.indexOf(` ${word} `) >= 0) cls = "lit";
        else if (source.charAt(index + word.length) === "(") cls = "fn";
        if (cls) emit(cls, word);
        else out += escapeCode(word);
        index += word.length;
        previous = "a";
        continue;
      }

      out += escapeCode(ch);
      if (!/\s/.test(ch)) previous = ch;
      index += 1;
    }

    return out;
  }

  function highlightCodeBlocks() {
    document.querySelectorAll('pre > code[class*="language-"]').forEach((code) => {
      if (code.dataset.highlighted === "true") return;
      const match = /language-([a-z0-9]+)/.exec(code.className);
      const grammar = match && SYNTAX_GRAMMARS[match[1]];
      if (!grammar) return;
      code.innerHTML = tokenizeCode(code.textContent, grammar);
      code.dataset.highlighted = "true";
    });
  }

  // stage 크기를 재기 전에 칠해 둔다.
  highlightCodeBlocks();

  buildToc();
  fitStage();
  applyTheme(savedTheme() === "dark" ? "dark" : "light");
  showSlide(hashIndex(), { skipHash: true });
  showChrome();
})();
