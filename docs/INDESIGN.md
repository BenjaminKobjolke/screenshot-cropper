# InDesign Support

This tool supports Adobe InDesign (.indd) files in addition to Photoshop (.psd) files.

## Prerequisites

1. **Adobe InDesign** must be installed on your system
2. **pypiwin32** package for COM automation:
   ```bash
   pip install pypiwin32
   ```

## Finding Your InDesign Version

Use the `--list-indesign-versions` command to detect available InDesign installations:

```bash
python main.py --list-indesign-versions
```

Example output:
```
Checking available InDesign versions...
--------------------------------------------------
Not found: InDesign.Application.2024
SUCCESS: InDesign.Application.2023 (Version: 18.5.4.138)
Not found: InDesign.Application.CC.2022
...
--------------------------------------------------
Recommended version string: InDesign.Application.2023
```

The tool automatically detects and uses the first available InDesign version.

## Usage with --prepare-and-export

### Direct Path Mode

Specify the InDesign file and output JSON path directly:

```bash
python main.py --file="path/to/poster.indd" --output="path/to/template.json" --prepare-and-export
```

### What This Mode Does

1. Opens the InDesign file
2. Iterates all TextFrames in the document
3. Sets each TextFrame's `Label` property to `lang_[sanitized_text]` format:
   - Text is converted to lowercase
   - Spaces are replaced with underscores
   - Allowed characters: a-z, 0-9, underscore, dot, and hyphen
   - Name is limited to 30 characters
4. Handles duplicate keys intelligently:
   - TextFrames with identical text share the same key
   - TextFrames with different text get numeric suffixes (`_2`, `_3`, etc.)
5. Exports/updates the template JSON with the sanitized names as keys and current text content as values
6. Saves the modified InDesign file

## TextFrame Labels

InDesign uses the `Label` property on TextFrames (not layer names like Photoshop). After running `--prepare-and-export`:

| Original Text | TextFrame Label | JSON Key |
|--------------|-----------------|----------|
| "Share Video Link!" | `lang_share_video_link` | `share_video_link` |
| "Vacation" | `lang_vacation` | `vacation` |

### Verifying Labels in InDesign

To confirm that labels were set correctly:

1. Open the modified `.indd` file in InDesign
2. Go to **Window > Utilities > Script Label**
3. Select any text frame in your document
4. The Script Label panel will show the assigned label (e.g., `lang_wirkstoffe_sekundre_4`)

If the labels are empty, the document may not have been saved properly. Re-run the `--prepare-and-export` command.

## Output JSON Format

The JSON output includes metadata, plain text, and detailed formatting information:

```json
{
    "_meta": {
        "application": "Adobe InDesign",
        "version": "21.1.0.56",
        "sourceFile": "poster.indd"
    },
    "headline": {
        "plainText": "Bold Title Here",
        "ranges": [
            {
                "text": "Bold ",
                "fontStyle": "Bold",
                "pointSize": 24.0,
                "appliedFont": "Arial",
                "underline": false,
                "strikeThru": false,
                "fillColor": "#000000",
                "baselineShift": 0.0
            },
            {
                "text": "Title Here",
                "fontStyle": "Regular",
                "pointSize": 24.0,
                "appliedFont": "Arial",
                "underline": false,
                "strikeThru": false,
                "fillColor": "#000000",
                "baselineShift": 0.0
            }
        ]
    }
}
```

### Metadata (`_meta`)

The `_meta` object contains:

| Property | Description |
|----------|-------------|
| `application` | "Adobe InDesign" or "Adobe Photoshop" |
| `version` | Application version (e.g., "21.1.0.56") |
| `sourceFile` | Original filename |

### Formatting Properties

Each text range includes:

| Property | Description |
|----------|-------------|
| `text` | The text content of this range |
| `fontStyle` | Font style: Regular, Bold, Italic, Bold Italic |
| `pointSize` | Font size in points |
| `appliedFont` | Font family name |
| `underline` | Whether text is underlined |
| `strikeThru` | Whether text has strikethrough |
| `fillColor` | Text color as hex (#000000) or color name |
| `baselineShift` | Vertical shift (positive = superscript, negative = subscript) |

## Troubleshooting

### "win32com not available" Error

Install the pypiwin32 package:
```bash
pip install pypiwin32
```

### "Could not connect to InDesign" Error

1. Ensure InDesign is installed
2. Run `--list-indesign-versions` to check available versions
3. Make sure InDesign is not blocked by antivirus/firewall

### No InDesign Versions Found

The tool tries these COM version strings in order:
- `InDesign.Application` (generic - uses system default, usually newest)
- `InDesign.Application.2026` (version 21.x)
- `InDesign.Application.2025` (version 20.x)
- `InDesign.Application.2024` (version 19.x)
- `InDesign.Application.2023` (version 18.x)
- `InDesign.Application.CC.2022`
- `InDesign.Application.CC.2021`
- `InDesign.Application.CC.2020`
- `InDesign.Application.CC.2019`

If none work, your InDesign version may use a different COM identifier.

## Differences from Photoshop

| Feature | Photoshop (.psd) | InDesign (.indd) |
|---------|------------------|------------------|
| Text container | Text Layers | TextFrames |
| Naming property | Layer name | TextFrame Label |
| API | photoshop-python-api | win32com (COM) |
