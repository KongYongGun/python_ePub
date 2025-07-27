#!/usr/bin/env python3
"""
폰트 크기 디버깅 테스트 스크립트
테마 변경 전후의 폰트 크기를 비교합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from ePub_ui import Ui_MainWindow
from ePub_loader import load_stylesheet_options
from ePub_db import get_css_theme_by_id

class FontDebugWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 초기 폰트 정보 수집
        self.collect_initial_font_info()

        # 테마 콤보박스 초기화
        self.initialize_theme_combobox()
        self.ui.comboBox_selectTheme.currentIndexChanged.connect(self.on_theme_changed)

        # 디버그 정보 출력 버튼 추가
        debug_button = QPushButton("폰트 정보 출력")
        debug_button.clicked.connect(self.print_font_info)
        self.ui.verticalLayout.addWidget(debug_button)

        self.setWindowTitle("폰트 크기 디버깅 테스트")

    def collect_initial_font_info(self):
        """초기 폰트 정보를 수집합니다."""
        print("=== 초기 폰트 정보 ===")
        self.print_widget_font_info("메인 창", self)
        self.print_widget_font_info("텍스트 파일 경로 라벨", self.ui.label_TextFilePath)
        if hasattr(self.ui, 'lineEdit_Title'):
            self.print_widget_font_info("제목 입력", self.ui.lineEdit_Title)
        if hasattr(self.ui, 'label_8'):
            self.print_widget_font_info("라벨_8", self.ui.label_8)

    def print_widget_font_info(self, name, widget):
        """위젯의 폰트 정보를 출력합니다."""
        font = widget.font()
        print(f"{name}:")
        print(f"  - 폰트 패밀리: {font.family()}")
        print(f"  - 폰트 크기: {font.pointSize()}pt")
        print(f"  - 픽셀 크기: {font.pixelSize()}px")
        print(f"  - 볼드: {font.bold()}")
        print(f"  - 기본 폰트 여부: {font.defaultFamily()}")
        print()

    def initialize_theme_combobox(self):
        """테마 콤보박스를 초기화합니다."""
        theme_options = load_stylesheet_options()
        self.ui.comboBox_selectTheme.clear()

        for option in theme_options:
            option_id, option_name, option_description, option_content, is_default = option
            display_text = f"{option_name}"
            if option_description:
                display_text += f" - {option_description}"
            self.ui.comboBox_selectTheme.addItem(display_text, option_id)

    def on_theme_changed(self):
        """테마가 변경되었을 때 호출됩니다."""
        theme_id = self.ui.comboBox_selectTheme.currentData()
        theme_name = self.ui.comboBox_selectTheme.currentText()

        print(f"\n=== 테마 변경: {theme_name} (ID: {theme_id}) ===")

        if theme_id:
            theme = get_css_theme_by_id(theme_id)
            if theme:
                theme_id, name, description, content, is_default = theme
                print(f"CSS 길이: {len(content)} 문자")

                # CSS 적용 전 폰트 정보
                print("\n--- CSS 적용 전 ---")
                self.print_current_font_info()

                # CSS 적용
                self.setStyleSheet(content)

                # CSS 적용 후 폰트 정보
                print("--- CSS 적용 후 ---")
                self.print_current_font_info()

                # CSS에서 폰트 관련 설정 확인
                self.analyze_css_font_settings(content)

    def print_current_font_info(self):
        """현재 폰트 정보를 출력합니다."""
        self.print_widget_font_info("메인 창", self)
        self.print_widget_font_info("텍스트 파일 경로 라벨", self.ui.label_TextFilePath)
        if hasattr(self.ui, 'lineEdit_Title'):
            self.print_widget_font_info("제목 입력", self.ui.lineEdit_Title)
        if hasattr(self.ui, 'label_8'):
            self.print_widget_font_info("라벨_8", self.ui.label_8)

    def analyze_css_font_settings(self, css_content):
        """CSS 내용에서 폰트 관련 설정을 분석합니다."""
        print("--- CSS 폰트 설정 분석 ---")
        lines = css_content.split('\n')
        font_related_lines = []

        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ['font', 'size']):
                font_related_lines.append(f"라인 {i+1}: {line.strip()}")

        if font_related_lines:
            print("폰트 관련 CSS 설정:")
            for line in font_related_lines:
                print(f"  {line}")
        else:
            print("폰트 관련 CSS 설정 없음")
        print()

    def print_font_info(self):
        """현재 폰트 정보를 출력합니다."""
        print(f"\n=== 현재 폰트 정보 (테마: {self.ui.comboBox_selectTheme.currentText()}) ===")
        self.print_current_font_info()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FontDebugWindow()
    window.show()
    sys.exit(app.exec())
