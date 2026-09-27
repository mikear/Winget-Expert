# AGENTS.md — WinGet Expert

Desktop app (PySide6) that wraps Windows `winget` CLI. Windows-only.
Entry: `main.py` → `MainWindow` (`src/ui/main_window.py`).

## Layout

- `src/core/winget_client.py` — all winget interaction (subprocess, table parser, actions)
- `src/core/models.py` — `Package` dataclass (`has_update`, `status`)
- `src/core/install_dates.py` — read-only install dates (registry + Appx,
  cached; refresh inside a worker, never on UI thread — Appx shells to PowerShell)
- `src/core/settings.py` — JSON in `%APPDATA%\WinGet GUI Manager\settings.json`
  (folder name kept for backwards compatibility even though the app is
  branded "WinGet Expert")
- `src/ui/` — `main_window.py`, `dialogs.py` (incl. `StreamWorker`,
  `OperationDialog`, `WinGetMissingDialog`), `additional_dialogs.py`,
  `mensajes.py`, `splash.py`, `app_icon.py`, `theme.py`
- `OperationDialog` — winget redraws progress with `\r`; `run_streaming`
  splits it and strips ANSI per line before `on_line`. The dialog parses
  percent/phase from those frames into a determinate progress bar + status
  label ("Descargando... 47%"); the LOG only gets meaningful lines plus
  progress milestones (every 25% or phase change), never raw progress spam.
- `src/ui/mensajes.py` — ALL user-facing QMessageBox/QDialogButtonBox go
  through this module: Qt standard buttons render in English otherwise
  (Yes/No/OK/Cancel/Close). Never call `QMessageBox.question(...)` static
  methods with StandardButton args; use `mensajes.pregunta/informar/
  advertir/error/acerca_de` and `mensajes.botonera_*` instead.
- `src/ui/app_icon.py` — single source of the app-icon design (rounded blue
  square, white box, green download badge, same as the splash). The splash
  paints it via `pintar_icono_app()`; `create_icon.py` renders
  `assets/icon.ico|png` from it. Window/taskbar icon: `icono_aplicacion()`.
- `tools/actualizar_imagenes_readme.py` — regenerates `docs/banner.png`
  (exact splash render) + the 4 README screenshots with real data; MUST run
  with the native Windows platform (offscreen breaks font rendering).
- `debug_winget.py` — capture real winget output for parser work
- `winget_gui.spec` — PyInstaller one-file build; `assets/` (icon, FA font) bundled via `datas`
- `instalador.iss` — Inno Setup 6 script (Spanish); builds
  `dist/WinGet_Expert_Instalador_v<ver>.exe` from the portable exe:
  `& "$env:LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" instalador.iss`
  (ISCC lives in %LOCALAPPDATA%\Programs\Inno Setup 6 on this machine).
  Detects a previous install (uninstall registry key, HKLM64/32 + HKCU32/64)
  and shows a custom wizard page: update in place / uninstall first / exit,
  with special cases for same version (reinstall) and newer installed
   (downgrade warning); refuses to continue while the app window is open.
- Inno `[Code]` gotcha: `ComparePackedVersion` takes **Int64**, not String —
  passing a version text compiles fine but dies at runtime with
  `Runtime error (at X:Y): Type Mismatch` the moment Setup opens. Convert
  first with `StrToVersion(text, v)`. Diagnose runtime script errors with
  `setup.exe /LOG=...` (the log pinpoints the failing event function).
  Also: `and`/`or` DO short-circuit in this Pascal Script, so
  `(Page <> nil) and (Page.ID = ...)` guards are safe.

## WinGet parser (most bug-prone area)

WinGet has no JSON output; `_table_rows()` parses text tables. Real quirks seen
against winget 1.29 (Spanish locale):

- Column widths shrink to content, so adjacent headers can end up **one space
  apart** (real case: `Disponible Origen` merged into one token). Handled by
  `_split_merged_headers()` — keep it when touching the parser.
- Separator line may contain spaces; detection tolerates that.
- `winget upgrade --include-pinned` may emit **several tables** separated by
  prose, and summaries can START AT COLUMN 0 (real case: `1 paquetes tienen
  un pin que debe quitarse antes de la actualización`). `_table_rows`
  re-syncs the header at every separator line and drops prose lines (they
  cut words mid-way at column boundaries, or are single-cell rows).
- Package IDs never contain whitespace: `_rows_to_packages` /
  `search_packages` / `list_pinned_ids` drop rows whose ID cell has spaces
  (belt and braces against mis-sliced summary text).
- Trailing summary lines (e.g. `7 actualizaciones disponibles.`) must be skipped
  (rows not starting at col 0, or empty ID).
- `get_upgrades()` must drop rows with empty/`Unknown` available version.
- `winget list` "Disponible" is empty for most rows — never treat source text as
  a version (regression test: `available_version not in ('winget','msstore')`).

## WinGet CLI flags

- `uninstall` rejects `--accept-package-agreements` (dumps full help text);
  only install/upgrade take it — see `_action_args()`.
- `_humanize_error()` must skip keyword heuristics when the output looks like
  help/usage (help text mentions "administrador" → false permission errors).

## Threading contract

- Long ops run in `WorkerThread`/`StreamWorker` (QThread); never touch widgets
  from workers — use signals.
- Functions used with `StreamWorker` **must** accept `on_line` + `cancel_event`
  kwargs (`install/upgrade/upgrade_all/uninstall_package` do).
- `QTableWidget` has sorting enabled: disable it while populating, and identify
  rows by `UserRole` package ID (survives column sorting). Same for
  `RestoreDialog` list items (store the full dict, filter entries without `id`).
- Table/tree view is tracked by explicit `self._tree_mode`, not widget
  visibility (unreliable offscreen); selection helpers must branch on it.

## Settings gotchas

- `window_geometry` is stored as hex string, restored as `QByteArray`
  (`QByteArray.fromHex` silently ignores garbage — validate with
  `bytes.fromhex` first).
- `silent_mode` (default True) threads through install/upgrade/uninstall/restore.
- `uninstall_package(..., silent=True)` — `winget uninstall` supports `--silent`.
- IDs starting `MSIX\` / `ARP\` are local entries, not catalog packages:
  `show` degrades to local data, pin is refused with a message, and they never
  appear as upgradable.
- `search_packages()` with no matches returns `([], None)`, not an error
  (winget exits non-zero; the UI shows "0 resultados").

## Startup gate

- `MainWindow.__init__` calls `_ensure_winget()` before loading anything:
  `WinGetClient.is_available()` (`shutil.which` + `winget --version`).
- If missing, `WinGetMissingDialog` offers Retry / Microsoft Store
  (`ms-windows-store://pdp/?ProductId=9NBLGGH4NNS1`, then re-check) / Exit.
  Exit path is `QTimer.singleShot(0, self.close)` — never `sys.exit()` from UI code.
- Destroy the dialog (`deleteLater()`) after `exec()`; hidden children linger
  and `findChildren(QDialog)` will return stale ones.

## Verify (no test suite in repo)

```powershell
python -m py_compile main.py src/core/models.py src/core/settings.py src/core/winget_client.py src/core/install_dates.py src/ui/main_window.py src/ui/dialogs.py src/ui/additional_dialogs.py src/ui/theme.py
$env:QT_QPA_PLATFORM='offscreen'; python -c "..."   # smoke: build MainWindow/dialogs
```

- There is no pytest/unittest setup; ad-hoc scripts in `%TEMP%\opencode` were used.
- Safe live checks: `list_packages`, `get_upgrades`, `search_packages`,
  `show_package_info`, `list_sources`, `list_pinned_ids`.
- **Do not** run `install/upgrade/uninstall/pin add/remove`, `source add/remove`,
  or `upgrade --all` without explicit user approval.
- Offscreen GUI tests: patch `QMessageBox.*` first — a modal popup blocks
  forever with no display. Note the app under test may also have a live
  instance running; concurrent winget calls can transiently fail.
- `findChildren()` returns hidden widgets too — filter `isVisible()` when
  driving dialogs from tests (a closed dialog stays parented until deleted).
- Offscreen font rendering is broken (glyph boxes); take README screenshots
  with a native-platform process instead (`tools/actualizar_imagenes_readme.py`,
  real data, regenerates banner + `docs/screenshots/`).

## Shell notes (PowerShell 5.1)

- No `head`, no `&&` (use `;`), `#` starts a comment (breaks `python -c` with `#`).
- Console is cp850/cp1252: `sys.stdout.reconfigure(encoding='utf-8')` in test
  scripts; never `print` emoji (use `[!]`/`[X]` style).
- `python file.py | Select-Object -First N` instead of pipes to Unix tools.
- `$variables` get mangled in inline `powershell -Command` strings — write a
  temporary `.ps1` file and run it with `-File` instead.

## Packaging

- `pyinstaller winget_gui.spec` (takes minutes). `upx=False` is intentional —
  UPX corrupts Qt DLLs. `icon='assets/icon.ico'`; regenerate via
  `python create_icon.py` (needs PySide6 + Pillow, dev-only, native platform).
- The version lives ONLY in `src/version.py` (`APP_VERSION`); the spec
  imports it to name the exe `dist/WinGet_Expert_v<ver>.exe`, and
  `splash.py`/`main_window.py` (About) read it too. When bumping, also
  update `#define VersionApp` in `instalador.iss` (Inno preprocessor can't
  read Python).
- The installer embeds the versioned exe but installs it as
  `WinGet_Expert.exe` (`DestName`) so shortcuts survive upgrades.
- Font Awesome (`assets/fonts/fa-solid-900.ttf`, CC BY 4.0 — keep the About
  attribution) loads at startup in `main.py`; works frozen via `sys._MEIPASS`.
- Don't commit `build/`, `dist/`, `__pycache__/`, `*.exe` or `*.log`
  (see `.gitignore`).
- The release binaries are NOT in git: they are assets of the GitHub
  Release (`…/releases/tag/v<ver>`) and the README download links point to
  `…/releases/download/v<ver>/<file>`. To publish a version: build both
  exes, create the tag + release and upload the two files (`gh` needs
  `gh auth login` first; a `repo`-scoped token also works), then update
  the README links. `dist/` stays local-only output.
  Kill running exe instances first — Windows locks the file and the build
  fails with `PermissionError`.
- Frozen-exe crash with no output: check Event Viewer → Application, Error 1000
  (`Qt6Core.dll`); then build a `--console --name WinGet_Debug` variant to see
  the traceback (delete its `.spec`/exe/`build/` afterwards).
