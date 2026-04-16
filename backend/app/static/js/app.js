document.querySelectorAll(".sidebar__link").forEach(function(link) {
  link.addEventListener("click", function() {
    document.querySelectorAll(".sidebar__link").forEach(function(a) {
      a.classList.remove("sidebar__link--active");
    });
    link.classList.add("sidebar__link--active");
  });
});

document.body.addEventListener("showToast", function(e) {
  var d = e.detail, el = document.createElement("div");
  el.className = "toast " + (d.ok ? "toast--ok" : "toast--error");
  el.textContent = d.message;
  document.getElementById("toast-container").appendChild(el);
  setTimeout(function() { el.remove(); }, 4000);
});

document.body.addEventListener("htmx:responseError", function(e) {
  var msg = "Fehler " + e.detail.xhr.status;
  try {
    var json = JSON.parse(e.detail.xhr.responseText);
    if (json.detail) msg = json.detail;
  } catch (_) {}
  var el = document.createElement("div");
  el.className = "toast toast--error";
  el.textContent = msg;
  var container = document.getElementById("toast-container");
  if (container) { container.appendChild(el); setTimeout(function() { el.remove(); }, 5000); }
});
