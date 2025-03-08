# Screenshot Cropper

A Python application to crop screenshots based on JSON configuration.

## Features

- Crop multiple PNG and JPG images at once
- Place cropped images on a background image
- Add localized text overlays to images
- Generate multiple language versions of each image
- Configure crop, background, and text settings via JSON
- Automatically create output directory
- Detailed logging

## Requirements

- Python 3.6 or higher
- Pillow library

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

1. Create a directory structure with:

   - An `input/screenshots` subdirectory containing the images to crop
   - A `screenshot-cropper.json` configuration file

2. Run the application:

   ```
   python main.py --directory path/to/your/directory
   ```

3. Cropped images will be saved in an `output` subdirectory.

## Configuration

Create a `screenshot-cropper.json` file with the following structure:

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

- `top`: Number of pixels to crop from the top
- `left`: Number of pixels to crop from the left
- `right`: Number of pixels to crop from the right
- `bottom`: Number of pixels to crop from the bottom

### Background Settings (Optional)

- `file`: Filename of the background image (located in the input directory)
- `position`: Position to place the cropped image on the background
  - `x`: X-coordinate (horizontal position)
  - `y`: Y-coordinate (vertical position)
- `size`: Size to resize the cropped image before placing on background
  - `width`: Width in pixels
  - `height`: Height in pixels

If background settings are not provided, images will only be cropped.

### Text Settings (Optional)

- `font`: Font settings for text overlay
  - `files`: Dictionary of language-specific font files
    - `default`: Default font file to use when no language-specific font is available
    - `[locale]`: Font file to use for specific locale (e.g., `ar` for Arabic)
  - `size`: Font size in pixels
  - `align`: Horizontal text alignment ("left", "center", "right")
  - `vertical-align`: Vertical text alignment ("top", "middle", "bottom")
  - `x`: X-coordinate for text position
  - `y`: Y-coordinate for text position
  - `width`: Width of text area (used for alignment)
  - `height`: Height of text area (used for vertical alignment)
  - `color`: RGB color values for the text
    - `r`: Red component (0-255)
    - `g`: Green component (0-255)
    - `b`: Blue component (0-255)

If text settings are provided, the application will look for locale files in the `input/locales` directory. Each locale file should be a JSON file named with the locale code (e.g., `en.json`, `de.json`) and contain a dictionary of texts with keys in the format "Text_1", "Text_2", etc.

Example locale file (`en.json`):

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
│   ├── bg.png                  # Background image
│   ├── locales/                # Locale directory
│   │   ├── en.json             # English texts
│   │   └── de.json             # German texts
│   └── screenshots/
│       ├── screenshot1.png
│       ├── screenshot2.jpg
│       └── screenshot3.png
└── screenshot-cropper.json
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
│       └── screenshot3.png
├── output/
│   ├── screenshot1_en.png     # English version
│   ├── screenshot1_de.png     # German version
│   ├── screenshot2_en.jpg     # English version
│   ├── screenshot2_de.jpg     # German version
│   ├── screenshot3_en.png     # English version
│   └── screenshot3_de.png     # German version
└── screenshot-cropper.json
```

## License

MIT
