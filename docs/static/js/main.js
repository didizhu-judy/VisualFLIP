// VisualFLIP project page — leaderboard sort (if present) + copy + scroll-reveal.
// No external deps. (Theme/language toggles removed: page is always light + English.)

(function () {
  document.addEventListener("DOMContentLoaded", function () {
    // ------------------ Leaderboard sort (only if sortable headers exist) ------------------
    var table = document.getElementById("leaderboard");
    if (table && table.tHead) {
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

    // ------------------ Scroll-reveal ------------------
    var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var reveals = document.querySelectorAll("[data-reveal]");
    if ("IntersectionObserver" in window && !reduceMotion) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        });
      }, { rootMargin: "0px 0px -10% 0px", threshold: 0.08 });
      reveals.forEach(function (el) { io.observe(el); });
    } else {
      reveals.forEach(function (el) { el.classList.add("is-visible"); });
    }
  });
})();
