"""
PSD processor module for the Screenshot Cropper application.
"""
import logging
import os
import json
import re

logger = logging.getLogger("screenshot_cropper")

class PSDProcessor:
    """Handler for PSD file processing operations."""
    
    def __init__(self, locale_handler=None, text_settings=None):
        """
        Initialize the PSDProcessor.
        
        Args:
            locale_handler (LocaleHandler, optional): Handler for locale texts.
            text_settings (TextSettings, optional): Text settings for font configuration.
        """
        self.locale_handler = locale_handler
        self.text_settings = text_settings
    
    def process_psd(self, psd_path, output_path, locale=None):
        """
        Process a PSD file, translate text layers, and save as PNG.
        
        Args:
            psd_path (str): Path to the PSD file.
            output_path (str): Path to save the output PNG file.
            locale (str, optional): Locale code for text translation.
            
        Returns:
            bool: True if processing was successful, False otherwise.
        """
        try:
            logger.info(f"Processing PSD file: {psd_path}")
            
            # Check if the PSD file exists
            if not os.path.isfile(psd_path):
                raise FileNotFoundError(f"PSD file not found: {psd_path}")
            
            # Get absolute paths
            abs_psd_path = os.path.abspath(psd_path)
            abs_output_path = os.path.abspath(output_path)
            
            logger.info(f"Absolute PSD path: {abs_psd_path}")
            logger.info(f"Absolute output path: {abs_output_path}")
            
            # Try to use Photoshop Python API with Session
            from photoshop import Session
            import time
            
            try:
                # Check if Photoshop is installed and accessible
                logger.info("Checking Photoshop installation...")
                with Session() as ps:
                    ps_version = ps.app.version
                    logger.info(f"Photoshop version: {ps_version}")
                    
                    # Close any open documents first
                    logger.info("Closing any open documents in Photoshop")
                    try:
                        while ps.app.documents.length > 0:
                            ps.active_document.close(ps.SaveOptions.DoNotSaveChanges)
                    except Exception as close_error:
                        logger.warning(f"Error closing documents: {close_error}")
                    
                    # Open the PSD file using system default application (Photoshop)
                    logger.info(f"Opening PSD file with system default application: {abs_psd_path}")
                    os.startfile(abs_psd_path)
                    
                    # Wait for the document to be loaded
                    max_wait_time = 30  # seconds
                    wait_start = time.time()
                    
                    logger.info("Waiting for document to open...")
                    while True:
                        try:
                            doc_count = ps.app.documents.length
                            logger.info(f"Documents open: {doc_count}")
                            
                            if doc_count >= 1:
                                break
                                
                            if time.time() - wait_start > max_wait_time:
                                raise TimeoutError(f"Timed out waiting for Photoshop to open {abs_psd_path}")
                                
                            time.sleep(1)
                        except Exception as wait_error:
                            logger.error(f"Error while waiting for document: {wait_error}")
                            if time.time() - wait_start > max_wait_time:
                                raise TimeoutError(f"Timed out waiting for Photoshop to open {abs_psd_path}")
                            time.sleep(1)
                    
                    # Get the active document
                    try:
                        doc = ps.active_document
                        logger.info(f"Successfully opened PSD file in Photoshop: {abs_psd_path}")
                        
                        # List all layers for debugging
                        logger.info("Listing all layers in the document:")
                        try:
                            for i, layer in enumerate(doc.artLayers):
                                logger.info(f"Layer {i}: {layer.name}")
                        except Exception as layer_error:
                            logger.warning(f"Error listing layers: {layer_error}")
                        
                        # Process text layers if locale handler is available
                        if self.locale_handler and locale:
                            self._translate_text_layers_with_session(ps, doc, locale)
                        
                        # Save as PNG
                        output_dir = os.path.dirname(abs_output_path)
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                        
                        # Use exportDocument with SaveForWeb for PNG export
                        logger.info(f"Exporting PSD as PNG: {abs_output_path}")
                        
                        try:
                            # Try using JavaScript to export
                            output_path_js = abs_output_path.replace('\\', '\\\\')
                            js_script = f'''
                            var doc = app.activeDocument;
                            var saveFile = new File("{output_path_js}");
                            var saveOptions = new ExportOptionsSaveForWeb();
                            saveOptions.format = SaveDocumentType.PNG;
                            saveOptions.PNG8 = false;
                            saveOptions.transparency = true;
                            saveOptions.quality = 100;
                            doc.exportDocument(saveFile, ExportType.SAVEFORWEB, saveOptions);
                            '''
                            ps.app.doJavaScript(js_script)
                            logger.info(f"Saved PSD as PNG using Photoshop JavaScript: {abs_output_path}")
                        except Exception as export_error:
                            logger.error(f"Error exporting with JavaScript: {export_error}")
                            
                            # Try alternative export method
                            try:
                                options = ps.ExportOptionsSaveForWeb()
                                options.format = ps.SaveDocumentType.PNG
                                options.PNG8 = False
                                options.transparency = True
                                options.quality = 100
                                
                                doc.exportDocument(abs_output_path, exportAs=ps.ExportType.SaveForWeb, options=options)
                                logger.info(f"Saved PSD as PNG using Photoshop API: {abs_output_path}")
                            except Exception as alt_export_error:
                                logger.error(f"Error with alternative export: {alt_export_error}")
                                
                                # Last resort: save as PSD then convert with PIL
                                try:
                                    temp_psd = abs_output_path.replace('.png', '_temp.psd')
                                    doc.saveAs(temp_psd)
                                    logger.info(f"Saved temporary PSD: {temp_psd}")
                                    
                                    from PIL import Image
                                    with Image.open(temp_psd) as img:
                                        img.save(abs_output_path)
                                    
                                    os.remove(temp_psd)
                                    logger.info(f"Converted PSD to PNG using PIL: {abs_output_path}")
                                except Exception as pil_error:
                                    logger.error(f"Error with PIL conversion: {pil_error}")
                                    raise
                        
                        # Close all documents when done
                        logger.info("Closing all documents in Photoshop")
                        try:
                            while ps.app.documents.length > 0:
                                ps.active_document.close(ps.SaveOptions.DoNotSaveChanges)
                        except Exception as final_close_error:
                            logger.warning(f"Error closing documents at end: {final_close_error}")
                    
                    except Exception as doc_error:
                        logger.error(f"Error working with document: {doc_error}")
                        raise
            
            except Exception as session_error:
                logger.error(f"Error in Photoshop session: {session_error}")
                raise
            
            return True
            
        except ImportError as import_error:
            logger.error(f"Photoshop Python API not available: {import_error}")
            logger.error("PSD processing requires Photoshop and photoshop-python-api")
            import sys
            sys.exit(1)
            
        except Exception as e:
            logger.error(f"Error processing PSD file {psd_path}: Please check if you have Photoshop installed correctly.")
            logger.error(f"Detailed error: {str(e)}")
            logger.error("Exiting application due to Photoshop error")
            import sys
            sys.exit(1)
    
    def _translate_text_layers_with_session(self, ps, doc, locale):
        """
        Find and translate text layers in a PSD file using Photoshop Session API.
        
        Args:
            ps: Photoshop session object.
            doc: Photoshop document object.
            locale (str): Locale code for text translation.
        """
        logger.info(f"Translating text layers for locale: {locale} using Photoshop Session API")
        
        # Track if we found any translatable layers
        found_translatable_layers = False
        
        # Process all layers in the document
        try:
            # First, make all layers visible to ensure we can access them
            for layer in doc.artLayers:
                layer.visible = True
            
            # Process text layers
            for layer in doc.artLayers:
                try:
                    # Check if it's a text layer and starts with "lang_"
                    if hasattr(layer, 'kind') and layer.kind == ps.LayerKind.TextLayer and layer.name.startswith("lang_"):
                        found_translatable_layers = True
                        
                        # Extract the translation key (part after "lang_")
                        translation_key = layer.name[5:]  # Remove "lang_" prefix
                        logger.info(f"Found translatable layer: {layer.name}, key: {translation_key}")
                        
                        # Get translation from locale handler
                        translated_text = self._get_translation(translation_key, locale)
                        
                        if translated_text:
                            # Update the text layer with translated text
                            try:
                                original_text = layer.textItem.contents
                                logger.info(f"Original text: '{original_text}'")
                                
                                # Set the layer as active before modifying
                                doc.activeLayer = layer
                                
                                # Use JavaScript to set the text content
                                # Use json.dumps to properly handle all special characters including newlines
                                js_safe_text = json.dumps(translated_text)
                                
                                # Get font name for this locale if available
                                font_name = None
                                if self.text_settings and hasattr(self.text_settings, 'font_names'):
                                    font_name = self.text_settings.font_names.get(locale)
                                    if font_name:
                                        logger.info(f"Using font name for locale 123 {locale}: {font_name}")
                                
                                # Create JavaScript that replaces \n with paragraph breaks (\r)
                                # and sets the font if specified
                                js_script_font_name = '''
                                var currentFont = app.activeDocument.activeLayer.textItem.font;
                                alert("Current font: " + currentFont);
                                '''
                                #ps.app.doJavaScript(js_script_name)  

                                js_script = f'''
                                var textContent = {js_safe_text};
                                // Replace encoded newlines with Photoshop paragraph breaks
                                textContent = textContent.replace(/\\n/g, "\\r");
                                app.activeDocument.activeLayer.textItem.contents = textContent;
                                '''
                                
                                # Add font setting if a font name is specified for this locale
                                if font_name:
                                    js_script += f'''
                                    // Set the font for the text layer
                                    try {{
                                        app.activeDocument.activeLayer.textItem.font = "{font_name}";
                                    }} catch(e) {{
                                        alert("Error setting font: " + e);
                                    }}
                                    '''
                                ps.app.doJavaScript(js_script)
                                
                                logger.info(f"Translated text layer '{translation_key}' to '{translated_text}'")
                            except Exception as text_error:
                                logger.error(f"Error setting text content: {text_error}")
                        else:
                            logger.warning(f"No translation found for key: {translation_key} in locale: {locale}")
                except Exception as layer_error:
                    logger.warning(f"Error processing layer {layer.name if hasattr(layer, 'name') else 'unknown'}: {layer_error}")
            
            # Process layer sets (groups)
            try:
                if hasattr(doc, 'layerSets'):
                    for layer_set in doc.layerSets:
                        self._process_layer_set_with_session(ps, doc, layer_set, locale, found_translatable_layers)
            except Exception as sets_error:
                logger.warning(f"Error processing layer sets: {sets_error}")
                
        except Exception as e:
            logger.error(f"Error in translate_text_layers: {e}")
        
        if not found_translatable_layers:
            logger.info("No translatable text layers (starting with 'lang_') found in the PSD file")
    
    def _process_layer_set_with_session(self, ps, doc, layer_set, locale, found_translatable_layers):
        """
        Process a layer set (group) recursively to find and translate text layers.
        
        Args:
            ps: Photoshop session object.
            doc: Photoshop document object.
            layer_set: Photoshop layer set object.
            locale (str): Locale code for text translation.
            found_translatable_layers (bool): Reference to track if translatable layers were found.
        """
        logger.info(f"Processing layer set: {layer_set.name if hasattr(layer_set, 'name') else 'unknown'}")
        
        # Process text layers in this group
        try:
            if hasattr(layer_set, 'artLayers'):
                for layer in layer_set.artLayers:
                    try:
                        # Check if it's a text layer and starts with "lang_"
                        if hasattr(layer, 'kind') and layer.kind == ps.LayerKind.TextLayer and layer.name.startswith("lang_"):
                            found_translatable_layers = True
                            
                            # Extract the translation key (part after "lang_")
                            translation_key = layer.name[5:]  # Remove "lang_" prefix
                            logger.info(f"Found translatable layer in group: {layer.name}, key: {translation_key}")
                            
                            # Get translation from locale handler
                            translated_text = self._get_translation(translation_key, locale)
                            
                            if translated_text:
                                # Update the text layer with translated text
                                try:
                                    original_text = layer.textItem.contents
                                    logger.info(f"Original text in group: '{original_text}'")
                                    
                                    # Set the layer as active before modifying
                                    doc.activeLayer = layer
                                    
                                    # Use JavaScript to set the text content
                                    # Use json.dumps to properly handle all special characters including newlines
                                    js_safe_text = json.dumps(translated_text)
                                    
                                    # Get font name for this locale if available
                                    font_name = None
                                    if self.text_settings and hasattr(self.text_settings, 'font_names'):
                                        font_name = self.text_settings.font_names.get(locale)
                                        if font_name:
                                            logger.info(f"Using font name for locale {locale}: {font_name}")
                                    
                                    js_script_font_name = '''
                                    var currentFont = app.activeDocument.activeLayer.textItem.font;
                                    alert("Current font: " + currentFont);
                                    '''
                                    #ps.app.doJavaScript(js_script_font_name)  


                                    # Create JavaScript that replaces \n with paragraph breaks (\r)
                                    # and sets the font if specified
                                    js_script = f'''
                                    var textContent = {js_safe_text};
                                    // Replace encoded newlines with Photoshop paragraph breaks
                                    textContent = textContent.replace(/\\n/g, "\\r");
                                    app.activeDocument.activeLayer.textItem.contents = textContent;
                                    '''
                                    
                                    # Add font setting if a font name is specified for this locale
                                    if font_name:
                                        js_script += f'''
                                        // Set the font for the text layer
                                        try {{
                                            app.activeDocument.activeLayer.textItem.font = "{font_name}";
                                        }} catch(e) {{
                                            alert("Error setting font: " + e);
                                        }}
                                        '''
                                    ps.app.doJavaScript(js_script)
                                    #ps.app.doJavaScript(js_script_font_name)  
                                    
                                    logger.info(f"Translated text layer in group '{translation_key}' to '{translated_text}'")
                                except Exception as text_error:
                                    logger.error(f"Error setting text content in group: {text_error}")
                            else:
                                logger.warning(f"No translation found for key: {translation_key} in locale: {locale}")
                    except Exception as layer_error:
                        logger.warning(f"Error processing layer in group {layer.name if hasattr(layer, 'name') else 'unknown'}: {layer_error}")
        except Exception as art_layers_error:
            logger.warning(f"Error accessing art layers in group: {art_layers_error}")
        
        # Process nested layer groups
        try:
            if hasattr(layer_set, 'layerSets'):
                for nested_layer_set in layer_set.layerSets:
                    try:
                        self._process_layer_set_with_session(ps, doc, nested_layer_set, locale, found_translatable_layers)
                    except Exception as nested_error:
                        logger.warning(f"Error processing nested layer set: {nested_error}")
        except Exception as layer_sets_error:
            logger.warning(f"Error accessing nested layer sets: {layer_sets_error}")
    
    def _get_translation(self, key, locale):
        """
        Get translation for a key in the specified locale.
        
        Args:
            key (str): Translation key.
            locale (str): Locale code.
            
        Returns:
            str: Translated text, or None if not found.
        """
        if not self.locale_handler:
            return None
            
        # Try to get translation from locale handler
        # First try with the key as is
        texts = self.locale_handler.locales.get(locale, {})
        
        # Handle dictionary format
        if isinstance(texts, dict):
            # Try different key formats
            if key in texts:
                return texts[key]
            if f"Text_{key}" in texts:
                return texts[f"Text_{key}"]
            
            # Try to find a key that ends with the translation key
            for text_key in texts:
                if text_key.endswith(key):
                    return texts[text_key]
        
        # Handle array format
        elif isinstance(texts, list):
            try:
                # Try to convert key to integer index
                index = int(key) - 1  # Convert to 0-based index
                if 0 <= index < len(texts):
                    return texts[index]
            except ValueError:
                # Key is not a valid integer
                pass
        
        logger.warning(f"Translation not found for key '{key}' in locale '{locale}'")
        return None

    def _sanitize_layer_name(self, name):
        """
        Sanitize a layer name for use as a translation key.

        Rules:
        - Convert to lowercase
        - Replace spaces with underscores
        - Keep only a-z and underscore characters
        - Limit to 30 characters, truncating at word boundaries when possible

        Args:
            name (str): Original layer name.

        Returns:
            str: Sanitized layer name.
        """
        # Convert to lowercase
        sanitized = name.lower()

        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')

        # Keep only a-z and underscore
        sanitized = re.sub(r'[^a-z_]', '', sanitized)

        # Limit to 30 characters, truncating at word boundaries
        if len(sanitized) > 30:
            # Find the last underscore within the 30-character limit
            truncated = sanitized[:30]
            last_underscore = truncated.rfind('_')

            if last_underscore > 0:
                # Truncate at the last underscore to end on a complete word
                sanitized = sanitized[:last_underscore]
            else:
                # No underscore found, use hard truncation
                sanitized = truncated

        return sanitized

    def prepare_and_export_template(self, psd_path, output_json_path):
        """
        Prepare a PSD file by renaming all text layers and exporting a template.

        This method:
        1. Loads existing template.json if it exists
        2. Opens the PSD file
        3. Traverses all text layers
        4. Renames each to lang_[sanitized_name]
        5. Exports/updates template.json with layer text content
        6. Saves the modified PSD file

        Args:
            psd_path (str): Path to the PSD file.
            output_json_path (str): Path to save the template JSON file.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            logger.info(f"Preparing PSD and exporting template: {psd_path}")

            # Load existing template if it exists
            template = {}
            if os.path.exists(output_json_path):
                try:
                    with open(output_json_path, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                    logger.info(f"Loaded existing template with {len(template)} keys")
                except Exception as load_error:
                    logger.warning(f"Could not load existing template: {load_error}")

            # Get absolute paths
            abs_psd_path = os.path.abspath(psd_path)
            abs_output_path = os.path.abspath(output_json_path)

            logger.info(f"Absolute PSD path: {abs_psd_path}")
            logger.info(f"Absolute template output path: {abs_output_path}")

            # Use Photoshop Python API with Session
            from photoshop import Session
            import time

            with Session() as ps:
                ps_version = ps.app.version
                logger.info(f"Photoshop version: {ps_version}")

                # Close any open documents first
                logger.info("Closing any open documents in Photoshop")
                try:
                    while ps.app.documents.length > 0:
                        ps.active_document.close(ps.SaveOptions.DoNotSaveChanges)
                except Exception as close_error:
                    logger.warning(f"Error closing documents: {close_error}")

                # Open the PSD file
                logger.info(f"Opening PSD file: {abs_psd_path}")
                os.startfile(abs_psd_path)

                # Wait for the document to be loaded
                max_wait_time = 30  # seconds
                wait_start = time.time()

                logger.info("Waiting for document to open...")
                while True:
                    try:
                        doc_count = ps.app.documents.length
                        if doc_count >= 1:
                            break
                        if time.time() - wait_start > max_wait_time:
                            raise TimeoutError(f"Timed out waiting for Photoshop to open {abs_psd_path}")
                        time.sleep(1)
                    except Exception as wait_error:
                        if time.time() - wait_start > max_wait_time:
                            raise TimeoutError(f"Timed out waiting for Photoshop to open {abs_psd_path}")
                        time.sleep(1)

                # Get the active document
                doc = ps.active_document
                logger.info(f"Successfully opened PSD file in Photoshop: {abs_psd_path}")

                # Process all text layers
                self._prepare_layers(ps, doc, template)

                # Save the template JSON
                output_dir = os.path.dirname(abs_output_path)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                with open(abs_output_path, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=4, ensure_ascii=False, sort_keys=True)
                logger.info(f"Exported template with {len(template)} keys to: {abs_output_path}")

                # Save the modified PSD file
                logger.info(f"Saving modified PSD file: {abs_psd_path}")
                doc.save()
                logger.info("PSD file saved successfully")

                # Close the document
                logger.info("Closing document")
                doc.close(ps.SaveOptions.DoNotSaveChanges)

            return True

        except ImportError as import_error:
            logger.error(f"Photoshop Python API not available: {import_error}")
            logger.error("This feature requires Photoshop and photoshop-python-api")
            return False

        except Exception as e:
            logger.error(f"Error preparing PSD file {psd_path}: {e}")
            return False

    def _prepare_layers(self, ps, doc, template):
        """
        Traverse all layers, rename text layers, and populate template.

        Args:
            ps: Photoshop session object.
            doc: Photoshop document object.
            template (dict): Template dictionary to populate.
        """
        logger.info("Processing all text layers for template preparation")

        # Process art layers
        try:
            for layer in doc.artLayers:
                self._process_text_layer_for_template(ps, layer, template)
        except Exception as art_error:
            logger.warning(f"Error processing art layers: {art_error}")

        # Process layer sets (groups)
        try:
            if hasattr(doc, 'layerSets'):
                for layer_set in doc.layerSets:
                    self._prepare_layer_set(ps, layer_set, template)
        except Exception as sets_error:
            logger.warning(f"Error processing layer sets: {sets_error}")

    def _prepare_layer_set(self, ps, layer_set, template):
        """
        Process a layer set (group) recursively for template preparation.

        Args:
            ps: Photoshop session object.
            layer_set: Photoshop layer set object.
            template (dict): Template dictionary to populate.
        """
        logger.info(f"Processing layer set: {layer_set.name if hasattr(layer_set, 'name') else 'unknown'}")

        # Process art layers in this group
        try:
            if hasattr(layer_set, 'artLayers'):
                for layer in layer_set.artLayers:
                    self._process_text_layer_for_template(ps, layer, template)
        except Exception as art_error:
            logger.warning(f"Error processing art layers in group: {art_error}")

        # Process nested layer groups
        try:
            if hasattr(layer_set, 'layerSets'):
                for nested_layer_set in layer_set.layerSets:
                    self._prepare_layer_set(ps, nested_layer_set, template)
        except Exception as sets_error:
            logger.warning(f"Error processing nested layer sets: {sets_error}")

    def _process_text_layer_for_template(self, ps, layer, template):
        """
        Process a single text layer: rename it and add to template.

        Args:
            ps: Photoshop session object.
            layer: Photoshop layer object.
            template (dict): Template dictionary to populate.
        """
        try:
            # Check if it's a text layer
            if hasattr(layer, 'kind') and layer.kind == ps.LayerKind.TextLayer:
                original_name = layer.name
                logger.info(f"Found text layer: {original_name}")

                # Get current text content
                text_content = layer.textItem.contents if hasattr(layer, 'textItem') else ""

                # Sanitize the layer name
                sanitized_name = self._sanitize_layer_name(original_name)

                # Create new layer name
                new_layer_name = f"lang_{sanitized_name}"

                # Rename the layer
                layer.name = new_layer_name
                logger.info(f"Renamed layer '{original_name}' to '{new_layer_name}'")

                # Add/update in template
                template[sanitized_name] = text_content
                logger.info(f"Added to template: {sanitized_name} = '{text_content}'")

        except Exception as layer_error:
            logger.warning(f"Error processing text layer: {layer_error}")
