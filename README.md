# Screenshot Cropper

A Python application to crop screenshots based on JSON configuration.

## Features

- Crop multiple PNG and JPG images at once
- Place cropped images on a background image
- Configure crop and background settings via JSON
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

## Example

For a directory structure:

```
my-screenshots/
├── input/
│   ├── bg.png                  # Background image
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
│   └── screenshots/
│       ├── screenshot1.png
│       ├── screenshot2.jpg
│       └── screenshot3.png
├── output/
│   ├── screenshot1.png        # Cropped and placed on background
│   ├── screenshot2.jpg        # Cropped and placed on background
│   └── screenshot3.png        # Cropped and placed on background
└── screenshot-cropper.json
```

## License

MIT
