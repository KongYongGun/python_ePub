"""
ePub 텍스트 변환기 - Python 기반 텍스트 파일을 ePub 파일로 변환하는 GUI 프로그램

프로젝트 개요:
- 목적: 텍스트 파일을 완전한 ePub 형식으로 변환
- 주요 기능:
  * 텍스트 파일 인코딩 자동 감지 및 UTF-8 변환
  * 정규식을 통한 챕터 자동 검출
  * 커버 이미지 및 챕터별 삽화 지원
  * 폰트 설정 및 호환성 검사
  * 텍스트 스타일 및 정렬 옵션
  * 완전한 ePub 3.0 표준 지원 (목차, 메타데이터, 스타일시트 포함)

사용 기술:
- Python 3.10+
- PyQt6 (GUI 프레임워크)
- SQLite (설정 및 데이터 저장)
- chardet (텍스트 인코딩 감지)
- zipfile (ePub 패키징)

작성자: ePub Python Team
최종 수정일: 2025-07-28
"""

import sys
import os
import re
import chardet
import urllib.parse
import webbrowser
import tempfile
import shutil
import logging
from pathlib import Path
import zipfile
import uuid
from datetime import datetime
from functools import partial

# PyQt6 Core
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QEvent

# PyQt6 GUI
from PyQt6.QtGui import QColor, QGuiApplication, QCursor, QFont, QFontDatabase, QKeySequence, QShortcut

# PyQt6 Widgets
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QTableWidgetItem, QCheckBox, QPushButton, QGraphicsView, QColorDialog
)

# UI
from ePub_ui import Ui_MainWindow  # pyuic6 -o ePub_ui.py 250714.ui

# DB
from ePub_db import initialize_database, update_punctuation_regex_data

# Loader (DB 관련 기능들)
from ePub_loader import (
    set_combobox_items_for_regex,
    load_chapter_regex_list,
    load_text_styles,
    load_punctuation_regex_list,
    set_combobox_items,
)

# 워커들
from encoding_worker import EncodingDetectWorker
from chapter_finder import ChapterFinderWorker
from font_checker_worker import FontCheckerWorker

# 스타일 매니저 (선택적 사용)
from style_manager import StyleManager

from functools import partial
from PyQt6.QtGui import QPixmap, QImage, QGuiApplication, QAction
from PyQt6.QtWidgets import QMenu, QProgressDialog
from PyQt6.QtWidgets import QMenu

# 메인 윈도우 클래스
class MainWindow(QMainWindow):
    """
    ePub 변환기의 메인 윈도우 클래스

    주요 기능:
    - GUI 초기화 및 이벤트 처리
    - 텍스트 파일 로딩 및 인코딩 처리
    - 챕터 검색 및 ePub 변환
    - 폰트 및 이미지 관리
    """

    def __init__(self):
        """
        메인 윈도우 초기화

        GUI 요소 설정, 이벤트 연결, 로깅 설정 등을 수행합니다.
        """
        super().__init__()

        # 로깅 설정
        self._setup_logging()

        # 데이터베이스 초기화 및 괄호 정규식 업데이트
        try:
            success, message = update_punctuation_regex_data()
            if success:
                logging.info(f"괄호 정규식 데이터 업데이트 완료: {message}")
            else:
                logging.warning(f"괄호 정규식 데이터 업데이트 실패: {message}")
        except Exception as e:
            logging.error(f"괄호 정규식 데이터 업데이트 중 오류: {e}")

        # UI 초기화
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.tabWidget.setCurrentIndex(0)
        self.initialize_comboboxes()
        self.move_to_mouse_screen_and_resize()

        # 정렬 콤보박스 초기화 확인
        logging.debug("정렬 콤보박스 초기화 완료")
        self.print_alignment_settings()

        # 버튼 이벤트 연결
        self._connect_button_events()

        # 초기 설정
        self.move_to_mouse_screen()
        self._initialize_workers()

        # 클립보드 붙여넣기 단축키 설정
        self.setup_clipboard_shortcuts()

        # 이벤트 필터 설정
        self.ui.label_CoverImage.installEventFilter(self)
        self.ui.label_ChapterImage.installEventFilter(self)

    def _setup_logging(self):
        """
        로깅 시스템 초기화

        DEBUG 레벨까지 로깅하며, 콘솔과 파일 양쪽에 출력합니다.
        """
        try:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                handlers=[
                    logging.FileHandler('epub_converter.log', encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            logging.info("ePub 변환기 시작")
        except Exception as e:
            print(f"로깅 설정 실패: {e}")

    def _connect_button_events(self):
        """
        모든 버튼 이벤트를 연결합니다.
        """
        try:
            # 파일 선택 버튼들
            self.ui.pushButton_SelectTextFile.clicked.connect(self.select_text_file)
            self.ui.pushButton_SelectCoverImage.clicked.connect(self.select_cover_image)
            self.ui.pushButton_DeleteCoverImage.clicked.connect(self.delete_cover_image)
            self.ui.pushButton_SelectChapterImage.clicked.connect(self.select_chapter_image)
            self.ui.pushButton_DeleteChapterImage.clicked.connect(self.delete_chapter_image)
            self.ui.pushButton_FindChapterList.clicked.connect(self.find_chapter_list)
            self.ui.pushButton_SelectBodyFont.clicked.connect(self.select_body_font)
            self.ui.pushButton_SelectChapterFont.clicked.connect(self.select_chapter_font)
            self.ui.pushButton_setFontFolder.clicked.connect(self.set_font_folder)

            # ePub 변환 버튼
            self.ui.pushButton_ePubGenerate.clicked.connect(self.convert_to_epub)

            logging.debug("버튼 이벤트 연결 완료")
        except Exception as e:
            logging.error(f"버튼 이벤트 연결 실패: {e}")

    def _initialize_workers(self):
        """
        백그라운드 워커 객체들을 초기화합니다.
        """
        self.encoding_worker = None
        self.font_checker_worker = None
        self.font_progress_dialog = None
        self.chapter_finder_worker = None
        self.chapter_progress_dialog = None
        logging.debug("워커 객체 초기화 완료")

    def setup_clipboard_shortcuts(self):
        """클립보드 붙여넣기 키보드 단축키를 설정합니다."""
        # 커버 이미지 붙여넣기 (Ctrl+V when cover image has focus)
        cover_paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self.ui.label_CoverImage)
        cover_paste_shortcut.activated.connect(self.paste_cover_image_from_clipboard)

        # 챕터 이미지 붙여넣기 (Ctrl+V when chapter image has focus)
        chapter_paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self.ui.label_ChapterImage)
        chapter_paste_shortcut.activated.connect(self.paste_chapter_image_from_clipboard)

    def paste_cover_image_from_clipboard(self):
        """클립보드에서 커버 이미지를 붙여넣습니다."""
        clipboard = QGuiApplication.clipboard()
        pixmap = clipboard.pixmap()

        if not pixmap.isNull():
            try:
                # 임시 파일로 저장
                temp_dir = tempfile.gettempdir()
                temp_file = os.path.join(temp_dir, f"cover_clipboard_{uuid.uuid4().hex[:8]}.png")

                if pixmap.save(temp_file, "PNG"):
                    if self.load_image_to_label(temp_file, self.ui.label_CoverImage):
                        if hasattr(self.ui, 'label_CoverImagePath'):
                            self.ui.label_CoverImagePath.setText(temp_file)
                        QMessageBox.information(self, "붙여넣기 완료", "클립보드에서 커버 이미지를 붙여넣었습니다.")
                    else:
                        QMessageBox.warning(self, "붙여넣기 실패", "이미지를 로드할 수 없습니다.")
                else:
                    QMessageBox.warning(self, "저장 실패", "임시 파일로 저장할 수 없습니다.")
            except Exception as e:
                QMessageBox.warning(self, "붙여넣기 실패", f"클립보드 이미지 처리 중 오류가 발생했습니다:\n{str(e)}")
        else:
            QMessageBox.information(self, "클립보드 비어있음", "클립보드에 이미지가 없습니다.")

    def paste_chapter_image_from_clipboard(self):
        """클립보드에서 챕터 이미지를 붙여넣습니다."""
        clipboard = QGuiApplication.clipboard()
        pixmap = clipboard.pixmap()

        if not pixmap.isNull():
            try:
                # 임시 파일로 저장
                temp_dir = tempfile.gettempdir()
                temp_file = os.path.join(temp_dir, f"chapter_clipboard_{uuid.uuid4().hex[:8]}.png")

                if pixmap.save(temp_file, "PNG"):
                    if self.load_image_to_label(temp_file, self.ui.label_ChapterImage):
                        if hasattr(self.ui, 'label_ChapterImagePath'):
                            self.ui.label_ChapterImagePath.setText(temp_file)
                        QMessageBox.information(self, "붙여넣기 완료", "클립보드에서 챕터 이미지를 붙여넣었습니다.")
                    else:
                        QMessageBox.warning(self, "붙여넣기 실패", "이미지를 로드할 수 없습니다.")
                else:
                    QMessageBox.warning(self, "저장 실패", "임시 파일로 저장할 수 없습니다.")
            except Exception as e:
                QMessageBox.warning(self, "붙여넣기 실패", f"클립보드 이미지 처리 중 오류가 발생했습니다:\n{str(e)}")
        else:
            QMessageBox.information(self, "클립보드 비어있음", "클립보드에 이미지가 없습니다.")

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

            # 10:9 비율로 창 크기 계산
            # 화면 크기에 맞춰 최적 크기 결정
            available_height = screen_height - 200  # 작업표시줄 등을 위한 여유 공간

            # 높이를 기준으로 10:9 비율 계산
            target_height = available_height
            target_width = int(target_height * 10 / 9)

            # 너비가 화면을 벗어나면 너비를 기준으로 다시 계산
            if target_width > screen_width - 100:  # 좌우 여유 공간
                target_width = screen_width - 100
                target_height = int(target_width * 9 / 10)

            # 최소/최대 크기 제한
            min_width = 800
            min_height = int(min_width * 9 / 10)  # 720

            new_width = max(min_width, min(target_width, 1600))
            new_height = max(min_height, min(target_height, 1440))

            # 정확한 10:9 비율 유지
            if new_width / new_height > 10 / 9:
                new_width = int(new_height * 10 / 9)
            else:
                new_height = int(new_width * 9 / 10)

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

        bracket_patterns = load_punctuation_regex_list()
        for i in range(1, 8):
            combo = getattr(self.ui, f"comboBox_Brackets{i}")
            # 괄호 패턴 설정: (id, pattern) 형태로 저장
            combo.clear()
            for pattern_id, name, pattern in bracket_patterns:
                combo.addItem(name, (pattern_id, pattern))

        # 정렬 옵션 초기화
        self.initialize_alignment_comboboxes()

        # 폰트 굵기 옵션 초기화
        self.initialize_weight_comboboxes()

        # 스타일 옵션 초기화
        self.initialize_style_comboboxes()

        # 색상 LineEdit 초기화
        self.initialize_color_lineedits()

        # 문자 스타일 기능 초기화
        self.initialize_character_styling()

        # 괄호 스타일 기능 초기화
        self.initialize_bracket_styling()

        # 챕터 스타일 기능 초기화
        self.initialize_chapter_styling()

        # ePub 분할 기능 초기화
        self.initialize_epub_divide()

        # 폰트 콤보박스 초기화
        self.initialize_font_comboboxes()

        self.bind_regex_checkbox_events()

    def initialize_alignment_comboboxes(self):
        """정렬 콤보박스들을 초기화합니다."""
        alignment_options = [
            ("왼쪽 정렬", "Left"),
            ("가운데 정렬", "Center"),
            ("오른쪽 정렬", "Right"),
            ("들여쓰기1", "Indent1"),
            ("들여쓰기2", "Indent2"),
            ("들여쓰기3", "Indent3")
        ]

        # comboBox_CharsAlign1~7 초기화
        for i in range(1, 8):
            combo_name = f'comboBox_CharsAlign{i}'
            if hasattr(self.ui, combo_name):
                combo = getattr(self.ui, combo_name)
                combo.clear()
                for display_text, code_value in alignment_options:
                    combo.addItem(display_text, code_value)
                # 변경 시그널 연결
                combo.currentTextChanged.connect(
                    lambda _, name=combo_name: self.on_alignment_changed(name)
                )

        # comboBox_BracketsAlign1~7 초기화
        for i in range(1, 8):
            combo_name = f'comboBox_BracketsAlign{i}'
            if hasattr(self.ui, combo_name):
                combo = getattr(self.ui, combo_name)
                combo.clear()
                for display_text, code_value in alignment_options:
                    combo.addItem(display_text, code_value)
                # 변경 시그널 연결
                combo.currentTextChanged.connect(
                    lambda _, name=combo_name: self.on_alignment_changed(name)
                )

    def on_alignment_changed(self, combo_name):
        """정렬 설정이 변경되었을 때 호출됩니다."""
        if hasattr(self.ui, combo_name):
            combo = getattr(self.ui, combo_name)
            display_text = combo.currentText()
            code_value = combo.currentData()
            logging.info(f"{combo_name} 정렬 변경: '{display_text}' -> 코드: '{code_value}'")

    def initialize_weight_comboboxes(self):
        """폰트 굵기 콤보박스들을 초기화합니다."""
        weight_options = [
            ("일반", "Normal"),
            ("굵게", "Bold"),
            ("직접입력", "Number")
        ]

        # comboBox_CharsWeight1~7 초기화
        for i in range(1, 8):
            combo_name = f'comboBox_CharsWeight{i}'
            if hasattr(self.ui, combo_name):
                combo = getattr(self.ui, combo_name)
                combo.clear()
                for display_text, code_value in weight_options:
                    combo.addItem(display_text, code_value)
                # 변경 시그널 연결
                combo.currentTextChanged.connect(
                    lambda _, name=combo_name: self.on_weight_changed(name)
                )

        # comboBox_BracketsWeight1~7 초기화
        for i in range(1, 8):
            combo_name = f'comboBox_BracketsWeight{i}'
            if hasattr(self.ui, combo_name):
                combo = getattr(self.ui, combo_name)
                combo.clear()
                for display_text, code_value in weight_options:
                    combo.addItem(display_text, code_value)
                # 변경 시그널 연결
                combo.currentTextChanged.connect(
                    lambda _, name=combo_name: self.on_weight_changed(name)
                )

    def on_weight_changed(self, combo_name):
        """폰트 굵기 설정이 변경되었을 때 호출됩니다."""
        if hasattr(self.ui, combo_name):
            combo = getattr(self.ui, combo_name)
            display_text = combo.currentText()
            code_value = combo.currentData()
            logging.info(f"{combo_name} 굵기 변경: '{display_text}' -> 코드: '{code_value}'")

    def initialize_style_comboboxes(self):
        """스타일 콤보박스들을 초기화합니다."""
        style_options = [
            ("일반", "Normal"),
            ("기울이기", "Oblique")
        ]

        # comboBox_CharsStyle1~7 초기화
        for i in range(1, 8):
            combo_name = f'comboBox_CharsStyle{i}'
            if hasattr(self.ui, combo_name):
                combo = getattr(self.ui, combo_name)
                combo.clear()
                for display_text, code_value in style_options:
                    combo.addItem(display_text, code_value)
                # 변경 시그널 연결
                combo.currentTextChanged.connect(
                    lambda _, name=combo_name: self.on_style_changed(name)
                )

        # comboBox_BracketsStyle1~7 초기화
        for i in range(1, 8):
            combo_name = f'comboBox_BracketsStyle{i}'
            if hasattr(self.ui, combo_name):
                combo = getattr(self.ui, combo_name)
                combo.clear()
                for display_text, code_value in style_options:
                    combo.addItem(display_text, code_value)
                # 변경 시그널 연결
                combo.currentTextChanged.connect(
                    lambda _, name=combo_name: self.on_style_changed(name)
                )

    def on_style_changed(self, combo_name):
        """스타일 설정이 변경되었을 때 호출됩니다."""
        if hasattr(self.ui, combo_name):
            combo = getattr(self.ui, combo_name)
            display_text = combo.currentText()
            code_value = combo.currentData()
            logging.info(f"{combo_name} 스타일 변경: '{display_text}' -> 코드: '{code_value}'")

    def initialize_color_lineedits(self):
        """색상 LineEdit들을 초기화하고 클릭 이벤트를 연결합니다."""
        # lineEdit_CharsColor1~7 초기화
        for i in range(1, 8):
            lineedit_name = f'lineEdit_CharsColor{i}'
            if hasattr(self.ui, lineedit_name):
                lineedit = getattr(self.ui, lineedit_name)
                # 기본 색상 설정 (흰색)
                self.set_color_to_lineedit(lineedit, "#ffffff")
                # 클릭 이벤트 연결
                lineedit.mousePressEvent = lambda event, name=lineedit_name: self.on_color_lineedit_clicked(name)
                # 읽기 전용으로 설정
                lineedit.setReadOnly(True)
                lineedit.setCursor(Qt.CursorShape.PointingHandCursor)

        # lineEdit_BracketsColor1~7 초기화
        for i in range(1, 8):
            lineedit_name = f'lineEdit_BracketsColor{i}'
            if hasattr(self.ui, lineedit_name):
                lineedit = getattr(self.ui, lineedit_name)
                # 기본 색상 설정 (흰색)
                self.set_color_to_lineedit(lineedit, "#ffffff")
                # 클릭 이벤트 연결
                lineedit.mousePressEvent = lambda event, name=lineedit_name: self.on_color_lineedit_clicked(name)
                # 읽기 전용으로 설정
                lineedit.setReadOnly(True)
                lineedit.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_color_to_lineedit(self, lineedit, color_hex):
        """LineEdit에 색상을 설정합니다."""
        lineedit.setText(color_hex)
        # 배경색에 따라 텍스트 색상 자동 조정
        if color_hex.upper() in ["#FFFFFF", "#FFFFFE", "#FFFEFF", "#FEFFFF"] or self._is_light_color(color_hex):
            text_color = "black"
        else:
            text_color = "white"
        lineedit.setStyleSheet(f"background-color: {color_hex}; color: {text_color}; font-weight: bold; font-size: 11pt; border: 2px solid #ccc;")

    def _is_light_color(self, color_hex):
        """색상이 밝은 색인지 판단합니다."""
        try:
            # #RRGGBB 형식에서 RGB 값 추출
            r = int(color_hex[1:3], 16)
            g = int(color_hex[3:5], 16)
            b = int(color_hex[5:7], 16)
            # 밝기 계산 (0.299*R + 0.587*G + 0.114*B)
            brightness = (r * 0.299 + g * 0.587 + b * 0.114)
            return brightness > 186  # 186보다 크면 밝은 색으로 판단
        except:
            return False

    def on_color_lineedit_clicked(self, lineedit_name):
        """색상 LineEdit가 클릭되었을 때 색상 선택 다이얼로그를 엽니다."""
        if hasattr(self.ui, lineedit_name):
            lineedit = getattr(self.ui, lineedit_name)
            current_color = lineedit.text()

            # QColorDialog로 색상 선택
            color = QColorDialog.getColor(QColor(current_color), self, f"{lineedit_name} 색상 선택")

            if color.isValid():
                color_hex = color.name()  # #rrggbb 형식으로 반환 (소문자)
                self.set_color_to_lineedit(lineedit, color_hex)
                logging.info(f"{lineedit_name} 색상 변경: {color_hex}")

    def get_alignment_setting(self, combobox_name):
        """정렬 콤보박스에서 현재 선택된 값(코드)을 반환합니다."""
        if hasattr(self.ui, combobox_name):
            combo = getattr(self.ui, combobox_name)
            return combo.currentData()
        return None

    def get_chars_alignment(self):
        """문자 정렬 설정을 반환합니다."""
        return self.get_alignment_setting('comboBox_CharsAlign1')

    def get_brackets_alignment(self):
        """괄호 정렬 설정을 반환합니다."""
        return self.get_alignment_setting('comboBox_BracketsAlign1')

    def get_chars_alignment_by_index(self, index):
        """특정 인덱스의 문자 정렬 설정을 반환합니다."""
        return self.get_alignment_setting(f'comboBox_CharsAlign{index}')

    def get_brackets_alignment_by_index(self, index):
        """특정 인덱스의 괄호 정렬 설정을 반환합니다."""
        return self.get_alignment_setting(f'comboBox_BracketsAlign{index}')

    def get_all_chars_alignments(self):
        """모든 문자 정렬 설정을 딕셔너리로 반환합니다."""
        alignments = {}
        for i in range(1, 8):
            combo_name = f'comboBox_CharsAlign{i}'
            if hasattr(self.ui, combo_name):
                alignments[i] = self.get_alignment_setting(combo_name)
        return alignments

    def get_all_brackets_alignments(self):
        """모든 괄호 정렬 설정을 딕셔너리로 반환합니다."""
        alignments = {}
        for i in range(1, 8):
            combo_name = f'comboBox_BracketsAlign{i}'
            if hasattr(self.ui, combo_name):
                alignments[i] = self.get_alignment_setting(combo_name)
        return alignments

    def get_weight_setting(self, combobox_name):
        """폰트 굵기 콤보박스에서 현재 선택된 값(코드)을 반환합니다."""
        if hasattr(self.ui, combobox_name):
            combo = getattr(self.ui, combobox_name)
            return combo.currentData()
        return None

    def get_chars_weight(self):
        """문자 굵기 설정을 반환합니다."""
        return self.get_weight_setting('comboBox_CharsWeight1')

    def get_brackets_weight(self):
        """괄호 굵기 설정을 반환합니다."""
        return self.get_weight_setting('comboBox_BracketsWeight1')

    def get_chars_weight_by_index(self, index):
        """특정 인덱스의 문자 굵기 설정을 반환합니다."""
        return self.get_weight_setting(f'comboBox_CharsWeight{index}')

    def get_brackets_weight_by_index(self, index):
        """특정 인덱스의 괄호 굵기 설정을 반환합니다."""
        return self.get_weight_setting(f'comboBox_BracketsWeight{index}')

    def get_all_chars_weights(self):
        """모든 문자 굵기 설정을 딕셔너리로 반환합니다."""
        weights = {}
        for i in range(1, 8):
            combo_name = f'comboBox_CharsWeight{i}'
            if hasattr(self.ui, combo_name):
                weights[i] = self.get_weight_setting(combo_name)
        return weights

    def get_all_brackets_weights(self):
        """모든 괄호 굵기 설정을 딕셔너리로 반환합니다."""
        weights = {}
        for i in range(1, 8):
            combo_name = f'comboBox_BracketsWeight{i}'
            if hasattr(self.ui, combo_name):
                weights[i] = self.get_weight_setting(combo_name)
        return weights

    def get_style_setting(self, combobox_name):
        """스타일 콤보박스에서 현재 선택된 값(코드)을 반환합니다."""
        if hasattr(self.ui, combobox_name):
            combo = getattr(self.ui, combobox_name)
            return combo.currentData()
        return None

    def get_chars_style(self):
        """문자 스타일 설정을 반환합니다."""
        return self.get_style_setting('comboBox_CharsStyle1')

    def get_brackets_style(self):
        """괄호 스타일 설정을 반환합니다."""
        return self.get_style_setting('comboBox_BracketsStyle1')

    def get_chars_style_by_index(self, index):
        """특정 인덱스의 문자 스타일 설정을 반환합니다."""
        return self.get_style_setting(f'comboBox_CharsStyle{index}')

    def get_brackets_style_by_index(self, index):
        """특정 인덱스의 괄호 스타일 설정을 반환합니다."""
        return self.get_style_setting(f'comboBox_BracketsStyle{index}')

    def get_all_chars_styles(self):
        """모든 문자 스타일 설정을 딕셔너리로 반환합니다."""
        styles = {}
        for i in range(1, 8):
            combo_name = f'comboBox_CharsStyle{i}'
            if hasattr(self.ui, combo_name):
                styles[i] = self.get_style_setting(combo_name)
        return styles

    def get_all_brackets_styles(self):
        """모든 괄호 스타일 설정을 딕셔너리로 반환합니다."""
        styles = {}
        for i in range(1, 8):
            combo_name = f'comboBox_BracketsStyle{i}'
            if hasattr(self.ui, combo_name):
                styles[i] = self.get_style_setting(combo_name)
        return styles

    def get_color_setting(self, lineedit_name):
        """색상 LineEdit에서 현재 설정된 색상을 반환합니다."""
        if hasattr(self.ui, lineedit_name):
            lineedit = getattr(self.ui, lineedit_name)
            return lineedit.text()
        return None

    def get_chars_color(self):
        """문자 색상 설정을 반환합니다."""
        return self.get_color_setting('lineEdit_CharsColor1')

    def get_brackets_color(self):
        """괄호 색상 설정을 반환합니다."""
        return self.get_color_setting('lineEdit_BracketsColor1')

    def get_chars_color_by_index(self, index):
        """특정 인덱스의 문자 색상 설정을 반환합니다."""
        return self.get_color_setting(f'lineEdit_CharsColor{index}')

    def get_brackets_color_by_index(self, index):
        """특정 인덱스의 괄호 색상 설정을 반환합니다."""
        return self.get_color_setting(f'lineEdit_BracketsColor{index}')

    def get_all_chars_colors(self):
        """모든 문자 색상 설정을 딕셔너리로 반환합니다."""
        colors = {}
        for i in range(1, 8):
            lineedit_name = f'lineEdit_CharsColor{i}'
            if hasattr(self.ui, lineedit_name):
                colors[i] = self.get_color_setting(lineedit_name)
        return colors

    def get_all_brackets_colors(self):
        """모든 괄호 색상 설정을 딕셔너리로 반환합니다."""
        colors = {}
        for i in range(1, 8):
            lineedit_name = f'lineEdit_BracketsColor{i}'
            if hasattr(self.ui, lineedit_name):
                colors[i] = self.get_color_setting(lineedit_name)
        return colors

    def print_alignment_settings(self):
        """
        현재 정렬, 굵기, 스타일, 색상 설정들을 디버그 로그로 출력합니다.

        디버그 모드에서만 활성화되며, 모든 UI 설정값을 로깅합니다.
        """
        try:
            logging.debug("=== 현재 정렬, 굵기, 스타일, 색상 설정 ===")

            # 모든 문자 정렬 설정 출력
            chars_alignments = self.get_all_chars_alignments()
            logging.debug("문자 정렬 설정:")
            for i, alignment in chars_alignments.items():
                combo_name = f'comboBox_CharsAlign{i}'
                if hasattr(self.ui, combo_name):
                    combo = getattr(self.ui, combo_name)
                    display_text = combo.currentText()
                    logging.debug(f"  CharsAlign{i}: '{display_text}' -> 코드: '{alignment}'")

            # 모든 괄호 정렬 설정 출력
            brackets_alignments = self.get_all_brackets_alignments()
            logging.debug("괄호 정렬 설정:")
            for i, alignment in brackets_alignments.items():
                combo_name = f'comboBox_BracketsAlign{i}'
                if hasattr(self.ui, combo_name):
                    combo = getattr(self.ui, combo_name)
                    display_text = combo.currentText()
                    logging.debug(f"  BracketsAlign{i}: '{display_text}' -> 코드: '{alignment}'")

            # 모든 문자 굵기 설정 출력
            chars_weights = self.get_all_chars_weights()
            logging.debug("문자 굵기 설정:")
            for i, weight in chars_weights.items():
                combo_name = f'comboBox_CharsWeight{i}'
                if hasattr(self.ui, combo_name):
                    combo = getattr(self.ui, combo_name)
                    display_text = combo.currentText()
                    logging.debug(f"  CharsWeight{i}: '{display_text}' -> 코드: '{weight}'")

            # 모든 괄호 굵기 설정 출력
            brackets_weights = self.get_all_brackets_weights()
            logging.debug("괄호 굵기 설정:")
            for i, weight in brackets_weights.items():
                combo_name = f'comboBox_BracketsWeight{i}'
                if hasattr(self.ui, combo_name):
                    combo = getattr(self.ui, combo_name)
                    display_text = combo.currentText()
                    logging.debug(f"  BracketsWeight{i}: '{display_text}' -> 코드: '{weight}'")

            # 모든 문자 스타일 설정 출력
            chars_styles = self.get_all_chars_styles()
            logging.debug("문자 스타일 설정:")
            for i, style in chars_styles.items():
                combo_name = f'comboBox_CharsStyle{i}'
                if hasattr(self.ui, combo_name):
                    combo = getattr(self.ui, combo_name)
                    display_text = combo.currentText()
                    logging.debug(f"  CharsStyle{i}: '{display_text}' -> 코드: '{style}'")

            # 모든 괄호 스타일 설정 출력
            brackets_styles = self.get_all_brackets_styles()
            logging.debug("괄호 스타일 설정:")
            for i, style in brackets_styles.items():
                combo_name = f'comboBox_BracketsStyle{i}'
                if hasattr(self.ui, combo_name):
                    combo = getattr(self.ui, combo_name)
                    display_text = combo.currentText()
                    logging.debug(f"  BracketsStyle{i}: '{display_text}' -> 코드: '{style}'")

            # 모든 문자 색상 설정 출력
            chars_colors = self.get_all_chars_colors()
            logging.debug("문자 색상 설정:")
            for i, color in chars_colors.items():
                lineedit_name = f'lineEdit_CharsColor{i}'
                if hasattr(self.ui, lineedit_name):
                    logging.debug(f"  CharsColor{i}: '{color}'")

            # 모든 괄호 색상 설정 출력
            brackets_colors = self.get_all_brackets_colors()
            logging.debug("괄호 색상 설정:")
            for i, color in brackets_colors.items():
                lineedit_name = f'lineEdit_BracketsColor{i}'
                if hasattr(self.ui, lineedit_name):
                    logging.debug(f"  BracketsColor{i}: '{color}'")

        except Exception as e:
            logging.error(f"설정값 출력 중 오류 발생: {e}")

    def apply_text_alignment(self, text, alignment_code):
        """
        텍스트에 정렬을 적용하는 예시 메서드
        실제 ePub 생성 시 사용할 수 있습니다.
        """
        if alignment_code == "Left":
            return f'<p style="text-align: left;">{text}</p>'
        elif alignment_code == "Center":
            return f'<p style="text-align: center;">{text}</p>'
        elif alignment_code == "Right":
            return f'<p style="text-align: right;">{text}</p>'
        elif alignment_code == "Indent1":
            return f'<p style="text-indent: 2em;">{text}</p>'
        elif alignment_code == "Indent2":
            return f'<p style="text-indent: 4em;">{text}</p>'
        elif alignment_code == "Indent3":
            return f'<p style="text-indent: 6em;">{text}</p>'
        else:
            return f'<p>{text}</p>'

    def apply_font_weight(self, text, weight_code):
        """
        텍스트에 폰트 굵기를 적용하는 예시 메서드
        실제 ePub 생성 시 사용할 수 있습니다.
        """
        if weight_code == "Normal":
            return f'<span style="font-weight: normal;">{text}</span>'
        elif weight_code == "Bold":
            return f'<span style="font-weight: bold;">{text}</span>'
        elif weight_code == "Number":
            # 직접입력의 경우 사용자가 별도로 숫자 값을 입력해야 함
            # 예시로 600 사용 (보통 bold보다 약간 얇음)
            return f'<span style="font-weight: 600;">{text}</span>'
        else:
            return text

    def apply_font_style(self, text, style_code):
        """
        텍스트에 폰트 스타일을 적용하는 예시 메서드
        실제 ePub 생성 시 사용할 수 있습니다.
        """
        if style_code == "Normal":
            return f'<span style="font-style: normal;">{text}</span>'
        elif style_code == "Oblique":
            return f'<span style="font-style: oblique;">{text}</span>'
        else:
            return text

    def apply_font_color(self, text, color_hex):
        """
        텍스트에 폰트 색상을 적용하는 예시 메서드
        실제 ePub 생성 시 사용할 수 있습니다.
        """
        if color_hex and color_hex != "#000000":  # 기본 검은색이 아닌 경우만 적용
            return f'<span style="color: {color_hex};">{text}</span>'
        else:
            return text

    def get_formatted_text_with_weight(self, text, use_chars_weight=True):
        """
        현재 선택된 굵기 설정을 사용하여 텍스트를 포맷팅합니다.
        """
        if use_chars_weight:
            weight_code = self.get_chars_weight()
            weight_type = "문자"
        else:
            weight_code = self.get_brackets_weight()
            weight_type = "괄호"

        if weight_code:
            formatted = self.apply_font_weight(text, weight_code)
            print(f"[INFO] {weight_type} 굵기 적용: {weight_code} -> {formatted}")
            return formatted
        else:
            return text

    def get_formatted_text_with_alignment(self, text, use_chars_align=True):
        """
        현재 선택된 정렬 설정을 사용하여 텍스트를 포맷팅합니다.
        """
        if use_chars_align:
            alignment_code = self.get_chars_alignment()
            align_type = "문자"
        else:
            alignment_code = self.get_brackets_alignment()
            align_type = "괄호"

        if alignment_code:
            formatted = self.apply_text_alignment(text, alignment_code)
            print(f"[INFO] {align_type} 정렬 적용: {alignment_code} -> {formatted}")
            return formatted
        else:
            return f'<p>{text}</p>'

    def get_formatted_text_with_style(self, text, use_chars_style=True):
        """
        현재 선택된 스타일 설정을 사용하여 텍스트를 포맷팅합니다.
        """
        if use_chars_style:
            style_code = self.get_chars_style()
            style_type = "문자"
        else:
            style_code = self.get_brackets_style()
            style_type = "괄호"

        if style_code:
            formatted = self.apply_font_style(text, style_code)
            print(f"[INFO] {style_type} 스타일 적용: {style_code} -> {formatted}")
            return formatted
        else:
            return text

    def get_formatted_text_with_color(self, text, use_chars_color=True):
        """
        현재 선택된 색상 설정을 사용하여 텍스트를 포맷팅합니다.
        """
        if use_chars_color:
            color_hex = self.get_chars_color()
            color_type = "문자"
        else:
            color_hex = self.get_brackets_color()
            color_type = "괄호"

        if color_hex:
            formatted = self.apply_font_color(text, color_hex)
            print(f"[INFO] {color_type} 색상 적용: {color_hex} -> {formatted}")
            return formatted
        else:
            return text

    # ePub 변환 관련 메서드들을 추가합니다
    def convert_to_epub(self):
        """
        설정된 정보를 기반으로 ePub 파일을 생성합니다.

        주요 과정:
        1. 필수 요구사항 검증 (텍스트 파일, 제목 등)
        2. 저장 경로 선택
        3. ePub 파일 생성
        4. 결과 알림

        Returns:
            None

        Raises:
            FileNotFoundError: 텍스트 파일이 존재하지 않을 때
            PermissionError: 파일 쓰기 권한이 없을 때
            Exception: ePub 생성 중 기타 오류 발생 시
        """
        try:
            logging.info("ePub 변환 시작")

            # 필수 요구사항 검증
            if not self.validate_epub_requirements():
                logging.warning("ePub 변환 요구사항 검증 실패")
                return

            # 저장 경로 선택
            default_filename = f"{self.ui.lineEdit_Title.text().strip()}.epub"
            save_path, _ = QFileDialog.getSaveFileName(
                self, "ePub 파일 저장", default_filename,
                "ePub Files (*.epub);;All Files (*)"
            )

            if not save_path:
                logging.info("사용자가 저장을 취소함")
                return

            logging.info(f"ePub 저장 경로: {save_path}")

            # ePub 분할 설정 확인
            divide_info = self.get_epub_divide_info()
            
            if divide_info['enabled']:
                # 분할 ePub 생성
                created_files = self.create_divided_epub_files(save_path, divide_info)
                
                # 분할 생성 완료 메시지
                if created_files:
                    files_list = '\n'.join([os.path.basename(f) for f in created_files])
                    total_volumes = len(created_files)
                    QMessageBox.information(
                        self, "분할 ePub 생성 완료",
                        f"총 {total_volumes}권의 ePub 파일이 생성되었습니다:\n\n{files_list}"
                    )
                    logging.info(f"분할 ePub 변환 완료: {total_volumes}개 파일")
            else:
                # 단일 ePub 생성
                self.create_epub_file(save_path)
                
                QMessageBox.information(
                    self, "변환 완료",
                    f"ePub 파일이 성공적으로 생성되었습니다:\n{save_path}"
                )
                logging.info(f"ePub 변환 완료: {save_path}")

        except PermissionError as e:
            error_msg = f"파일 쓰기 권한이 없습니다: {str(e)}"
            QMessageBox.critical(self, "권한 오류", error_msg)
            logging.error(error_msg)
        except FileNotFoundError as e:
            error_msg = f"필요한 파일을 찾을 수 없습니다: {str(e)}"
            QMessageBox.critical(self, "파일 오류", error_msg)
            logging.error(error_msg)
        except Exception as e:
            error_msg = f"ePub 변환 중 오류가 발생했습니다: {str(e)}"
            QMessageBox.critical(self, "변환 실패", error_msg)
            logging.error(error_msg)

    def validate_epub_requirements(self):
        """
        ePub 변환에 필요한 최소 요구사항을 검증합니다.

        검증 항목:
        - 텍스트 파일 존재 여부
        - 제목 입력 여부
        - 챕터 리스트 (없을 경우 사용자 선택)

        Returns:
            bool: 검증 통과 시 True, 실패 시 False
        """
        try:
            logging.debug("ePub 변환 요구사항 검증 시작")

            # 텍스트 파일 검증
            text_file_path = self.ui.label_TextFilePath.text().strip()
            if not text_file_path or not os.path.exists(text_file_path):
                QMessageBox.warning(
                    self, "변환 실패",
                    "텍스트 파일이 선택되지 않았거나 존재하지 않습니다."
                )
                logging.warning(f"텍스트 파일 검증 실패: {text_file_path}")
                return False

            # 제목 검증
            title = self.ui.lineEdit_Title.text().strip()
            if not title:
                QMessageBox.warning(self, "변환 실패", "제목을 입력해주세요.")
                logging.warning("제목이 입력되지 않음")
                return False

            # 챕터 리스트 검증
            table = self.ui.tableWidget_ChapterList
            if table.rowCount() == 0:
                reply = QMessageBox.question(
                    self, "챕터 없음",
                    "챕터 리스트가 비어있습니다. 전체 텍스트를 하나의 챕터로 만들까요?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.No:
                    logging.info("사용자가 단일 챕터 생성을 거부함")
                    return False
                else:
                    logging.info("단일 챕터로 ePub 생성 예정")

            logging.debug("ePub 변환 요구사항 검증 완료")
            return True

        except Exception as e:
            logging.error(f"요구사항 검증 중 오류 발생: {e}")
            return False

    def create_epub_file(self, save_path):
        """
        실제 ePub 파일을 생성합니다.

        주요 과정:
        1. 기존 파일 백업 (존재하는 경우)
        2. 임시 디렉토리 생성
        3. ePub 구조 생성
        4. ZIP 패키징
        5. 임시 파일 정리

        Args:
            save_path (str): ePub 파일을 저장할 경로

        Raises:
            PermissionError: 파일 쓰기 권한이 없을 때
            OSError: 디스크 공간 부족 등 시스템 오류
        """
        try:
            logging.info(f"ePub 파일 생성 시작: {save_path}")

            # 기존 파일 백업
            backup_path = self._create_backup_if_exists(save_path)
            if backup_path:
                logging.info(f"기존 파일 백업 완료: {backup_path}")

            # 임시 디렉토리 생성
            temp_dir = os.path.join(os.path.dirname(save_path), f"temp_epub_{uuid.uuid4().hex[:8]}")
            os.makedirs(temp_dir, exist_ok=True)
            logging.debug(f"임시 디렉토리 생성: {temp_dir}")

            try:
                # ePub 구조 생성
                self.create_epub_structure(temp_dir)

                # ZIP 패키징
                self.create_zip_epub(temp_dir, save_path)

                logging.info(f"ePub 파일 생성 완료: {save_path}")

            finally:
                # 임시 디렉토리 정리
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logging.debug(f"임시 디렉토리 삭제: {temp_dir}")

        except Exception as e:
            logging.error(f"ePub 파일 생성 중 오류 발생: {e}")
            raise

    def create_divided_epub_files(self, base_save_path, divide_info):
        """
        챕터를 분할하여 여러 개의 ePub 파일을 생성합니다.
        
        Args:
            base_save_path (str): 기본 저장 경로
            divide_info (dict): 분할 설정 정보
        """
        try:
            logging.info("분할 ePub 생성 시작")
            
            # 전체 챕터 정보 가져오기
            chapters = self.get_chapters_from_table()
            total_chapters = len(chapters)
            chapters_per_volume = divide_info['chapters_per_volume']
            
            if total_chapters == 0:
                raise ValueError("생성할 챕터가 없습니다.")
                
            # 권 정보 계산
            volume_info = self.calculate_volume_info(total_chapters, chapters_per_volume)
            
            # 기본 파일명에서 확장자 제거
            base_filename = os.path.splitext(base_save_path)[0]
            
            created_files = []
            
            # 각 권별로 ePub 생성
            for volume_idx, (start_chapter, end_chapter) in enumerate(volume_info['volume_ranges']):
                volume_number = volume_idx + 1
                
                # 권별 파일명 생성
                volume_filename = self.generate_volume_filename(
                    base_filename, volume_number, volume_info['volume_digits']
                )
                
                # 해당 권의 챕터들 추출
                volume_chapters = chapters[start_chapter:end_chapter]
                
                logging.info(f"권 {volume_number} 생성 중: {len(volume_chapters)}개 챕터 ({start_chapter+1}~{end_chapter})")
                
                # 임시로 원본 챕터를 백업하고 권별 챕터로 교체
                original_chapters = self.backup_and_replace_chapters(volume_chapters)
                
                try:
                    # 권별 ePub 생성
                    self.create_epub_file(volume_filename)
                    created_files.append(volume_filename)
                    
                    logging.info(f"권 {volume_number} 생성 완료: {volume_filename}")
                    
                finally:
                    # 원본 챕터 복원
                    self.restore_original_chapters(original_chapters)
            
            # 생성 완료 메시지 업데이트 (convert_to_epub에서 처리하도록 수정)
            logging.info(f"분할 ePub 생성 완료: 총 {len(created_files)}개 파일")
            
            # 생성된 파일 목록을 반환하여 메시지에서 사용
            return created_files
            
        except Exception as e:
            error_msg = f"분할 ePub 생성 중 오류 발생: {e}"
            logging.error(error_msg)
            raise

    def get_chapters_from_table(self):
        """
        챕터 테이블에서 챕터 정보를 가져옵니다.
        
        Returns:
            list: 챕터 정보 리스트
        """
        try:
            chapters = []
            row_count = self.ui.tableWidget_Chapter.rowCount()
            
            for row in range(row_count):
                # 라인 번호
                line_item = self.ui.tableWidget_Chapter.item(row, 0)
                line_no = int(line_item.text()) if line_item else 0
                
                # 챕터 제목
                title_item = self.ui.tableWidget_Chapter.item(row, 1)
                title = title_item.text() if title_item else f"챕터 {row + 1}"
                
                # 챕터 내용 (실제 텍스트에서 추출해야 함)
                content = self.extract_chapter_content(line_no, row)
                
                chapters.append({
                    'line_no': line_no,
                    'title': title,
                    'content': content
                })
                
            logging.debug(f"챕터 테이블에서 {len(chapters)}개 챕터 정보 추출")
            return chapters
            
        except Exception as e:
            logging.error(f"챕터 정보 추출 실패: {e}")
            return []

    def extract_chapter_content(self, start_line, chapter_index):
        """
        지정된 라인부터 다음 챕터까지의 내용을 추출합니다.
        
        Args:
            start_line (int): 시작 라인 번호
            chapter_index (int): 현재 챕터 인덱스
            
        Returns:
            str: 챕터 내용
        """
        try:
            # 전체 텍스트 가져오기
            full_text = self.ui.textEdit_Text.toPlainText()
            lines = full_text.split('\n')
            
            # 시작 라인 인덱스 (1-based -> 0-based)
            start_idx = max(0, start_line - 1)
            
            # 다음 챕터의 시작 라인 찾기
            next_chapter_row = chapter_index + 1
            if next_chapter_row < self.ui.tableWidget_Chapter.rowCount():
                next_line_item = self.ui.tableWidget_Chapter.item(next_chapter_row, 0)
                if next_line_item:
                    end_idx = max(0, int(next_line_item.text()) - 1)
                else:
                    end_idx = len(lines)
            else:
                end_idx = len(lines)
            
            # 챕터 내용 추출
            chapter_lines = lines[start_idx:end_idx]
            content = '\n'.join(chapter_lines).strip()
            
            logging.debug(f"챕터 {chapter_index} 내용 추출: {start_idx}~{end_idx} 라인")
            return content
            
        except Exception as e:
            logging.error(f"챕터 내용 추출 실패: {e}")
            return f"챕터 {chapter_index + 1} 내용"

    def backup_and_replace_chapters(self, volume_chapters):
        """
        현재 챕터 테이블을 백업하고 권별 챕터로 교체합니다.
        
        Args:
            volume_chapters (list): 권별 챕터 리스트
            
        Returns:
            list: 백업된 원본 챕터 정보
        """
        try:
            # 원본 챕터 정보 백업
            original_chapters = []
            row_count = self.ui.tableWidget_Chapter.rowCount()
            
            for row in range(row_count):
                row_data = []
                for col in range(self.ui.tableWidget_Chapter.columnCount()):
                    item = self.ui.tableWidget_Chapter.item(row, col)
                    row_data.append(item.text() if item else "")
                original_chapters.append(row_data)
            
            # 테이블 초기화
            self.ui.tableWidget_Chapter.setRowCount(0)
            
            # 권별 챕터로 교체
            for idx, chapter in enumerate(volume_chapters):
                self.ui.tableWidget_Chapter.insertRow(idx)
                
                # 라인 번호
                line_item = QTableWidgetItem(str(chapter['line_no']))
                self.ui.tableWidget_Chapter.setItem(idx, 0, line_item)
                
                # 챕터 제목
                title_item = QTableWidgetItem(chapter['title'])
                self.ui.tableWidget_Chapter.setItem(idx, 1, title_item)
                
                # 기타 컬럼이 있다면 빈 값으로 설정
                for col in range(2, self.ui.tableWidget_Chapter.columnCount()):
                    empty_item = QTableWidgetItem("")
                    self.ui.tableWidget_Chapter.setItem(idx, col, empty_item)
            
            logging.debug(f"챕터 테이블 교체 완료: {len(volume_chapters)}개 챕터")
            return original_chapters
            
        except Exception as e:
            logging.error(f"챕터 테이블 교체 실패: {e}")
            return []

    def restore_original_chapters(self, original_chapters):
        """
        백업된 원본 챕터 정보를 복원합니다.
        
        Args:
            original_chapters (list): 백업된 원본 챕터 정보
        """
        try:
            # 테이블 초기화
            self.ui.tableWidget_Chapter.setRowCount(0)
            
            # 원본 챕터 정보 복원
            for idx, row_data in enumerate(original_chapters):
                self.ui.tableWidget_Chapter.insertRow(idx)
                
                for col, data in enumerate(row_data):
                    item = QTableWidgetItem(data)
                    self.ui.tableWidget_Chapter.setItem(idx, col, item)
            
            logging.debug(f"원본 챕터 테이블 복원 완료: {len(original_chapters)}개 챕터")
            
        except Exception as e:
            logging.error(f"원본 챕터 테이블 복원 실패: {e}")

    def _create_backup_if_exists(self, file_path):
        """
        파일이 존재하는 경우 백업을 생성합니다.

        Args:
            file_path (str): 백업할 파일 경로

        Returns:
            str or None: 백업 파일 경로 (백업이 생성된 경우), 없으면 None
        """
        if not os.path.exists(file_path):
            return None

        try:
            # 백업 폴더 생성
            backup_dir = os.path.join(os.path.dirname(file_path), "backup")
            os.makedirs(backup_dir, exist_ok=True)

            # 백업 파일명 생성 (YYYYMMDD_HHMMSS_원본파일명)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = os.path.basename(file_path)
            backup_filename = f"{timestamp}_{original_name}"
            backup_path = os.path.join(backup_dir, backup_filename)

            # 백업 파일 복사
            shutil.copy2(file_path, backup_path)
            logging.info(f"파일 백업 생성: {file_path} -> {backup_path}")

            return backup_path

        except Exception as e:
            logging.warning(f"백업 생성 실패 (계속 진행): {e}")
            return None

    def create_epub_structure(self, temp_dir):
        """
        ePub의 디렉토리 구조와 파일들을 생성합니다.

        생성되는 구조:
        - META-INF/container.xml
        - OEBPS/content.opf (메타데이터)
        - OEBPS/toc.ncx (목차)
        - OEBPS/nav.xhtml (ePub 3.0 네비게이션)
        - OEBPS/Styles/style.css (스타일시트)
        - OEBPS/Images/ (이미지 파일들)
        - OEBPS/chapter*.xhtml (챕터 파일들)
        - mimetype (MIME 타입 정의)

        Args:
            temp_dir (str): ePub 구조를 생성할 임시 디렉토리 경로
        """
        try:
            logging.debug("ePub 구조 생성 시작")

            # 디렉토리 구조 생성
            meta_inf_dir = os.path.join(temp_dir, "META-INF")
            oebps_dir = os.path.join(temp_dir, "OEBPS")
            images_dir = os.path.join(oebps_dir, "Images")
            styles_dir = os.path.join(oebps_dir, "Styles")

            for dir_path in [meta_inf_dir, oebps_dir, images_dir, styles_dir]:
                os.makedirs(dir_path, exist_ok=True)

            # ePub 필수 파일들 생성
            self.create_mimetype_file(temp_dir)
            self.create_container_xml(meta_inf_dir)
            self.create_content_opf(oebps_dir)
            self.create_toc_ncx(oebps_dir)
            self.create_nav_xhtml(oebps_dir)  # ePub 3.0 네비게이션 파일
            self.create_stylesheet(styles_dir)
            self.create_cover_page(oebps_dir)  # 커버 페이지
            self.create_chapter_files(oebps_dir)
            self.copy_images(images_dir)

            logging.debug("ePub 구조 생성 완료")

        except Exception as e:
            logging.error(f"ePub 구조 생성 중 오류 발생: {e}")
            raise

    def create_mimetype_file(self, temp_dir):
        """
        ePub의 mimetype 파일을 생성합니다.

        Args:
            temp_dir (str): mimetype 파일을 생성할 디렉토리
        """
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
        manifest_items.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
        spine_items = []

        # 폰트 파일들을 매니페스트에 추가
        body_font_path = self.ui.label_BodyFontPath.text().strip()
        chapter_font_path = self.ui.label_ChapterFontPath.text().strip()

        if body_font_path and body_font_path != "TextLabel" and os.path.exists(body_font_path):
            font_filename = os.path.basename(body_font_path)
            font_ext = os.path.splitext(font_filename)[1].lower()
            if font_ext == '.ttf':
                font_media_type = "font/truetype"
            elif font_ext == '.otf':
                font_media_type = "font/opentype"
            elif font_ext in ['.woff', '.woff2']:
                font_media_type = f"font/{font_ext[1:]}"
            else:
                font_media_type = "font/truetype"
            manifest_items.append(f'<item id="body-font" href="Fonts/{font_filename}" media-type="{font_media_type}"/>')

        if chapter_font_path and chapter_font_path != "TextLabel" and os.path.exists(chapter_font_path) and chapter_font_path != body_font_path:
            font_filename = os.path.basename(chapter_font_path)
            font_ext = os.path.splitext(font_filename)[1].lower()
            if font_ext == '.ttf':
                font_media_type = "font/truetype"
            elif font_ext == '.otf':
                font_media_type = "font/opentype"
            elif font_ext in ['.woff', '.woff2']:
                font_media_type = f"font/{font_ext[1:]}"
            else:
                font_media_type = "font/truetype"
            manifest_items.append(f'<item id="chapter-font" href="Fonts/{font_filename}" media-type="{font_media_type}"/>')

        # 커버 이미지 처리
        cover_image_path = self.ui.label_CoverImagePath.text().strip()
        has_cover = cover_image_path and cover_image_path != "---" and os.path.exists(cover_image_path)

        if has_cover:
            # 파일 확장자에 따라 적절한 미디어 타입 설정
            _, ext = os.path.splitext(cover_image_path)
            if ext.lower() in ['.jpg', '.jpeg']:
                cover_media_type = "image/jpeg"
                cover_filename = "cover.jpg"
            elif ext.lower() == '.png':
                cover_media_type = "image/png"
                cover_filename = "cover.png"
            else:
                cover_media_type = "image/jpeg"
                cover_filename = "cover.jpg"

            manifest_items.append(f'<item id="cover-image" href="Images/{cover_filename}" media-type="{cover_media_type}"/>')
            manifest_items.append('<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.append('<itemref idref="cover"/>')

        for i, chapter in enumerate(chapters, 1):
            manifest_items.append(f'<item id="chapter{i}" href="chapter{i}.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.append(f'<itemref idref="chapter{i}"/>')

        # 메타데이터에 커버 이미지 정보 추가
        cover_metadata = ""
        if has_cover:
            cover_metadata = '<meta name="cover" content="cover-image"/>'

        content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="BookId">{uuid.uuid4()}</dc:identifier>
        <dc:title>{title}</dc:title>
        <dc:creator>{author_text}</dc:creator>
        <dc:language>ko</dc:language>
        <dc:date>{datetime.now().strftime('%Y-%m-%d')}</dc:date>
        <meta property="dcterms:modified">{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}</meta>
        {cover_metadata}
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
        play_order = 1

        # 커버 페이지가 있으면 목차에 추가
        cover_image_path = self.ui.label_CoverImagePath.text().strip()
        has_cover = cover_image_path and cover_image_path != "---" and os.path.exists(cover_image_path)

        if has_cover:
            nav_points.append(f'''
        <navPoint id="cover" playOrder="{play_order}">
            <navLabel>
                <text>표지</text>
            </navLabel>
            <content src="cover.xhtml"/>
        </navPoint>''')
            play_order += 1

        # 챕터들을 목차에 추가
        for i, chapter in enumerate(chapters, 1):
            nav_points.append(f'''
        <navPoint id="chapter{i}" playOrder="{play_order}">
            <navLabel>
                <text>{chapter['title']}</text>
            </navLabel>
            <content src="chapter{i}.xhtml"/>
        </navPoint>''')
            play_order += 1

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

    def create_nav_xhtml(self, oebps_dir):
        """ePub 3.0용 네비게이션 파일을 생성합니다."""
        title = self.ui.lineEdit_Title.text().strip()
        chapters = self.get_chapter_info()

        nav_items = []

        # 커버 페이지가 있으면 네비게이션에 추가
        cover_image_path = self.ui.label_CoverImagePath.text().strip()
        has_cover = cover_image_path and cover_image_path != "---" and os.path.exists(cover_image_path)

        if has_cover:
            nav_items.append('<li><a href="cover.xhtml">표지</a></li>')

        # 챕터들을 네비게이션에 추가
        for i, chapter in enumerate(chapters, 1):
            nav_items.append(f'<li><a href="chapter{i}.xhtml">{chapter["title"]}</a></li>')

        nav_xhtml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>목차</title>
    <link rel="stylesheet" type="text/css" href="Styles/style.css"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>목차</h1>
        <ol>
            {chr(10).join(nav_items)}
        </ol>
    </nav>
</body>
</html>'''

        with open(os.path.join(oebps_dir, "nav.xhtml"), 'w', encoding='utf-8') as f:
            f.write(nav_xhtml)

    def create_stylesheet(self, styles_dir):
        """CSS 스타일시트를 생성합니다."""

        # 폰트 정보 수집
        body_font_path = self.ui.label_BodyFontPath.text().strip()
        chapter_font_path = self.ui.label_ChapterFontPath.text().strip()

        # 폰트 CSS 생성
        font_css = ""

        # 본문 폰트 처리
        if body_font_path and body_font_path != "TextLabel" and os.path.exists(body_font_path):
            font_name = os.path.splitext(os.path.basename(body_font_path))[0]
            body_font_family = f"'{font_name}', serif"
            # 폰트 파일을 Fonts 폴더로 복사
            fonts_dir = os.path.join(os.path.dirname(styles_dir), "Fonts")
            os.makedirs(fonts_dir, exist_ok=True)
            import shutil
            font_filename = os.path.basename(body_font_path)
            shutil.copy2(body_font_path, os.path.join(fonts_dir, font_filename))

            font_css += f"""
@font-face {{
    font-family: '{font_name}';
    src: url('../Fonts/{font_filename}');
}}
"""
        else:
            body_font_family = "serif"

        # 챕터 폰트 처리
        if chapter_font_path and chapter_font_path != "TextLabel" and os.path.exists(chapter_font_path):
            font_name = os.path.splitext(os.path.basename(chapter_font_path))[0]
            chapter_font_family = f"'{font_name}', serif"
            # 폰트 파일을 Fonts 폴더로 복사
            fonts_dir = os.path.join(os.path.dirname(styles_dir), "Fonts")
            os.makedirs(fonts_dir, exist_ok=True)
            import shutil
            font_filename = os.path.basename(chapter_font_path)
            shutil.copy2(chapter_font_path, os.path.join(fonts_dir, font_filename))

            if body_font_path != chapter_font_path:  # 중복 방지
                font_css += f"""
@font-face {{
    font-family: '{font_name}';
    src: url('../Fonts/{font_filename}');
}}
"""
        else:
            chapter_font_family = body_font_family

        css_content = f'''{font_css}
body {{
    font-family: {body_font_family};
    line-height: 1.6;
    margin: 0;
    padding: 1em;
    text-align: justify;
}}

h1, h2, h3 {{
    font-family: {chapter_font_family};
    margin-top: 2em;
    margin-bottom: 1em;
    font-weight: bold;
}}

h1 {{
    font-size: 1.5em;
    text-align: center;
}}

p {{
    margin-bottom: 1em;
    text-indent: 1em;
}}

.chapter-title {{
    font-family: {chapter_font_family};
    text-align: center;
    font-size: 1.3em;
    font-weight: bold;
    margin: 2em 0;
}}

.cover-image {{
    text-align: center;
    margin: 0;
    padding: 0;
}}

.cover-image img {{
    max-width: 100%;
    max-height: 100vh;
}}
'''

        with open(os.path.join(styles_dir, "style.css"), 'w', encoding='utf-8') as f:
            f.write(css_content)

    def create_cover_page(self, oebps_dir):
        """커버 페이지를 생성합니다."""
        cover_image_path = self.ui.label_CoverImagePath.text().strip()

        if not cover_image_path or cover_image_path == "---" or not os.path.exists(cover_image_path):
            return  # 커버 이미지가 없으면 커버 페이지도 생성하지 않음

        title = self.ui.lineEdit_Title.text().strip()

        # 파일 확장자에 따라 적절한 파일명 설정
        _, ext = os.path.splitext(cover_image_path)
        if ext.lower() in ['.jpg', '.jpeg']:
            cover_filename = "cover.jpg"
        elif ext.lower() == '.png':
            cover_filename = "cover.png"
        else:
            cover_filename = "cover.jpg"

        cover_xhtml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>커버</title>
    <link rel="stylesheet" type="text/css" href="Styles/style.css"/>
    <style type="text/css">
        body {{
            margin: 0;
            padding: 0;
            text-align: center;
        }}
        .cover-container {{
            width: 100%;
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
        }}
        .cover-image {{
            max-width: 100%;
            max-height: 85vh;
            object-fit: contain;
        }}
        .cover-nav {{
            position: absolute;
            bottom: 2em;
            text-align: center;
        }}
        .cover-nav a {{
            color: #666;
            text-decoration: none;
            font-size: 0.9em;
            padding: 0.5em 1em;
            border: 1px solid #ccc;
            border-radius: 3px;
            background-color: rgba(255, 255, 255, 0.8);
        }}
        .cover-nav a:hover {{
            background-color: #f0f0f0;
        }}
    </style>
</head>
<body>
    <div class="cover-container">
        <img src="Images/{cover_filename}" alt="{title} 커버" class="cover-image"/>
        <div class="cover-nav">
            <a href="nav.xhtml">목차 보기</a>
        </div>
    </div>
</body>
</html>'''

        with open(os.path.join(oebps_dir, "cover.xhtml"), 'w', encoding='utf-8') as f:
            f.write(cover_xhtml)

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
            # 파일 인코딩 자동 감지
            encoding = self._detect_file_encoding(text_file_path)
            with open(text_file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            QMessageBox.critical(self, "파일 읽기 오류", f"텍스트 파일을 읽을 수 없습니다:\n{str(e)}")
            return ""

    def _detect_file_encoding(self, file_path):
        """파일의 인코딩을 자동 감지합니다."""
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(8192)
                if sample:
                    result = chardet.detect(sample)
                    encoding = result.get('encoding', 'utf-8')
                    confidence = result.get('confidence', 0)

                    # 신뢰도가 낮으면 utf-8 시도
                    if confidence < 0.7:
                        encoding = 'utf-8'

                    return encoding
                else:
                    return 'utf-8'
        except Exception:
            return 'utf-8'

    def extract_chapter_contents(self, chapters):
        """각 챕터의 내용을 추출합니다."""
        text_file_path = self.ui.label_TextFilePath.text().strip()
        try:
            # 파일 인코딩 자동 감지
            encoding = self._detect_file_encoding(text_file_path)
            with open(text_file_path, 'r', encoding=encoding) as f:
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
            try:
                # 챕터 내용을 라인별로 분할
                lines = chapter['content'].split('\n')

                # 각 라인에 문자 스타일링 적용
                styled_lines = self.apply_character_styling_to_text(lines)

                # HTML 문단으로 변환
                content_parts = []
                for line in styled_lines:
                    line = line.strip()
                    if line:
                        # 이미 HTML 스타일이 적용된 라인인지 확인
                        if line.startswith('<div') and line.endswith('</div>'):
                            # 이미 div로 감싸진 경우 그대로 사용
                            content_parts.append(line)
                        else:
                            # 일반 텍스트인 경우 p 태그로 감싸기
                            content_parts.append(f'<p>{line}</p>')

                content = '\n'.join(content_parts) if content_parts else '<p></p>'

                # 챕터 스타일 정보 가져오기
                chapter_style_info = self.get_chapter_style_info()

                # 챕터 제목에 스타일 적용
                styled_chapter_title = self.apply_chapter_title_style(chapter['title'], chapter_style_info)

                chapter_xhtml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{chapter['title']}</title>
    <link rel="stylesheet" type="text/css" href="Styles/style.css"/>
</head>
<body>
    {styled_chapter_title}
    {content}
</body>
</html>'''

                with open(os.path.join(oebps_dir, f"chapter{i}.xhtml"), 'w', encoding='utf-8') as f:
                    f.write(chapter_xhtml)

                logging.debug(f"챕터 {i} 파일 생성 완료 (문자 스타일링 적용)")

            except Exception as e:
                logging.error(f"챕터 {i} 파일 생성 실패: {e}")
                # 오류 발생 시 기본 방식으로 생성
                content = chapter['content'].replace('\n', '</p>\n<p>').strip()
                if content:
                    content = f'<p>{content}</p>'

                # 챕터 스타일 정보 가져오기 (오류 발생 시에도 적용)
                chapter_style_info = self.get_chapter_style_info()

                # 챕터 제목에 스타일 적용
                styled_chapter_title = self.apply_chapter_title_style(chapter['title'], chapter_style_info)

                chapter_xhtml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{chapter['title']}</title>
    <link rel="stylesheet" type="text/css" href="Styles/style.css"/>
</head>
<body>
    {styled_chapter_title}
    {content}
</body>
</html>'''

                with open(os.path.join(oebps_dir, f"chapter{i}.xhtml"), 'w', encoding='utf-8') as f:
                    f.write(chapter_xhtml)

    def copy_images(self, images_dir):
        """선택된 이미지들을 ePub에 복사합니다."""
        import shutil

        # 커버 이미지 복사
        cover_image_path = self.ui.label_CoverImagePath.text().strip()
        if cover_image_path and cover_image_path != "---" and os.path.exists(cover_image_path):
            # 파일 확장자에 따라 적절한 파일명 생성
            _, ext = os.path.splitext(cover_image_path)
            if ext.lower() in ['.jpg', '.jpeg']:
                dst_path = os.path.join(images_dir, "cover.jpg")
            elif ext.lower() == '.png':
                dst_path = os.path.join(images_dir, "cover.png")
            else:
                # 기본적으로 jpg로 변환
                dst_path = os.path.join(images_dir, "cover.jpg")

            try:
                shutil.copy2(cover_image_path, dst_path)
                print(f"커버 이미지 복사 완료: {cover_image_path} -> {dst_path}")
            except Exception as e:
                print(f"커버 이미지 복사 실패: {e}")
        else:
            print(f"커버 이미지가 없거나 경로가 유효하지 않음: {cover_image_path}")

        # 챕터별 이미지 복사 (향후 확장 가능)
        # TODO: 챕터별 이미지 처리 로직 추가

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
        """
        정규식을 사용하여 텍스트 파일에서 챕터 목록을 검색합니다.

        주요 기능:
        - 테이블 위젯 초기화 및 설정
        - 선택된 텍스트 파일 유효성 검사
        - 체크된 정규식 패턴 수집
        - 백그라운드 워커를 통한 챕터 검색 시작

        Raises:
            FileNotFoundError: 텍스트 파일이 존재하지 않을 때
            UnicodeDecodeError: 텍스트 파일 읽기 실패 시
        """
        try:
            logging.info("챕터 목록 검색 시작")

            # 테이블 초기화
            table = self.ui.tableWidget_ChapterList
            table.setRowCount(0)
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels([
                "적용", "목차 순서", "챕터 제목", "라인 번호", "삽화 선택", "삽화 경로"
            ])

            # 열 너비 설정
            table.setColumnWidth(0, 50)   # 적용
            table.setColumnWidth(1, 70)   # 목차 순서
            table.setColumnWidth(2, 300)  # 챕터 제목
            table.setColumnWidth(5, 300)  # 삽화 경로

            # 중앙 정렬 설정
            table.horizontalHeaderItem(0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.horizontalHeaderItem(1).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # 스타일: 줄무늬 배경
            table.setAlternatingRowColors(True)

            # 텍스트 파일 경로 확인
            file_path = self.ui.label_TextFilePath.text().strip()
            if not file_path or not os.path.exists(file_path):
                QMessageBox.warning(self, "오류", "텍스트 파일이 선택되지 않았거나 존재하지 않습니다.")
                logging.warning(f"유효하지 않은 텍스트 파일 경로: {file_path}")
                return

            # 텍스트 파일 읽기 (UTF-8)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logging.debug(f"텍스트 파일 읽기 완료: {len(content)} 문자")
            except Exception as e:
                QMessageBox.critical(self, "파일 읽기 실패", str(e))
                logging.error(f"텍스트 파일 읽기 실패: {e}")
                return

            # 체크된 정규식만 수집
            selected_patterns = []
            for i in range(1, 10):
                cb = getattr(self.ui, f"checkBox_RegEx{i}")
                cmb = getattr(self.ui, f"comboBox_RegEx{i}")
                if cb.isChecked():
                    pattern = cmb.currentData()
                    if pattern:
                        selected_patterns.append((i, pattern))

            if not selected_patterns:
                QMessageBox.information(self, "정규식 없음", "체크된 정규식이 없습니다.")
                logging.warning("선택된 정규식 패턴이 없음")
                return

            logging.info(f"선택된 정규식 패턴 수: {len(selected_patterns)}")

            # QThread로 백그라운드 작업 실행
            self.chapter_worker = ChapterFinderWorker(content, selected_patterns)
            self.chapter_worker.chapter_found.connect(self.add_chapter_row)  # 실시간 행 추가
            self.chapter_worker.progress.connect(self.ui.progressBar.setValue)
            self.chapter_worker.finished.connect(self.finish_chapter_search)
            self.chapter_worker.start()

            logging.info("챕터 검색 워커 시작")

        except Exception as e:
            logging.error(f"챕터 목록 검색 중 오류 발생: {e}")
            QMessageBox.critical(self, "오류", f"챕터 검색 중 오류가 발생했습니다:\n{str(e)}")

    def bind_regex_checkbox_events(self):
        """정규식 체크박스 이벤트를 바인딩합니다."""
        for i in range(1, 10):
            checkbox = getattr(self.ui, f"checkBox_RegEx{i}")
            combo = getattr(self.ui, f"comboBox_RegEx{i}")

            # 체크박스 상태 변경 시 콤보박스 활성화/비활성화
            checkbox.toggled.connect(partial(self.on_regex_checkbox_toggled, i))

            # 초기 상태 설정
            combo.setEnabled(checkbox.isChecked())

    def on_regex_checkbox_toggled(self, index, checked):
        """정규식 체크박스 토글 이벤트 처리"""
        combo = getattr(self.ui, f"comboBox_RegEx{index}")
        combo.setEnabled(checked)

    def initialize_character_styling(self):
        """문자 스타일 기능을 초기화합니다."""
        logging.debug("문자 스타일 기능 초기화 시작")

        # checkBox_Chars1~7과 관련 컴포넌트들 이벤트 연결
        for i in range(1, 8):
            try:
                # 체크박스 이벤트 연결
                checkbox_name = f"checkBox_Chars{i}"
                if hasattr(self.ui, checkbox_name):
                    checkbox = getattr(self.ui, checkbox_name)
                    checkbox.toggled.connect(partial(self.on_chars_checkbox_toggled, i))

                # 색상 체크박스 이벤트 연결
                color_checkbox_name = f"checkBox_CharsColor{i}"
                if hasattr(self.ui, color_checkbox_name):
                    color_checkbox = getattr(self.ui, color_checkbox_name)
                    color_checkbox.toggled.connect(partial(self.on_chars_color_checkbox_toggled, i))

                # 굵기 콤보박스 변경 이벤트 연결
                weight_combo_name = f"comboBox_CharsWeight{i}"
                if hasattr(self.ui, weight_combo_name):
                    weight_combo = getattr(self.ui, weight_combo_name)
                    weight_combo.currentTextChanged.connect(partial(self.on_chars_weight_changed, i))

                # SpinBox 변경 이벤트 연결
                spinbox_name = f"spinBox_CharsWeight{i}"
                if hasattr(self.ui, spinbox_name):
                    spinbox = getattr(self.ui, spinbox_name)
                    spinbox.valueChanged.connect(partial(self.on_chars_weight_spinbox_changed, i))
                    # 기본값 400으로 설정
                    spinbox.setValue(400)

                # 초기 컴포넌트 상태 설정
                self.update_chars_components_state(i)

                logging.debug(f"문자 스타일 {i}번 컴포넌트 초기화 완료")

            except Exception as e:
                logging.error(f"문자 스타일 {i}번 초기화 실패: {e}")

        logging.debug("문자 스타일 기능 초기화 완료")

    def initialize_bracket_styling(self):
        """괄호 스타일 기능을 초기화합니다."""
        logging.debug("괄호 스타일 기능 초기화 시작")

        # checkBox_Brackets1~7과 관련 컴포넌트들 이벤트 연결
        for i in range(1, 8):
            try:
                # 체크박스 이벤트 연결
                checkbox_name = f"checkBox_Brackets{i}"
                if hasattr(self.ui, checkbox_name):
                    checkbox = getattr(self.ui, checkbox_name)
                    checkbox.toggled.connect(partial(self.on_brackets_checkbox_toggled, i))

                # 색상 체크박스 이벤트 연결
                color_checkbox_name = f"checkBox_BracketsColor{i}"
                if hasattr(self.ui, color_checkbox_name):
                    color_checkbox = getattr(self.ui, color_checkbox_name)
                    color_checkbox.toggled.connect(partial(self.on_brackets_color_checkbox_toggled, i))

                # 굵기 콤보박스 변경 이벤트 연결
                weight_combo_name = f"comboBox_BracketsWeight{i}"
                if hasattr(self.ui, weight_combo_name):
                    weight_combo = getattr(self.ui, weight_combo_name)
                    weight_combo.currentTextChanged.connect(partial(self.on_brackets_weight_changed, i))

                # SpinBox 변경 이벤트 연결
                spinbox_name = f"spinBox_BracketsWeight{i}"
                if hasattr(self.ui, spinbox_name):
                    spinbox = getattr(self.ui, spinbox_name)
                    spinbox.valueChanged.connect(partial(self.on_brackets_weight_spinbox_changed, i))
                    # 기본값 400으로 설정
                    spinbox.setValue(400)

                # 초기 컴포넌트 상태 설정
                self.update_brackets_components_state(i)

                logging.debug(f"괄호 스타일 {i}번 컴포넌트 초기화 완료")

            except Exception as e:
                logging.error(f"괄호 스타일 {i}번 초기화 실패: {e}")

        logging.debug("괄호 스타일 기능 초기화 완료")

    def on_brackets_checkbox_toggled(self, index, checked):
        """괄호 체크박스 토글 이벤트 처리"""
        logging.debug(f"괄호 체크박스 {index} 토글: {checked}")
        self.update_brackets_components_state(index)

    def on_brackets_color_checkbox_toggled(self, index, checked):
        """괄호 색상 체크박스 토글 이벤트 처리"""
        logging.debug(f"괄호 색상 체크박스 {index} 토글: {checked}")
        self.update_brackets_components_state(index)

    def on_brackets_weight_changed(self, index, text):
        """괄호 굵기 콤보박스 변경 이벤트 처리"""
        logging.debug(f"괄호 굵기 {index} 변경: {text}")
        self.update_brackets_components_state(index)

    def on_brackets_weight_spinbox_changed(self, index, value):
        """괄호 굵기 SpinBox 변경 이벤트 처리"""
        logging.debug(f"괄호 굵기 SpinBox {index} 변경: {value}")

    def update_brackets_components_state(self, index):
        """괄호 관련 컴포넌트들의 활성화 상태를 업데이트합니다."""
        try:
            # 기본 체크박스 상태 확인
            checkbox_name = f"checkBox_Brackets{index}"
            brackets_enabled = False
            if hasattr(self.ui, checkbox_name):
                checkbox = getattr(self.ui, checkbox_name)
                brackets_enabled = checkbox.isChecked()

            # 색상 체크박스 상태 확인
            color_checkbox_name = f"checkBox_BracketsColor{index}"
            color_enabled = False
            if hasattr(self.ui, color_checkbox_name):
                color_checkbox = getattr(self.ui, color_checkbox_name)
                color_enabled = color_checkbox.isChecked()

            # 굵기 콤보박스에서 '직접입력' 선택 여부 확인
            weight_combo_name = f"comboBox_BracketsWeight{index}"
            is_direct_input = False
            if hasattr(self.ui, weight_combo_name):
                weight_combo = getattr(self.ui, weight_combo_name)
                current_data = weight_combo.currentData()
                is_direct_input = (current_data == "Number")

            # 각 컴포넌트 활성화/비활성화
            component_names = [
                f"comboBox_Brackets{index}",
                f"comboBox_BracketsAlign{index}",
                f"comboBox_BracketsWeight{index}",
                f"comboBox_BracketsStyle{index}"
            ]

            for comp_name in component_names:
                if hasattr(self.ui, comp_name):
                    component = getattr(self.ui, comp_name)
                    component.setEnabled(brackets_enabled)

            # SpinBox는 굵기가 '직접입력'이고 체크박스가 활성화된 경우에만 활성화
            spinbox_name = f"spinBox_BracketsWeight{index}"
            if hasattr(self.ui, spinbox_name):
                spinbox = getattr(self.ui, spinbox_name)
                spinbox.setEnabled(brackets_enabled and is_direct_input)

            # 색상 관련 컴포넌트는 색상 체크박스 상태에 따라 결정
            color_lineedit_name = f"lineEdit_BracketsColor{index}"
            if hasattr(self.ui, color_lineedit_name):
                color_lineedit = getattr(self.ui, color_lineedit_name)
                color_lineedit.setEnabled(brackets_enabled and color_enabled)

        except Exception as e:
            logging.error(f"괄호 컴포넌트 {index} 상태 업데이트 실패: {e}")

    # ==================================================================================
    # 챕터 스타일링 기능
    # ==================================================================================

    def initialize_chapter_styling(self):
        """챕터 스타일 기능을 초기화합니다."""
        logging.debug("챕터 스타일 기능 초기화 시작")

        try:
            # comboBox_ChapterSize 초기화
            if hasattr(self.ui, 'comboBox_ChapterSize'):
                self.ui.comboBox_ChapterSize.clear()
                chapter_sizes = [
                    ("<H1>", "H1"),
                    ("<H2>", "H2"),
                    ("<H3>", "H3"),
                    ("<H4>", "H4"),
                    ("<H5>", "H5"),
                    ("<H6>", "H6")
                ]

                for display_text, data_value in chapter_sizes:
                    self.ui.comboBox_ChapterSize.addItem(display_text, data_value)

                # 기본값을 <H4>로 설정
                default_index = self.ui.comboBox_ChapterSize.findData("H4")
                if default_index >= 0:
                    self.ui.comboBox_ChapterSize.setCurrentIndex(default_index)

            # comboBox_ChapterAlign 초기화
            if hasattr(self.ui, 'comboBox_ChapterAlign'):
                self.ui.comboBox_ChapterAlign.clear()
                chapter_aligns = [
                    ("<왼쪽>", "Left"),
                    ("<가운데>", "Center"),
                    ("<오른쪽>", "Right")
                ]

                for display_text, data_value in chapter_aligns:
                    self.ui.comboBox_ChapterAlign.addItem(display_text, data_value)

                # 기본값을 <왼쪽>으로 설정
                default_index = self.ui.comboBox_ChapterAlign.findData("Left")
                if default_index >= 0:
                    self.ui.comboBox_ChapterAlign.setCurrentIndex(default_index)

            # checkBox_ChapterStyle 이벤트 연결
            if hasattr(self.ui, 'checkBox_ChapterStyle'):
                self.ui.checkBox_ChapterStyle.toggled.connect(self.on_chapter_style_checkbox_toggled)

            # 초기 컴포넌트 상태 설정
            self.update_chapter_components_state()

            logging.debug("챕터 스타일 기능 초기화 완료")

        except Exception as e:
            logging.error(f"챕터 스타일 기능 초기화 실패: {e}")

    def on_chapter_style_checkbox_toggled(self, checked):
        """챕터 스타일 체크박스 토글 이벤트 처리"""
        logging.debug(f"챕터 스타일 체크박스 토글: {checked}")
        self.update_chapter_components_state()

    def update_chapter_components_state(self):
        """챕터 스타일 관련 컴포넌트들의 활성화 상태를 업데이트합니다."""
        try:
            # checkBox_ChapterStyle 상태 확인
            chapter_style_enabled = False
            if hasattr(self.ui, 'checkBox_ChapterStyle'):
                checkbox = self.ui.checkBox_ChapterStyle
                chapter_style_enabled = checkbox.isChecked()

            # comboBox_ChapterSize 활성화/비활성화
            if hasattr(self.ui, 'comboBox_ChapterSize'):
                self.ui.comboBox_ChapterSize.setEnabled(chapter_style_enabled)

            # comboBox_ChapterAlign 활성화/비활성화
            if hasattr(self.ui, 'comboBox_ChapterAlign'):
                self.ui.comboBox_ChapterAlign.setEnabled(chapter_style_enabled)

            logging.debug(f"챕터 스타일 컴포넌트 상태 업데이트: {chapter_style_enabled}")

        except Exception as e:
            logging.error(f"챕터 스타일 컴포넌트 상태 업데이트 실패: {e}")

    def get_chapter_style_info(self):
        """
        챕터 스타일 정보를 수집합니다.

        Returns:
            dict: 챕터 스타일 정보 딕셔너리
        """
        style_info = {
            'enabled': False,
            'size': 'H4',
            'align': 'Left'
        }

        try:
            # 스타일 활성화 여부 확인
            if hasattr(self.ui, 'checkBox_ChapterStyle'):
                style_info['enabled'] = self.ui.checkBox_ChapterStyle.isChecked()

            # 챕터 크기 정보
            if hasattr(self.ui, 'comboBox_ChapterSize'):
                size_data = self.ui.comboBox_ChapterSize.currentData()
                if size_data:
                    style_info['size'] = size_data

            # 챕터 정렬 정보
            if hasattr(self.ui, 'comboBox_ChapterAlign'):
                align_data = self.ui.comboBox_ChapterAlign.currentData()
                if align_data:
                    style_info['align'] = align_data

            logging.debug(f"챕터 스타일 정보: {style_info}")
            return style_info

        except Exception as e:
            logging.error(f"챕터 스타일 정보 수집 실패: {e}")
            return style_info

    def apply_chapter_title_style(self, title, style_info):
        """
        챕터 제목에 스타일을 적용합니다.

        Args:
            title (str): 원본 챕터 제목
            style_info (dict): 챕터 스타일 정보

        Returns:
            str: 스타일이 적용된 챕터 제목 HTML
        """
        try:
            if not style_info['enabled']:
                # 스타일이 비활성화된 경우 기본 div 태그 사용
                return f'<div class="chapter-title">{title}</div>'

            # HTML 태그 및 CSS 클래스 설정
            tag = style_info['size'].lower()  # H1, H2, H3, H4, H5, H6 -> h1, h2, h3, h4, h5, h6

            # 정렬 스타일 CSS 클래스 매핑
            align_mapping = {
                'Left': 'text-align: left;',
                'Center': 'text-align: center;',
                'Right': 'text-align: right;'
            }

            align_style = align_mapping.get(style_info['align'], 'text-align: left;')

            # 스타일이 적용된 챕터 제목 HTML 생성
            styled_title = f'<{tag} class="chapter-title" style="{align_style}">{title}</{tag}>'

            logging.debug(f"챕터 제목 스타일 적용: {title} -> {styled_title}")
            return styled_title

        except Exception as e:
            logging.error(f"챕터 제목 스타일 적용 실패: {e}")
            # 오류 발생 시 기본 형태로 반환
            return f'<div class="chapter-title">{title}</div>'

    # ==================================================================================
    # ePub 분할 기능
    # ==================================================================================

    def initialize_epub_divide(self):
        """ePub 분할 기능을 초기화합니다."""
        logging.debug("ePub 분할 기능 초기화 시작")
        
        try:
            # spinBox_ChapterCnt 초기값 설정
            if hasattr(self.ui, 'spinBox_ChapterCnt'):
                self.ui.spinBox_ChapterCnt.setMinimum(1)
                self.ui.spinBox_ChapterCnt.setMaximum(1000)
                self.ui.spinBox_ChapterCnt.setValue(10)  # 기본값 10개 챕터
                
            # checkBox_ePubDivide 이벤트 연결
            if hasattr(self.ui, 'checkBox_ePubDivide'):
                self.ui.checkBox_ePubDivide.toggled.connect(self.on_epub_divide_checkbox_toggled)
                
            # 초기 컴포넌트 상태 설정
            self.update_epub_divide_components_state()
            
            logging.debug("ePub 분할 기능 초기화 완료")
            
        except Exception as e:
            logging.error(f"ePub 분할 기능 초기화 실패: {e}")

    def on_epub_divide_checkbox_toggled(self, checked):
        """ePub 분할 체크박스 토글 이벤트 처리"""
        logging.debug(f"ePub 분할 체크박스 토글: {checked}")
        self.update_epub_divide_components_state()

    def update_epub_divide_components_state(self):
        """ePub 분할 관련 컴포넌트들의 활성화 상태를 업데이트합니다."""
        try:
            # checkBox_ePubDivide 상태 확인
            epub_divide_enabled = False
            if hasattr(self.ui, 'checkBox_ePubDivide'):
                checkbox = self.ui.checkBox_ePubDivide
                epub_divide_enabled = checkbox.isChecked()
                
            # spinBox_ChapterCnt 활성화/비활성화
            if hasattr(self.ui, 'spinBox_ChapterCnt'):
                self.ui.spinBox_ChapterCnt.setEnabled(epub_divide_enabled)
                
            logging.debug(f"ePub 분할 컴포넌트 상태 업데이트: {epub_divide_enabled}")
            
        except Exception as e:
            logging.error(f"ePub 분할 컴포넌트 상태 업데이트 실패: {e}")

    def get_epub_divide_info(self):
        """
        ePub 분할 설정 정보를 수집합니다.
        
        Returns:
            dict: ePub 분할 설정 정보
        """
        divide_info = {
            'enabled': False,
            'chapters_per_volume': 10
        }
        
        try:
            # 분할 활성화 여부 확인
            if hasattr(self.ui, 'checkBox_ePubDivide'):
                divide_info['enabled'] = self.ui.checkBox_ePubDivide.isChecked()
                
            # 권당 챕터 수 확인
            if hasattr(self.ui, 'spinBox_ChapterCnt'):
                divide_info['chapters_per_volume'] = self.ui.spinBox_ChapterCnt.value()
                
            logging.debug(f"ePub 분할 정보: {divide_info}")
            return divide_info
            
        except Exception as e:
            logging.error(f"ePub 분할 정보 수집 실패: {e}")
            return divide_info

    def calculate_volume_info(self, total_chapters, chapters_per_volume):
        """
        전체 챕터 수와 권당 챕터 수를 기반으로 권 정보를 계산합니다.
        
        Args:
            total_chapters (int): 전체 챕터 수
            chapters_per_volume (int): 권당 챕터 수
            
        Returns:
            dict: 권 정보 (총 권수, 자릿수, 권별 챕터 범위)
        """
        try:
            total_volumes = (total_chapters + chapters_per_volume - 1) // chapters_per_volume
            volume_digits = len(str(total_volumes))
            
            volume_ranges = []
            for volume in range(total_volumes):
                start_chapter = volume * chapters_per_volume
                end_chapter = min((volume + 1) * chapters_per_volume, total_chapters)
                volume_ranges.append((start_chapter, end_chapter))
                
            volume_info = {
                'total_volumes': total_volumes,
                'volume_digits': volume_digits,
                'volume_ranges': volume_ranges
            }
            
            logging.debug(f"권 정보 계산 결과: {volume_info}")
            return volume_info
            
        except Exception as e:
            logging.error(f"권 정보 계산 실패: {e}")
            return {'total_volumes': 1, 'volume_digits': 1, 'volume_ranges': [(0, total_chapters)]}

    def generate_volume_filename(self, base_filename, volume_number, volume_digits):
        """
        권수에 따른 파일명을 생성합니다.
        
        Args:
            base_filename (str): 기본 파일명 (확장자 제외)
            volume_number (int): 권 번호 (1부터 시작)
            volume_digits (int): 권수 표시 자릿수
            
        Returns:
            str: 권수가 포함된 파일명
        """
        try:
            # 권수를 지정된 자릿수로 포맷팅
            volume_str = str(volume_number).zfill(volume_digits)
            volume_filename = f"{base_filename}_{volume_str}권.epub"
            
            logging.debug(f"권 파일명 생성: {base_filename} -> {volume_filename}")
            return volume_filename
            
        except Exception as e:
            logging.error(f"권 파일명 생성 실패: {e}")
            return f"{base_filename}_{volume_number}권.epub"

    def on_chars_checkbox_toggled(self, index, checked):
        """문자 체크박스 토글 이벤트 처리"""
        logging.debug(f"문자 체크박스 {index} 토글: {checked}")
        self.update_chars_components_state(index)

    def on_chars_color_checkbox_toggled(self, index, checked):
        """문자 색상 체크박스 토글 이벤트 처리"""
        logging.debug(f"문자 색상 체크박스 {index} 토글: {checked}")
        self.update_chars_components_state(index)

    def on_chars_weight_changed(self, index, text):
        """문자 굵기 콤보박스 변경 이벤트 처리"""
        logging.debug(f"문자 굵기 {index} 변경: {text}")
        self.update_chars_components_state(index)

    def on_chars_weight_spinbox_changed(self, index, value):
        """문자 굵기 SpinBox 변경 이벤트 처리"""
        logging.debug(f"문자 굵기 SpinBox {index} 변경: {value}")

    def update_chars_components_state(self, index):
        """문자 관련 컴포넌트들의 활성화 상태를 업데이트합니다."""
        try:
            # 기본 체크박스 상태 확인
            checkbox_name = f"checkBox_Chars{index}"
            chars_enabled = False
            if hasattr(self.ui, checkbox_name):
                checkbox = getattr(self.ui, checkbox_name)
                chars_enabled = checkbox.isChecked()

            # 색상 체크박스 상태 확인
            color_checkbox_name = f"checkBox_CharsColor{index}"
            color_enabled = False
            if hasattr(self.ui, color_checkbox_name):
                color_checkbox = getattr(self.ui, color_checkbox_name)
                color_enabled = color_checkbox.isChecked()

            # 굵기 콤보박스에서 '직접입력' 선택 여부 확인
            weight_combo_name = f"comboBox_CharsWeight{index}"
            is_direct_input = False
            if hasattr(self.ui, weight_combo_name):
                weight_combo = getattr(self.ui, weight_combo_name)
                current_data = weight_combo.currentData()
                is_direct_input = (current_data == "Number")

            # 각 컴포넌트 활성화/비활성화
            component_names = [
                f"lineEdit_Chars{index}",
                f"comboBox_CharsAlign{index}",
                f"comboBox_CharsWeight{index}",
                f"comboBox_CharsStyle{index}"
            ]

            for comp_name in component_names:
                if hasattr(self.ui, comp_name):
                    component = getattr(self.ui, comp_name)
                    component.setEnabled(chars_enabled)

            # SpinBox는 굵기가 '직접입력'이고 체크박스가 활성화된 경우에만 활성화
            spinbox_name = f"spinBox_CharsWeight{index}"
            if hasattr(self.ui, spinbox_name):
                spinbox = getattr(self.ui, spinbox_name)
                spinbox.setEnabled(chars_enabled and is_direct_input)

            # 색상 관련 컴포넌트는 색상 체크박스 상태에 따라 결정
            color_lineedit_name = f"lineEdit_CharsColor{index}"
            if hasattr(self.ui, color_lineedit_name):
                color_lineedit = getattr(self.ui, color_lineedit_name)
                color_lineedit.setEnabled(chars_enabled and color_enabled)

        except Exception as e:
            logging.error(f"문자 컴포넌트 {index} 상태 업데이트 실패: {e}")

    def apply_character_styling_to_text(self, text_lines):
        """
        텍스트 라인들에 문자 및 괄호 스타일링을 적용합니다.

        Args:
            text_lines (list): 텍스트 라인들의 리스트

        Returns:
            list: 스타일이 적용된 텍스트 라인들
        """
        try:
            styled_lines = []

            # 전체 텍스트를 하나의 문자열로 결합 (괄호 스타일링용)
            full_text = '\n'.join(text_lines)

            for line in text_lines:
                styled_line = line

                # 각 문자 스타일 설정을 확인하고 적용
                for i in range(1, 8):
                    styled_line = self.apply_single_character_style(styled_line, i)

                styled_lines.append(styled_line)

            # 괄호 스타일링을 전체 텍스트에 적용
            styled_text = self.apply_bracket_styling_to_text(full_text)

            # 다시 라인별로 분할
            if styled_text != full_text:
                styled_lines = styled_text.split('\n')

            return styled_lines

        except Exception as e:
            logging.error(f"문자 및 괄호 스타일링 적용 실패: {e}")
            return text_lines

    def apply_single_character_style(self, line, index):
        """
        단일 문자 스타일을 라인에 적용합니다.

        Args:
            line (str): 대상 텍스트 라인
            index (int): 문자 스타일 인덱스 (1-7)

        Returns:
            str: 스타일이 적용된 라인
        """
        try:
            # 체크박스가 체크되어 있는지 확인
            checkbox_name = f"checkBox_Chars{index}"
            if not hasattr(self.ui, checkbox_name):
                return line

            checkbox = getattr(self.ui, checkbox_name)
            if not checkbox.isChecked():
                return line

            # 타겟 문자열 가져오기
            lineedit_name = f"lineEdit_Chars{index}"
            if not hasattr(self.ui, lineedit_name):
                return line

            lineedit = getattr(self.ui, lineedit_name)
            target_text = lineedit.text().strip()

            if not target_text:
                return line

            # 완전히 일치하는 라인인지 확인
            if line.strip() != target_text:
                return line

            logging.debug(f"문자 스타일 {index} 적용 대상 라인 발견: '{line.strip()}'")

            # 스타일 정보 수집
            style_info = self.get_character_style_info(index)

            # HTML 스타일 적용
            styled_line = self.apply_character_html_styles(line, style_info)

            logging.debug(f"문자 스타일 {index} 적용 완료: '{styled_line}'")
            return styled_line

        except Exception as e:
            logging.error(f"단일 문자 스타일 {index} 적용 실패: {e}")
            return line

    def get_character_style_info(self, index):
        """
        지정된 인덱스의 문자 스타일 정보를 수집합니다.

        Args:
            index (int): 문자 스타일 인덱스 (1-7)

        Returns:
            dict: 스타일 정보 딕셔너리
        """
        style_info = {
            'alignment': None,
            'weight': None,
            'style': None,
            'color': None,
            'weight_value': None
        }

        try:
            # 정렬 정보
            align_combo_name = f"comboBox_CharsAlign{index}"
            if hasattr(self.ui, align_combo_name):
                align_combo = getattr(self.ui, align_combo_name)
                style_info['alignment'] = align_combo.currentData()

            # 굵기 정보
            weight_combo_name = f"comboBox_CharsWeight{index}"
            if hasattr(self.ui, weight_combo_name):
                weight_combo = getattr(self.ui, weight_combo_name)
                weight_data = weight_combo.currentData()

                if weight_data == "Number":
                    # 직접입력인 경우 SpinBox 값 사용
                    spinbox_name = f"spinBox_CharsWeight{index}"
                    if hasattr(self.ui, spinbox_name):
                        spinbox = getattr(self.ui, spinbox_name)
                        style_info['weight_value'] = spinbox.value()
                else:
                    style_info['weight'] = weight_data

            # 스타일 정보
            style_combo_name = f"comboBox_CharsStyle{index}"
            if hasattr(self.ui, style_combo_name):
                style_combo = getattr(self.ui, style_combo_name)
                style_info['style'] = style_combo.currentData()

            # 색상 정보 (색상 체크박스가 체크된 경우에만)
            color_checkbox_name = f"checkBox_CharsColor{index}"
            if hasattr(self.ui, color_checkbox_name):
                color_checkbox = getattr(self.ui, color_checkbox_name)
                if color_checkbox.isChecked():
                    color_lineedit_name = f"lineEdit_CharsColor{index}"
                    if hasattr(self.ui, color_lineedit_name):
                        color_lineedit = getattr(self.ui, color_lineedit_name)
                        color_value = color_lineedit.text().strip()
                        if color_value and color_value.startswith('#'):
                            style_info['color'] = color_value

            logging.debug(f"문자 스타일 {index} 정보 수집: {style_info}")
            return style_info

        except Exception as e:
            logging.error(f"문자 스타일 {index} 정보 수집 실패: {e}")
            return style_info

    def apply_character_html_styles(self, text, style_info):
        """
        텍스트에 HTML 스타일을 적용합니다.

        Args:
            text (str): 원본 텍스트
            style_info (dict): 스타일 정보

        Returns:
            str: HTML 스타일이 적용된 텍스트
        """
        try:
            # 이미 HTML 태그가 있는지 확인하여 중복 적용 방지
            if '<' in text and '>' in text:
                content = text
            else:
                content = text.strip()

            styles = []

            # 정렬 스타일 적용
            if style_info.get('alignment'):
                alignment = style_info['alignment']
                if alignment == "Left":
                    styles.append("text-align: left")
                elif alignment == "Center":
                    styles.append("text-align: center")
                elif alignment == "Right":
                    styles.append("text-align: right")
                elif alignment == "Justify":
                    styles.append("text-align: justify")

            # 굵기 스타일 적용
            if style_info.get('weight'):
                weight = style_info['weight']
                if weight == "Normal":
                    styles.append("font-weight: normal")
                elif weight == "Bold":
                    styles.append("font-weight: bold")
            elif style_info.get('weight_value'):
                styles.append(f"font-weight: {style_info['weight_value']}")

            # 폰트 스타일 적용
            if style_info.get('style'):
                font_style = style_info['style']
                if font_style == "Normal":
                    styles.append("font-style: normal")
                elif font_style == "Italic":
                    styles.append("font-style: italic")
                elif font_style == "Oblique":
                    styles.append("font-style: oblique")

            # 색상 스타일 적용
            if style_info.get('color'):
                styles.append(f"color: {style_info['color']}")

            # 스타일이 있으면 적용
            if styles:
                style_string = "; ".join(styles)
                # div 태그로 감싸서 블록 레벨 스타일 적용
                styled_text = f'<div style="{style_string}">{content}</div>'
                logging.debug(f"HTML 스타일 적용: {styled_text}")
                return styled_text
            else:
                return text

        except Exception as e:
            logging.error(f"HTML 스타일 적용 실패: {e}")
            return text

    def apply_bracket_styling_to_text(self, text):
        """
        텍스트에 괄호 스타일링을 적용합니다.

        Args:
            text (str): 원본 텍스트

        Returns:
            str: 괄호 스타일이 적용된 텍스트
        """
        try:
            styled_text = text

            # 각 괄호 스타일 설정을 확인하고 적용
            for i in range(1, 8):
                styled_text = self.apply_single_bracket_style(styled_text, i)

            return styled_text

        except Exception as e:
            logging.error(f"괄호 스타일링 적용 실패: {e}")
            return text

    def apply_single_bracket_style(self, text, index):
        """
        단일 괄호 스타일을 텍스트에 적용합니다.

        Args:
            text (str): 대상 텍스트
            index (int): 괄호 스타일 인덱스 (1-7)

        Returns:
            str: 스타일이 적용된 텍스트
        """
        try:
            # 체크박스가 체크되어 있는지 확인
            checkbox_name = f"checkBox_Brackets{index}"
            if not hasattr(self.ui, checkbox_name):
                return text

            checkbox = getattr(self.ui, checkbox_name)
            if not checkbox.isChecked():
                return text

            # 선택된 괄호 패턴 가져오기
            combo_name = f"comboBox_Brackets{index}"
            if not hasattr(self.ui, combo_name):
                return text

            combo = getattr(self.ui, combo_name)
            pattern_data = combo.currentData()

            if not pattern_data:
                return text

            # 패턴 정보 분석
            pattern_id, pattern_regex = pattern_data
            pattern_name = combo.currentText()

            logging.debug(f"괄호 스타일 {index} 적용 시작: {pattern_name}, 패턴: {pattern_regex}")

            # 패턴 유형에 따라 다른 처리 방식 적용
            if self.is_line_based_pattern(pattern_name):
                # 라인 기반 패턴 (Starts with Dash, Starts with Box Drawing Character)
                styled_text = self.apply_line_based_bracket_style(text, pattern_regex, index)
            else:
                # 범위 기반 패턴 (Quotes, Brackets 등)
                styled_text = self.apply_range_based_bracket_style(text, pattern_regex, index)

            logging.debug(f"괄호 스타일 {index} 적용 완료")
            return styled_text

        except Exception as e:
            logging.error(f"단일 괄호 스타일 {index} 적용 실패: {e}")
            return text

    def is_line_based_pattern(self, pattern_name):
        """패턴이 라인 기반인지 확인합니다."""
        line_based_patterns = [
            "Starts with Dash",
            "Starts with Box Drawing Character"
        ]
        return any(pattern in pattern_name for pattern in line_based_patterns)

    def apply_line_based_bracket_style(self, text, pattern_regex, index):
        """
        라인 기반 괄호 패턴의 스타일을 적용합니다.
        (Starts with Dash, Starts with Box Drawing Character)
        """
        try:
            import re
            lines = text.split('\n')
            styled_lines = []

            for line in lines:
                match = re.match(pattern_regex, line)
                if match:
                    # 스타일 정보 수집
                    style_info = self.get_bracket_style_info(index)

                    # HTML 스타일 적용
                    styled_line = self.apply_bracket_html_styles(line, style_info)
                    styled_lines.append(styled_line)

                    logging.debug(f"라인 기반 괄호 스타일 적용: '{line}' -> '{styled_line}'")
                else:
                    styled_lines.append(line)

            return '\n'.join(styled_lines)

        except Exception as e:
            logging.error(f"라인 기반 괄호 스타일 적용 실패: {e}")
            return text

    def apply_range_based_bracket_style(self, text, pattern_regex, index):
        """
        범위 기반 괄호 패턴의 스타일을 적용합니다.
        (Quotes, Brackets 등 - 줄바꿈을 포함한 범위)
        """
        try:
            import re

            # DOTALL 플래그를 사용하여 줄바꿈도 매치
            flags = re.DOTALL | re.MULTILINE

            # 스타일 정보 수집
            style_info = self.get_bracket_style_info(index)

            def style_replacement(match):
                """매치된 텍스트에 스타일을 적용하는 함수"""
                matched_text = match.group(0)
                return self.apply_bracket_html_styles(matched_text, style_info)

            # 패턴에 매치되는 모든 텍스트에 스타일 적용
            styled_text = re.sub(pattern_regex, style_replacement, text, flags=flags)

            if styled_text != text:
                logging.debug(f"범위 기반 괄호 스타일 적용 완료")

            return styled_text

        except Exception as e:
            logging.error(f"범위 기반 괄호 스타일 적용 실패: {e}")
            return text

    def get_bracket_style_info(self, index):
        """
        지정된 인덱스의 괄호 스타일 정보를 수집합니다.

        Args:
            index (int): 괄호 스타일 인덱스 (1-7)

        Returns:
            dict: 스타일 정보 딕셔너리
        """
        style_info = {
            'alignment': None,
            'weight': None,
            'style': None,
            'color': None,
            'weight_value': None
        }

        try:
            # 정렬 정보
            align_combo_name = f"comboBox_BracketsAlign{index}"
            if hasattr(self.ui, align_combo_name):
                align_combo = getattr(self.ui, align_combo_name)
                style_info['alignment'] = align_combo.currentData()

            # 굵기 정보
            weight_combo_name = f"comboBox_BracketsWeight{index}"
            if hasattr(self.ui, weight_combo_name):
                weight_combo = getattr(self.ui, weight_combo_name)
                weight_data = weight_combo.currentData()

                if weight_data == "Number":
                    # 직접입력인 경우 SpinBox 값 사용
                    spinbox_name = f"spinBox_BracketsWeight{index}"
                    if hasattr(self.ui, spinbox_name):
                        spinbox = getattr(self.ui, spinbox_name)
                        style_info['weight_value'] = spinbox.value()
                else:
                    style_info['weight'] = weight_data

            # 스타일 정보
            style_combo_name = f"comboBox_BracketsStyle{index}"
            if hasattr(self.ui, style_combo_name):
                style_combo = getattr(self.ui, style_combo_name)
                style_info['style'] = style_combo.currentData()

            # 색상 정보 (색상 체크박스가 체크된 경우에만)
            color_checkbox_name = f"checkBox_BracketsColor{index}"
            if hasattr(self.ui, color_checkbox_name):
                color_checkbox = getattr(self.ui, color_checkbox_name)
                if color_checkbox.isChecked():
                    color_lineedit_name = f"lineEdit_BracketsColor{index}"
                    if hasattr(self.ui, color_lineedit_name):
                        color_lineedit = getattr(self.ui, color_lineedit_name)
                        color_value = color_lineedit.text().strip()
                        if color_value and color_value.startswith('#'):
                            style_info['color'] = color_value

            logging.debug(f"괄호 스타일 {index} 정보 수집: {style_info}")
            return style_info

        except Exception as e:
            logging.error(f"괄호 스타일 {index} 정보 수집 실패: {e}")
            return style_info

    def apply_bracket_html_styles(self, text, style_info):
        """
        텍스트에 괄호 HTML 스타일을 적용합니다.

        Args:
            text (str): 원본 텍스트
            style_info (dict): 스타일 정보

        Returns:
            str: HTML 스타일이 적용된 텍스트
        """
        # 기존 apply_character_html_styles와 동일한 로직 사용
        return self.apply_character_html_styles(text, style_info)

    def add_chapter_row(self, line_no, title, regex_name, pattern):
        table = self.ui.tableWidget_ChapterList
        row = table.rowCount()
        table.insertRow(row)

        # 체크박스
        chk = QCheckBox()
        chk.setChecked(True)
        chk.stateChanged.connect(self.update_chapter_order)
        table.setCellWidget(row, 0, chk)

        table.setItem(row, 1, QTableWidgetItem(""))  # 순서
        table.setItem(row, 2, QTableWidgetItem(title))
        table.setItem(row, 3, QTableWidgetItem(str(line_no)))

        btn = QPushButton("선택")
        btn.clicked.connect(lambda _, r=row: self.select_chapter_image(r))
        table.setCellWidget(row, 4, btn)

        table.setItem(row, 5, QTableWidgetItem(""))

        self.update_chapter_order()

    def finish_chapter_search(self, total):
        self.ui.label_ChapterCount.setText(f"총 {total}개의 목차를 찾았습니다.")

    def update_chapter_order(self):
        """체크된 챕터들의 순서를 업데이트합니다."""
        table = self.ui.tableWidget_ChapterList
        order = 1

        for row in range(table.rowCount()):
            checkbox = table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                order_item = table.item(row, 1)
                if order_item:
                    order_item.setText(str(order))
                    order += 1
                else:
                    table.setItem(row, 1, QTableWidgetItem(str(order)))
                    order += 1
            else:
                order_item = table.item(row, 1)
                if order_item:
                    order_item.setText("")

    def select_chapter_image(self, row=None):
        """챕터 이미지를 선택합니다. row가 지정되면 특정 행의 삽화를 선택합니다."""
        if row is None:
            # 기존 동작: 전체 챕터 이미지 선택
            file_path, _ = QFileDialog.getOpenFileName(
                self, "챕터 이미지 선택", "",
                "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All Files (*)"
            )
            if not file_path:
                return
            if self.load_image_to_label(file_path, self.ui.label_ChapterImage):
                if hasattr(self.ui, 'label_ChapterImagePath'):
                    self.ui.label_ChapterImagePath.setText(file_path)
        else:
            # 새로운 동작: 특정 행의 삽화 선택
            file_path, _ = QFileDialog.getOpenFileName(
                self, f"행 {row + 1} 삽화 선택", "",
                "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All Files (*)"
            )
            if file_path:
                table = self.ui.tableWidget_ChapterList
                table.setItem(row, 5, QTableWidgetItem(file_path))

    def on_chapter_found(self, line_no, title, regex_name, pattern):
        """챕터가 발견되었을 때 호출됩니다."""
        print(f"[DEBUG] 챕터 발견: Line {line_no}, Title: '{title}'")

        table = self.ui.tableWidget_ChapterList
        row = table.rowCount()
        table.insertRow(row)

        # 체크박스
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        table.setCellWidget(row, 0, checkbox)

        # 순서 (자동 증가)
        order_item = QTableWidgetItem(str(row + 1))
        table.setItem(row, 1, order_item)

        # 제목
        title_item = QTableWidgetItem(title)
        table.setItem(row, 2, title_item)

        # 라인 번호
        line_item = QTableWidgetItem(str(line_no))
        table.setItem(row, 3, line_item)

        # 정규식 이름
        regex_item = QTableWidgetItem(regex_name)
        table.setItem(row, 4, regex_item)

    def on_chapter_search_finished(self, total_found):
        """챕터 검색 완료 처리"""
        print(f"[DEBUG] 검색 완료: {total_found}개 발견, 테이블 행 수: {self.ui.tableWidget_ChapterList.rowCount()}")

        if hasattr(self, 'chapter_progress_dialog') and self.chapter_progress_dialog:
            self.chapter_progress_dialog.close()
            self.chapter_progress_dialog = None

        if total_found == 0:
            QMessageBox.information(self, "검색 완료", "선택한 정규식 패턴으로 챕터를 찾을 수 없습니다.")
        else:
            QMessageBox.information(self, "검색 완료", f"총 {total_found}개의 챕터를 찾았습니다.")

    def on_chapter_search_canceled(self):
        """챕터 검색 취소 처리"""
        if hasattr(self, 'chapter_finder_worker') and self.chapter_finder_worker.isRunning():
            self.chapter_finder_worker.terminate()
            self.chapter_finder_worker.wait()

        if hasattr(self, 'chapter_progress_dialog') and self.chapter_progress_dialog:
            self.chapter_progress_dialog.close()
            self.chapter_progress_dialog = None

    def select_body_font(self):
        """본문 폰트를 선택하는 다이얼로그를 엽니다."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "본문 폰트 선택",
            "",
            "Font Files (*.ttf *.otf *.woff *.woff2);;All Files (*)"
        )

        if file_path:
            self.ui.label_BodyFontPath.setText(file_path)

            # 선택된 폰트를 label_BodyFontExample에 적용
            if hasattr(self.ui, 'label_BodyFontExample'):
                font_id = QFontDatabase.addApplicationFont(file_path)
                if font_id != -1:
                    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                    font = QFont(font_family)
                    font.setPointSize(16)
                    self.ui.label_BodyFontExample.setFont(font)

                    # 폰트 예시 텍스트 설정
                    sample_text = f"""폰트: {font_family}
한글: 그놈의 택시 기사 왈, "퀵서비스 줍쇼~"라며 휘파람을 불었다.
영어: The quick brown fox jumps over the lazy dog.
한자: 風林火山 不動如山 雷霆萬鈞 電光石火
숫자: 0123456789
특수문자: !@#$%^&*()_+-=[]{{}}|;':",./<>?`~"""
                    self.ui.label_BodyFontExample.setText(sample_text)
                else:
                    QMessageBox.warning(self, "폰트 로드 실패", "선택한 폰트를 로드할 수 없습니다.")

            # 백그라운드에서 폰트 호환성 확인
            self.start_background_font_check(file_path, "본문 폰트")

    def select_chapter_font(self):
        """챕터 폰트를 선택하는 다이얼로그를 엽니다."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "챕터 폰트 선택",
            "",
            "Font Files (*.ttf *.otf *.woff *.woff2);;All Files (*)"
        )

        if file_path:
            self.ui.label_ChapterFontPath.setText(file_path)

            # 선택된 폰트를 label_ChapterFontExample에 적용
            if hasattr(self.ui, 'label_ChapterFontExample'):
                font_id = QFontDatabase.addApplicationFont(file_path)
                if font_id != -1:
                    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                    font = QFont(font_family)
                    font.setPointSize(16)
                    self.ui.label_ChapterFontExample.setFont(font)

                    # 폰트 예시 텍스트 설정
                    sample_text = f"""폰트: {font_family}
한글: 그놈의 택시 기사 왈, "퀵서비스 줍쇼~"라며 휘파람을 불었다.
영어: The quick brown fox jumps over the lazy dog.
한자: 風林火山 不動如山 雷霆萬鈞 電光石火
숫자: 0123456789
특수문자: !@#$%^&*()_+-=[]{{}}|;':",./<>?`~"""
                    self.ui.label_ChapterFontExample.setText(sample_text)
                else:
                    QMessageBox.warning(self, "폰트 로드 실패", "선택한 폰트를 로드할 수 없습니다.")

            # 백그라운드에서 폰트 호환성 확인
            self.start_background_font_check(file_path, "챕터 폰트")

    def start_background_font_check(self, font_path, font_type):
        """백그라운드에서 폰트 호환성 확인을 시작합니다."""
        text_file_path = self.ui.label_TextFilePath.text().strip()

        if not text_file_path or not os.path.exists(text_file_path):
            return  # 텍스트 파일이 없으면 검사하지 않음

        # 기존 워커가 실행 중이면 정지
        if self.font_checker_worker and self.font_checker_worker.isRunning():
            self.font_checker_worker.stop()
            self.font_checker_worker.wait()

        # 제목과 저자 정보 수집
        title = self.ui.lineEdit_Title.text().strip()
        author = getattr(self.ui, 'lineEdit_Author', None)
        author_text = author.text().strip() if author else ""

        # 워커 생성 및 시작
        self.font_checker_worker = FontCheckerWorker(
            font_path, text_file_path, title, author_text
        )

        # 진행 상황 다이얼로그 생성
        self.font_progress_dialog = QProgressDialog(
            f"{font_type} 호환성 확인 중...",
            "취소",
            0, 100,
            self
        )
        self.font_progress_dialog.setModal(True)
        self.font_progress_dialog.setMinimumDuration(1000)  # 1초 후에 표시

        # 시그널 연결
        self.font_checker_worker.progress.connect(self.font_progress_dialog.setValue)
        self.font_checker_worker.status_update.connect(self.font_progress_dialog.setLabelText)
        self.font_checker_worker.result_ready.connect(self.on_font_check_completed)
        self.font_checker_worker.error_occurred.connect(self.on_font_check_error)
        self.font_progress_dialog.canceled.connect(self.on_font_check_canceled)

        # 워커 시작
        self.font_checker_worker.start()

    def on_font_check_completed(self, result):
        """폰트 호환성 검사 완료 처리"""
        if self.font_progress_dialog:
            self.font_progress_dialog.close()
            self.font_progress_dialog = None

        if not result['is_compatible']:
            unsupported_count = result['unsupported_count']
            compatibility_rate = result['compatibility_rate']
            font_name = result['font_name']

            # 샘플 문자들 (최대 20개)
            sample_chars = result['unsupported_chars'][:20]
            sample_text = ''.join(sample_chars) if sample_chars else ""

            message = f"""⚠️ 폰트 호환성 경고

폰트: {font_name}
호환률: {compatibility_rate:.1f}%
지원되지 않는 문자: {unsupported_count:,}개

샘플 문자: {sample_text}

이 폰트를 사용하면 일부 문자가 제대로 표시되지 않을 수 있습니다.
다른 폰트를 선택하시거나 계속 진행하시겠습니까?"""

            reply = QMessageBox.question(
                self,
                "폰트 호환성 경고",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                # 사용자가 다른 폰트를 선택하려는 경우
                # 여기서는 아무것도 하지 않음 (폰트 경로는 그대로 유지)
                pass

    def on_font_check_error(self, error_message):
        """폰트 호환성 검사 에러 처리"""
        if self.font_progress_dialog:
            self.font_progress_dialog.close()
            self.font_progress_dialog = None

        QMessageBox.warning(self, "폰트 검사 실패", f"폰트 호환성 검사 중 오류가 발생했습니다:\n{error_message}")

    def on_font_check_canceled(self):
        """폰트 호환성 검사 취소 처리"""
        if self.font_checker_worker and self.font_checker_worker.isRunning():
            self.font_checker_worker.stop()
            self.font_checker_worker.wait()

        if self.font_progress_dialog:
            self.font_progress_dialog.close()
            self.font_progress_dialog = None

    def load_image_to_label(self, image_path, label):
        """이미지를 라벨에 로드합니다."""
        try:
            if not os.path.exists(image_path):
                return False

            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                return False

            # 라벨 크기에 맞게 이미지 스케일링
            label_size = label.size()
            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            label.setPixmap(scaled_pixmap)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return True

        except Exception as e:
            QMessageBox.warning(self, "이미지 로드 실패", f"이미지를 로드할 수 없습니다:\n{str(e)}")
            return False

    def eventFilter(self, obj, event):
        """이벤트 필터 - 이미지 라벨 우클릭 및 더블클릭 처리"""
        if obj in [self.ui.label_CoverImage, self.ui.label_ChapterImage]:
            if event.type() == QEvent.Type.ContextMenu:
                self.show_image_context_menu(obj, event.globalPos())
                return True
            elif event.type() == QEvent.Type.MouseButtonDblClick:
                if obj == self.ui.label_CoverImage:
                    self.search_cover_image_on_google()
                elif obj == self.ui.label_ChapterImage:
                    self.search_chapter_image_on_google()
                return True
        return super().eventFilter(obj, event)

    def search_cover_image_on_google(self):
        """커버 이미지를 구글에서 검색합니다."""
        title = self.ui.lineEdit_Title.text().strip()
        if not title:
            QMessageBox.information(self, "제목 없음", "먼저 제목을 입력해주세요.")
            return

        # 구글 이미지 검색 URL 생성
        search_query = f"{title} 책 표지 커버"
        encoded_query = urllib.parse.quote(search_query)
        google_url = f"https://www.google.com/search?tbm=isch&q={encoded_query}"

        try:
            webbrowser.open(google_url)
        except Exception as e:
            QMessageBox.warning(self, "브라우저 열기 실패", f"브라우저를 열 수 없습니다:\n{str(e)}")

    def search_chapter_image_on_google(self):
        """챕터 이미지를 구글에서 검색합니다."""
        title = self.ui.lineEdit_Title.text().strip()
        if not title:
            QMessageBox.information(self, "제목 없음", "먼저 제목을 입력해주세요.")
            return

        # 구글 이미지 검색 URL 생성
        search_query = f"{title} 챕터 삽화 일러스트"
        encoded_query = urllib.parse.quote(search_query)
        google_url = f"https://www.google.com/search?tbm=isch&q={encoded_query}"

        try:
            webbrowser.open(google_url)
        except Exception as e:
            QMessageBox.warning(self, "브라우저 열기 실패", f"브라우저를 열 수 없습니다:\n{str(e)}")

    def show_image_context_menu(self, label, position):
        """이미지 라벨의 컨텍스트 메뉴를 표시합니다."""
        menu = QMenu(self)

        if label == self.ui.label_CoverImage:
            select_action = menu.addAction("커버 이미지 선택")
            paste_action = menu.addAction("클립보드에서 붙여넣기 (Ctrl+V)")
            menu.addSeparator()
            delete_action = menu.addAction("커버 이미지 삭제")

            select_action.triggered.connect(self.select_cover_image)
            paste_action.triggered.connect(self.paste_cover_image_from_clipboard)
            delete_action.triggered.connect(self.delete_cover_image)

            # 클립보드에 이미지가 있는지 확인하여 붙여넣기 메뉴 활성화/비활성화
            clipboard = QGuiApplication.clipboard()
            paste_action.setEnabled(not clipboard.pixmap().isNull())

        elif label == self.ui.label_ChapterImage:
            select_action = menu.addAction("챕터 이미지 선택")
            paste_action = menu.addAction("클립보드에서 붙여넣기 (Ctrl+V)")
            menu.addSeparator()
            delete_action = menu.addAction("챕터 이미지 삭제")

            select_action.triggered.connect(self.select_chapter_image)
            paste_action.triggered.connect(self.paste_chapter_image_from_clipboard)
            delete_action.triggered.connect(self.delete_chapter_image)

            # 클립보드에 이미지가 있는지 확인하여 붙여넣기 메뉴 활성화/비활성화
            clipboard = QGuiApplication.clipboard()
            paste_action.setEnabled(not clipboard.pixmap().isNull())

        menu.exec(position)

    # =================================================================
    # 스타일 관리 메서드들 (선택적 사용)
    # =================================================================

    def init_style_manager(self):
        """스타일 매니저를 초기화합니다. (선택적 사용)"""
        try:
            self.style_manager = StyleManager()
            return True
        except Exception as e:
            print(f"[ERROR] 스타일 매니저 초기화 실패: {str(e)}")
            return False

    def apply_custom_styles(self, style_files: list = None):
        """
        통합된 CSS 스타일을 적용합니다. (선택적 사용)

        Args:
            style_files: 사용하지 않음 (호환성을 위해 유지)
        """
        if not hasattr(self, 'style_manager'):
            if not self.init_style_manager():
                return

        try:
            stylesheet = self.style_manager.get_combined_stylesheet()
            self.setStyleSheet(stylesheet)
            print(f"[INFO] 통합 스타일 적용 완료: {len(stylesheet)} 문자")
        except Exception as e:
            print(f"[ERROR] 스타일 적용 실패: {str(e)}")

    def apply_button_styles_only(self):
        """통합 스타일을 적용합니다. (호환성을 위해 유지)"""
        self.apply_custom_styles()

    def apply_table_styles_only(self):
        """통합 스타일을 적용합니다. (호환성을 위해 유지)"""
        self.apply_custom_styles()

    def apply_form_styles_only(self):
        """통합 스타일을 적용합니다. (호환성을 위해 유지)"""
        self.apply_custom_styles()

    def apply_essential_styles_only(self):
        """통합 스타일을 적용합니다. (호환성을 위해 유지)"""
        self.apply_custom_styles()

    def reset_to_default_styles(self):
        """기본 PyQt6 스타일로 리셋합니다."""
        self.setStyleSheet("")
        print("[INFO] 기본 스타일로 리셋 완료")

    def get_style_template_info(self):
        """스타일 템플릿 정보를 출력합니다."""
        if not hasattr(self, 'style_manager'):
            if not self.init_style_manager():
                return

        print("\n=== 사용 가능한 스타일 템플릿 ===")
        templates = [
            ("button", "버튼"),
            ("label", "라벨"),
            ("combobox", "콤보박스"),
            ("table", "테이블"),
            ("lineedit", "입력창"),
            ("checkbox", "체크박스"),
            ("tab", "탭"),
            ("progressbar", "진행바")
        ]

        for control_type, korean_name in templates:
            props = self.style_manager.get_template_properties(control_type)
            print(f"{korean_name} ({control_type}): {', '.join(props)}")

    def initialize_font_comboboxes(self):
        """폰트 콤보박스들을 초기화합니다."""
        from ePub_db import get_font_folder

        # 드롭다운 최소 너비 설정 (폰트 폴더가 없어도 미리 설정)
        self.ui.comboBox_SelectBodyFont.view().setMinimumWidth(400)
        self.ui.comboBox_SelectChapterFont.view().setMinimumWidth(400)

        font_folder = get_font_folder()
        if font_folder and os.path.exists(font_folder):
            self.load_fonts_from_folder(font_folder)
            self.ui.comboBox_SelectBodyFont.setEnabled(True)
            self.ui.comboBox_SelectChapterFont.setEnabled(True)
        else:
            # 폰트 폴더가 없으면 비활성화하고 기본 항목만 추가
            self.ui.comboBox_SelectBodyFont.clear()
            self.ui.comboBox_SelectChapterFont.clear()
            self.ui.comboBox_SelectBodyFont.addItem("폰트 폴더를 먼저 설정하세요", "")
            self.ui.comboBox_SelectChapterFont.addItem("폰트 폴더를 먼저 설정하세요", "")
            self.ui.comboBox_SelectBodyFont.setEnabled(False)
            self.ui.comboBox_SelectChapterFont.setEnabled(False)

    def set_font_folder(self):
        """폰트 폴더를 선택하고 설정합니다."""
        from ePub_db import save_font_folder

        folder_path = QFileDialog.getExistingDirectory(
            self, "폰트 폴더 선택", "",
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )

        if not folder_path:
            return

        # 폴더에 폰트 파일이 있는지 확인
        font_files = self.get_font_files_from_folder(folder_path)
        if not font_files:
            QMessageBox.warning(
                self, "폰트 없음",
                "선택한 폴더에 폰트 파일(.ttf, .otf, .woff, .woff2)이 없습니다."
            )
            return

        # 데이터베이스에 저장
        success, message = save_font_folder(folder_path)
        if success:
            # 폰트 목록 로드
            self.load_fonts_from_folder(folder_path)
            self.ui.comboBox_SelectBodyFont.setEnabled(True)
            self.ui.comboBox_SelectChapterFont.setEnabled(True)
            QMessageBox.information(self, "성공", f"폰트 폴더가 설정되었습니다.\n{len(font_files)}개의 폰트 파일을 찾았습니다.")
        else:
            QMessageBox.critical(self, "오류", message)

    def get_font_files_from_folder(self, folder_path):
        """폴더에서 폰트 파일 목록을 반환합니다."""
        font_extensions = ['.ttf', '.otf', '.woff', '.woff2']
        font_files = []

        try:
            for file_name in os.listdir(folder_path):
                file_ext = os.path.splitext(file_name)[1].lower()
                if file_ext in font_extensions:
                    font_files.append({
                        'name': os.path.splitext(file_name)[0],
                        'path': os.path.join(folder_path, file_name),
                        'filename': file_name
                    })
        except Exception as e:
            print(f"폰트 파일 검색 중 오류: {str(e)}")

        # 이름순으로 정렬
        font_files.sort(key=lambda x: x['name'])
        return font_files

    def load_fonts_from_folder(self, folder_path):
        """폴더의 폰트들을 콤보박스에 로드합니다."""
        font_files = self.get_font_files_from_folder(folder_path)

        # 콤보박스 초기화
        self.ui.comboBox_SelectBodyFont.clear()
        self.ui.comboBox_SelectChapterFont.clear()

        # 드롭다운 최소 너비 설정
        self.ui.comboBox_SelectBodyFont.view().setMinimumWidth(400)
        self.ui.comboBox_SelectChapterFont.view().setMinimumWidth(400)

        # 기본 항목 추가
        self.ui.comboBox_SelectBodyFont.addItem("폰트 선택", "")
        self.ui.comboBox_SelectChapterFont.addItem("폰트 선택", "")

        # 시스템에 폰트 등록 및 콤보박스에 추가
        for font_info in font_files:
            # 폰트 파일을 시스템에 등록
            font_id = QFontDatabase.addApplicationFont(font_info['path'])

            if font_id != -1:
                # 등록된 폰트 패밀리 이름 가져오기
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    font_family = font_families[0]

                    # 콤보박스에 항목 추가
                    self.ui.comboBox_SelectBodyFont.addItem(font_info['name'], font_info['path'])
                    self.ui.comboBox_SelectChapterFont.addItem(font_info['name'], font_info['path'])

                    # 현재 추가된 항목의 인덱스
                    body_index = self.ui.comboBox_SelectBodyFont.count() - 1
                    chapter_index = self.ui.comboBox_SelectChapterFont.count() - 1

                    # 해당 폰트로 표시되도록 폰트 설정
                    font = QFont(font_family, 14)  # 폰트 크기를 14로 증가
                    self.ui.comboBox_SelectBodyFont.setItemData(body_index, font, Qt.ItemDataRole.FontRole)
                    self.ui.comboBox_SelectChapterFont.setItemData(chapter_index, font, Qt.ItemDataRole.FontRole)
            else:
                # 폰트 등록 실패 시 기본 폰트로 추가
                self.ui.comboBox_SelectBodyFont.addItem(font_info['name'], font_info['path'])
                self.ui.comboBox_SelectChapterFont.addItem(font_info['name'], font_info['path'])

        # 이벤트 연결
        self.ui.comboBox_SelectBodyFont.currentTextChanged.connect(self.on_body_font_changed)
        self.ui.comboBox_SelectChapterFont.currentTextChanged.connect(self.on_chapter_font_changed)

    def on_body_font_changed(self):
        """본문 폰트가 변경되었을 때 호출됩니다."""
        font_path = self.ui.comboBox_SelectBodyFont.currentData()
        if font_path and os.path.exists(font_path):
            # 폰트 경로를 라벨에 표시 (기존 동작과 호환)
            if hasattr(self.ui, 'label_BodyFontPath'):
                self.ui.label_BodyFontPath.setText(font_path)

            # 폰트 예시 업데이트
            if hasattr(self.ui, 'label_BodyFontExample'):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                    font = QFont(font_family)
                    font.setPointSize(16)
                    self.ui.label_BodyFontExample.setFont(font)

                    # 폰트 예시 텍스트 설정
                    sample_text = f"""폰트: {font_family}
한글: 그놈의 택시 기사 왈, "퀵서비스 줍쇼~"라며 휘파람을 불었다.
영어: The quick brown fox jumps over the lazy dog.
한자: 風林火山 不動如山 雷霆萬鈞 電光石火
숫자: 0123456789
특수문자: !@#$%^&*()_+-=[]{{}}|;':",./<>?`~"""
                    self.ui.label_BodyFontExample.setText(sample_text)

            print(f"[INFO] 본문 폰트 선택: {os.path.basename(font_path)}")

    def on_chapter_font_changed(self):
        """챕터 폰트가 변경되었을 때 호출됩니다."""
        font_path = self.ui.comboBox_SelectChapterFont.currentData()
        if font_path and os.path.exists(font_path):
            # 폰트 경로를 라벨에 표시 (기존 동작과 호환)
            if hasattr(self.ui, 'label_ChapterFontPath'):
                self.ui.label_ChapterFontPath.setText(font_path)

            # 폰트 예시 업데이트
            if hasattr(self.ui, 'label_ChapterFontExample'):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                    font = QFont(font_family)
                    font.setPointSize(16)
                    self.ui.label_ChapterFontExample.setFont(font)

                    # 폰트 예시 텍스트 설정
                    sample_text = f"""폰트: {font_family}
한글: 그놈의 택시 기사 왈, "퀵서비스 줍쇼~"라며 휘파람을 불었다.
영어: The quick brown fox jumps over the lazy dog.
한자: 風林火山 不動如山 雷霆萬鈞 電光石火
숫자: 0123456789
특수문자: !@#$%^&*()_+-=[]{{}}|;':",./<>?`~"""
                    self.ui.label_ChapterFontExample.setText(sample_text)

            print(f"[INFO] 챕터 폰트 선택: {os.path.basename(font_path)}")

    def select_body_font(self):
        """본문 폰트를 개별 파일로 선택합니다. (기존 방식 유지)"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "본문 폰트 선택", "",
            "Font Files (*.ttf *.otf *.woff *.woff2);;All Files (*)"
        )
        if file_path and hasattr(self.ui, 'label_BodyFontPath'):
            self.ui.label_BodyFontPath.setText(file_path)

    def select_chapter_font(self):
        """챕터 폰트를 개별 파일로 선택합니다. (기존 방식 유지)"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "챕터 폰트 선택", "",
            "Font Files (*.ttf *.otf *.woff *.woff2);;All Files (*)"
        )
        if file_path and hasattr(self.ui, 'label_ChapterFontPath'):
            self.ui.label_ChapterFontPath.setText(file_path)


if __name__ == "__main__":
    """
    애플리케이션 진입점

    데이터베이스 초기화 후 GUI 애플리케이션을 시작합니다.
    """
    try:
        # 데이터베이스 초기화
        initialize_database()
        logging.info("데이터베이스 초기화 완료")

        # PyQt6 애플리케이션 시작
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()

        logging.info("GUI 애플리케이션 시작")
        sys.exit(app.exec())

    except Exception as e:
        logging.critical(f"애플리케이션 시작 실패: {e}")
        if 'app' in locals():
            app.quit()
        sys.exit(1)
