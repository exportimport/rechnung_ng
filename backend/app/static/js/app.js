document.querySelectorAll(".sidebar__link").forEach(function(link) {
  link.addEventListener("click", function() {
    document.querySelectorAll(".sidebar__link").forEach(function(a) {
      a.classList.remove("sidebar__link--active");
    });
    link.classList.add("sidebar__link--active");
  });
});

// Select-all checkbox for invoice bulk actions
document.body.addEventListener("change", function(e) {
  if (e.target && e.target.id === "select-all") {
    document.querySelectorAll(".inv-check").forEach(function(c) {
      c.checked = e.target.checked;
    });
  }
});

function showToast(message, ok) {
  var el = document.createElement("div");
  el.className = "toast " + (ok ? "toast--ok" : "toast--error");
  el.textContent = message;
  var container = document.getElementById("toast-container");
  if (container) { container.appendChild(el); setTimeout(function() { el.remove(); }, 4000); }
}

document.body.addEventListener("showToast", function(e) {
  showToast(e.detail.message, e.detail.ok);
});

document.body.addEventListener("htmx:responseError", function(e) {
  var msg = "Fehler " + e.detail.xhr.status;
  try {
    var json = JSON.parse(e.detail.xhr.responseText);
    if (json.detail) msg = json.detail;
  } catch (_) {}
  showToast(msg, false);
});
