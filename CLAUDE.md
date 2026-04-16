# CLAUDE.md — rechnung_ng v2 (HTMX + FastAPI)

## Entwicklungsumgebung

- **Distrobox:** `rechnung-htmx` (Ubuntu 24.04) — alle Shell-Befehle im Projekt laufen hier
- **Python:** 3.12, venv unter `backend/.venv/`
- **Starten:** `distrobox enter rechnung-htmx -- bash -c "cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000"`
- **Styling:** Plain CSS (kein Tailwind, kein Build-Step)

## Projektziel

Kompletter Umbau des Frontends von React/TypeScript/Vite auf **HTMX + Jinja2-Templates**, ausgeliefert direkt durch FastAPI. Kein npm, kein Node.js, kein JavaScript-Build-Step. Das Ziel ist eine minimale Supply-Chain-Angriffsfläche bei voller Funktionsparität.

## Motivation

Das Projekt verarbeitet personenbezogene Daten (Kundennamen, Adressen, IBANs, E-Mail-Adressen, Steuer-IDs) und läuft auf Systemen mit potenziellem Internetzugang (SMTP-Versand). Die bisherige React-Frontend-Architektur zieht über 300 transitive npm-Dependencies nach sich, darunter native Bindings (Rolldown, Tailwind Oxide, LightningCSS). Jede davon ist ein potenzieller Supply-Chain-Angriffsvektor. HTMX reduziert die clientseitige Abhängigkeit auf eine einzige, lokal gebündelte JS-Datei (~14 KB gzipped).

---

## Architektur-Übersicht

### Vorher (React SPA)
```
Browser → React (JS-Bundle, ~300+ npm-Deps) → fetch(/api/v1/...) → JSON → React rendert DOM
                                                ↓
                                     FastAPI (JSON-API)
```

### Nachher (HTMX + Server-Side Rendering)
```
Browser → HTMX (~14 KB, lokal) → GET/POST /... → FastAPI rendert HTML-Fragment → HTMX swappt DOM
                                                    ↓
                                         Jinja2-Templates
```

**Ein Server, ein Prozess, ein Port.** Keine CORS-Konfiguration nötig, kein separater Dev-Server.

---

## Tech-Stack

| Komponente | Technologie | Anmerkung |
|---|---|---|
| Backend / Server | FastAPI + Uvicorn | Bleibt wie bisher |
| Templating | Jinja2 | Bereits als Dependency vorhanden (PDF-Rendering) |
| Client-Interaktivität | HTMX 2.x | Einzelne JS-Datei, lokal ausgeliefert unter `/static/js/htmx.min.js` |
| SSE (Fortschritt) | htmx SSE-Extension | `ext/sse.js`, ebenfalls lokal gebündelt |
| Styling | Plain CSS oder Tailwind Standalone CLI | Kein npm erforderlich; Tailwind CLI als einzelnes Binary |
| Icons | Inline SVG oder ein kleines Icon-Set als SVG-Sprite | Keine externe Dependency |
| Validierung | Pydantic (server-seitig) | Client-seitig nur native HTML5-Validierung |
| Datenbank | YAML Flat-File (YamlStore) | Bleibt unverändert |
| PDF-Generierung | WeasyPrint + Jinja2 | Bleibt unverändert |
| E-Mail | smtplib | Bleibt unverändert |

---

## Verzeichnisstruktur (Ziel)

```
rechnung_ng/
├── CLAUDE.md
├── README.md
├── LICENSE
├── assets/                          # Logo, Invoice-CSS (wie bisher)
├── backend/
│   ├── pyproject.toml
│   ├── .env
│   ├── data/                        # YAML-Dateien (Laufzeitdaten)
│   ├── output/                      # Generierte PDFs
│   ├── uploads/                     # Vertragsscan-Uploads
│   ├── app/
│   │   ├── main.py                  # FastAPI-App, Lifespan, Middleware
│   │   ├── config.py                # AppConfig laden
│   │   ├── db/
│   │   │   └── yaml_store.py        # YamlStore (unverändert)
│   │   ├── models/                  # Pydantic-Modelle (unverändert)
│   │   │   ├── customer.py
│   │   │   ├── contract.py
│   │   │   ├── plan.py
│   │   │   └── invoice.py
│   │   ├── services/                # Business-Logik (unverändert)
│   │   │   ├── invoice_generator.py
│   │   │   ├── mail_service.py
│   │   │   └── cancellation.py
│   │   ├── routers/                 # HTMX-orientierte Routes (HTML-Responses)
│   │   │   ├── pages.py             # Vollständige Seiten (GET /)
│   │   │   ├── customers.py         # Kunden CRUD (HTML-Fragmente)
│   │   │   ├── contracts.py
│   │   │   ├── plans.py
│   │   │   ├── invoices.py
│   │   │   ├── mail_templates.py
│   │   │   ├── dashboard.py
│   │   │   └── settings.py
│   │   ├── templates/               # Jinja2-Templates
│   │   │   ├── base.html.j2         # Layout mit Sidebar, HTMX-Includes
│   │   │   ├── partials/            # Wiederverwendbare Fragmente
│   │   │   │   ├── _sidebar.html.j2
│   │   │   │   ├── _toast.html.j2
│   │   │   │   ├── _confirm_modal.html.j2
│   │   │   │   ├── _data_table.html.j2
│   │   │   │   └── _pagination.html.j2
│   │   │   ├── pages/               # Vollseiten-Templates
│   │   │   │   ├── dashboard.html.j2
│   │   │   │   ├── customers.html.j2
│   │   │   │   ├── customer_form.html.j2
│   │   │   │   ├── contracts.html.j2
│   │   │   │   ├── contract_form.html.j2
│   │   │   │   ├── plans.html.j2
│   │   │   │   ├── plan_form.html.j2
│   │   │   │   ├── invoices.html.j2
│   │   │   │   ├── mail_templates.html.j2
│   │   │   │   └── settings.html.j2
│   │   │   ├── fragments/           # HTMX-Swap-Fragmente
│   │   │   │   ├── customer_row.html.j2
│   │   │   │   ├── customer_table.html.j2
│   │   │   │   ├── contract_row.html.j2
│   │   │   │   ├── contract_table.html.j2
│   │   │   │   ├── plan_row.html.j2
│   │   │   │   ├── invoice_table.html.j2
│   │   │   │   ├── invoice_progress.html.j2
│   │   │   │   ├── dashboard_stats.html.j2
│   │   │   │   ├── settings_form.html.j2
│   │   │   │   └── toast_message.html.j2
│   │   │   ├── invoice.html.j2      # PDF-Template (unverändert)
│   │   │   └── cancellation.html.j2 # PDF-Template (unverändert)
│   │   └── static/                  # Statische Dateien
│   │       ├── js/
│   │       │   ├── htmx.min.js      # HTMX 2.x (lokal, KEIN CDN)
│   │       │   └── ext/
│   │       │       └── sse.js        # HTMX SSE-Extension
│   │       ├── css/
│   │       │   └── style.css         # Gesamtes Styling
│   │       └── img/
│   │           └── logo.svg
│   └── tests/                       # Pytest (unverändert + neue HTML-Tests)
```

**Das `frontend/`-Verzeichnis wird komplett entfernt.**

---

## Routing-Schema

Alle Routes liefern HTML. HTMX-Requests (erkennbar an `HX-Request: true` Header) erhalten nur das Fragment; normale Browser-Requests erhalten die vollständige Seite mit Layout.

### Pattern für Vollseite vs. Fragment

```python
from fastapi import Request
from fastapi.responses import HTMLResponse

def render(request: Request, template: str, fragment_template: str, context: dict) -> HTMLResponse:
    """Liefert das Fragment bei HTMX-Request, sonst die volle Seite."""
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        html = templates.get_template(fragment_template).render(**context)
    else:
        # Fallback: Volle Seite mit base-Layout (für Direktzugriff / Reload)
        context["content_template"] = fragment_template
        html = templates.get_template(template).render(**context)
    return HTMLResponse(html)
```

### URL-Übersicht

| Methode | URL | Beschreibung | HTMX-Response |
|---|---|---|---|
| GET | `/` | Dashboard | `pages/dashboard.html.j2` |
| GET | `/customers` | Kundenliste | `pages/customers.html.j2` |
| GET | `/customers/new` | Neues Kundenformular | `pages/customer_form.html.j2` |
| GET | `/customers/{id}` | Kundenformular (Edit) | `pages/customer_form.html.j2` |
| POST | `/customers` | Kunde erstellen | Fragment: Redirect + Toast |
| PUT | `/customers/{id}` | Kunde aktualisieren | Fragment: Formular-Feedback |
| DELETE | `/customers/{id}` | Kunde löschen | Fragment: leere Row / Redirect |
| GET | `/customers?q=...` | Suche (nur Tabelle) | `fragments/customer_table.html.j2` |
| GET | `/plans` | Tarifliste | `pages/plans.html.j2` |
| GET | `/plans/new` | Neues Tarifformular | `pages/plan_form.html.j2` |
| GET | `/plans/{id}` | Tarifformular (Edit) | `pages/plan_form.html.j2` |
| POST | `/plans` | Tarif erstellen | Redirect + Toast |
| PUT | `/plans/{id}` | Tarif aktualisieren | Fragment |
| POST | `/plans/{id}/price` | Preis hinzufügen | Fragment: Preishistorie |
| GET | `/contracts` | Vertragsliste | `pages/contracts.html.j2` |
| GET | `/contracts?status=...` | Gefilterte Vertragsliste | `fragments/contract_table.html.j2` |
| GET | `/contracts/new` | Neues Vertragsformular | `pages/contract_form.html.j2` |
| GET | `/contracts/{id}` | Vertragsformular (Edit) | `pages/contract_form.html.j2` |
| POST | `/contracts` | Vertrag erstellen | Redirect + Toast |
| PUT | `/contracts/{id}` | Vertrag aktualisieren | Fragment |
| POST | `/contracts/{id}/cancel` | Vertrag kündigen | Fragment: Status-Update |
| POST | `/contracts/{id}/scan` | Scan hochladen | Fragment: Scan-Bereich |
| GET | `/invoices` | Rechnungsliste | `pages/invoices.html.j2` |
| GET | `/invoices?year=&month=&status=` | Gefiltert | `fragments/invoice_table.html.j2` |
| POST | `/invoices/generate` | Rechnungen generieren (SSE) | SSE-Stream |
| POST | `/invoices/{id}/send` | Einzelne Rechnung senden | Fragment: Row-Update |
| POST | `/invoices/send-batch` | Batch-Versand | Fragment: Tabellen-Update |
| POST | `/invoices/bulk-delete` | Bulk-Löschen | Fragment: Tabellen-Update |
| GET | `/invoices/{id}/pdf` | PDF herunterladen | FileResponse |
| GET | `/mail-templates` | Mail-Vorlagen | `pages/mail_templates.html.j2` |
| PUT | `/mail-templates/{id}` | Vorlage speichern | Fragment: Feedback |
| GET | `/settings` | Einstellungen | `pages/settings.html.j2` |
| PUT | `/settings` | Einstellungen speichern | Fragment: Feedback |
| GET | `/output/...` | Statische PDF-Dateien | StaticFiles (wie bisher) |

---

## HTMX-Patterns

### 1. Tabelle mit Inline-Suche (Kunden)

```html
<!-- pages/customers.html.j2 -->
<input type="search" name="q"
       hx-get="/customers"
       hx-trigger="input changed delay:300ms, search"
       hx-target="#customer-table"
       hx-push-url="true"
       placeholder="Suchen…">

<div id="customer-table">
  {% include "fragments/customer_table.html.j2" %}
</div>
```

### 2. Formular mit Server-Validierung

```html
<!-- pages/customer_form.html.j2 -->
<form hx-post="/customers" hx-target="#main-content" hx-push-url="true">
  <input name="vorname" required minlength="1">
  <input name="nachname" required minlength="1">
  <input name="email" type="email" required>
  <input name="iban" required>
  <!-- ... -->
  <button type="submit">Erstellen</button>
</form>
```

Bei Validierungsfehlern gibt der Server das Formular mit Fehlermeldungen zurück (HTTP 422, `HX-Reswap: innerHTML`).

### 3. Löschen mit Bestätigung

```html
<button hx-delete="/customers/{{ customer.id }}"
        hx-confirm="Kunde wirklich löschen?"
        hx-target="closest tr"
        hx-swap="outerHTML swap:500ms">
  Löschen
</button>
```

### 4. Filterung (Verträge nach Status)

```html
<select name="status"
        hx-get="/contracts"
        hx-trigger="change"
        hx-target="#contract-table"
        hx-push-url="true">
  <option value="">Alle Status</option>
  <option value="active">Aktiv</option>
  <option value="not_yet_active">Noch nicht aktiv</option>
  <option value="cancelled">Gekündigt</option>
</select>
```

### 5. Rechnungsgenerierung mit SSE-Fortschritt

```html
<!-- Trigger-Button -->
<button hx-post="/invoices/generate"
        hx-vals='{"year": 2026, "month": 4}'
        hx-target="#generate-status"
        hx-indicator="#generate-spinner">
  Rechnungen generieren
</button>

<!-- Fortschrittsbereich -->
<div id="generate-status"
     hx-ext="sse"
     sse-connect="/invoices/generate-stream?year=2026&month=4"
     sse-swap="progress"
     sse-close="done">
</div>
```

Der SSE-Endpunkt liefert HTML-Fragmente für den Fortschrittsbalken:

```python
@router.get("/invoices/generate-stream")
async def generate_stream(year: int, month: int):
    async def event_generator():
        for event in generate_invoices(year, month, store):
            if event[0] == "progress":
                _, current, total = event
                pct = int(current / total * 100)
                html = f'<div class="progress-bar" style="width:{pct}%">{current}/{total}</div>'
                yield f"event: progress\ndata: {html}\n\n"
            elif event[0] == "done":
                yield f"event: done\ndata: <div>Fertig!</div>\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 6. Toast-Benachrichtigungen

Über HTMX Response-Header:

```python
from fastapi import Response

def set_toast(response: Response, message: str, ok: bool = True):
    response.headers["HX-Trigger"] = json.dumps({
        "showToast": {"message": message, "ok": ok}
    })
```

Im Base-Template ein Listener:

```html
<div id="toast-container"></div>
<script>
document.body.addEventListener("showToast", function(e) {
    const {message, ok} = e.detail;
    const el = document.createElement("div");
    el.className = "toast " + (ok ? "toast-ok" : "toast-error");
    el.textContent = message;
    document.getElementById("toast-container").appendChild(el);
    setTimeout(() => el.remove(), 4000);
});
</script>
```

Dies ist das einzige Stück Inline-JavaScript im gesamten Projekt (~10 Zeilen).

### 7. Browser-Navigation (URL-Updates)

HTMX unterstützt `hx-push-url="true"`, damit die Browser-URL bei Navigation aktualisiert wird. Zusammen mit dem Vollseiten-Fallback (wenn `HX-Request` Header fehlt) funktionieren Bookmarks, Browser-Back und Reload korrekt.

---

## Styling-Strategie

### Option A: Tailwind Standalone CLI (empfohlen)

```bash
# Einmalig herunterladen (kein npm!)
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
chmod +x tailwindcss-linux-x64

# CSS bauen
./tailwindcss-linux-x64 -i app/static/css/input.css -o app/static/css/style.css --minify
```

Die `input.css` enthält nur `@tailwind base; @tailwind components; @tailwind utilities;` plus projektspezifische Ergänzungen. Der CLI scannt die `.html.j2`-Templates nach genutzten Klassen.

### Option B: Plain CSS

Eine einzige `style.css`-Datei mit CSS Custom Properties für Theming. Kein Build-Step. Geeignet wenn das bisherige Glassmorphism-Design vereinfacht werden soll.

---

## Sicherheitsverbesserungen (im Rahmen des Umbaus)

### MUSS (beim Umbau umsetzen)

1. **SSTI-Schutz:** Jinja2 `SandboxedEnvironment` für alle Templates, die User-Input rendern (insbesondere Mail-Templates). Die PDF- und Page-Templates nutzen das reguläre `Environment` mit `autoescape=True`.

2. **Autoescape aktivieren:** Alle HTML-Templates MÜSSEN `autoescape=True` verwenden. Im Base-Template:
   ```python
   env = Environment(loader=FileSystemLoader("templates"), autoescape=True)
   ```

3. **CSRF-Schutz:** Da jetzt Formulare direkt gepostet werden (statt JSON-API), ist CSRF-Schutz Pflicht:
   ```python
   # Einfacher Token-basierter CSRF-Schutz
   # Token wird im base.html.j2 als Meta-Tag gesetzt
   # HTMX sendet ihn automatisch via hx-headers
   ```
   ```html
   <meta name="csrf-token" content="{{ csrf_token }}">
   <body hx-headers='{"X-CSRF-Token": "{{ csrf_token }}"}'>
   ```

4. **Content-Security-Policy Header:**
   ```python
   # Kein inline-JS außer dem Toast-Handler
   # Kein externes JS/CSS
   response.headers["Content-Security-Policy"] = (
       "default-src 'self'; "
       "script-src 'self'; "
       "style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data:; "
       "connect-src 'self'"
   )
   ```

5. **File-Upload-Validierung:** Vertragsscan-Uploads: MIME-Type prüfen (magic bytes), nicht nur Dateiendung.

### SOLL (priorisiert einplanen)

6. **Basic Auth / Session-Auth:** Mindestens ein konfigurierbarer Username/Passwort-Schutz als Middleware. Kann über `config.yaml` konfiguriert werden. Empfehlung: Cookie-basierte Session mit HMAC-signiertem Token.

7. **Rate Limiting:** Für Login-Versuche und API-Endpunkte (z.B. `slowapi`).

8. **Verschlüsselung sensibler Felder:** IBANs und E-Mail-Adressen in den YAML-Dateien mit einem lokalen Schlüssel verschlüsseln (z.B. Fernet/AES).

---

## Migration: Schritt-für-Schritt

### Phase 1: Infrastruktur

1. HTMX und SSE-Extension herunterladen, unter `app/static/js/` ablegen
2. `app/static/css/style.css` erstellen (Tailwind CLI oder Plain CSS)
3. Jinja2 Template-Engine in `main.py` konfigurieren:
   ```python
   from jinja2 import Environment, FileSystemLoader, select_autoescape

   templates = Environment(
       loader=FileSystemLoader("app/templates"),
       autoescape=select_autoescape(["html", "html.j2"]),
   )
   ```
4. StaticFiles-Mount für `/static` einrichten
5. `base.html.j2` mit Sidebar-Navigation, HTMX-Include, Toast-Container erstellen
6. CSRF-Middleware implementieren
7. Render-Hilfsfunktion (Vollseite vs. Fragment) implementieren
8. Jinja2-Filter registrieren: `format_euro`, `format_date`, Statuslabel/-farben

### Phase 2: Seiten (eine nach der anderen)

Reihenfolge nach Komplexität:

1. **Dashboard** — Einfachste Seite, nur Lesezugriff. Guter Startpunkt.
2. **Settings** — Ein großes Formular, keine Tabelle.
3. **Kunden** — CRUD mit Tabelle und Suche. Erstes vollständiges Pattern.
4. **Tarife** — CRUD mit verschachtelter Preishistorie.
5. **Verträge** — CRUD mit Filterung, Scan-Upload, Kündigung.
6. **Mail-Vorlagen** — Textarea-basierte Bearbeitung.
7. **Rechnungen** — Komplexeste Seite: SSE, Batch-Operationen, Bulk-Delete, Checkboxen.

**Jede Seite wird einzeln migriert und getestet, bevor die nächste beginnt.**

### Phase 3: Aufräumen

1. Gesamtes `frontend/`-Verzeichnis löschen
2. CORS-Middleware aus `main.py` entfernen (nicht mehr nötig)
3. Alle JSON-only-Endpoints entfernen oder als sekundäre API beibehalten (optional)
4. `README.md` aktualisieren
5. `.gitignore` anpassen (npm/node-Einträge entfernen)

### Phase 4: Sicherheit

1. Basic-Auth-Middleware einbauen
2. CSP-Header setzen
3. File-Upload-Validierung härten
4. SMTP-Egress prüfen / einschränken

---

## Bestehende Backend-Komponenten: Was bleibt unverändert

Diese Dateien werden **nicht** verändert:

- `app/db/yaml_store.py` — Datenpersistenz
- `app/models/*` — Alle Pydantic-Modelle
- `app/services/invoice_generator.py` — PDF-Rendering + Rechnungslogik
- `app/services/mail_service.py` — E-Mail-Versand
- `app/services/cancellation.py` — Kündigungsdokument-Generierung
- `app/config.py` — Konfigurationsladung
- `data/mail_templates.yaml` — E-Mail-Vorlagen
- `assets/` — Logo, Invoice-CSS
- `templates/invoice.html.j2` — PDF-Template
- `templates/cancellation.html.j2` — PDF-Template

Die **Router** (`app/routers/*`) werden umgebaut: statt JSON-Responses liefern sie HTML-Fragmente. Die Business-Logik in den Routern bleibt gleich, nur die Response-Formatierung ändert sich.

---

## Jinja2-Template-Konventionen

- Dateien enden auf `.html.j2`
- Partials (wiederverwendbare Snippets) beginnen mit `_` und liegen in `partials/`
- Fragmente (HTMX-Swap-Ziele) liegen in `fragments/`
- Vollständige Seiten liegen in `pages/` und extenden `base.html.j2`
- Autoescape ist global aktiv; `|safe` nur wenn explizit nötig (und dokumentiert warum)
- Alle User-Eingaben werden escaped; niemals `|safe` auf User-Input
- Template-Variablen verwenden snake_case

### Verfügbare Jinja2-Filter

```python
# In main.py registrieren:
templates.filters["euro"] = lambda v: f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
templates.filters["date_de"] = lambda v: v.strftime("%d.%m.%Y") if v else "—"
templates.globals["InvoiceStatus"] = InvoiceStatus
templates.globals["ContractStatus"] = ContractStatus
```

---

## Testen

### HTML-Response-Tests

Die bestehenden Pytest-Tests (httpx + ASGITransport) werden erweitert. Statt JSON-Assertions werden HTML-Fragmente geprüft:

```python
async def test_customer_list_page(client: AsyncClient):
    await client.post("/customers", data={"vorname": "Max", "nachname": "Mustermann", ...})
    res = await client.get("/customers")
    assert res.status_code == 200
    assert "Max" in res.text
    assert "Mustermann" in res.text

async def test_customer_create_htmx(client: AsyncClient):
    res = await client.post(
        "/customers",
        data={"vorname": "Max", "nachname": "Mustermann", ...},
        headers={"HX-Request": "true"},
    )
    assert res.status_code == 200
    assert "HX-Trigger" in res.headers  # Toast-Trigger
```

### Optionale JSON-API

Wenn gewünscht, kann eine JSON-API unter `/api/v1/` parallel bestehen bleiben (z.B. für Scripting oder zukünftige Integrationen). Das ist optional und hat niedrige Priorität.

---

## Entwicklung

### Starten

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Kein zweiter Terminal nötig. App läuft auf `http://localhost:8000`.

### CSS-Rebuild (nur bei Tailwind-Standalone)

```bash
./tailwindcss -i app/static/css/input.css -o app/static/css/style.css --watch
```

### HTMX aktualisieren

```bash
# Version prüfen: https://github.com/bigskysoftware/htmx/releases
curl -sL https://unpkg.com/htmx.org@2.x.x/dist/htmx.min.js -o app/static/js/htmx.min.js
# SHA256 prüfen und in CSP script-src als integrity eintragen
sha256sum app/static/js/htmx.min.js
```

---

## Abhängigkeiten (komplett)

### Python (pyproject.toml) — unverändert
```
fastapi>=0.111
uvicorn[standard]>=0.29
pydantic[email]>=2.7
pyyaml>=6.0
filelock>=3.14
weasyprint>=62
jinja2>=3.1
python-multipart>=0.0.9
python-dotenv>=1.0
```

### JavaScript — lokal gebündelt, KEIN npm
```
htmx.min.js          (~50 KB, ~14 KB gzipped)
ext/sse.js           (~3 KB)
```

**Gesamte clientseitige Dependencies: 2 Dateien, ~53 KB unkomprimiert.**

Zum Vergleich vorher: ~300+ npm-Pakete, ~250 MB node_modules.

---

## Codestil / Konventionen

- Python: Ruff (`ruff check`, `ruff format`), Zielversion py312, line-length 100
- HTML-Templates: 2 Spaces Einrückung, Jinja2-Blöcke auf eigener Zeile
- CSS-Klassen: BEM-Namenskonvention wenn Plain CSS, Tailwind-Utilities wenn Tailwind CLI
- Commits: Konventionelle Commits auf Deutsch (`feat:`, `fix:`, `refactor:`, `docs:`)
- Jede Seite wird in einem eigenen Commit migriert
- Tests laufen nach jedem Migrationsschritt grün
