#!/usr/bin/env python3
"""
테마 변경 시 폰트 크기 변화 실시간 측정
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

class FontTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("폰트 크기 테스트 - 테마를 변경해보세요")

        # 테마 콤보박스 초기화
        self.initialize_theme_combobox()
        self.ui.comboBox_selectTheme.currentIndexChanged.connect(self.on_theme_changed)

        # 테스트 위젯들의 초기 폰트 크기 저장
        self.initial_fonts = {}
        self.store_initial_fonts()

        # 디버그 정보를 표시할 라벨 추가
        self.debug_label = QLabel("테마를 변경하면 폰트 크기 변화를 확인할 수 있습니다.")
        self.debug_label.setWordWrap(True)
        self.debug_label.setStyleSheet("background-color: lightyellow; padding: 10px; border: 1px solid gray;")

        # 메인 레이아웃에 디버그 라벨 추가
        if hasattr(self.ui, 'verticalLayout'):
            self.ui.verticalLayout.addWidget(self.debug_label)

        self.show_initial_info()

    def store_initial_fonts(self):
        """초기 폰트 정보를 저장합니다."""
        test_widgets = [
            ("메인창", self),
            ("텍스트 파일 경로", self.ui.label_TextFilePath),
        ]

        if hasattr(self.ui, 'lineEdit_Title'):
            test_widgets.append(("제목 입력", self.ui.lineEdit_Title))
        if hasattr(self.ui, 'label_8'):
            test_widgets.append(("라벨_8", self.ui.label_8))

        for name, widget in test_widgets:
            font = widget.font()
            self.initial_fonts[name] = {
                'family': font.family(),
                'pointSize': font.pointSize(),
                'pixelSize': font.pixelSize()
            }

    def show_initial_info(self):
        """초기 폰트 정보를 표시합니다."""
        info = "=== 초기 폰트 크기 ===\n"
        for name, font_info in self.initial_fonts.items():
            info += f"{name}: {font_info['pointSize']}pt ({font_info['family']})\n"
        print(info)
        self.debug_label.setText(info)

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

        if theme_id:
            theme = get_css_theme_by_id(theme_id)
            if theme:
                theme_id, name, description, content, is_default = theme

                # CSS 적용
                self.setStyleSheet(content)

                # 폰트 크기 변화 확인
                self.check_font_changes(theme_name)

    def check_font_changes(self, theme_name):
        """폰트 크기 변화를 확인합니다."""
        current_info = f"=== 테마 변경 후: {theme_name} ===\n"
        changes_detected = False

        test_widgets = [
            ("메인창", self),
            ("텍스트 파일 경로", self.ui.label_TextFilePath),
        ]

        if hasattr(self.ui, 'lineEdit_Title'):
            test_widgets.append(("제목 입력", self.ui.lineEdit_Title))
        if hasattr(self.ui, 'label_8'):
            test_widgets.append(("라벨_8", self.ui.label_8))

        for name, widget in test_widgets:
            current_font = widget.font()
            initial = self.initial_fonts[name]

            current_size = current_font.pointSize()
            initial_size = initial['pointSize']

            if current_size != initial_size:
                changes_detected = True
                current_info += f"🔴 {name}: {initial_size}pt → {current_size}pt (변화: {current_size - initial_size:+d}pt)\n"
            else:
                current_info += f"✅ {name}: {current_size}pt (변화 없음)\n"

        if changes_detected:
            current_info += "\n⚠️ 폰트 크기 변화가 감지되었습니다!"
        else:
            current_info += "\n✅ 모든 폰트 크기가 유지되었습니다."

        print(current_info)
        self.debug_label.setText(current_info)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FontTestWindow()
    window.show()
    sys.exit(app.exec())
