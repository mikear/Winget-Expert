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
  `dist/WinGet_Expert_Instalador.exe` from the portable exe:
  `& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" instalador.iss`
  (ISCC lives in %LOCALAPPDATA%\Programs\Inno Setup 6 on this machine)

## WinGet parser (most bug-prone area)

WinGet has no JSON output; `_table_rows()` parses text tables. Real quirks seen
against winget 1.29 (Spanish locale):

- Column widths shrink to content, so adjacent headers can end up **one space
  apart** (real case: `Disponible Origen` merged into one token). Handled by
  `_split_merged_headers()` — keep it when touching the parser.
- Separator line may contain spaces; detection tolerates that.
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
- The exe is named `dist/WinGet_Expert.exe` (spec `name=`); renaming it
  means updating `instalador.iss`, README links and this file.
- Font Awesome (`assets/fonts/fa-solid-900.ttf`, CC BY 4.0 — keep the About
  attribution) loads at startup in `main.py`; works frozen via `sys._MEIPASS`.
- Don't commit `build/`, `dist/`, `__pycache__/` (see `.gitignore`).
- Exception: the release binaries `dist/WinGet_Expert.exe` and
  `dist/WinGet_Expert_Instalador.exe` are tracked via `git add -f` on
  purpose (README links them); rebuilds need the same flag. Kill running
  exe instances first — Windows locks the file and the build fails with
  `PermissionError`.
- Frozen-exe crash with no output: check Event Viewer → Application, Error 1000
  (`Qt6Core.dll`); then build a `--console --name WinGet_Debug` variant to see
  the traceback (delete its `.spec`/exe/`build/` afterwards).
