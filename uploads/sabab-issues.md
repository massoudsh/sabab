# sabab (چرا / Chera): issue drafts (glass UI/UX, features, improvements)

Repo: https://github.com/massoudsh/sabab

16 issues, each with a title, labels and a body written so an AI agent can pick it up cold: context with real file paths, tasks, acceptance criteria. Bodies are in English for agent reliability; every user-facing string in the product stays Persian.

How to use:
- Each issue starts with `## ISSUE`, then `Title:`, `Labels:` and `Body:`. Copy by hand, or split on `## ISSUE` for a script (for example `gh issue create --title ... --label ... --body-file ...`).
- Create **S16 (epic)** last, then replace the `S01`...`S15` references in its checklist with the real issue numbers.
- New labels used: `ui`, `ux`, `frontend`, `backend`, `agent-ready`. Probably existing: `feature`, `infra`, `security`, `epic`, `p0`, `p1`, `p2`.

Already open in the repo, so not duplicated here (the new issues reference them): #1 auth and persistent storage, #2 chat history, #3 LLM layer, #4 proactive alerts and suggested actions, #5 live data connectors, #6 multi-tenancy/RBAC/audit log, #7 insight thresholds and feedback, #8 hardening roadmap.

Findings these issues are based on (all verified in the repo):
- `frontend/style.css` names Vazirmatn but never loads it (no `@font-face`, no `<link>`); Chart.js is loaded from a CDN; many text sizes are 10 to 12 px; I found no base rule for `.feature-center` / `.feature-card`, so those cards are probably unstyled.
- In the UI: the three setting switches have no handlers, the notification dot and the user chip ("مدیر پروژه") are hard-coded, the forecast result only appears in a 3-second toast, saved dashboards are created but never listed (`GET /api/dashboards` is never called), and datasets cannot be deleted from the UI although `DELETE /api/datasets/{id}` exists. `uploaded_at` is shown as a raw ISO string.
- In the backend: CORS is `*`; datasets are stored as pickle; the upload size limit is checked only after the whole file is read into memory; datasets over 200,000 rows are silently truncated; `datastore.py` and `workspace.py` write JSON without atomic replace or locking; deleting a dataset leaves its dashboards, alerts, connections and comments behind; `POST /api/connections/{id}/sync` returns metadata and re-reads nothing; Excel read errors expose the raw exception text to the client.
- In the NLU: `ParsedIntent.filters` exists but is never set or used; keywords are matched as substrings, not tokens.
- The landing page's main CTA is `href="#"`, and it promises drag-and-drop upload, which the app does not have.
- `AGENTS.md` tells agents to maintain `.noqte/wiki/`, but that directory does not exist. There is no Dockerfile and no CI. `docs/ARCHITECTURE.md` mentions `app.js: loadInsights`, which does not exist.

---

## ISSUE S01

Title: refactor(frontend): foundations: load the font, self-host Chart.js, fix missing card styles, readable sizes, ES modules

Labels: ui, frontend, p1, agent-ready

Body:

## Context
`frontend/style.css` is one long minified-style file that declares `font-family:"Vazirmatn",...` but never loads it: there is no `@font-face` and no font `<link>` in `frontend/index.html`, so most machines fall back to Tahoma. `index.html` loads Chart.js from `cdn.jsdelivr.net`, which contradicts the landing page promise that data stays on the user's infrastructure and breaks offline use. This is the prerequisite for the glass redesign (see the epic).

## Tasks
1. Self-host Vazirmatn (400/500/600/700, woff2, OFL license) in `frontend/fonts/` with `@font-face` and `font-display: swap`.
2. Self-host Chart.js 4.4.4 as `frontend/vendor/chart.umd.min.js` and remove the CDN `<script>`. Keep a short `frontend/vendor/README.md` with the version and source.
3. Find and fix the missing base styles: `.feature-center` and `.feature-card` only appear inside media queries and descendant selectors. Give them proper grid/card rules so the "اتصال داده / داشبورد / هشدار / پیش‌بینی / همکاری" cards render as cards.
4. Reformat `style.css` into labelled sections (tokens, base, layout, components, views, utilities). Keep behavior identical.
5. Raise the smallest text sizes: nothing below 12 px; body at least 14 px; use `rem` tokens instead of fixed `px` (`.data-table th`, `.suggestions button`, `.stat-label`, `.feature-card p` are 10 to 11 px today).
6. Replace inline `style="--stat-color:..."` in `renderStats()` (and any other inline styles built in `app.js`) with classes or data attributes, so a strict CSP is possible later.
7. Split `frontend/app.js` (about 20 KB, very long one-line functions) into ES modules loaded with `<script type="module">`: `api.js`, `state.js`, `format.js`, `charts.js`, and one file per view. Still no bundler. Add a Prettier config. May be a separate follow-up PR if too large.

## Acceptance criteria
- [ ] No request to any third-party host on any page load (DevTools, Network tab)
- [ ] Text renders in Vazirmatn on a machine without it installed
- [ ] Feature-center cards look like cards at 375, 768 and 1280 px
- [ ] No visual regression otherwise; `cd backend && python -m pytest tests/ -v` passes

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S02

Title: feat(ui): glass design system (tokens, primitives, aurora background, light/dark, fallbacks)

Labels: ui, frontend, feature, p1, agent-ready

Body:

## Context
Today the app is a dark navy sidebar (`#101827`) next to flat white cards on `#f5f7fb`, with purple (`#635bdf`) and teal (`#16b8a6`) accents. Goal: a modern glassmorphism language where frosted translucent panels float over an ambient purple/teal gradient, readable enough for long analysis sessions. Depends on S01.

## Tokens to add
```css
--glass-bg: rgba(255,255,255,.58);
--glass-bg-strong: rgba(255,255,255,.76);
--glass-border: rgba(255,255,255,.65);
--glass-highlight: inset 0 1px 0 rgba(255,255,255,.7);
--glass-shadow: 0 10px 40px rgba(31,41,64,.12);
--glass-blur: 20px;
--glass-saturate: 165%;
```
Provide dark-theme values (translucent navy with a faint white border) and chart colors as tokens (`--chart-1..6`).

## Tasks
1. Ambient background: fixed layered radial gradients (purple, teal, a touch of amber) behind the app, CSS only; slow drift allowed, disabled under `prefers-reduced-motion`.
2. Primitives: `.glass`, `.glass-strong`, `.glass-interactive` (hover lift and brighter border), `.glass-inset` (inputs, selects), plus restyled `.primary-button` (gloss and soft glow), `.secondary-button` (glass), `.status-badge`, `.switch`, tables (`.data-table` on glass with sticky header), `.toast`.
3. Convert `.panel`, `.stat-card`, `.insight-card`, `.report-card`, `.feature-card`, `.bubble` and `.welcome-banner` to the primitives.
4. Fallbacks: `@supports not (backdrop-filter: blur(1px))` gives solid surfaces at about .94 alpha; `prefers-reduced-transparency: reduce` gives solid surfaces; `prefers-contrast: more` gives stronger borders.
5. Themes: light and dark via `prefers-color-scheme` plus a `data-theme` attribute override (the toggle itself is in S09).
6. Performance: at most about 8 `backdrop-filter` elements per viewport; do not apply it to every table row or every chat bubble; verify smooth scrolling with 6x CPU throttling.
7. Docs: `docs/design/glass-design-system.md` (tokens, do/don't, contrast table) and a dev-only `/styleguide` page (served only when an env flag such as `CHERA_DEV=1` is set) that renders every primitive.

## Acceptance criteria
- [ ] Text on every glass surface keeps at least 4.5:1 contrast (3:1 for large text) in both themes, checked over the worst-case background in the styleguide
- [ ] Correct with `backdrop-filter` unsupported, with reduced transparency, and in dark mode
- [ ] `/styleguide` is not reachable unless the dev flag is set
- [ ] No third-party assets

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S03

Title: feat(ui): glass app shell: floating sidebar and topbar, real notifications, hash routing, mobile nav, command palette

Labels: ui, ux, frontend, feature, p1, agent-ready

Body:

## Context
`frontend/index.html` has a fixed dark sidebar and a plain topbar. Several shell elements are decorative: the notification button always shows a red dot and does nothing, the user chip is hard-coded to «مدیر پروژه» with avatar «م», and `switchView()` in `app.js` only toggles classes, so the browser Back button leaves the app and views cannot be linked. On phones the sidebar becomes a stacked block and a horizontally scrolling nav row. Depends on S01 and S02.

## Tasks
1. Sidebar as a floating frosted panel (inset from the edges, rounded), active item with a soft teal glow; topbar as a sticky glass bar.
2. Hash routing: `#/dashboard`, `#/chat`, `#/datasets`, `#/insights`, `#/reports`, `#/settings`; Back/Forward work; selected dataset is kept in the hash or in `sessionStorage`; focus moves to the page `<h1>` on view change.
3. Notifications: the dot appears only when `GET /api/alerts` returns at least one `triggered: true`; clicking opens a glass popover listing triggered alerts (name, current value vs threshold) with a link to the alerts tool.
4. User chip: replace the hard-coded name with a neutral placeholder and a menu (settings, about) until auth exists (issue #1); no fake identity.
5. Mobile (under 700 px): bottom glass tab bar for the main views and a drawer for the dataset list; respect `env(safe-area-inset-bottom)`; touch targets at least 44 px.
6. Command palette (`Ctrl/Cmd+K`, optional but recommended): switch views, select a dataset, run a suggested question. Fully keyboard-operable, `role="dialog"`, focus trap.
7. Replace the text glyph icons (⌂ ▤ ✦ ▥ ⚙) with inline SVG icons (`aria-hidden="true"`).

## Acceptance criteria
- [ ] Back/Forward and deep links work for every view
- [ ] No decorative-but-fake controls remain (dot, user chip)
- [ ] Shell correct at 375, 768 and 1280 px; nothing overlaps the iOS home indicator
- [ ] Command palette fully usable with keyboard only

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S04

Title: feat(ux): dedicated chat workspace with answer cards, "how this was computed", contextual suggestions and export

Labels: ui, ux, frontend, feature, p0, agent-ready

Body:

## Context
Asking questions is the core of the product, but it lives in a small card on the dashboard (`#dashboard-chat`, `min-height:115px`). `askQuestion()` in `app.js` appends HTML with `insertAdjacentHTML`, never scrolls, shows no loading state except a disabled input, and the three suggestion chips («روند فروش», «علت افت», «بیشترین مقدار») assume a column called فروش. Fallback answers (`ok:false`) look the same as real answers. Chat history persistence is tracked separately in issue #2; this issue is UI only. Depends on S02.

## Tasks
1. New full-height «گفت‌وگو» view (nav item and `#/chat`). The dashboard card becomes a compact preview that links to it.
2. Message components: user bubble; answer card with narrative, optional table (sticky header, sortable, row limit with "show more") and optional chart; clearly different style for `ok:false` fallbacks, showing the dataset's columns as clickable chips that fill the input.
3. "نحوهٔ محاسبه" disclosure on each answer showing the interpretation: intent, metric column, group column, date column, function. Extend `AskResponse` (`backend/app/schemas.py`) with an optional `explanation` object filled in `main.py` from `ParsedIntent`; add tests.
4. Loading state: typing/skeleton bubble, auto-scroll to the newest message, `aria-live="polite"` on the message list.
5. Suggestions generated from the selected dataset's real columns (numeric, date, categorical from `DatasetDetail`), not hard-coded.
6. Export: copy answer text, download table as CSV (UTF-8 with BOM so Excel shows Persian correctly), download chart as PNG.
7. Input: `textarea` with Enter to send and Shift+Enter for a new line; ArrowUp recalls the previous question.
8. Keep the chat state in an in-memory store module so issue #2 can plug server-side history in later.

## Acceptance criteria
- [ ] A user can ask three questions in a row and always sees the newest answer without scrolling manually
- [ ] Suggestions change with the dataset and never reference a column that does not exist
- [ ] Every answer shows how it was interpreted; a wrong interpretation is visible at a glance
- [ ] CSV export opens correctly in Excel with Persian headers
- [ ] Backend tests cover the new `explanation` field

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S05

Title: feat(ui): glass dashboard, insights and report views with properly themed RTL charts

Labels: ui, frontend, feature, p1, agent-ready

Body:

## Context
Views: overview (`#view-dashboard`), insights (`#view-insights`), reports (`#view-reports`). Charts are created in `renderChart()` with `new Chart(...)` every time a view re-renders and are never destroyed (`chartCounter` is incremented and never used), so repeated dataset switches leak canvases and Chart instances. Chart styling is hard-coded (`font: Tahoma`, grey ticks, English legend defaults), tooltips and axes are not RTL-aware, and tick labels use Latin digits. `selectDataset()` awaits two requests one after the other and shows no loading state. Depends on S01 and S02.

## Tasks
1. Chart helper in `charts.js`: one theme object built from CSS tokens (font Vazirmatn, colors `--chart-1..6`, grid and tick colors per theme), RTL legend and tooltip, Persian digits via `toLocaleString('fa-IR')`, and a registry that destroys the previous chart for a canvas before creating a new one.
2. Skeleton placeholders for stat cards, insight cards and charts while data loads; fetch detail and insights in parallel with `Promise.all`.
3. Overview: stat cards as `.glass-interactive`; welcome banner as a gradient glass hero; show real KPI cards from `GET /api/datasets/{id}/kpis` (currently only used for a count in `renderFeatureStatus`).
4. Insights page: severity shown with icon plus text, not color alone; each card keeps its mini chart; add a "ask about this" button that opens the chat (S04) with a prefilled question.
5. Report page: dataset summary, column profile table (name, detected type, null %, example values; add a small backend field if needed with tests), preview table; a print stylesheet (white background, glass off, hide shell) for the existing «چاپ گزارش» button.
6. Empty and error states for every view (reuse the existing `.empty-state` markup, restyled).

## Acceptance criteria
- [ ] Switching datasets 20 times does not increase the number of live Chart instances or canvases
- [ ] Charts use the app font, show Persian digits and read correctly right-to-left in both themes
- [ ] Print preview of the report is clean and readable
- [ ] No view shows a blank area while loading

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S06

Title: feat(ux): analysis tools panel: forecast chart, saved dashboards, alerts, comments and honest connections

Labels: ui, ux, frontend, backend, feature, p1, agent-ready

Body:

## Context
`renderFeatureCenter()` in `app.js` renders five small forms (connection, dashboard, alert, forecast, comment). Problems:
- The forecast result is shown only in a toast for about 3 seconds as text («دورهٔ بعد ۱: ...»); the periods are hard-coded to 3 although the API allows 1 to 12.
- `POST /api/dashboards` stores `widgets: ["overview","insights","forecast"]`, but the UI never calls `GET /api/dashboards`, so saved dashboards cannot be opened, shared or deleted, and nothing consumes `widgets`.
- Alerts can be created and show up only as a count; they cannot be listed or deleted from the UI although `DELETE /api/alerts/{id}` exists.
- `POST /api/connections/{id}/sync` returns the dataset metadata and re-reads nothing, so «اتصال داده» suggests live syncing that does not exist (real connectors are issue #5).
- Comments have no list, no timestamps and a free-text author.
Proactive alerts and suggested actions are tracked in issue #4; this issue is about the existing features. Depends on S02 and S04.

## Tasks
1. Replace the five mini cards with a tabbed glass panel «ابزارهای تحلیل» (forecast, dashboards, alerts, notes, sources), each tab with a list plus a create form.
2. Forecast: render a chart (history as a solid line, forecast as a dashed line), periods selector 1 to 12, and a short note on the method and its limits (taken from `analytics.forecast_by_period`); keep the result visible until dismissed.
3. Dashboards: list saved dashboards with open and delete. Opening renders the widgets named in `widgets` (overview KPIs, insights, forecast) for the saved dataset. Orphaned dashboards (dataset deleted) show a clear state.
4. Alerts: list with current value vs threshold, status chip («فعال» / «عادی»), delete; validate the form; surface triggered alerts in the topbar popover (S03).
5. Sources: rename the feature to «منبع داده (فایل)» and show the file, row count and upload date. Either implement a real "refresh" (re-upload replaces the dataset content and keeps the same id) or remove the sync endpoint's implication; do not claim live sync until issue #5.
6. Notes: per-dataset thread with Jalali timestamps (`Intl.DateTimeFormat('fa-IR-u-ca-persian')`), author name remembered in `localStorage` until auth exists (issue #1), delete via a new `DELETE /api/comments/{id}`.
7. Tests for every new or changed endpoint (`DELETE /api/comments/{id}`, refresh behavior).

## Acceptance criteria
- [ ] A forecast is shown as a chart and stays on screen
- [ ] A saved dashboard can be listed, opened and deleted from the UI
- [ ] An alert can be created, seen with its current value, and deleted
- [ ] No label in the UI promises a capability the backend does not have
- [ ] New endpoints have tests

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S07

Title: feat(ux): upload and dataset management: drag and drop, progress, preview, delete, Jalali dates, sample data

Labels: ui, ux, frontend, feature, p1, agent-ready

Body:

## Context
Upload is a button that opens a file picker (`upload-trigger`), although the landing page says «بکش و رها کن». The datasets table shows `uploaded_at` as a raw ISO string, the status badge always says «آماده تحلیل», and there is no way to delete a dataset in the UI although `DELETE /api/datasets/{id}` exists. A new user with no file has nothing to try. Datasets over 200,000 rows are silently cut to the first 200,000 (`df.head(MAX_ROWS)` in `datastore.save_upload`); the user is never told (backend change in S12).

## Tasks
1. Drag-and-drop zone over the whole app (visible overlay while dragging), plus the existing button; accept `.csv .tsv .xlsx .xls`; reject other types client-side with a Persian message.
2. Upload progress using `XMLHttpRequest` (fetch has no upload progress), cancel button, clear error states using the server's Persian error text.
3. After upload: a preview step showing the first rows, detected column types (numeric, date, category) and a warning list (empty columns, duplicate names, truncation); a button to continue to the chat.
4. Datasets table: delete with a confirmation dialog (`DELETE /api/datasets/{id}`), search (exists), sort by name, rows, date; show dependent items that will be removed (dashboards, alerts, notes; see S12).
5. Show `uploaded_at` as a Jalali date and time (`fa-IR-u-ca-persian`), not raw ISO.
6. Sample data: ship a small synthetic Persian sales CSV (about 200 rows with Jalali dates, products, channels) in `docs/samples/sales-sample.csv` and a «امتحان با داده نمونه» button that uploads it through the normal endpoint. The data must be clearly synthetic.
7. Truncation notice: when the backend reports `truncated: true` (S12) show a prominent warning on the dataset and in the report.

## Acceptance criteria
- [ ] A file dropped anywhere on the page uploads; unsupported types are refused with a clear message
- [ ] A dataset can be deleted from the UI after confirmation
- [ ] A new user can reach a working answer in under a minute using only the sample button
- [ ] Dates display in the Jalali calendar

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S08

Title: a11y: accessibility, keyboard and RTL audit of the web client

Labels: ux, ui, frontend, p1, agent-ready

Body:

## Context
Glass UIs regress accessibility easily. Known problems in the current client: much of the text is 10 to 12 px; muted text `#718096` on light backgrounds is probably below 4.5:1 at those sizes (measure it); navigation icons are text glyphs read aloud by screen readers; chart canvases have no text alternative; the toggle switches are bare checkboxes; dynamic areas (chat, toast, upload status) have only partial live-region support; the «حالت کم‌تحرک» switch does not exist in behavior and `prefers-reduced-motion` is not honored.

## Tasks
1. Contrast audit of every text/background pair in both themes against WCAG 2.2 AA; fix tokens.
2. Landmarks and semantics: `header`, `nav`, `main`, skip link; the view switcher marked with `aria-current="page"`; icons `aria-hidden`; headings in order (one `h1` per view).
3. Keyboard: visible `:focus-visible` rings on every control, logical tab order, no keyboard traps, command palette and dialogs trap and restore focus.
4. Charts: each chart gets `role="img"` and an `aria-label` summarising it, plus a "view as table" toggle that shows the same data (S05 helper).
5. Switches: `role="switch"` with `aria-checked`; labels tied to inputs; settings feedback announced.
6. Live regions: chat messages, toasts, upload and processing status.
7. Honor `prefers-reduced-motion` and `prefers-reduced-transparency` globally.
8. RTL audit: logical properties instead of physical `left/right` where they are not deliberately RTL-specific (`.notification-dot`, `.toast{left:..}`, `.switch:before{right:..}`); mixed Persian/Latin strings in table cells and dataset names use `<bdi>` or `dir="auto"`.
9. Add an automated axe-core check (Playwright script, no bundler) that runs against each view with the sample dataset loaded and fails CI on serious or critical violations.

## Acceptance criteria
- [ ] Axe reports no serious or critical violations on any view
- [ ] Upload, ask a question, create an alert and delete a dataset can all be done with the keyboard only
- [ ] No text below 12 px; contrast at least 4.5:1 in both themes
- [ ] Reduced-motion users see no animation

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S09

Title: feat(ux): settings that actually work (numerals, auto-insights, reduced motion, theme, density)

Labels: ux, frontend, feature, p2, agent-ready

Body:

## Context
The settings view text says «این گزینه‌ها برای همین فضای کاری ذخیره می‌شوند», but nothing is saved or applied: the three `.switch` inputs have no handlers, and the tabs «اعلان‌ها» and «دسترسی و امنیت» do nothing. Persian digits are forced everywhere by the `fa()` helper regardless of the first switch. Server-side workspace settings come with auth (issue #1); this issue stores them in the browser.

## Tasks
1. `settings.js` module: typed settings with defaults, stored in `localStorage` under `chera.settings.v1` (wrapped in try/catch), change events, and a reset button.
2. «نمایش اعداد فارسی»: one central `formatNumber()` honoring the setting; replace the scattered `fa()` / `toLocaleString('fa-IR')` calls (charts included, S05).
3. «بینش خودکار پس از انتخاب دیتاست»: when off, do not fetch insights on dataset selection; show a «تحلیل کن» button instead.
4. «حالت کم‌تحرک»: sets `data-reduce-motion` on `<html>`; CSS disables transitions and background drift; defaults to on when `prefers-reduced-motion` is set.
5. Add theme (سیستم / روشن / تاریک) and density (راحت / فشرده) controls wired to S02.
6. Tabs: implement real content for «اعلان‌ها» (which alert states appear in the popover) or mark the tabs «به‌زودی» and disable them. «دسترسی و امنیت» must not imply controls that do not exist; link to the auth roadmap issue instead.
7. The sentence about saving must be true: say "در این مرورگر ذخیره می‌شود" until server-side settings exist.

## Acceptance criteria
- [ ] Every control in the settings view changes behavior immediately and survives reload
- [ ] No control or tab exists that does nothing
- [ ] Turning Persian digits off switches stat cards, tables and charts to Latin digits

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S10

Title: feat(landing): glass landing page redesign, working CTAs and claims that match the product

Labels: ui, frontend, feature, p1, agent-ready

Body:

## Context
`landing/index.html` and `landing/style.css` are a separate static page. Problems:
- The main CTA «شروع رایگان» in the final section is `href="#"`, and nothing links to the app.
- It promises «بکش و رها کن» upload (not implemented until S07) and a tool that «پیشنهاد می‌کند حالا چه کاری باید انجام شود» (suggested actions are issue #4, not built).
- Emoji icons, no social/OG tags, no screenshots of the real product.
- The demo conversation is static text.

## Tasks
1. Apply the glass design system (S02): aurora hero, glass feature cards, glass demo window; light and dark themes; self-hosted Vazirmatn (no third-party requests).
2. All CTAs point to the app (`/` when served together; make the app URL configurable in one place) and to the sample-data flow (S07).
3. Replace the static demo with a short scripted, CSS/JS-only animated conversation (question, answer, chart) that respects `prefers-reduced-motion`; or real screenshots of the redesigned app with alt text.
4. Make every claim true: remove or reword drag-and-drop and "suggests what to do" until those features ship; keep «داده روی زیرساخت شماست» only while no third-party calls exist.
5. SEO and sharing: `<meta>` description (exists), Open Graph and Twitter tags, canonical, favicon set, `lang="fa"`, JSON-LD `SoftwareApplication`.
6. Replace emojis with inline SVG icons; add a footer with link to the repository and license.
7. Serve the landing page from the backend at `/landing` (or document how to host it) so Docker (S14) ships both.

## Acceptance criteria
- [ ] Every button and link on the page goes somewhere real
- [ ] Lighthouse accessibility and best-practices at least 95; no third-party requests
- [ ] No feature claim on the page is missing from the product at that commit

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S11

Title: feat(nlu): filters, period comparison, token-safe matching, clarification questions and a Persian question benchmark

Labels: backend, feature, p1, agent-ready

Body:

## Context
`backend/app/nlu.py` is the default (rule-based) question engine. Gaps found:
- `ParsedIntent.filters` is declared but never set or used, so questions like «فروش تهران در فروردین» ignore «تهران».
- Keywords are matched as substrings (`normalize(kw) in norm_q` in `_detect_func`, trigger lists), so short keywords such as «کل» or «جمع» can match inside unrelated words.
- When several columns match or none clearly does, the engine silently picks one (for example `categorical_cols[0]` for `explain_change`) instead of asking.
- There is no explicit "this period vs the previous one" intent; «چرا» questions use whatever periods `explain_change` picks.
- There are only a handful of unit tests (`backend/tests/test_nlu.py`), so changes cannot be measured.
The LLM fallback layer is tracked in issue #3 and chat history in issue #2; keep this issue rule-based. The `explanation` field from S04 consumes the intent details.

## Tasks
1. Token-aware keyword matching (word boundaries after `textnorm.normalize`), with tests for the known false positives.
2. Filters: support equality filters on categorical columns and date-range filters («در فروردین ۱۴۰۳», «بین فروردین و خرداد») using `jalali.py`; apply them to aggregate, groupby, trend and explain_change.
3. Period comparison: «این ماه نسبت به ماه قبل», «فروردین در برابر اردیبهشت» as an explicit `compare` intent that feeds `explain_change` with the chosen periods.
4. Ambiguity handling: return a `clarify` intent with candidate columns (as chips for S04) when two columns score within a small margin, or when a metric/group had to be guessed.
5. Show-your-work: include matched columns, filters and periods in the parse result so the backend can return the `explanation` object (S04).
6. Benchmark: `backend/tests/fixtures/questions_fa.jsonl` with at least 100 Persian questions (formal and colloquial, mixed digits) over 2 or 3 small fixture datasets; each with expected intent, columns and, where applicable, the numeric answer computed independently with pandas.
7. `python -m backend.tests.bench_nlu` (or a pytest marker) prints intent accuracy and answer accuracy; CI fails if either drops below the stored baseline.

## Acceptance criteria
- [ ] Known substring false positives fixed, with regression tests
- [ ] Filtered and period-comparison questions return correct numbers verified against pandas
- [ ] Ambiguous questions produce a clarification, never a silent guess
- [ ] Benchmark runs offline and reports accuracy; baseline stored in the repo

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S12

Title: fix(backend): data correctness and robustness: truncation notice, streaming size limit, atomic stores, cascade delete, honest sync

Labels: backend, p0, agent-ready

Body:

## Context
Confirmed in `backend/app/datastore.py`, `workspace.py` and `main.py`:
1. `save_upload` silently keeps only the first 200,000 rows (`df.head(MAX_ROWS)`); every answer afterwards is computed on partial data and the user is never told.
2. `upload_dataset` does `content = await file.read()` and only then checks the 25 MB limit, so the whole body is already in memory.
3. `_save_manifest` and `workspace._save` rewrite JSON files in place with no atomic replace and no lock: a crash mid-write or two concurrent requests can lose or corrupt data.
4. `DELETE /api/datasets/{id}` removes the file and manifest entry only; dashboards, alerts, connections and comments for that dataset stay (orphans).
5. `POST /api/connections/{id}/sync` returns stored metadata and re-reads nothing.
6. CSV reading uses `engine="python"` (slow on large files); column names are stripped, which can create duplicates.
7. Excel read errors return `f"...: {exc}"`, leaking internal exception text to the client.
Persistent multi-user storage is issue #1; this issue makes the current stores safe in the meantime.

## Tasks
1. Add `truncated` and `original_rows` to `DatasetMeta` (`schemas.py`) and to the upload response; keep the first rows but make the truncation visible in the API (the UI part is in S07).
2. Enforce the size limit while streaming (read in chunks, abort with 413 and a Persian message when the limit is crossed) instead of reading everything first.
3. Atomic writes for `manifest.json` and `workspace.json`: write to a temp file in the same directory, `fsync`, `os.replace`; protect read-modify-write sections with a process-level lock (and a file lock if running multiple workers; document the limit).
4. Cascade delete: deleting a dataset also removes its dashboards, alerts, connections and comments (or marks them orphaned and the listing endpoints filter them out); return what was removed so the UI can confirm.
5. Replace the fake sync with a real "refresh from file" (re-upload to the same dataset id) or rename/remove the endpoint; update `docs/ARCHITECTURE.md` section 5 accordingly.
6. Use the faster C CSV engine first and fall back to the Python engine on failure; deduplicate column names (`name`, `name_2`); report skipped bad lines.
7. Return a generic Persian error for unreadable Excel files and log the real exception server-side.
8. Verify that cells with Persian/Arabic-Indic digits and thousands separators (for example «۱٬۲۰۰٬۰۰۰», «1,200,000») are detected as numeric columns and summed correctly; add fixtures and fix `analytics.numeric_columns` / loading if they are not.
9. Tests for every item (including a simulated crash during write and a concurrent-write test).

## Acceptance criteria
- [ ] Uploading 250,000 rows returns `truncated: true` and `original_rows: 250000`
- [ ] A 100 MB upload is rejected without being fully buffered
- [ ] Killing the process mid-write never leaves a corrupt manifest
- [ ] After deleting a dataset no dashboard, alert, connection or note refers to it
- [ ] Persian-digit numeric columns work in aggregates and trends

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S13

Title: security: pre-auth hardening: replace pickle, restrict CORS, upload validation, rate limits, security headers

Labels: security, backend, p0, agent-ready

Body:

## Context
Auth and multi-tenancy are separate roadmap items (#1, #6), but the app is already reachable by anyone who can reach the server. Findings:
- `datastore.py` stores each dataset with `DataFrame.to_pickle` and loads it with `pd.read_pickle`. Unpickling executes code, so anyone who can write into `backend/data/` (a restored backup, a shared volume, a future upload bug) gets code execution.
- `main.py` sets `allow_origins=["*"]` with all methods and headers.
- Uploads are validated by file extension only.
- No rate limit on `/api/datasets/upload` or `/api/ask`; no request size limit besides the in-memory check (see S12).
- No security headers or CSP; the frontend loads Chart.js from a CDN (S01 removes it).
- Comments take a free-text `author`, so anyone can impersonate anyone (resolved properly with auth, issue #1).
- Overlaps the hardening checklist in issue #8; close those items here where they apply.

## Tasks
1. Replace pickle with Parquet (`pyarrow`) for dataset storage. Provide a one-time migration command for existing `.pkl` files that only runs when the operator asks for it (never auto-unpickle at startup), then remove `read_pickle` from the code.
2. CORS: configurable allowlist from an env var (`CHERA_CORS_ORIGINS`), default same-origin only; no wildcard with credentials.
3. Upload validation: extension plus magic bytes (xlsx must be a valid zip with expected parts; reject encrypted or macro-enabled workbooks), a decompressed-size check for xlsx (zip bomb), a maximum column count, safe handling of formula/CSV-injection when exporting data back out (prefix cells starting with `= + - @`).
4. Rate limiting for upload and ask endpoints (per client IP; in-memory limiter is acceptable, document multi-worker limits); return 429 with a Persian message.
5. Security headers via middleware: CSP (`default-src 'self'`, no inline script; styles per S01), `X-Content-Type-Options`, `Referrer-Policy`, `frame-ancestors 'none'`, HSTS when served over HTTPS.
6. Never return raw exception text to the client (see S12 item 7); central exception handler that logs details and returns a generic Persian error.
7. Optional shared-secret gate for demos: if `CHERA_ACCESS_TOKEN` is set, every `/api` call requires it (until real auth ships), so the app can be exposed safely for a demo.
8. Tests: path traversal attempts on dataset ids, malformed uploads, CORS preflight, rate limit, header presence.

## Acceptance criteria
- [ ] No `read_pickle` / `to_pickle` left in the code base
- [ ] Cross-origin requests from an unlisted origin are refused
- [ ] A crafted xlsx zip bomb is rejected without exhausting memory
- [ ] Responses carry the security headers; the app works with the CSP enabled
- [ ] With `CHERA_ACCESS_TOKEN` set, unauthenticated API calls return 401

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S14

Title: infra(docker): Docker as the primary install method (backend + frontend + landing), manual install as the alternative

Labels: infra, p1, agent-ready

Body:

## Context
The README only documents the manual flow (venv, pip, uvicorn). There is no Dockerfile or compose file. Because FastAPI already serves `frontend/` as static files, one image is enough for the app; the landing page is static. Goal: `docker compose up` is the main way to install, with the manual steps documented as the alternative.

## Tasks
1. `backend/Dockerfile` (or a root `Dockerfile` with the repo as build context, since the backend serves `../frontend`): multi-stage, pinned Python slim image, `pip install --no-cache-dir -r requirements.txt`, non-root user, `HEALTHCHECK` on `/api/health`, no secrets baked in. The image must include `frontend/` and `landing/`.
2. `docker-compose.yml`: service `app` (uvicorn, port 8000), a named volume mounted at `backend/data` (datasets, manifest, workspace) so data survives restarts, and `restart: unless-stopped`. Optional profile for a reverse proxy serving `landing/` on its own port.
3. `.dockerignore` (venv, `__pycache__`, `backend/data`, tests, docs).
4. Env: `.env.example` listing every variable (`CHERA_CORS_ORIGINS`, `CHERA_ACCESS_TOKEN`, `CHERA_DEV`, limits from S12/S13) with safe defaults; compose reads `.env`.
5. README restructure (Persian, command blocks in English): "نصب با Docker" first (`cp .env.example .env`, `docker compose up -d`, open `http://localhost:8000`), "نصب دستی" second (existing steps), plus how to back up the data volume and how to upgrade.
6. CI (see S15): build the image on every PR; optionally publish to GHCR on tags.
7. Make the data directory configurable (`CHERA_DATA_DIR`, default `backend/data`) in `datastore.py` and `workspace.py` so the volume path is explicit; add tests.

## Acceptance criteria
- [ ] On a clean machine with only Docker, `docker compose up` yields a working app on port 8000 and the sample dataset flow works
- [ ] Data survives `docker compose down && docker compose up`
- [ ] The container runs as non-root; `docker compose config` shows no secrets
- [ ] The manual install steps still work and are documented as the alternative

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S15

Title: chore(agents): make AGENTS.md match reality, add CI, templates, lint, and a browser smoke test

Labels: infra, p0, agent-ready

Body:

## Context
`AGENTS.md` instructs every agent to read and maintain `.noqte/wiki/` (`overview.md`, `index.md`, `log.md`, `entities/`, `concepts/`), but that directory does not exist in the repository. An agent following the file fails at step one, and the "update the wiki after every change" rule can never be met. There is also no CI, no linter, no issue/PR template, and `docs/ARCHITECTURE.md` has drifted (it mentions `app.js: loadInsights`, which does not exist). Overlaps the checklist in issue #8; close those items here.

## Tasks
1. Resolve the wiki mismatch. Preferred: create `.noqte/wiki/` exactly as `AGENTS.md` specifies: `schema.md`, `overview.md` (at most 400 words), `index.md`, `log.md`, entity pages for `datastore`, `workspace`, `nlu-engine`, `analytics`, `insights`, `jalali`, `textnorm`, `api-main` and the frontend views, and concept pages for the rule-based NLU decision, the Jalali month-boundary decision, the MVP storage decision and the roadmap. Alternative: remove the wiki sections from `AGENTS.md`. Either way the file and the repo must agree.
2. Add to `AGENTS.md`: quick commands (install, run, test, lint, docker), the architecture map with file paths, the ground rules below, a definition of done, and a **do not change without maintainer review** list: Jalali month-boundary logic in `analytics.py`/`jalali.py` (changes need tests with real Jalali dates), the privacy rule (no raw customer data to external LLMs without consent, from `ARCHITECTURE.md` section 6), and the "never execute unsandboxed model-generated code" rule.
3. Fix documentation drift in `docs/ARCHITECTURE.md` (function names, where insights appear in the UI, storage after S13, connections after S12).
4. `.github/workflows/ci.yml`: Python pinned, install, `ruff check`, `ruff format --check`, `pytest`, Docker build; separate jobs for gitleaks, CodeQL and Dependabot (pip and github-actions) configuration.
5. `ruff` configuration and `pyproject.toml` (or `ruff.toml`); add pre-commit config; fix or justify existing findings in the same PR.
6. Frontend checks without a bundler: Prettier config and an ESLint config for the ES modules from S01.
7. Playwright smoke test (headless): upload the sample CSV, ask «چرا فروش افت کرد؟», expect an answer card with a chart; upload screenshots as CI artifacts so reviewers and agents can see UI changes. Axe checks from S08 run in the same job.
8. `.github/ISSUE_TEMPLATE/agent-task.yml` (context, files, tasks, acceptance criteria) and `.github/pull_request_template.md` (tests, RTL check, screenshots for UI changes, privacy-rule confirmation).
9. Pin dependency versions in `backend/requirements.txt` (and add a lock or hashes file); verify the current state first.

## Acceptance criteria
- [ ] An agent that reads only `AGENTS.md` can run, test and lint the project and finds every file it references
- [ ] CI is green on `main` from a fresh clone without manual steps
- [ ] The smoke test fails if upload or the ask flow breaks
- [ ] No secrets in the repository or its history that need rotating (report if found, never paste values into the issue)

**Ground rules:** FastAPI + pandas backend; frontend is plain HTML/CSS/JS served by FastAPI from `frontend/` (no bundler or framework, per `docs/ARCHITECTURE.md`); Persian RTL UI with logical CSS properties; no third-party network calls at runtime (the product promises data stays on the user's infrastructure), so self-host assets; rule-based NLU stays the default and model-generated code never runs outside a sandbox; follow `AGENTS.md`; `cd backend && python -m pytest tests/ -v` must pass.

---

## ISSUE S16 (create last)

Title: [Epic] Glass UI/UX redesign and agent-ready platform improvements

Labels: epic, ui, p1

Body:

## Goal
A modern glassmorphism client that is fast, accessible and RTL-correct, an honest feature set (no controls or claims without a working backend), safer data handling, and the foundations (Docker, CI, AGENTS.md, benchmarks) that let AI agents and humans contribute safely. Every child issue is written to be picked up independently by an AI agent. Related roadmap issues that stay separate: #1 auth/storage, #2 chat history, #3 LLM layer, #4 proactive alerts and actions, #5 connectors, #6 multi-tenancy/RBAC, #7 insight thresholds, #8 hardening checklist.

## Order of work
1. Foundations: S15 (AGENTS.md, CI), S01 (frontend foundations), S12 (data correctness), S13 (security)
2. Design system and shell: S02, S03
3. Core experience: S04, S05, S06, S07
4. Polish and reach: S08, S09, S10
5. Engine quality and delivery: S11, S14

## Checklist
(replace `S..` with the real issue numbers once created)
- [ ] S01 Frontend foundations
- [ ] S02 Glass design system
- [ ] S03 Glass app shell, routing, notifications
- [ ] S04 Chat workspace
- [ ] S05 Dashboard, insights, report and charts
- [ ] S06 Analysis tools panel
- [ ] S07 Upload and dataset management
- [ ] S08 Accessibility and RTL audit
- [ ] S09 Working settings
- [ ] S10 Landing page
- [ ] S11 NLU improvements and benchmark
- [ ] S12 Data correctness and robustness
- [ ] S13 Pre-auth security hardening
- [ ] S14 Docker as primary install
- [ ] S15 AGENTS.md, CI, templates, smoke tests

## Ground rules (apply to every child issue)
- FastAPI + pandas backend; plain HTML/CSS/JS frontend served from `frontend/`, no bundler or framework.
- Persian RTL UI: user-facing strings stay Persian, use logical CSS properties.
- No third-party network calls at runtime; self-host fonts, charts and assets.
- Rule-based NLU stays the default; model-generated code never runs outside a sandbox; no raw customer data to external LLMs without consent.
- `cd backend && python -m pytest tests/ -v` must pass; add tests for new logic; keep each PR focused on one issue.

## Definition of done (epic)
1. All child issues closed, CI green on `main`
2. A new contributor (human or agent) can run the project with `docker compose up` in under 15 minutes
3. Axe, smoke and NLU benchmark checks run in CI
4. No UI control or landing-page claim without a working implementation
