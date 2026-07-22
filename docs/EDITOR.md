# Visual Editor

A PySide6 desktop editor for `screenshot-cropper.json` with a live preview. The preview is rendered by the same compositing pipeline (`ImageCompositor.compose`) that produces the real output, so what you see — including text overlays — is what the batch run produces.

## Usage

```bash
uv run python main.py --directory path/to/your/directory --editor
```

Or use the shortcut batch file from the repo root:

```bash
editor.bat "path\to\your\directory"
```

With no argument, `editor.bat` uses the current directory. If the directory contains no `screenshot-cropper.json`, the editor shows a **start page** with the last 10 opened projects as large buttons — click one to open it, or use **File > Open Directory...**. Recent projects are stored in `~/.screenshot-cropper/recent_projects.json`; entries whose config file no longer exists are hidden.

## Window Layout

- **Left**: settings panels (scrollable)
- **Right**: live preview, scaled to fit
- **Toolbar**: screenshot and locale selectors — pick which screenshot is previewed and which locale's text is rendered
- **Status bar**: load/save feedback

The preview re-renders automatically ~300ms after the last change (debounced).

## Editable Settings

| Panel | Values |
|---|---|
| Screenshot Crop | `crop.top/left/right/bottom` — pixel insets cropped from the **screenshot** before it is placed on the background |
| Final Image Crop | `final_crop.top/left/right/bottom` — pixel insets cropped from the **finished composite** as the last step (after overlay). Always shown; the section is only written to the JSON once a value is non-zero |
| Background / Screenshot placement | background `file` (picked from `input/`), `position.x/y` (where the cropped screenshot is pasted on the background), `size.width` (screenshot is resized to this width; height follows the aspect ratio), `size.height` (informational — the pipeline ignores it) |
| Screenshot Mask | `screenshot_mask.file` — image whose opaque pixels are subtracted from the screenshot, aligned to the output canvas (author at background size; scaled to fit if dimensions differ). Background/text/overlay stay unmasked |
| Overlay | overlay `file`, `position.x/y` (pasted on top at native size) |
| Text | "Render text" checkbox (`text.enabled` — unchecked disables text rendering entirely), font `size`, `line-height` (multiplier of font size, "auto" = font metrics + 20% spacing), box `x/y/width/height`, `align`, `vertical-align`, `color` (color picker), default font file |
| Export | `format` (png/webp), `quality`, `lossless`, `keep_cropped` |

Optional sections (Background, Overlay, Screenshot Mask, Text) have a **checkbox in the panel title**: checked = section exists in the JSON. Checking an unconfigured panel adds the section with the shown default values on save; unchecking removes the section from the JSON on save.

Per-locale font files (`text.font.files.<locale>`) and PostScript font names (`text.font.names`) are not editable in the UI; they are preserved untouched on save. Edit those directly in the JSON.

## Saving

**Ctrl+S** or **File > Save** writes back to `screenshot-cropper.json`:

- Only editor-managed keys are updated
- Everything else (`directories`, per-locale font files, font names, unknown keys) is preserved verbatim
- Format: JSON, 2-space indent, UTF-8

## Notes

- **PSD screenshots** are previewed via Pillow's flattened composite. Photoshop is never launched by the editor — the preview may differ from the Photoshop pipeline for PSDs whose text layers are replaced per locale (the flattened composite shows the saved layer state).
- **Fonts** for the text preview load from the repo's `fonts/` directory relative to the working directory. `editor.bat` handles this by switching to the repo root before launching.
- **Locale text** mapping matches the pipeline exactly: numbered screenshots (`07.psd`) use their number as text index; unnumbered files use their position (see `resolve_text_index` in `src/filename_utils.py`).

## Architecture

```
src/editor/
├── app.py            entry point (QApplication), imported lazily by --editor
├── main_window.py    window, menu, toolbar, panel wiring, start page
├── state.py          EditorState — settings + save, Qt-free (unit-testable)
├── sources.py        screenshot discovery + locale loading
├── recents.py        recent-projects store (JSON in ~/.screenshot-cropper), Qt-free
├── renderer.py       debounced preview rendering via ImageCompositor.compose
├── preview.py        PIL → QPixmap widget, zoom-to-fit
├── panels_layout.py  panel base + crop/background/mask/overlay panels
└── panels_style.py   text + export panels
```

Config round-trip lives in `src/config_writer.py` (`merge_settings_into_config` + `ConfigWriter`).

Tests: `tests/unit/test_editor_*.py`, `tests/unit/test_compose.py`, `tests/unit/test_config_writer.py`, `tests/integration/test_editor_smoke.py` (offscreen Qt).
