# Screenshot Cropper

A Python application to crop screenshots based on JSON configuration.

## Features

-   Crop multiple PNG, JPG, and PSD images at once
-   Place cropped images on a background image
-   Add localized text overlays to images
-   Process PSD files with text layer translation
-   Generate multiple language versions of each image
-   Configure crop, background, and text settings via JSON
-   Automatically create output directory
-   Detailed logging

## Requirements

-   Python 3.6 or higher
-   Pillow library
-   photoshop-python-api (optional, for advanced PSD processing)

## Installation

1. Clone this repository:

    ```
    git clone https://github.com/yourusername/screenshot-cropper.git
    cd screenshot-cropper
    ```

2. Create a virtual environment (optional but recommended):

    ```
    python -m venv venv
    venv\Scripts\activate
    ```

3. Install dependencies:
    ```
    pip install -r requirements.txt
    ```

## Usage

1. Create a directory structure. Key subdirectories include:

    - `input/screenshots/`: Contains images (PNG, JPG) for cropping and text overlay. PSD files for text layer translation and PNG export should also be placed here.
    - `input/locales/`: (Optional) Contains JSON locale files (e.g., `en.json`, `de.json`) for text localization in both screenshots and PSDs.
    - A `screenshot-cropper.json` configuration file in the main directory. This file is **required** for image cropping, background placement, and text overlay on screenshots. If this file is missing or does not contain valid `crop` settings, these operations will be skipped. PSD processing will still be attempted if relevant files are present.

2. Run the application:

    ```
    python main.py --directory path/to/your/directory
    ```

    **Optional: Process a specific screenshot only**

    To process only a single screenshot by its number, use the `--screenshot` argument:

    ```
    python main.py --directory path/to/your/directory --screenshot 7
    ```

    This will only process files with the number 7 in their filename, such as:
    - `7.png`
    - `screenshot_07.psd`
    - `screenshot_7.jpg`

    This is useful when you need to quickly update a single screenshot without reprocessing all files.

3. Cropped images will be saved in an `output` subdirectory.

## Configuration (`screenshot-cropper.json`)

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

### Crop Settings

-   `top`: Number of pixels to crop from the top
-   `left`: Number of pixels to crop from the left
-   `right`: Number of pixels to crop from the right
-   `bottom`: Number of pixels to crop from the bottom

### Background Settings (Optional)

-   `file`: Filename of the background image (located in the input directory)
-   `position`: Position to place the cropped image on the background
    -   `x`: X-coordinate (horizontal position)
    -   `y`: Y-coordinate (vertical position)
-   `size`: Size to resize the cropped image before placing on background
    -   `width`: Width in pixels
    -   `height`: Height in pixels

If background settings are not provided, images will only be cropped (assuming `crop` settings are valid).

### Text Settings (Optional, within `screenshot-cropper.json`)

-   `font`: Font settings for text overlay
    -   `files`: Dictionary of language-specific font files
        -   `default`: Default font file to use when no language-specific font is available
        -   `[locale]`: Font file to use for specific locale (e.g., `ar` for Arabic)
    -   `size`: Font size in pixels
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
python main.py --directory my-screenshots
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
