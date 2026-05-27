// VisualFLIP project page — theme + language + leaderboard sort + copy
// + scroll-reveal + stat count-up.  No external deps.

(function () {
  // ------------------ Theme (light / dark) ------------------
  var THEME_KEY = "visualflip-theme";
  var saved = localStorage.getItem(THEME_KEY);
  if (saved) document.documentElement.dataset.theme = saved;

  document.addEventListener("DOMContentLoaded", function () {
    var themeBtn = document.getElementById("theme-toggle");
    function paintTheme() {
      var cur = document.documentElement.dataset.theme;
      if (!cur) {
        var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
        cur = prefersDark ? "dark" : "light";
      }
      if (themeBtn) {
        themeBtn.textContent = cur === "dark" ? "Light" : "Dark";
        themeBtn.setAttribute("aria-label", cur === "dark" ? "Switch to light theme" : "Switch to dark theme");
      }
    }
    paintTheme();
    if (themeBtn) {
      themeBtn.addEventListener("click", function () {
        var cur = document.documentElement.dataset.theme || "light";
        var next = cur === "dark" ? "light" : "dark";
        document.documentElement.dataset.theme = next;
        localStorage.setItem(THEME_KEY, next);
        paintTheme();
      });
    }

    // ------------------ Language (EN / 中文) ------------------
    var LANG_KEY = "visualflip-lang";
    var langBtn = document.getElementById("lang-toggle");
    function applyLang(lang) {
      document.body.classList.toggle("lang-zh", lang === "zh");
      if (langBtn) langBtn.textContent = lang === "zh" ? "EN" : "中文";
      localStorage.setItem(LANG_KEY, lang);
    }
    var initialLang = localStorage.getItem(LANG_KEY) || "en";
    applyLang(initialLang);
    if (langBtn) {
      langBtn.addEventListener("click", function () {
        var cur = document.body.classList.contains("lang-zh") ? "zh" : "en";
        applyLang(cur === "zh" ? "en" : "zh");
      });
    }

    // ------------------ Leaderboard sort ------------------
    var table = document.getElementById("leaderboard");
    if (table) {
      var tbody = table.tBodies[0];
      var headers = Array.from(table.tHead.rows[0].cells);
      headers.forEach(function (th, idx) {
        if (!th.hasAttribute("data-sort-num")) return;
        var asc = false;
        th.addEventListener("click", function () {
          asc = !asc;
          headers.forEach(function (h) { h.classList.remove("sort-asc", "sort-desc"); });
          th.classList.add(asc ? "sort-asc" : "sort-desc");
          var rows = Array.from(tbody.rows);
          rows.sort(function (a, b) {
            var va = parseFloat(a.cells[idx].textContent.replace(/[^\d.\-]/g, "")) || 0;
            var vb = parseFloat(b.cells[idx].textContent.replace(/[^\d.\-]/g, "")) || 0;
            return asc ? va - vb : vb - va;
          });
          rows.forEach(function (r) { tbody.appendChild(r); });
        });
      });
    }

    // ------------------ Copy buttons ------------------
    document.querySelectorAll("[data-copy-target]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var t = document.getElementById(btn.getAttribute("data-copy-target"));
        if (!t) return;
        var text = t.innerText;
        var orig = btn.textContent;
        function done(label) {
          btn.textContent = label;
          setTimeout(function () { btn.textContent = orig; }, 1500);
        }
        if (navigator.clipboard) {
          navigator.clipboard.writeText(text).then(function () { done("Copied"); }).catch(function () { done("Error"); });
        } else {
          done("Unsupported");
        }
      });
    });

    // ------------------ Scroll-reveal + count-up ------------------
    var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function countUp(el) {
      var target = parseInt(el.getAttribute("data-count"), 10);
      if (!target || el.dataset.counted === "1") return;
      el.dataset.counted = "1";
      if (reduceMotion) { el.textContent = String(target); return; }
      var dur = 900;
      var t0 = null;
      function step(t) {
        if (t0 === null) t0 = t;
        var p = Math.min(1, (t - t0) / dur);
        // ease-out cubic
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = String(Math.round(target * eased));
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }

    var reveals = document.querySelectorAll("[data-reveal]");
    if ("IntersectionObserver" in window && !reduceMotion) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          entry.target.querySelectorAll("[data-count]").forEach(countUp);
          io.unobserve(entry.target);
        });
      }, { rootMargin: "0px 0px -10% 0px", threshold: 0.08 });
      reveals.forEach(function (el) { io.observe(el); });
    } else {
      // No IO or reduced motion → show everything immediately + fill stats.
      reveals.forEach(function (el) {
        el.classList.add("is-visible");
        el.querySelectorAll("[data-count]").forEach(countUp);
      });
    }
  });
})();
