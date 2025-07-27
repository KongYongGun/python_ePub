import sys
import os
import re
import chardet
from pathlib import Path
import zipfile
import uuid
from datetime import datetime

# PyQt6 Core
from PyQt6.QtCore import Qt, QSize, pyqtSignal

# PyQt6 GUI
from PyQt6.QtGui import QColor, QGuiApplication, QCursor, QFont, QFontDatabase

# PyQt6 Widgets
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QTableWidgetItem, QCheckBox, QPushButton, QGraphicsView
)

# UI
from ePub_ui import Ui_MainWindow  # pyuic6 -o ePub_ui.py 250714.ui

# DB
from ePub_db import initialize_database

# Loader (DB 관련 기능들)
from ePub_loader import (
    set_combobox_items_for_regex,
    load_chapter_regex_list,
    load_text_styles,
    load_punctuation_regex_list,
    set_combobox_items,
    apply_default_stylesheet,
    load_stylesheet_options,
    get_default_stylesheet,
)

# 워커들
from encoding_worker import EncodingDetectWorker
from chapter_finder import ChapterFinderWorker

from functools import partial
from PyQt6.QtGui import QPixmap, QImage, QGuiApplication, QAction
from PyQt6.QtWidgets import QMenu

# 메인 윈도우 클래스
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.tabWidget.setCurrentIndex(0)
        self.initialize_comboboxes()
        self.move_to_mouse_screen_and_resize()

        # 버튼 이벤트 연결
        self.ui.pushButton_SelectTextFile.clicked.connect(self.select_text_file)
        self.ui.pushButton_SelectCoverImage.clicked.connect(self.select_cover_image)
        self.ui.pushButton_DeleteCoverImage.clicked.connect(self.delete_cover_image)
        self.ui.pushButton_SelectChapterImage.clicked.connect(self.select_chapter_image)
        self.ui.pushButton_DeleteChapterImage.clicked.connect(self.delete_chapter_image)
        self.ui.pushButton_FindChapterList.clicked.connect(self.find_chapter_list)
        self.ui.pushButton_SelectBodyFont.clicked.connect(self.select_body_font)
        self.ui.pushButton_SelectChapterFont.clicked.connect(self.select_chapter_font)

        # ePub 변환 버튼 연결 (UI에 있는 경우)
        if hasattr(self.ui, 'pushButton_ConvertToEpub'):
            self.ui.pushButton_ConvertToEpub.clicked.connect(self.convert_to_epub)

        self.move_to_mouse_screen()
        self.encoding_worker = None

        self.initialize_theme_combobox()
        self.ui.comboBox_selectTheme.currentIndexChanged.connect(self.on_theme_selected)

        self.ui.label_CoverImage.installEventFilter(self)
        self.ui.label_ChapterImage.installEventFilter(self)

    def move_to_mouse_screen(self):
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos)
        if screen:
            geometry = screen.geometry()
            win_width = self.width()
            win_height = self.height()
            center_x = geometry.x() + (geometry.width() - win_width) // 2
            center_y = geometry.y() - 40 + (geometry.height() - win_height) // 2
            self.move(center_x, center_y)

    def move_to_mouse_screen_and_resize(self):
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos)
        if screen:
            geometry = screen.geometry()
            screen_width = geometry.width()
            screen_height = geometry.height()
            new_width = min(1380, screen_width)
            new_height = screen_height - 200
            self.resize(QSize(new_width, new_height))
            center_x = geometry.x() + (screen_width - new_width) // 2
            center_y = geometry.y() + (screen_height - new_height) // 2
            self.move(center_x, center_y)

    def select_text_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "텍스트 파일 선택", "", "Text Files (*.txt);;All Files (*)"
        )
        if not file_path:
            return
        self.encoding_worker = EncodingDetectWorker(file_path)
        self.encoding_worker.finished.connect(self.on_encoding_detected)
        self.encoding_worker.error.connect(self.on_encoding_error)
        self.encoding_worker.start()

    def select_cover_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "커버 이미지 선택", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All Files (*)"
        )
        if not file_path:
            return
        if self.load_image_to_label(file_path, self.ui.label_CoverImage):
            if hasattr(self.ui, 'label_CoverImagePath'):
                self.ui.label_CoverImagePath.setText(file_path)

    def delete_cover_image(self):
        reply = QMessageBox.question(
            self, "이미지 삭제 확인", "커버 이미지를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.ui.label_CoverImage.clear()
            self.ui.label_CoverImage.setText("Cover Image")
            self.ui.label_CoverImage.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if hasattr(self.ui, 'label_CoverImagePath'):
                self.ui.label_CoverImagePath.setText("---")

    def select_chapter_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "챕터 이미지 선택", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All Files (*)"
        )
        if not file_path:
            return
        if self.load_image_to_label(file_path, self.ui.label_ChapterImage):
            if hasattr(self.ui, 'label_ChapterImagePath'):
                self.ui.label_ChapterImagePath.setText(file_path)

    def delete_chapter_image(self):
        reply = QMessageBox.question(
            self, "이미지 삭제 확인", "챕터 이미지를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.ui.label_ChapterImage.clear()
            self.ui.label_ChapterImage.setText("Chapter Image")
            self.ui.label_ChapterImage.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if hasattr(self.ui, 'label_ChapterImagePath'):
                self.ui.label_ChapterImagePath.setText("---")

    def on_encoding_detected(self, file_path, encoding):
        if encoding.lower() != 'utf-8':
            try:
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                    decoded_text = raw_data.decode(encoding)
                utf8_path = self.insert_suffix_to_filename(file_path, "_utf8")
                with open(utf8_path, 'w', encoding='utf-8') as f:
                    f.write(decoded_text)
                file_path = utf8_path
                QMessageBox.information(self, "인코딩 변환", f"'{encoding}' → 'utf-8' 변환 완료:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "변환 실패", str(e))
                return
        self.ui.label_TextFilePath.setText(file_path)
        file_stem = Path(file_path).stem
        self.ui.lineEdit_Title.setText(file_stem)

    def on_encoding_error(self, message):
        QMessageBox.warning(self, "인코딩 오류", message)

    def insert_suffix_to_filename(self, path, suffix):
        base, ext = os.path.splitext(path)
        return f"{base}{suffix}{ext}"

    def initialize_comboboxes(self):
        regex_list = load_chapter_regex_list()
        for i in range(1, 10):
            combo = getattr(self.ui, f"comboBox_RegEx{i}")
            set_combobox_items_for_regex(combo, regex_list)

        bracket_styles = load_text_styles("bracket")
        for i in range(1, 8):
            combo = getattr(self.ui, f"comboBox_CharsStyle{i}")
            set_combobox_items(combo, bracket_styles)

        bracket_patterns = load_punctuation_regex_list()
        for i in range(1, 8):
            combo = getattr(self.ui, f"comboBox_Brackets{i}")
            set_combobox_items(combo, bracket_patterns)

        self.bind_regex_checkbox_events()

    # ePub 변환 관련 메서드들을 추가합니다
    def convert_to_epub(self):
        """설정된 정보를 기반으로 ePub 파일을 생성합니다."""
        if not self.validate_epub_requirements():
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "ePub 파일 저장", f"{self.ui.lineEdit_Title.text()}.epub",
            "ePub Files (*.epub);;All Files (*)"
        )

        if not save_path:
            return

        try:
            self.create_epub_file(save_path)
            QMessageBox.information(self, "변환 완료", f"ePub 파일이 성공적으로 생성되었습니다:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "변환 실패", f"ePub 변환 중 오류가 발생했습니다:\n{str(e)}")

    def validate_epub_requirements(self):
        """ePub 변환에 필요한 최소 요구사항을 검증합니다."""
        text_file_path = self.ui.label_TextFilePath.text().strip()
        if not text_file_path or not os.path.exists(text_file_path):
            QMessageBox.warning(self, "변환 실패", "텍스트 파일이 선택되지 않았거나 존재하지 않습니다.")
            return False

        title = self.ui.lineEdit_Title.text().strip()
        if not title:
            QMessageBox.warning(self, "변환 실패", "제목을 입력해주세요.")
            return False

        table = self.ui.tableWidget_ChapterList
        if table.rowCount() == 0:
            reply = QMessageBox.question(
                self, "챕터 없음",
                "챕터 리스트가 비어있습니다. 전체 텍스트를 하나의 챕터로 만들까요?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.No:
                return False

        return True

    def create_epub_file(self, save_path):
        """실제 ePub 파일을 생성합니다."""
        temp_dir = os.path.join(os.path.dirname(save_path), f"temp_epub_{uuid.uuid4().hex[:8]}")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            self.create_epub_structure(temp_dir)
            self.create_zip_epub(temp_dir, save_path)
        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def create_epub_structure(self, temp_dir):
        """ePub의 디렉토리 구조와 파일들을 생성합니다."""
        meta_inf_dir = os.path.join(temp_dir, "META-INF")
        oebps_dir = os.path.join(temp_dir, "OEBPS")
        images_dir = os.path.join(oebps_dir, "Images")
        styles_dir = os.path.join(oebps_dir, "Styles")

        for dir_path in [meta_inf_dir, oebps_dir, images_dir, styles_dir]:
            os.makedirs(dir_path, exist_ok=True)

        self.create_mimetype_file(temp_dir)
        self.create_container_xml(meta_inf_dir)
        self.create_content_opf(oebps_dir)
        self.create_toc_ncx(oebps_dir)
        self.create_stylesheet(styles_dir)
        self.create_chapter_files(oebps_dir)
        self.copy_images(images_dir)

    def create_mimetype_file(self, temp_dir):
        """ePub의 mimetype 파일을 생성합니다."""
        with open(os.path.join(temp_dir, "mimetype"), 'w', encoding='utf-8') as f:
            f.write("application/epub+zip")

    def create_container_xml(self, meta_inf_dir):
        """META-INF/container.xml 파일을 생성합니다."""
        container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''

        with open(os.path.join(meta_inf_dir, "container.xml"), 'w', encoding='utf-8') as f:
            f.write(container_xml)

    def create_content_opf(self, oebps_dir):
        """OEBPS/content.opf 파일을 생성합니다."""
        title = self.ui.lineEdit_Title.text().strip()
        author = getattr(self.ui, 'lineEdit_Author', None)
        author_text = author.text().strip() if author else "Unknown Author"

        chapters = self.get_chapter_info()

        manifest_items = ['<item id="stylesheet" href="Styles/style.css" media-type="text/css"/>']
        spine_items = []

        cover_image_path = getattr(self.ui, 'label_CoverImagePath', None)
        if cover_image_path and cover_image_path.text() != "---":
            manifest_items.append('<item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg"/>')

        for i, chapter in enumerate(chapters, 1):
            manifest_items.append(f'<item id="chapter{i}" href="chapter{i}.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.append(f'<itemref idref="chapter{i}"/>')

        content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="BookId">{uuid.uuid4()}</dc:identifier>
        <dc:title>{title}</dc:title>
        <dc:creator>{author_text}</dc:creator>
        <dc:language>ko</dc:language>
        <dc:date>{datetime.now().strftime('%Y-%m-%d')}</dc:date>
        <meta property="dcterms:modified">{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}</meta>
    </metadata>
    <manifest>
        <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
        {chr(10).join(manifest_items)}
    </manifest>
    <spine toc="toc">
        {chr(10).join(spine_items)}
    </spine>
</package>'''

        with open(os.path.join(oebps_dir, "content.opf"), 'w', encoding='utf-8') as f:
            f.write(content_opf)

    def create_toc_ncx(self, oebps_dir):
        """OEBPS/toc.ncx 파일을 생성합니다."""
        title = self.ui.lineEdit_Title.text().strip()
        chapters = self.get_chapter_info()

        nav_points = []
        for i, chapter in enumerate(chapters, 1):
            nav_points.append(f'''
        <navPoint id="chapter{i}" playOrder="{i}">
            <navLabel>
                <text>{chapter['title']}</text>
            </navLabel>
            <content src="chapter{i}.xhtml"/>
        </navPoint>''')

        toc_ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">
    <head>
        <meta name="dtb:uid" content="{uuid.uuid4()}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle>
        <text>{title}</text>
    </docTitle>
    <navMap>{''.join(nav_points)}
    </navMap>
</ncx>'''

        with open(os.path.join(oebps_dir, "toc.ncx"), 'w', encoding='utf-8') as f:
            f.write(toc_ncx)

    def create_stylesheet(self, styles_dir):
        """CSS 스타일시트를 생성합니다."""
        css_content = '''
body {
    font-family: serif;
    line-height: 1.6;
    margin: 0;
    padding: 1em;
}

h1, h2, h3 {
    margin-top: 2em;
    margin-bottom: 1em;
    font-weight: bold;
}

h1 {
    font-size: 1.5em;
    text-align: center;
}

p {
    margin-bottom: 1em;
    text-indent: 1em;
}

.chapter-title {
    text-align: center;
    font-size: 1.3em;
    font-weight: bold;
    margin: 2em 0;
}
'''

        with open(os.path.join(styles_dir, "style.css"), 'w', encoding='utf-8') as f:
            f.write(css_content)

    def get_chapter_info(self):
        """챕터 테이블에서 정보를 수집합니다."""
        chapters = []
        table = self.ui.tableWidget_ChapterList

        if table.rowCount() == 0:
            title = self.ui.lineEdit_Title.text().strip()
            chapters.append({
                'title': title,
                'content': self.get_full_text_content(),
                'order': 1
            })
        else:
            for row in range(table.rowCount()):
                checkbox = table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    order_item = table.item(row, 1)
                    title_item = table.item(row, 2)
                    line_item = table.item(row, 3)

                    if order_item and title_item and line_item:
                        chapters.append({
                            'title': title_item.text(),
                            'line_no': int(line_item.text()),
                            'order': int(order_item.text()) if order_item.text() else 999
                        })

            chapters.sort(key=lambda x: x['order'])
            self.extract_chapter_contents(chapters)

        return chapters

    def get_full_text_content(self):
        """전체 텍스트 내용을 반환합니다."""
        text_file_path = self.ui.label_TextFilePath.text().strip()
        try:
            with open(text_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            QMessageBox.critical(self, "파일 읽기 오류", f"텍스트 파일을 읽을 수 없습니다:\n{str(e)}")
            return ""

    def extract_chapter_contents(self, chapters):
        """각 챕터의 내용을 추출합니다."""
        text_file_path = self.ui.label_TextFilePath.text().strip()
        try:
            with open(text_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, chapter in enumerate(chapters):
                start_line = chapter['line_no'] - 1
                end_line = chapters[i + 1]['line_no'] - 1 if i + 1 < len(chapters) else len(lines)
                chapter_lines = lines[start_line:end_line]
                chapter['content'] = ''.join(chapter_lines).strip()

        except Exception as e:
            QMessageBox.critical(self, "챕터 추출 오류", f"챕터 내용을 추출할 수 없습니다:\n{str(e)}")

    def create_chapter_files(self, oebps_dir):
        """각 챕터의 XHTML 파일을 생성합니다."""
        chapters = self.get_chapter_info()

        for i, chapter in enumerate(chapters, 1):
            content = chapter['content'].replace('\n', '</p>\n<p>').strip()
            if content:
                content = f'<p>{content}</p>'

            chapter_xhtml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{chapter['title']}</title>
    <link rel="stylesheet" type="text/css" href="Styles/style.css"/>
</head>
<body>
    <div class="chapter-title">{chapter['title']}</div>
    {content}
</body>
</html>'''

            with open(os.path.join(oebps_dir, f"chapter{i}.xhtml"), 'w', encoding='utf-8') as f:
                f.write(chapter_xhtml)

    def copy_images(self, images_dir):
        """선택된 이미지들을 ePub에 복사합니다."""
        import shutil
        cover_image_path = getattr(self.ui, 'label_CoverImagePath', None)
        if cover_image_path and cover_image_path.text() != "---":
            src_path = cover_image_path.text()
            if os.path.exists(src_path):
                dst_path = os.path.join(images_dir, "cover.jpg")
                shutil.copy2(src_path, dst_path)

    def create_zip_epub(self, temp_dir, save_path):
        """ePub 구조를 ZIP 파일로 압축합니다."""
        with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as epub_zip:
            mimetype_path = os.path.join(temp_dir, "mimetype")
            epub_zip.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)

            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == "mimetype":
                        continue
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, temp_dir)
                    epub_zip.write(file_path, arc_path)

    # 기존 메서드들을 여기에 추가해야 합니다 (간략화를 위해 일부만 포함)
    def find_chapter_list(self):
        # 기존 구현 유지
        pass

    def bind_regex_checkbox_events(self):
        # 기존 구현 유지
        pass

    def select_body_font(self):
        # 기존 구현 유지
        pass

    def select_chapter_font(self):
        # 기존 구현 유지
        pass

    # 추가 메서드들...


if __name__ == "__main__":
    initialize_database()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
