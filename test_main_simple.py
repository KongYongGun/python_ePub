#!/usr/bin/env python3
"""
실제 main.py와 유사한 환경에서 폰트 크기 변화를 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from ePub_ui import Ui_MainWindow
from ePub_loader import load_stylesheet_options
from ePub_db import get_css_theme_by_id, get_default_css_theme

class MainTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 테마 콤보박스 초기화
        self.initialize_theme_combobox()
        self.ui.comboBox_selectTheme.currentIndexChanged.connect(self.on_theme_selected)

        # 기본 테마 적용
        self.apply_default_css_theme()

        self.setWindowTitle("메인 앱 폰트 테스트 - 테마를 변경해보세요")

        # 폰트 크기 체크 버튼 추가
        check_button = QPushButton("현재 폰트 크기 확인")
        check_button.clicked.connect(self.check_current_fonts)
        if hasattr(self.ui, 'verticalLayout'):
            self.ui.verticalLayout.addWidget(check_button)

        # 초기 폰트 크기 출력
        print("=== 앱 시작 시 폰트 크기 ===")
        self.check_current_fonts()

    def initialize_theme_combobox(self):
        """테마 콤보박스를 초기화합니다."""
        theme_options = load_stylesheet_options()
        self.ui.comboBox_selectTheme.clear()

        default_index = 0
        for i, option in enumerate(theme_options):
            option_id, option_name, option_description, option_content, is_default = option
            display_text = f"{option_name}"
            if option_description:
                display_text += f" - {option_description}"
            self.ui.comboBox_selectTheme.addItem(display_text, option_id)

            if is_default:
                default_index = i

        self.ui.comboBox_selectTheme.setCurrentIndex(default_index)

    def apply_default_css_theme(self):
        """기본 CSS 테마를 적용합니다."""
        try:
            theme = get_default_css_theme()
            if theme:
                theme_id, name, description, content, is_default = theme
                print(f"기본 테마 적용: {name}")
                self.setStyleSheet(content)
            else:
                print("기본 테마를 찾을 수 없습니다.")
        except Exception as e:
            print(f"기본 테마 적용 실패: {str(e)}")

    def on_theme_selected(self):
        """테마가 선택되었을 때 호출됩니다."""
        theme_id = self.ui.comboBox_selectTheme.currentData()
        theme_name = self.ui.comboBox_selectTheme.currentText()

        print(f"\n=== 테마 변경: {theme_name} ===")

        if theme_id:
            try:
                theme = get_css_theme_by_id(theme_id)
                if theme:
                    theme_id, name, description, content, is_default = theme
                    print(f"테마 적용 중: {name}")
                    self.setStyleSheet(content)
                    print("테마 적용 완료")

                    # 폰트 크기 확인
                    self.check_current_fonts()
                else:
                    print(f"테마를 찾을 수 없습니다. ID: {theme_id}")
            except Exception as e:
                print(f"테마 적용 실패: {str(e)}")

    def check_current_fonts(self):
        """현재 폰트 크기를 확인합니다."""
        widgets_to_check = [
            ("메인창", self),
            ("텍스트 파일 경로", self.ui.label_TextFilePath),
        ]

        if hasattr(self.ui, 'lineEdit_Title'):
            widgets_to_check.append(("제목 입력", self.ui.lineEdit_Title))

        print("현재 폰트 크기:")
        for name, widget in widgets_to_check:
            font = widget.font()
            print(f"  {name}: {font.pointSize()}pt ({font.family()})")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainTestWindow()
    window.show()
    sys.exit(app.exec())
