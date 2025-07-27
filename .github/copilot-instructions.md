# Copilot Instructions for ePub Python Project

## Overview
This project is an ePub editor built using Python and PyQt6. It provides a graphical user interface (GUI) for managing ePub files, including features like:
- Selecting and deleting cover and chapter images.
- Detecting text encoding and converting files to UTF-8.
- Managing chapter lists using regular expressions.
- Applying themes and stylesheets.

The project integrates SQLite for database management and uses multithreading for background tasks like encoding detection and chapter finding.

## Key Files and Directories
- **`main.py`**: Contains the main application logic, including GUI event handling and image management.
- **`ePub_ui.py`**: Auto-generated PyQt6 UI file defining widgets and layouts.
- **`250714.ui`**: XML-based UI definition file created with Qt Designer.
- **`ePub_db.py`**: Handles database initialization and interactions.
- **`ePub_loader.py`**: Provides utility functions for loading data into the UI.
- **`encoding_worker.py`**: Implements a worker thread for detecting text encoding.
- **`chapter_finder.py`**: Implements a worker thread for finding chapters in text files.
- **`resource/`**: Contains static resources like images.

## Developer Workflows
### Running the Application
1. Ensure Python 3.10+ is installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

### Building the UI
If you modify the `250714.ui` file, regenerate the `ePub_ui.py` file using:
```bash
pyuic6 -o ePub_ui.py 250714.ui
```

### Database Initialization
The database is automatically initialized when the application starts. The `initialize_database` function in `ePub_db.py` handles this.

## Project-Specific Conventions
- **Event Handling**: All button click events are connected in the `MainWindow` constructor (`__init__` method).
- **Image Management**: Images are loaded into QLabel widgets using the `load_image_to_label` method. Deletion resets the QLabel to a default state.
- **Regular Expressions**: Regular expressions for chapter detection are managed via comboboxes and checkboxes in the UI.
- **Multithreading**: Long-running tasks like encoding detection and chapter finding are offloaded to worker threads (`EncodingDetectWorker` and `ChapterFinderWorker`).

## Patterns and Examples
### Adding a New Button
1. Add the button in `250714.ui` using Qt Designer.
2. Regenerate `ePub_ui.py`.
3. Connect the button to a method in `main.py`:
   ```python
   self.ui.pushButton_NewFeature.clicked.connect(self.new_feature_method)
   ```
4. Implement the method in `MainWindow`.

### Loading an Image
Use the `load_image_to_label` method:
```python
if self.load_image_to_label(file_path, self.ui.label_CoverImage):
    self.ui.label_CoverImagePath.setText(file_path)
```

### Deleting an Image
Use the `delete_cover_image` or `delete_chapter_image` methods as templates. Ensure the QLabel is cleared and reset to its default state.

## External Dependencies
- **PyQt6**: For GUI development.
- **SQLite**: For database management.
- **chardet**: For text encoding detection.

## Integration Points
- **Database**: Interact with the SQLite database using functions in `ePub_db.py`.
- **UI**: Modify the UI using Qt Designer and regenerate `ePub_ui.py`.
- **Workers**: Implement background tasks by subclassing `QThread` (see `encoding_worker.py` and `chapter_finder.py`).

## Notes
- Follow the existing patterns for event handling and worker thread management.
- Test new features thoroughly to ensure they integrate seamlessly with the existing functionality.
