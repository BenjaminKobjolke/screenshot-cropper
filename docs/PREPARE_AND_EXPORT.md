# Prepare and Export Mode

This mode prepares a PSD file for localization by renaming text layers and exporting a template JSON file.

## Usage

There are two ways to use this mode:

### Direct Path Mode

Specify the PSD file and output JSON path directly:

```bash
python main.py --file="path/to/screenshot.psd" --output="path/to/template.json" --prepare-and-export
```

### Directory Mode

Use a directory structure with screenshot number:

```bash
python main.py --directory path/to/your/directory --screenshot 5 --prepare-and-export
```

This will:
- Find the PSD file matching screenshot number 5 (e.g., `screenshot_05.psd`) in `input/screenshots/`
- Output to `output/template.json`

## What This Mode Does

1. Opens the PSD file matching the screenshot number (e.g., `screenshot_05.psd`)
2. Traverses all text layers in the document (including nested groups)
3. Renames each text layer to `lang_[sanitized_text]` format based on the **text content** of the layer:
   - Text is converted to lowercase
   - Spaces are replaced with underscores
   - Allowed characters: a-z, 0-9, underscore, dot, and hyphen
   - Existing `lang_` prefixes are stripped (fixes already processed layers)
   - Photoshop's ` copy` suffixes are stripped (e.g., "Button copy 2" -> "button")
   - Name is limited to 30 characters
4. Handles duplicate keys intelligently:
   - Layers with identical text share the same key
   - Layers with different text get numeric suffixes (`_2`, `_3`, etc.)
5. Exports/updates the template JSON with the sanitized names as keys and current text content as values
6. Saves the modified PSD file

If `template.json` already exists, it will be updated with the new keys (existing keys are preserved or updated if they match).

## Examples

### Layer Renaming

| Original Text | Layer Name in PSD | JSON Key |
|--------------|-------------------|----------|
| "Share Video Link!" | `lang_share_video_link` | `share_video_link` |
| "Vacation" | `lang_vacation` | `vacation` |
| "Button copy 2" | `lang_button` | `button` |

### Duplicate Handling

- Two layers with text "Vacation" share the same key: `"vacation": "Vacation"`
- Layers with "vacation" and "Vacation" get separate keys: `"vacation"` and `"vacation_2"`

### Output JSON Format

```json
{
    "share_video_link": "Share Video Link!",
    "vacation": "Vacation",
    "button": "Click Me"
}
```

## Requirements

- Adobe Photoshop must be installed
- `photoshop-python-api` package must be available
