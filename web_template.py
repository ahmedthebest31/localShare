# web_template.py
# The browser page served by the LAN server. Kept in its own module so the
# HTML/CSS/JS does not clutter server_handler.py. PyInstaller bundles it
# automatically because server_handler imports it (no spec/datas change).
# Uses Jinja2 {{ variables }} and {% raw %} blocks for the CSS/JS sections.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light dark">
    <meta name="description" content="Share files with anyone on your local network.">
    <title>{{ title }}</title>
    <style>{% raw %}
        :root, :root[data-theme="light"] {
            color-scheme: light;
            --bg: #F8FAFC;
            --surface: #FFFFFF;
            --surface-alt: #F8FAFC;
            --text: #111827;
            --text-muted: #374151;
            --border: #E5E7EB;
            --border-strong: #9CA3AF;
            --link: #1E40AF;
            --link-hover: #1E3A8A;
            --btn-bg: #1E40AF;
            --btn-text: #FFFFFF;
            --btn-hover: #1E3A8A;
            --btn2-bg: #FFFFFF;
            --btn2-text: #1E40AF;
            --btn2-border: #D1D5DB;
            --btn2-hover: #F8FAFC;
            --chip-bg: #EFF6FF;
            --focus: #1E40AF;
            --ok-text: #065F46;
            --ok-bg: #ECFDF5;
            --ok-border: #A7F3D0;
            --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 8px 24px rgba(0,0,0,0.05);
        }
        @media (prefers-color-scheme: dark) {
            :root:not([data-theme="light"]) {
                color-scheme: dark;
                --bg: #0F172A;
                --surface: #1E293B;
                --surface-alt: #26334A;
                --text: #F1F5F9;
                --text-muted: #CBD5E1;
                --border: #334155;
                --border-strong: #475569;
                --link: #93C5FD;
                --link-hover: #BFDBFE;
                --btn-bg: #93C5FD;
                --btn-text: #0F172A;
                --btn-hover: #BFDBFE;
                --btn2-bg: #1E293B;
                --btn2-text: #93C5FD;
                --btn2-border: #475569;
                --btn2-hover: #26334A;
                --chip-bg: #334155;
                --focus: #FBBF24;
                --ok-text: #A7F3D0;
                --ok-bg: #064E3B;
                --ok-border: #065F46;
                --shadow: 0 1px 3px rgba(0,0,0,0.4), 0 8px 24px rgba(0,0,0,0.35);
            }
        }
        :root[data-theme="dark"] {
            color-scheme: dark;
            --bg: #0F172A;
            --surface: #1E293B;
            --surface-alt: #26334A;
            --text: #F1F5F9;
            --text-muted: #CBD5E1;
            --border: #334155;
            --border-strong: #475569;
            --link: #93C5FD;
            --link-hover: #BFDBFE;
            --btn-bg: #93C5FD;
            --btn-text: #0F172A;
            --btn-hover: #BFDBFE;
            --btn2-bg: #1E293B;
            --btn2-text: #93C5FD;
            --btn2-border: #475569;
            --btn2-hover: #26334A;
            --chip-bg: #334155;
            --focus: #FBBF24;
            --ok-text: #A7F3D0;
            --ok-bg: #064E3B;
            --ok-border: #065F46;
            --shadow: 0 1px 3px rgba(0,0,0,0.4), 0 8px 24px rgba(0,0,0,0.35);
        }
        * { box-sizing: border-box; }
        html { -webkit-text-size-adjust: 100%; }
        body {
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            font-size: 16px;
            line-height: 1.5;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        [hidden] { display: none !important; }
        .skip-link {
            position: absolute;
            inset-inline-start: -9999px;
            top: 0;
            z-index: 100;
            background: var(--surface);
            color: var(--link);
            padding: 0.75rem 1.25rem;
            font-weight: 600;
            border-end-end-radius: 8px;
        }
        .skip-link:focus {
            inset-inline-start: 0;
            outline: 3px solid var(--focus);
            outline-offset: 0;
        }
        a { color: var(--link); }
        a:hover { color: var(--link-hover); }
        :focus-visible {
            outline: 3px solid var(--focus);
            outline-offset: 2px;
        }
        .sr-only {
            position: absolute;
            width: 1px; height: 1px;
            margin: -1px; padding: 0;
            overflow: hidden;
            clip: rect(0 0 0 0);
            white-space: nowrap;
            border: 0;
        }
        .app-header {
            background: var(--surface);
            border-bottom: 1px solid var(--border);
        }
        .app-header-inner {
            max-width: 960px;
            margin: 0 auto;
            padding: 0.75rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }
        .brand {
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
            font-size: 1.125rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            color: var(--text);
        }
        .brand svg { flex-shrink: 0; }
        .header-actions {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        .status {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--ok-text);
            background: var(--ok-bg);
            border: 1px solid var(--ok-border);
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
        }
        .status::before {
            content: "";
            width: 8px; height: 8px;
            border-radius: 50%;
            background: currentColor;
        }
        main { flex: 1; width: 100%; }
        .container {
            max-width: 960px;
            margin: 0 auto;
            padding: 2rem 1.5rem 3rem;
            width: 100%;
        }
        h1 {
            font-size: 1.75rem;
            margin: 0 0 0.25rem;
            line-height: 1.25;
            letter-spacing: -0.025em;
        }
        .page-subtitle {
            margin: 0 0 2rem;
            color: var(--text-muted);
            font-size: 1rem;
            max-width: 65ch;
        }
        h2 {
            font-size: 1.125rem;
            margin: 0;
            letter-spacing: -0.01em;
        }
        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            box-shadow: var(--shadow);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .card-title {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        .file-count {
            color: var(--text-muted);
            font-size: 0.875rem;
            margin-inline-end: auto;
        }
        form { margin: 0; }
        label {
            display: block;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--text);
        }
        .upload-row {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        input[type="file"] {
            width: 100%;
            padding: 0.75rem;
            border: 2px dashed var(--border-strong);
            border-radius: 8px;
            background: var(--surface-alt);
            color: var(--text);
            font-size: 1rem;
            min-height: 48px;
        }
        .drop-hint {
            margin-top: 0.75rem;
            font-size: 0.875rem;
            color: var(--text-muted);
        }
        .card.drag-over {
            border-color: var(--focus);
            background: var(--chip-bg);
        }
        progress {
            width: 100%;
            height: 8px;
            margin-top: 0.75rem;
            border: none;
            border-radius: 999px;
        }
        progress::-webkit-progress-bar { background: var(--surface-alt); border-radius: 999px; }
        progress::-webkit-progress-value { background: var(--link); border-radius: 999px; }
        progress::-moz-progress-bar { background: var(--link); border-radius: 999px; }
        .upload-status {
            margin-top: 0.5rem;
            font-size: 0.875rem;
            color: var(--text-muted);
        }
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            min-height: 48px;
            padding: 0.625rem 1.5rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid transparent;
            text-decoration: none;
            transition: background-color 150ms ease;
            font-family: inherit;
        }
        .btn-primary {
            background: var(--btn-bg);
            color: var(--btn-text);
        }
        .btn-primary:hover { background: var(--btn-hover); }
        .btn-secondary {
            background: var(--btn2-bg);
            color: var(--btn2-text);
            border-color: var(--btn2-border);
        }
        .btn-secondary:hover { background: var(--btn2-hover); }
        .btn-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 48px;
            height: 48px;
            border-radius: 8px;
            background: var(--surface);
            color: var(--text);
            border: 1px solid var(--border-strong);
            cursor: pointer;
            transition: background-color 150ms ease;
        }
        .btn-icon:hover { background: var(--surface-alt); }
        .search-wrap {
            position: relative;
            margin-bottom: 1rem;
        }
        .search-wrap input[type="search"] {
            width: 100%;
            min-height: 48px;
            padding: 0.625rem 2.75rem 0.625rem 0.875rem;
            border: 1px solid var(--border-strong);
            border-radius: 8px;
            background: var(--surface-alt);
            color: var(--text);
            font-size: 1rem;
        }
        .search-clear {
            position: absolute;
            inset-inline-end: 0.375rem;
            top: 50%;
            transform: translateY(-50%);
            width: 40px;
            height: 40px;
            border: none;
            border-radius: 8px;
            background: transparent;
            color: var(--text-muted);
            font-size: 1.25rem;
            cursor: pointer;
            line-height: 1;
        }
        .search-clear:hover { background: var(--surface); color: var(--text); }
        .file-list { list-style: none; margin: 0; padding: 0; }
        .file-item + .file-item { margin-top: 0.5rem; }
        .file-link {
            display: flex;
            align-items: center;
            gap: 0.875rem;
            min-height: 52px;
            padding: 0.5rem 0.875rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface-alt);
            color: var(--link);
            text-decoration: none;
            word-break: break-all;
            transition: border-color 150ms ease, background-color 150ms ease;
        }
        .file-link:hover {
            border-color: var(--border-strong);
            background: var(--surface);
            color: var(--link-hover);
            text-decoration: underline;
        }
        .icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 40px; height: 40px;
            flex-shrink: 0;
            border-radius: 8px;
            background: var(--chip-bg);
            font-size: 1.25rem;
            line-height: 1;
        }
        .icon::after { content: "\\1F4C4"; }
        .icon-video::after { content: "\\1F3AC"; }
        .icon-audio::after { content: "\\1F3B5"; }
        .icon-image::after { content: "\\1F5BC"; }
        .icon-archive::after { content: "\\1F4E6"; }
        .icon-text::after { content: "\\1F4DD"; }
        .file-name { flex: 1; min-width: 0; }
        .file-download {
            color: var(--text-muted);
            font-size: 1.125rem;
            flex-shrink: 0;
        }
        .file-list.grid-view {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 0.75rem;
        }
        .file-list.grid-view .file-item { margin: 0; }
        .file-list.grid-view .file-link {
            flex-direction: column;
            text-align: center;
            justify-content: center;
            min-height: 132px;
            padding: 1rem 0.625rem;
            gap: 0.5rem;
        }
        .file-list.grid-view .icon { width: 56px; height: 56px; font-size: 1.75rem; border-radius: 12px; }
        .file-list.grid-view .file-name { word-break: break-all; }
        .file-list.grid-view .file-download { display: none; }
        .empty {
            padding: 2rem 1rem;
            text-align: center;
            color: var(--text-muted);
            border: 1px dashed var(--border-strong);
            border-radius: 8px;
            margin: 0;
        }
        .app-footer {
            border-top: 1px solid var(--border);
            background: var(--surface);
            padding: 1rem 1.5rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.875rem;
        }
        .modal {
            position: fixed;
            inset: 0;
            z-index: 50;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .modal-backdrop {
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0.6);
        }
        .modal-dialog {
            position: relative;
            z-index: 1;
            width: min(92vw, 900px);
            max-height: 90vh;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            box-shadow: var(--shadow);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .modal-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border);
        }
        .modal-title {
            flex: 1;
            margin: 0;
            font-size: 1rem;
            word-break: break-all;
            color: var(--text);
        }
        .modal-close {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 44px;
            height: 44px;
            border: none;
            border-radius: 8px;
            background: transparent;
            color: var(--text);
            font-size: 1.5rem;
            cursor: pointer;
            line-height: 1;
        }
        .modal-close:hover { background: var(--surface-alt); }
        .modal-content {
            padding: 1rem;
            overflow: auto;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 200px;
        }
        .modal-content img { max-width: 100%; max-height: 65vh; border-radius: 8px; }
        .modal-content video, .modal-content audio { max-width: 100%; }
        .modal-content iframe { width: 100%; height: 65vh; border: 0; border-radius: 8px; }
        .modal-footer {
            display: flex;
            justify-content: flex-end;
            gap: 0.75rem;
            padding: 0.75rem 1rem;
            border-top: 1px solid var(--border);
        }
        @media (min-width: 640px) {
            .upload-row { flex-direction: row; align-items: center; }
            input[type="file"] { flex: 1; }
            .container { padding-inline: 2rem; }
        }
        @media (prefers-reduced-motion: reduce) {
            * { transition: none !important; }
        }
    {% endraw %}</style>
    <script>{% raw %}
        (function () {
            var t = null;
            try { t = localStorage.getItem('theme'); } catch (e) {}
            if (t === 'dark' || t === 'light') {
                document.documentElement.setAttribute('data-theme', t);
            }
        })();
    {% endraw %}</script>
</head>
<body>
    <a class="skip-link" href="#main">Skip to content</a>

    <header class="app-header">
        <div class="app-header-inner">
            <span class="brand">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">
                    <path d="M3 7.5A2.5 2.5 0 0 1 5.5 5h3.2l1.9 2.2h7.9A2.5 2.5 0 0 1 21 9.7v7.8a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 17.5v-10Z" fill="#3B82F6"/>
                    <circle cx="8.5" cy="13.5" r="1.4" fill="#FFFFFF"/>
                    <circle cx="13.5" cy="16" r="1.4" fill="#FFFFFF"/>
                    <circle cx="15" cy="11" r="1.4" fill="#FFFFFF"/>
                </svg>
                <span>localShare</span>
            </span>
            <span class="header-actions">
                <span class="status">Online</span>
                <button type="button" id="themeToggle" class="btn-icon" aria-pressed="false" aria-label="Switch to dark mode">
                    <svg id="iconSun" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true" focusable="false">
                        <circle cx="12" cy="12" r="4"></circle>
                        <line x1="12" y1="2" x2="12" y2="5"></line>
                        <line x1="12" y1="19" x2="12" y2="22"></line>
                        <line x1="2" y1="12" x2="5" y2="12"></line>
                        <line x1="19" y1="12" x2="22" y2="12"></line>
                        <line x1="4.9" y1="4.9" x2="7" y2="7"></line>
                        <line x1="17" y1="17" x2="19.1" y2="19.1"></line>
                        <line x1="4.9" y1="19.1" x2="7" y2="17"></line>
                        <line x1="17" y1="7" x2="19.1" y2="4.9"></line>
                    </svg>
                    <svg id="iconMoon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true" focusable="false" hidden>
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                    </svg>
                </button>
            </span>
        </div>
    </header>

    <main id="main" tabindex="-1">
        <div class="container">
            <h1>{{ title }}</h1>
            <p class="page-subtitle">Share files with anyone on your local network.</p>

            {% if allow_upload %}
            <section class="card" id="uploadCard" aria-labelledby="upload-heading">
                <h2 class="card-title" id="upload-heading">Upload File</h2>
                <form method="post" enctype="multipart/form-data">
                    <label for="filetoupload">Choose a file to upload</label>
                    <div class="upload-row">
                        <input type="file" name="filetoupload" id="filetoupload" required>
                        <button type="submit" class="btn btn-primary">Upload</button>
                    </div>
                </form>
                <p class="drop-hint">You can also drag and drop files here.</p>
                <progress id="uploadProgress" max="100" value="0" hidden></progress>
                <p class="upload-status" id="uploadStatus" hidden></p>
            </section>
            {% endif %}

            <section class="card" aria-labelledby="files-heading">
                <div class="card-title">
                    <h2 id="files-heading">Shared Files</h2>
                    <span class="file-count" id="file-count">{{ files|length }} file{% if files|length != 1 %}s{% endif %}</span>
                    <button type="button" id="toggleView" class="btn btn-secondary" aria-pressed="false" aria-controls="file-list">List view</button>
                </div>
                <div class="search-wrap">
                    <label for="fileSearch" class="sr-only">Search files</label>
                    <input type="search" id="fileSearch" placeholder="Search files..." autocomplete="off">
                    <button type="button" id="searchClear" class="search-clear" aria-label="Clear search" hidden>&#215;</button>
                </div>
                <p class="sr-only" id="searchStatus" role="status" aria-live="polite"></p>
                <ul id="file-list" class="file-list">
                    {% for file in files %}
                    <li class="file-item">
                        <a class="file-link" href="{{ url_for('download_file', filename=file.name) }}">
                            <span class="icon {{ file.icon }}" aria-hidden="true"></span>
                            <span class="file-name">{{ file.name }}</span>
                            <span class="file-download" aria-hidden="true">&#8595;</span>
                        </a>
                    </li>
                    {% else %}
                    <li class="empty">No files found.</li>
                    {% endfor %}
                    <li class="empty" id="noResults" hidden>No files match your search.</li>
                </ul>
            </section>
        </div>
    </main>

    <footer class="app-footer">
        Files are shared only within your local network.
    </footer>

    <div id="previewModal" class="modal" role="dialog" aria-modal="true" aria-labelledby="previewTitle" aria-keyshortcuts="Escape" hidden>
        <div class="modal-backdrop"></div>
        <div class="modal-dialog">
            <div class="modal-header">
                <h2 class="modal-title" id="previewTitle"></h2>
                <button type="button" id="previewClose" class="modal-close" aria-label="Close preview">&#215;</button>
            </div>
            <div class="modal-content" id="previewContent"></div>
            <div class="modal-footer">
                <a id="previewDownload" class="btn btn-secondary" href="#" target="_blank" rel="noopener">Open original</a>
            </div>
        </div>
    </div>

    <script>{% raw %}
        (function () {
            var doc = document;

            function ready(fn) {
                if (doc.readyState !== 'loading') { fn(); } else { doc.addEventListener('DOMContentLoaded', fn); }
            }

            ready(function () {

                var toggleView = doc.getElementById('toggleView');
                var fileList = doc.getElementById('file-list');
                if (toggleView && fileList) {
                    function applyView(view) {
                        var grid = view === 'grid';
                        fileList.classList.toggle('grid-view', grid);
                        toggleView.textContent = grid ? 'Grid view' : 'List view';
                        toggleView.setAttribute('aria-pressed', grid ? 'true' : 'false');
                    }
                    toggleView.addEventListener('click', function () {
                        var isGrid = fileList.classList.contains('grid-view');
                        applyView(isGrid ? 'list' : 'grid');
                        try { localStorage.setItem('viewMode', isGrid ? 'list' : 'grid'); } catch (e) {}
                    });
                    var savedView = null;
                    try { savedView = localStorage.getItem('viewMode'); } catch (e) {}
                    if (savedView === 'grid') { applyView('grid'); }
                }

                var themeBtn = doc.getElementById('themeToggle');
                if (themeBtn) {
                    function isDark() {
                        var a = doc.documentElement.getAttribute('data-theme');
                        if (a === 'dark') { return true; }
                        if (a === 'light') { return false; }
                        return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
                    }
                    function refreshThemeUI() {
                        var dark = isDark();
                        themeBtn.setAttribute('aria-pressed', dark ? 'true' : 'false');
                        themeBtn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
                        var sun = doc.getElementById('iconSun');
                        var moon = doc.getElementById('iconMoon');
                        if (sun) { sun.hidden = dark; }
                        if (moon) { moon.hidden = !dark; }
                    }
                    themeBtn.addEventListener('click', function () {
                        var next = isDark() ? 'light' : 'dark';
                        doc.documentElement.setAttribute('data-theme', next);
                        try { localStorage.setItem('theme', next); } catch (e) {}
                        refreshThemeUI();
                    });
                    refreshThemeUI();
                }

                var searchInput = doc.getElementById('fileSearch');
                var clearBtn = doc.getElementById('searchClear');
                var noResults = doc.getElementById('noResults');
                var countEl = doc.getElementById('file-count');
                var searchStatus = doc.getElementById('searchStatus');
                if (searchInput && fileList) {
                    var items = Array.prototype.slice.call(fileList.querySelectorAll('.file-item'));
                    var totalItems = items.length;
                    function applyFilter() {
                        var q = searchInput.value.trim().toLowerCase();
                        var shown = 0;
                        items.forEach(function (li) {
                            var nameEl = li.querySelector('.file-name');
                            if (!nameEl) { return; }
                            var match = !q || nameEl.textContent.toLowerCase().indexOf(q) !== -1;
                            li.hidden = !match;
                            if (match) { shown++; }
                        });
                        if (noResults) { noResults.hidden = shown !== 0; }
                        if (countEl) {
                            countEl.textContent = q ? shown + ' of ' + totalItems + ' file' + (shown === 1 ? '' : 's') + ' shown' : totalItems + ' file' + (totalItems === 1 ? '' : 's');
                        }
                        if (searchStatus) {
                            searchStatus.textContent = q ? shown + ' of ' + totalItems + ' files shown' : 'All ' + totalItems + ' files shown';
                        }
                        if (clearBtn) { clearBtn.hidden = !q; }
                    }
                    searchInput.addEventListener('input', applyFilter);
                    if (clearBtn) {
                        clearBtn.addEventListener('click', function () {
                            searchInput.value = '';
                            applyFilter();
                            searchInput.focus();
                        });
                    }
                }

                var uploadCard = doc.getElementById('uploadCard');
                var progress = doc.getElementById('uploadProgress');
                var uploadStatus = doc.getElementById('uploadStatus');
                if (uploadCard && progress && uploadStatus) {
                    ['dragenter', 'dragover'].forEach(function (evt) {
                        uploadCard.addEventListener(evt, function (e) {
                            e.preventDefault();
                            e.stopPropagation();
                            uploadCard.classList.add('drag-over');
                        });
                    });
                    ['dragleave', 'drop'].forEach(function (evt) {
                        uploadCard.addEventListener(evt, function (e) {
                            e.preventDefault();
                            e.stopPropagation();
                            uploadCard.classList.remove('drag-over');
                        });
                    });
                    doc.addEventListener('dragover', function (e) { e.preventDefault(); });
                    doc.addEventListener('drop', function (e) { e.preventDefault(); });
                    uploadCard.addEventListener('drop', function (e) {
                        var files = e.dataTransfer ? e.dataTransfer.files : null;
                        if (!files || !files.length) { return; }
                        uploadFiles(Array.prototype.slice.call(files));
                    });
                }

                function uploadFiles(files) {
                    var done = 0;
                    var failed = [];
                    var total = files.length;
                    progress.hidden = false;
                    progress.max = total;
                    progress.value = 0;
                    uploadStatus.hidden = false;
                    function finish() {
                        var msg = (total - failed.length) + ' file' + ((total - failed.length) === 1 ? '' : 's') + ' uploaded';
                        if (failed.length) {
                            msg += ', ' + failed.length + ' failed: ' + failed.join(', ');
                        }
                        uploadStatus.textContent = msg;
                        progress.hidden = true;
                        setTimeout(function () { location.reload(); }, 800);
                    }
                    function next() {
                        var index = done + failed.length;
                        if (index >= total) { finish(); return; }
                        var file = files[index];
                        uploadStatus.textContent = 'Uploading ' + (index + 1) + ' of ' + total + ': ' + file.name;
                        var fd = new FormData();
                        fd.append('filetoupload', file);
                        fetch('/', { method: 'POST', body: fd }).then(function (resp) {
                            progress.value = index + 1;
                            if (resp.ok) { done++; } else { failed.push(file.name); }
                            next();
                        }).catch(function () {
                            failed.push(file.name);
                            progress.value = index + 1;
                            next();
                        });
                    }
                    next();
                }

                var previewTypes = {
                    image: ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'avif'],
                    video: ['mp4', 'webm', 'ogv', 'mov'],
                    audio: ['mp3', 'wav', 'ogg', 'oga', 'm4a', 'aac', 'flac'],
                    pdf: ['pdf']
                };
                function extOf(name) {
                    var i = name.lastIndexOf('.');
                    return i === -1 ? '' : name.slice(i + 1).toLowerCase();
                }
                function previewKind(name) {
                    var e = extOf(name);
                    for (var kind in previewTypes) {
                        if (previewTypes[kind].indexOf(e) !== -1) { return kind; }
                    }
                    return null;
                }

                var modal = doc.getElementById('previewModal');
                var previewContent = doc.getElementById('previewContent');
                var previewTitle = doc.getElementById('previewTitle');
                var previewClose = doc.getElementById('previewClose');
                var previewDownload = doc.getElementById('previewDownload');
                var lastTrigger = null;

                function closePreview() {
                    if (!modal || modal.hidden) { return; }
                    modal.hidden = true;
                    doc.body.style.overflow = '';
                    previewContent.innerHTML = '';
                    if (lastTrigger) { lastTrigger.focus(); }
                }

                if (modal && previewContent && previewClose && fileList) {
                    fileList.addEventListener('click', function (e) {
                        var link = e.target.closest ? e.target.closest('.file-link') : null;
                        if (!link || !modal) { return; }
                        var nameEl = link.querySelector('.file-name');
                        if (!nameEl) { return; }
                        var kind = previewKind(nameEl.textContent);
                        if (!kind) { return; }
                        e.preventDefault();
                        lastTrigger = link;
                        previewTitle.textContent = nameEl.textContent;
                        previewContent.innerHTML = '';
                        var href = link.getAttribute('href');
                        var node = null;
                        if (kind === 'image') {
                            node = doc.createElement('img');
                            node.src = href;
                            node.alt = '';
                        } else if (kind === 'video') {
                            node = doc.createElement('video');
                            node.src = href;
                            node.controls = true;
                        } else if (kind === 'audio') {
                            node = doc.createElement('audio');
                            node.src = href;
                            node.controls = true;
                        } else if (kind === 'pdf') {
                            node = doc.createElement('iframe');
                            node.src = href;
                            node.title = nameEl.textContent;
                        }
                        if (node) { previewContent.appendChild(node); }
                        previewDownload.setAttribute('href', href);
                        modal.hidden = false;
                        doc.body.style.overflow = 'hidden';
                        previewClose.focus();
                    });

                    modal.addEventListener('keydown', function (e) {
                        if (e.key === 'Escape') {
                            e.preventDefault();
                            closePreview();
                            return;
                        }
                        if (e.key !== 'Tab') { return; }
                        var focusables = modal.querySelectorAll('a[href], button, video, audio, iframe, [tabindex]:not([tabindex="-1"])');
                        if (!focusables.length) { return; }
                        var first = focusables[0];
                        var last = focusables[focusables.length - 1];
                        if (e.shiftKey && doc.activeElement === first) {
                            e.preventDefault();
                            last.focus();
                        } else if (!e.shiftKey && doc.activeElement === last) {
                            e.preventDefault();
                            first.focus();
                        }
                    });

                    previewClose.addEventListener('click', closePreview);
                    modal.querySelector('.modal-backdrop').addEventListener('click', closePreview);
                }
            });
        })();
    {% endraw %}</script>
</body>
</html>
"""
