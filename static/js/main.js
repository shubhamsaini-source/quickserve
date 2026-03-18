/* QuickServe – Top Loading Bar */
(function() {

  var bar = document.createElement("div");
  bar.id = "qs-topbar";
  document.body.appendChild(bar);

  // Page load ho — bar chalao
  window.addEventListener("load", function() {
    bar.className = "run";
  });

  // Link click
  document.addEventListener("click", function(e) {
    var link = e.target.closest("a");
    if (!link) return;
    var href = link.getAttribute("href");
    if (!href || href.startsWith("#") || href.startsWith("http") ||
        href.startsWith("mailto") || href.startsWith("javascript") ||
        link.target === "_blank") return;
    e.preventDefault();
    bar.className = "run";
    document.body.style.transition = "opacity 0.2s ease";
    document.body.style.opacity = "0";
    setTimeout(function() { window.location.href = href; }, 200);
  });

  // Form submit
  document.addEventListener("submit", function() {
    bar.className = "run";
  });

  // Page enter fade
  window.addEventListener("pageshow", function() {
    document.body.style.opacity = "0";
    document.body.style.transition = "none";
    requestAnimationFrame(function() {
      requestAnimationFrame(function() {
        document.body.style.transition = "opacity 0.3s ease";
        document.body.style.opacity = "1";
      });
    });
  });

})();

// Auto dismiss alerts
document.addEventListener("DOMContentLoaded", function() {
  document.querySelectorAll(".alert").forEach(function(el) {
    setTimeout(function() {
      try { bootstrap.Alert.getOrCreateInstance(el).close(); } catch(e) {}
    }, 4000);
  });
  var today = new Date().toISOString().split("T")[0];
  document.querySelectorAll('input[type="date"]').forEach(function(el) {
    if (!el.getAttribute("min")) el.setAttribute("min", today);
  });
});
