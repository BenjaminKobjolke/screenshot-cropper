# Screenshot Cropper

A Python application to crop screenshots based on JSON configuration.

## Features

-   Crop multiple PNG, JPG, and PSD images at once
-   Place cropped images on a background image, with optional overlay frame on top
-   **Screenshot mask**: punch out screenshot pixels via a canvas-aligned mask image (e.g. phone-shaped window)
-   **Final crop**: trim the finished composite as a last step
-   Add localized text overlays (per-locale fonts, alignment, configurable line height, can be disabled via `text.enabled`)
-   Process PSD files with text layer translation
-   Generate multiple language versions of each image
-   Configure everything via `screenshot-cropper.json`
-   **Export to PNG or WebP** with configurable quality settings
-   **Visual Editor** ([docs/EDITOR.md](docs/EDITOR.md)): PySide6 GUI with live preview, edits every config value, adds/removes optional sections, start page with recent projects (`editor.bat`)
-   Automatically create output directory
-   Detailed logging

## Requirements

-   Python 3.11 or higher
-   [uv](https://docs.astral.sh/uv/getting-started/installation/)
-   Pillow library
-   [adobe-document-handler](https://github.com/BenjaminKobjolke/adobe-document-handler) - Handles PSD and InDesign text layer processing, localization, and font management

## Installation

### For Users

1. Clone this repository:

    ```
    git clone https://github.com/BenjaminKobjolke/screenshot-cropper.git
    cd screenshot-cropper
    ```

2. Run the installation script:

    ```
    install.bat
    ```

    This creates the virtual environment via `uv sync` and installs all dependencies including `adobe-document-handler` from GitHub.

### For Developers

If you're developing locally and have `adobe-document-handler` cloned as a sibling directory:

```
install_local.bat
```

This installs `adobe-document-handler` in editable mode from `../adobe-document-handler`, allowing you to modify both projects simultaneously. Note: a later `uv sync` reverts it to the git version — re-run `install_local.bat` afterwards.

### Manual Installation

```
uv sync --all-extras
```

### Updating Dependencies

```
update.bat
```

### Running Tests

```
tools\run_tests.bat
tools\run_integration_tests.bat
```

## Usage

1. Create a directory structure. Key subdirectories include:

    - `input/screenshots/`: Contains images (PNG, JPG) for cropping and text overlay. PSD files for text layer translation and PNG export should also be placed here.
    - `input/locales/`: (Optional) Contains JSON locale files (e.g., `en.json`, `de.json`) for text localization in both screenshots and PSDs.
    - A `screenshot-cropper.json` configuration file in the main directory. This file is **required** for image cropping, background placement, and text overlay on screenshots. If this file is missing or does not contain valid `crop` settings, these operations will be skipped. PSD processing will still be attempted if relevant files are present.

2. Run the application:

    ```
    uv run python main.py --directory path/to/your/directory
    ```

    **Optional: Process a specific screenshot only**

    To process only a single screenshot by its number, use the `--screenshot` argument:

    ```
    uv run python main.py --directory path/to/your/directory --screenshot 7
    ```

    This will only process files with the number 7 in their filename, such as:
    - `7.png`
    - `screenshot_07.psd`
    - `screenshot_7.jpg`

    This is useful when you need to quickly update a single screenshot without reprocessing all files.

    **Optional: Process a specific language only**

    To process only a single language, use the `--language` argument:

    ```
    uv run python main.py --directory path/to/your/directory --language ar
    ```

    This will only process the Arabic (ar) locale, skipping all other languages.

    **Optional: Skip existing output files**

    To skip processing for languages where output files already exist, use the `--skip-existing` flag:

    ```
    uv run python main.py --directory path/to/your/directory --skip-existing
    ```

    This is useful for incremental processing:
    - Only processes screenshots for languages where output files don't exist yet
    - Significantly speeds up iteration when only some languages have changed
    - For PSD files, if all languages are skipped, Photoshop won't be opened at all
    - Can be combined with other flags:
      ```
      uv run python main.py --directory path/to/your/directory --screenshot 5 --skip-existing
      ```

    **Optional: Prepare PSD and export template**

    To prepare a PSD file for localization by renaming text layers and exporting a template JSON file, use `--prepare-and-export`. See [docs/PREPARE_AND_EXPORT.md](docs/PREPARE_AND_EXPORT.md) for detailed documentation.

    **Visual Editor Mode**

    To visually configure crop settings, screenshot position, and size without manually editing the JSON, use the `--editor` flag:

    ```
    uv run python main.py --directory path/to/your/directory --editor
    ```

    Or use the shortcut batch file (defaults to the current directory when no argument is given):

    ```
    editor.bat "path\to\your\directory"
    ```

    This launches a PySide6 GUI with a live preview (debounced ~300ms) that is rendered by the same compositing pipeline as the real output — including text overlays. You can edit every config value:

    -   **Crop**: top, left, right, bottom insets
    -   **Background / screenshot placement**: background file, position X/Y, screenshot width (height follows aspect ratio)
    -   **Overlay**: file and position
    -   **Text**: font size, box X/Y/width/height, align, vertical align, color, default font file
    -   **Export**: format (png/webp), quality, lossless, keep cropped copies

    A toolbar selects which screenshot and locale to preview (PSD screenshots are previewed via their flattened composite — Photoshop is not launched). `File > Open Directory...` switches projects; **Ctrl+S** saves back to `screenshot-cropper.json`, preserving all keys the editor does not manage (e.g. `directories`, per-locale font files).

    See [docs/EDITOR.md](docs/EDITOR.md) for full documentation.

3. Cropped images will be saved in an `output` subdirectory.

## Configuration (`screenshot-cropper.json`)

Ready-to-copy example configs and locale files live in [examples/](examples/).

The `screenshot-cropper.json` file is used to configure cropping, background placement, and text overlays for images in the `input/screenshots/` directory. It also provides font settings that can be used by the PSD processor if text layers are being translated.

**If this file is not present, or if the `crop` settings are missing or invalid, the screenshot cropping, background addition, and text overlay features will be skipped.** PSD processing will still be attempted independently.

The file should have the following structure:

```json
{
    "crop": {
        "top": 280,
        "left": 0,
        "right": 0,
        "bottom": 150
    },
    "background": {
        "file": "bg.png",
        "position": {
            "x": 322,
            "y": 878
        },
        "size": {
            "width": 897,
            "height": 1685
        }
    },
    "text": {
        "font": {
            "files": {
                "default": "DroidSans-Bold.ttf",
                "ar": "DroidSans-Bold_ar.ttf"
            },
            "size": 164,
            "align": "center",
            "vertical-align": "middle",
            "x": 50,
            "y": 200,
            "width": 500,
            "height": 500,
            "color": {
                "r": 255,
                "g": 0,
                "b": 0
            }
        }
    }
}
```

### Crop Settings (`crop`)

Crops the **screenshot** before it is placed on the background:

-   `top`: Number of pixels to crop from the top
-   `left`: Number of pixels to crop from the left
-   `right`: Number of pixels to crop from the right
-   `bottom`: Number of pixels to crop from the bottom

### Screenshot Mask Settings (`screenshot_mask`, Optional)

An image whose **non-transparent pixels are subtracted from the screenshot** — where the mask is opaque, the screenshot becomes transparent (e.g. to cut rounded corners or a camera notch before the screenshot is placed in the frame):

```json
{
    "screenshot_mask": {
        "file": "mask.png"
    }
}
```

-   `file`: Mask image in the `input/` directory
-   The mask aligns with the **output canvas** (the background image; author it at background size, e.g. exported from the layout PSD). Without a background it aligns with the cropped screenshot. If dimensions differ it is scaled to fit
-   Only the screenshot is masked — background, text, and overlay are unaffected
-   Partial transparency subtracts proportionally (anti-aliased mask edges stay smooth)

### Final Crop Settings (`final_crop`, Optional)

Crops the **finished composite image** as the very last step (after background, text, and overlay). Same keys as `crop`:

```json
{
    "final_crop": {
        "top": 0,
        "left": 0,
        "right": 0,
        "bottom": 120
    }
}
```

If omitted (or all values are 0), the final image is not cropped.

### Background Settings (Optional)

-   `file`: Filename of the background image (located in the input directory)
-   `position`: Position to place the cropped image on the background
    -   `x`: X-coordinate (horizontal position)
    -   `y`: Y-coordinate (vertical position)
-   `size`: Size to resize the cropped image before placing on background
    -   `width`: Width in pixels
    -   `height`: Height in pixels

If background settings are not provided, images will only be cropped (assuming `crop` settings are valid).

### Overlay Settings (Optional)

An overlay image can be placed on top of the final composite image:

```json
{
    "overlay": {
        "file": "overlay.png",
        "position": {
            "x": 0,
            "y": 0
        }
    }
}
```

-   `file`: Filename of the overlay image (located in the input directory). Should be a PNG with transparency.
-   `position`: Position to place the overlay on the final image
    -   `x`: X-coordinate (horizontal position)
    -   `y`: Y-coordinate (vertical position)

The overlay is applied after the screenshot is placed on the background, making it useful for adding frames, watermarks, or other decorative elements.

### Export Settings (Optional)

Configure the output format, quality, and whether to keep intermediate cropped images:

```json
{
    "export": {
        "format": "webp",
        "quality": 90,
        "lossless": true,
        "keep_cropped": true
    }
}
```

-   `format`: Output format - `"png"` (default) or `"webp"`
-   `quality`: Quality setting for WebP compression (1-100). Higher values produce better quality but larger files. Default: 90. Ignored when `lossless` is `true`.
-   `lossless`: If `true`, uses lossless WebP compression which preserves transparency. Default: `false`. When enabled, `quality` is ignored.
-   `keep_cropped`: If `true`, saves the cropped images (before placing on background) to a separate `cropped/` subfolder. Default: `false`.

When `keep_cropped` is enabled, the output structure will include a `cropped` folder:

```
output/
├── en/
│   └── 1_en.webp           # Final composited image
├── cropped/
│   └── en/
│       └── 1_en.webp       # Cropped-only image
```

If the `export` section is not present, images will be saved as PNG (backwards compatible with existing configurations).

### Text Settings (Optional, within `screenshot-cropper.json`)

-   `enabled`: Optional, set to `false` to disable text rendering entirely (the `text` object is ignored when creating screenshots). Absent or `true` = text is rendered
-   `font`: Font settings for text overlay
    -   `files`: Dictionary of language-specific font files (located in the `fonts/` directory)
        -   `default`: Default font file to use when no language-specific font is available
        -   `[locale]`: Font file to use for specific locale (e.g., `ar` for Arabic, `ko` for Korean)
    -   `size`: Font size in pixels
    -   `line-height`: Optional line height as a multiplier of the font size (e.g. `1.2` = 120% of font size per line). Omit for automatic spacing (font metrics + 20% of font size)
    -   `align`: Horizontal text alignment ("left", "center", "right")
    -   `vertical-align`: Vertical text alignment ("top", "middle", "bottom")
    -   `x`: X-coordinate for text position
    -   `y`: Y-coordinate for text position
    -   `width`: Width of text area (used for alignment)
    -   `height`: Height of text area (used for vertical alignment)
    -   `color`: RGB color values for the text
        -   `r`: Red component (0-255)
        -   `g`: Green component (0-255)
        -   `b`: Blue component (0-255)

#### Automatic Font Detection for PSD Processing

When processing PSD files, the application automatically extracts the PostScript font name from TTF files using `fontTools`. This means you only need to configure `font.files` - the correct Photoshop font name is derived automatically.

For example, with this configuration:
```json
{
    "text": {
        "font": {
            "files": {
                "default": "NotoSans-Bold.ttf",
                "ko": "NotoSansKR-Bold.ttf",
                "ja": "NotoSansJP-Bold.ttf"
            }
        }
    }
}
```

When processing a PSD for Korean (`ko`), the application will:
1. Look up `NotoSansKR-Bold.ttf` from the `fonts/` directory
2. Extract the PostScript name (e.g., `NotoSansKR-Bold`) using fontTools
3. Apply that font to Photoshop text layers

This ensures proper rendering of non-Latin scripts (Korean, Japanese, Chinese, Arabic, etc.) without manual font name configuration.

If text settings are provided, the application will look for locale files in the `input/locales` directory. Each locale file should be a JSON file named with the locale code (e.g., `en.json`, `de.json`) and contain a dictionary of texts with keys in the format "Text_1", "Text_2", etc.

#### Text Formatting

The application supports the following text formatting features:

-   **Newline Characters**: You can use `\n` in your text strings to create line breaks. For example:

    ```json
    {
        "Text_1": "Share video link\nand ask questions"
    }
    ```

    This will display "Share video link" and "and ask questions" on separate lines.

-   **Automatic Text Wrapping**: Text that exceeds the specified width will be automatically wrapped to fit within the text area.

### Filename-based Text Indexing

The application supports using filenames as indices for text retrieval. If your image filenames are numeric (e.g., "01.png", "02.png", "1.psd", "2.psd"), the application will use these numbers as indices to retrieve the corresponding text from the locale files.

For example:

-   An image named "01.png" will use the text with key "Text_1" or "1" from the locale file
-   An image named "02.png" will use the text with key "Text_2" or "2" from the locale file

This feature allows you to explicitly control which text is applied to which image, regardless of the order in which the images are processed. If a filename is not numeric, the application will fall back to using the iteration index.

## PSD Processing

The application processes PSD files found in the `input/screenshots/` directory (alongside other image files). This processing occurs independently of the main screenshot cropping operations and does not strictly require `screenshot-cropper.json` to run, though font settings from it can be utilized if present.

PSD files are processed in the following manner:

1. **Export to PNG**: PSD files are exported as PNGs.
2. **Text Layer Translation (with Photoshop)**: If Photoshop is installed, the `photoshop-python-api` package is available, and locale files exist in `input/locales/`, the application will attempt to translate text layers within the PSDs.
    - Text layers named with the prefix `lang_` (e.g., `lang_title`) will have their content replaced with translations from the locale files.
    - Font configurations for specific locales, if defined in `screenshot-cropper.json` under `text.font.files`, will be applied during this translation. If `screenshot-cropper.json` or these specific font settings are absent, Photoshop's default/current font for the layer will be used.

If Photoshop or the `photoshop-python-api` is not available, text layers will not be translated, but the application might still attempt a basic export if other tools were integrated for it (currently, it relies on Photoshop for PSD export).

### Text Layer Translation in PSD Files

To enable text layer translation in PSD files:

1. Name your text layers with the prefix `lang_` followed by the translation key. For example, a text layer named `lang_email` will be translated using the key "email" from the locale files.

2. Ensure your locale files contain the corresponding translation keys. For example, if you have a text layer named `lang_email`, your locale files should contain an entry for "email" or "Text_email".

Example of text layer translation:

-   A PSD file in `input/screenshots/` has a text layer named `lang_email`.
-   `input/locales/en.json` contains: `{ "email": "Email Address" }`
-   `input/locales/de.json` contains: `{ "email": "E-Mail-Adresse" }`

The application will generate `output/en/your_psd_name.png` and `output/de/your_psd_name.png` (or `output/default/your_psd_name.png` if no locales are active) with the email text translated.

Example locale file (`en.json`) for general text keys:

```json
{
    "Text_1": "Amazing App!",
    "Text_2": "Great App!",
    "Text_3": "Super App!",
    "Text_4": "Wow App!"
}
```

The application will generate a separate output image for each locale, with the locale code appended to the filename (e.g., `screenshot1_en.png`).

## Example

For a directory structure:

```
my-screenshots/
├── input/
│   ├── bg.png                     # Optional: Background for screenshots
│   ├── overlay.png                # Optional: Overlay pasted on top (e.g. phone frame)
│   ├── mask.png                   # Optional: Screenshot mask (canvas-aligned punch-out)
│   ├── locales/                   # Optional: Locale files for text
│   │   ├── en.json
│   │   └── de.json
│   └── screenshots/               # Screenshots (PNG, JPG) and PSDs
│       ├── screenshot1.png
│       ├── screenshot2.jpg
│       └── design_template.psd    # PSD file for processing
└── screenshot-cropper.json        # Optional for screenshot cropping/overlay
```

Run:

```
uv run python main.py --directory my-screenshots
```

The processed images will be saved in:

```
my-screenshots/
├── input/
│   ├── bg.png
│   ├── locales/
│   │   ├── en.json
│   │   └── de.json
│   └── screenshots/
│       ├── screenshot1.png
│       ├── screenshot2.jpg
│       └── design_template.psd
├── output/
│   ├── en/                              # Output for 'en' locale PSDs
│   │   └── design_template.png          # English version of PSD
│   ├── de/                              # Output for 'de' locale PSDs
│   │   └── design_template.png          # German version of PSD
│   ├── default/                         # Output for PSDs if no locales active
│   │   └── another_design.png
│   ├── screenshot1_en.png               # Cropped/overlaid screenshots
│   ├── screenshot1_de.png
│   ├── screenshot2_en.jpg
│   └── screenshot2_de.jpg
└── screenshot-cropper.json
```

## License

MIT
