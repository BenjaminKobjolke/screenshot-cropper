# Screenshot Cropper

A Python application to crop screenshots based on JSON configuration.

## Features

- Crop multiple PNG and JPG images at once
- Configure crop settings via JSON
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

   - An `input` subdirectory containing the images to crop
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
  "top": 50,
  "left": 0,
  "right": 0,
  "bottom": 0
}
```

Where:

- `top`: Number of pixels to crop from the top
- `left`: Number of pixels to crop from the left
- `right`: Number of pixels to crop from the right
- `bottom`: Number of pixels to crop from the bottom

## Example

For a directory structure:

```
my-screenshots/
├── input/
│   ├── screenshot1.png
│   ├── screenshot2.jpg
│   └── screenshot3.png
└── screenshot-cropper.json
```

Run:

```
python main.py --directory my-screenshots
```

The cropped images will be saved in:

```
my-screenshots/
├── input/
│   ├── screenshot1.png
│   ├── screenshot2.jpg
│   └── screenshot3.png
├── output/
│   ├── screenshot1.png
│   ├── screenshot2.jpg
│   └── screenshot3.png
└── screenshot-cropper.json
```

## License

MIT
