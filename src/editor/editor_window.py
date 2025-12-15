"""
Visual Editor for Screenshot Cropper configuration.
Allows interactive positioning and scaling of background, screenshot, and overlay layers.
"""
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk


class EditorWindow:
    """Main editor window for visual configuration."""

    def __init__(self, base_dir, config_path):
        """
        Initialize the editor.

        Args:
            base_dir: Base directory containing input folder
            config_path: Path to screenshot-cropper.json
        """
        self.base_dir = base_dir
        self.config_path = config_path
        self.input_dir = os.path.join(base_dir, "input")

        # Load config
        self.config = self._load_config()

        # Layer data: {name: {image, position, size, original_size}}
        self.layers = {}
        self.layer_vars = {}
        self.layer_frames = {}
        self.selected_layer = None
        self.drag_start = None

        # Crop settings
        crop_config = self.config.get('crop', {})
        self.crop_settings = {
            'top': crop_config.get('top', 0),
            'left': crop_config.get('left', 0),
            'right': crop_config.get('right', 0),
            'bottom': crop_config.get('bottom', 0)
        }
        self.crop_vars = {}

        # Canvas zoom/pan
        self.zoom = 0.5  # Start at 50% zoom for large images
        self.pan_offset = (0, 0)

        # Setup window
        self.root = tk.Tk()
        self.root.title("Screenshot Cropper Editor")
        self.root.geometry("1400x900")

        # Bind keyboard shortcuts
        self.root.bind('<Control-s>', lambda e: self._save_config())
        self.root.bind('<Left>', lambda e: self._nudge(-1, 0))
        self.root.bind('<Right>', lambda e: self._nudge(1, 0))
        self.root.bind('<Up>', lambda e: self._nudge(0, -1))
        self.root.bind('<Down>', lambda e: self._nudge(0, 1))
        self.root.bind('<Shift-Left>', lambda e: self._nudge(-10, 0))
        self.root.bind('<Shift-Right>', lambda e: self._nudge(10, 0))
        self.root.bind('<Shift-Up>', lambda e: self._nudge(0, -10))
        self.root.bind('<Shift-Down>', lambda e: self._nudge(0, 10))

        # Load images first to know which layers exist
        self._load_images()
        self._setup_ui()
        self._sync_controls_from_layers()  # Sync UI with loaded values
        self._update_canvas()

    def _load_config(self):
        """Load configuration from JSON file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_config(self):
        """Save current layer positions/sizes to config JSON."""
        # Update crop settings
        if 'crop' not in self.config:
            self.config['crop'] = {}
        self.config['crop']['top'] = self.crop_settings['top']
        self.config['crop']['left'] = self.crop_settings['left']
        self.config['crop']['right'] = self.crop_settings['right']
        self.config['crop']['bottom'] = self.crop_settings['bottom']

        # Update screenshot settings (stored in background.position and background.size)
        # Note: background.position is where the screenshot is placed ON the background
        if 'screenshot' in self.layers:
            layer = self.layers['screenshot']
            if 'background' not in self.config:
                self.config['background'] = {}
            if 'position' not in self.config['background']:
                self.config['background']['position'] = {}
            if 'size' not in self.config['background']:
                self.config['background']['size'] = {}

            # Screenshot position is where cropped image is placed on background
            self.config['background']['position']['x'] = layer['position'][0]
            self.config['background']['position']['y'] = layer['position'][1]
            self.config['background']['size']['width'] = layer['size'][0]
            self.config['background']['size']['height'] = layer['size'][1]

        # Update overlay settings
        if 'overlay' in self.layers:
            layer = self.layers['overlay']
            if 'overlay' not in self.config:
                self.config['overlay'] = {}
            if 'position' not in self.config['overlay']:
                self.config['overlay']['position'] = {}

            self.config['overlay']['position']['x'] = layer['position'][0]
            self.config['overlay']['position']['y'] = layer['position'][1]

        # Write config
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

        self._update_status("Configuration saved!")
        messagebox.showinfo("Saved", f"Configuration saved to:\n{self.config_path}")

    def _setup_ui(self):
        """Setup the main UI layout."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left: Canvas area
        canvas_frame = ttk.LabelFrame(main_frame, text="Preview")
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Canvas with scrollbars
        self.canvas = tk.Canvas(canvas_frame, bg='#333333', cursor='crosshair')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Canvas bindings
        self.canvas.bind('<Button-1>', self._on_canvas_click)
        self.canvas.bind('<B1-Motion>', self._on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_canvas_release)
        self.canvas.bind('<MouseWheel>', self._on_mouse_wheel)

        # Right: Controls panel
        controls_frame = ttk.Frame(main_frame, width=300)
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y)
        controls_frame.pack_propagate(False)

        # Crop controls
        crop_frame = ttk.LabelFrame(controls_frame, text="Crop (pixels from edge)")
        crop_frame.pack(fill=tk.X, pady=(0, 10))

        # Top/Bottom row
        tb_frame = ttk.Frame(crop_frame)
        tb_frame.pack(fill=tk.X, pady=2)
        ttk.Label(tb_frame, text="Top:").pack(side=tk.LEFT)
        top_var = tk.IntVar(value=self.crop_settings['top'])
        top_spin = ttk.Spinbox(tb_frame, from_=0, to=9999, width=6, textvariable=top_var)
        top_spin.pack(side=tk.LEFT, padx=2)
        top_var.trace_add('write', lambda *args: self._on_crop_change())
        self.crop_vars['top'] = top_var

        ttk.Label(tb_frame, text="Bottom:").pack(side=tk.LEFT, padx=(10, 0))
        bottom_var = tk.IntVar(value=self.crop_settings['bottom'])
        bottom_spin = ttk.Spinbox(tb_frame, from_=0, to=9999, width=6, textvariable=bottom_var)
        bottom_spin.pack(side=tk.LEFT, padx=2)
        bottom_var.trace_add('write', lambda *args: self._on_crop_change())
        self.crop_vars['bottom'] = bottom_var

        # Left/Right row
        lr_frame = ttk.Frame(crop_frame)
        lr_frame.pack(fill=tk.X, pady=2)
        ttk.Label(lr_frame, text="Left:").pack(side=tk.LEFT)
        left_var = tk.IntVar(value=self.crop_settings['left'])
        left_spin = ttk.Spinbox(lr_frame, from_=0, to=9999, width=6, textvariable=left_var)
        left_spin.pack(side=tk.LEFT, padx=2)
        left_var.trace_add('write', lambda *args: self._on_crop_change())
        self.crop_vars['left'] = left_var

        ttk.Label(lr_frame, text="Right:").pack(side=tk.LEFT, padx=(10, 0))
        right_var = tk.IntVar(value=self.crop_settings['right'])
        right_spin = ttk.Spinbox(lr_frame, from_=0, to=9999, width=6, textvariable=right_var)
        right_spin.pack(side=tk.LEFT, padx=2)
        right_var.trace_add('write', lambda *args: self._on_crop_change())
        self.crop_vars['right'] = right_var

        # Zoom control
        zoom_frame = ttk.LabelFrame(controls_frame, text="Zoom")
        zoom_frame.pack(fill=tk.X, pady=(0, 10))

        self.zoom_var = tk.StringVar(value=f"{int(self.zoom * 100)}%")
        zoom_label = ttk.Label(zoom_frame, textvariable=self.zoom_var)
        zoom_label.pack(side=tk.LEFT, padx=5)

        ttk.Button(zoom_frame, text="-", width=3, command=lambda: self._adjust_zoom(-0.1)).pack(side=tk.LEFT)
        ttk.Button(zoom_frame, text="+", width=3, command=lambda: self._adjust_zoom(0.1)).pack(side=tk.LEFT)
        ttk.Button(zoom_frame, text="Fit", width=4, command=self._fit_zoom).pack(side=tk.LEFT, padx=5)

        # Layer controls - only create for layers that exist
        for layer_name in ['background', 'screenshot', 'overlay']:
            if layer_name in self.layers:
                self._create_layer_controls(controls_frame, layer_name)
            else:
                # Show placeholder for missing layer
                frame = ttk.LabelFrame(controls_frame, text=f"{layer_name.capitalize()} (not found)")
                frame.pack(fill=tk.X, pady=5)
                ttk.Label(frame, text="Image file not found", foreground='gray').pack(pady=5)

        # Save button
        save_frame = ttk.Frame(controls_frame)
        save_frame.pack(fill=tk.X, pady=10)
        ttk.Button(save_frame, text="Save Configuration (Ctrl+S)", command=self._save_config).pack(fill=tk.X)

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Click a layer to select, drag to move")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_layer_controls(self, parent, layer_name):
        """Create control panel for a layer."""
        frame = ttk.LabelFrame(parent, text=layer_name.capitalize())
        frame.pack(fill=tk.X, pady=5)
        self.layer_frames[layer_name] = frame

        # Background has no position controls (it's always the base at 0,0)
        if layer_name == 'background':
            ttk.Label(frame, text="Base layer (fixed at 0,0)", foreground='gray').pack(pady=5)
            self.layer_vars[layer_name] = {}
            return

        # Selection indicator
        select_btn = ttk.Button(frame, text="Select",
                                command=lambda: self._select_layer(layer_name))
        select_btn.pack(fill=tk.X)

        # Position controls
        pos_frame = ttk.Frame(frame)
        pos_frame.pack(fill=tk.X, pady=2)

        ttk.Label(pos_frame, text="X:").pack(side=tk.LEFT)
        x_var = tk.IntVar(value=0)
        x_spin = ttk.Spinbox(pos_frame, from_=-9999, to=9999, width=6, textvariable=x_var)
        x_spin.pack(side=tk.LEFT, padx=2)
        x_var.trace_add('write', lambda *args, ln=layer_name, v=x_var: self._on_position_change(ln, 'x', v))

        ttk.Label(pos_frame, text="Y:").pack(side=tk.LEFT, padx=(10, 0))
        y_var = tk.IntVar(value=0)
        y_spin = ttk.Spinbox(pos_frame, from_=-9999, to=9999, width=6, textvariable=y_var)
        y_spin.pack(side=tk.LEFT, padx=2)
        y_var.trace_add('write', lambda *args, ln=layer_name, v=y_var: self._on_position_change(ln, 'y', v))

        # Store references
        self.layer_vars[layer_name] = {'x': x_var, 'y': y_var}

        # Size controls (only for screenshot)
        if layer_name == 'screenshot':
            size_frame = ttk.Frame(frame)
            size_frame.pack(fill=tk.X, pady=2)

            ttk.Label(size_frame, text="Width:").pack(side=tk.LEFT)
            w_var = tk.IntVar(value=0)
            w_spin = ttk.Spinbox(size_frame, from_=1, to=9999, width=6, textvariable=w_var)
            w_spin.pack(side=tk.LEFT, padx=2)
            w_var.trace_add('write', lambda *args, v=w_var: self._on_width_change(v))
            self.layer_vars[layer_name]['width'] = w_var

            ttk.Label(size_frame, text="Height:").pack(side=tk.LEFT, padx=(10, 0))
            h_var = tk.IntVar(value=0)
            h_label = ttk.Label(size_frame, textvariable=h_var, width=6)
            h_label.pack(side=tk.LEFT, padx=2)
            self.layer_vars[layer_name]['height'] = h_var

    def _find_file(self, filename):
        """Find file in multiple locations (like original compositor)."""
        # Check if it's an absolute path
        if os.path.isabs(filename) and os.path.exists(filename):
            return filename

        # Check in input directory
        path = os.path.join(self.input_dir, filename)
        if os.path.exists(path):
            return path

        # Check in base directory
        path = os.path.join(self.base_dir, filename)
        if os.path.exists(path):
            return path

        return None

    def _load_images(self):
        """Load background, screenshot, and overlay images."""
        # Load background
        bg_config = self.config.get('background', {})
        bg_file = bg_config.get('file', 'bg.png')
        bg_path = self._find_file(bg_file)

        try:
            if bg_path:
                img = Image.open(bg_path)
                self.layers['background'] = {
                    'image': img,
                    'position': (0, 0),  # Background is the base, always at 0,0
                    'size': img.size,
                    'original_size': img.size
                }
                print(f"Loaded background: {bg_path}")
            else:
                print(f"Warning: Background file not found: {bg_file}")
        except Exception as e:
            print(f"Warning: Could not load background image: {e}")

        # Build list of files to exclude (background and overlay)
        exclude_files = set()
        if bg_file:
            exclude_files.add(bg_file.lower())
        overlay_config = self.config.get('overlay')
        if overlay_config:
            overlay_file = overlay_config.get('file', '')
            if overlay_file:
                exclude_files.add(overlay_file.lower())

        # Load first screenshot - check multiple locations
        screenshot_dirs = [
            os.path.join(self.input_dir, "screenshots"),
            self.input_dir,
            self.base_dir
        ]

        screenshot_loaded = False
        for screenshots_dir in screenshot_dirs:
            if screenshot_loaded:
                break
            try:
                if os.path.isdir(screenshots_dir):
                    for fname in sorted(os.listdir(screenshots_dir)):
                        # Skip background and overlay files
                        if fname.lower() in exclude_files:
                            continue
                        if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                            screenshot_path = os.path.join(screenshots_dir, fname)
                            img = Image.open(screenshot_path)

                            # Get position and size from config
                            pos_x = bg_config.get('position', {}).get('x', 0)
                            pos_y = bg_config.get('position', {}).get('y', 0)
                            width = bg_config.get('size', {}).get('width', img.width)
                            height = bg_config.get('size', {}).get('height', img.height)

                            self.layers['screenshot'] = {
                                'image': img,
                                'position': (pos_x, pos_y),
                                'size': (width, height),
                                'original_size': img.size
                            }
                            print(f"Loaded screenshot: {screenshot_path}")
                            screenshot_loaded = True
                            break
            except Exception as e:
                print(f"Warning: Could not load screenshot from {screenshots_dir}: {e}")

        if not screenshot_loaded:
            print("Warning: No screenshot found in input/screenshots/, input/, or base directory")

        # Load overlay - only if overlay section exists in config
        overlay_config = self.config.get('overlay')
        if overlay_config:
            overlay_file = overlay_config.get('file', 'overlay.png')
            overlay_path = self._find_file(overlay_file)

            try:
                if overlay_path:
                    img = Image.open(overlay_path)
                    pos_x = overlay_config.get('position', {}).get('x', 0)
                    pos_y = overlay_config.get('position', {}).get('y', 0)
                    self.layers['overlay'] = {
                        'image': img,
                        'position': (pos_x, pos_y),
                        'size': img.size,
                        'original_size': img.size
                    }
                    print(f"Loaded overlay: {overlay_path}")
                else:
                    print(f"Warning: Overlay file not found: {overlay_file}")
            except Exception as e:
                print(f"Warning: Could not load overlay image: {e}")

    def _sync_controls_from_layers(self):
        """Sync control values from layer data."""
        for layer_name, layer_data in self.layers.items():
            if layer_name in self.layer_vars:
                vars_dict = self.layer_vars[layer_name]
                # Background has no position controls
                if 'x' in vars_dict:
                    vars_dict['x'].set(layer_data['position'][0])
                if 'y' in vars_dict:
                    vars_dict['y'].set(layer_data['position'][1])
                if 'width' in vars_dict:
                    vars_dict['width'].set(layer_data['size'][0])
                if 'height' in vars_dict:
                    vars_dict['height'].set(layer_data['size'][1])

    def _update_canvas(self):
        """Render the composite image on canvas."""
        self.canvas.delete('all')

        if not self.layers:
            return

        # Determine canvas size based on background or largest layer
        if 'background' in self.layers:
            base_size = self.layers['background']['size']
        else:
            base_size = (1000, 1000)

        # Create composite image
        composite = Image.new('RGBA', base_size, (50, 50, 50, 255))

        # Render layers in order: background, screenshot, overlay
        for layer_name in ['background', 'screenshot', 'overlay']:
            if layer_name not in self.layers:
                continue

            layer = self.layers[layer_name]
            img = layer['image'].copy()

            # Apply crop and resize to screenshot
            if layer_name == 'screenshot':
                # Apply crop first
                orig_w, orig_h = layer['original_size']
                crop_left = self.crop_settings['left']
                crop_top = self.crop_settings['top']
                crop_right = orig_w - self.crop_settings['right']
                crop_bottom = orig_h - self.crop_settings['bottom']

                # Validate crop box
                if crop_left < crop_right and crop_top < crop_bottom:
                    img = img.crop((crop_left, crop_top, crop_right, crop_bottom))

                # Then resize to target size
                if layer['size'][0] > 0 and layer['size'][1] > 0:
                    img = img.resize(layer['size'], Image.Resampling.LANCZOS)

            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Paste at position
            pos = layer['position']
            try:
                composite.paste(img, pos, img if img.mode == 'RGBA' else None)
            except ValueError:
                # Handle case where paste position is partially outside
                composite.paste(img, pos)

        # Apply zoom
        display_size = (int(base_size[0] * self.zoom), int(base_size[1] * self.zoom))
        display_img = composite.resize(display_size, Image.Resampling.LANCZOS)

        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(display_img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # Draw selection indicator
        if self.selected_layer and self.selected_layer in self.layers:
            layer = self.layers[self.selected_layer]
            x, y = layer['position']
            w, h = layer['size']

            # Scale to zoom
            x1, y1 = int(x * self.zoom), int(y * self.zoom)
            x2, y2 = int((x + w) * self.zoom), int((y + h) * self.zoom)

            self.canvas.create_rectangle(x1, y1, x2, y2, outline='#00FF00', width=2, dash=(5, 5))

        # Update zoom display
        self.zoom_var.set(f"{int(self.zoom * 100)}%")

    def _select_layer(self, layer_name):
        """Select a layer for editing."""
        # Background cannot be selected (it's fixed at 0,0)
        if layer_name == 'background':
            return

        if layer_name in self.layers:
            self.selected_layer = layer_name
            self._update_status(f"Selected: {layer_name.capitalize()}")
            self._update_canvas()

            # Update frame appearance
            for name, frame in self.layer_frames.items():
                if name == layer_name:
                    frame.configure(style='Selected.TLabelframe')
                else:
                    frame.configure(style='TLabelframe')

    def _on_canvas_click(self, event):
        """Handle canvas click - select layer at click position."""
        # Convert to image coordinates
        img_x = int(event.x / self.zoom)
        img_y = int(event.y / self.zoom)

        # Check layers in reverse order (top to bottom)
        for layer_name in reversed(['background', 'screenshot', 'overlay']):
            if layer_name not in self.layers:
                continue

            layer = self.layers[layer_name]
            x, y = layer['position']
            w, h = layer['size']

            if x <= img_x <= x + w and y <= img_y <= y + h:
                self._select_layer(layer_name)
                self.drag_start = (event.x, event.y, x, y)
                return

        # Click on empty space - deselect
        self.selected_layer = None
        self._update_canvas()

    def _on_canvas_drag(self, event):
        """Handle canvas drag - move selected layer."""
        if not self.selected_layer or not self.drag_start:
            return

        # Calculate delta in image coordinates
        dx = int((event.x - self.drag_start[0]) / self.zoom)
        dy = int((event.y - self.drag_start[1]) / self.zoom)

        # Update position
        new_x = self.drag_start[2] + dx
        new_y = self.drag_start[3] + dy

        self.layers[self.selected_layer]['position'] = (new_x, new_y)
        self._sync_controls_from_layers()
        self._update_canvas()
        self._update_status(f"{self.selected_layer.capitalize()}: ({new_x}, {new_y})")

    def _on_canvas_release(self, event):
        """Handle canvas release."""
        self.drag_start = None

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel - zoom or scale screenshot."""
        if self.selected_layer == 'screenshot' and 'screenshot' in self.layers:
            # Scale screenshot width
            layer = self.layers['screenshot']
            delta = 10 if event.delta > 0 else -10
            new_width = max(10, layer['size'][0] + delta)

            # Calculate new height preserving aspect ratio
            aspect = layer['original_size'][1] / layer['original_size'][0]
            new_height = int(new_width * aspect)

            layer['size'] = (new_width, new_height)
            self._sync_controls_from_layers()
            self._update_canvas()
        else:
            # Zoom canvas
            delta = 0.1 if event.delta > 0 else -0.1
            self._adjust_zoom(delta)

    def _adjust_zoom(self, delta):
        """Adjust canvas zoom level."""
        self.zoom = max(0.1, min(2.0, self.zoom + delta))
        self._update_canvas()

    def _fit_zoom(self):
        """Fit zoom to show entire image in canvas."""
        if 'background' in self.layers:
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            img_w, img_h = self.layers['background']['size']

            if canvas_w > 1 and canvas_h > 1:
                zoom_w = canvas_w / img_w
                zoom_h = canvas_h / img_h
                self.zoom = min(zoom_w, zoom_h, 1.0) * 0.95  # 95% to leave margin
                self._update_canvas()

    def _nudge(self, dx, dy):
        """Nudge selected layer by dx, dy pixels."""
        if not self.selected_layer or self.selected_layer not in self.layers:
            return

        layer = self.layers[self.selected_layer]
        x, y = layer['position']
        layer['position'] = (x + dx, y + dy)
        self._sync_controls_from_layers()
        self._update_canvas()

    def _on_position_change(self, layer_name, axis, var):
        """Handle position spinbox change."""
        if layer_name not in self.layers:
            return

        try:
            value = var.get()
        except tk.TclError:
            return

        layer = self.layers[layer_name]
        x, y = layer['position']

        if axis == 'x':
            layer['position'] = (value, y)
        else:
            layer['position'] = (x, value)

        self._update_canvas()

    def _on_width_change(self, var):
        """Handle screenshot width spinbox change."""
        if 'screenshot' not in self.layers:
            return

        try:
            new_width = var.get()
        except tk.TclError:
            return

        if new_width < 1:
            return

        layer = self.layers['screenshot']
        # Use cropped size for aspect ratio calculation
        cropped_size = self._get_cropped_size()
        if cropped_size[0] > 0:
            aspect = cropped_size[1] / cropped_size[0]
        else:
            aspect = layer['original_size'][1] / layer['original_size'][0]
        new_height = int(new_width * aspect)

        layer['size'] = (new_width, new_height)
        self.layer_vars['screenshot']['height'].set(new_height)
        self._update_canvas()

    def _on_crop_change(self):
        """Handle crop spinbox change."""
        try:
            self.crop_settings['top'] = self.crop_vars['top'].get()
            self.crop_settings['left'] = self.crop_vars['left'].get()
            self.crop_settings['right'] = self.crop_vars['right'].get()
            self.crop_settings['bottom'] = self.crop_vars['bottom'].get()
        except tk.TclError:
            return

        # Update screenshot size to maintain aspect ratio with new crop
        if 'screenshot' in self.layers:
            layer = self.layers['screenshot']
            cropped_size = self._get_cropped_size()
            if cropped_size[0] > 0 and cropped_size[1] > 0:
                # Keep width, recalculate height based on new aspect ratio
                aspect = cropped_size[1] / cropped_size[0]
                new_height = int(layer['size'][0] * aspect)
                layer['size'] = (layer['size'][0], new_height)
                if 'height' in self.layer_vars.get('screenshot', {}):
                    self.layer_vars['screenshot']['height'].set(new_height)

        self._update_canvas()

    def _get_cropped_size(self):
        """Get the size of the screenshot after cropping."""
        if 'screenshot' not in self.layers:
            return (0, 0)

        orig_w, orig_h = self.layers['screenshot']['original_size']
        crop_left = self.crop_settings['left']
        crop_right = self.crop_settings['right']
        crop_top = self.crop_settings['top']
        crop_bottom = self.crop_settings['bottom']

        cropped_w = orig_w - crop_left - crop_right
        cropped_h = orig_h - crop_top - crop_bottom

        return (max(1, cropped_w), max(1, cropped_h))

    def _update_status(self, message):
        """Update status bar message."""
        self.status_var.set(message)

    def run(self):
        """Start the editor main loop."""
        # Initial fit after window is displayed
        self.root.after(100, self._fit_zoom)
        self.root.mainloop()


def launch_editor(base_dir, config_path):
    """Launch the editor window."""
    editor = EditorWindow(base_dir, config_path)
    editor.run()
