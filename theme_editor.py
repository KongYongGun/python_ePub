"""
CSS 테마 편집 다이얼로그
사용자가 CSS 테마를 편집하고 새로 만들 수 있는 기능을 제공합니다.
"""

import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QComboBox, QMessageBox, QSplitter,
    QListWidget, QListWidgetItem, QWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCharFormat, QSyntaxHighlighter
import re

class CSSHighlighter(QSyntaxHighlighter):
    """CSS 구문 강조를 위한 클래스"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # CSS 규칙 색상 정의
        # 속성명 (color, background-color 등)
        property_format = QTextCharFormat()
        property_format.setForeground(Qt.GlobalColor.blue)
        property_format.setFontWeight(QFont.Weight.Bold)
        property_pattern = r'\b[a-zA-Z-]+(?=\s*:)'
        self.highlighting_rules.append((re.compile(property_pattern), property_format))

        # 선택자 (QMainWindow, QPushButton 등)
        selector_format = QTextCharFormat()
        selector_format.setForeground(Qt.GlobalColor.darkMagenta)
        selector_format.setFontWeight(QFont.Weight.Bold)
        selector_pattern = r'Q[A-Za-z]+|[.#][a-zA-Z-_][a-zA-Z0-9-_]*'
        self.highlighting_rules.append((re.compile(selector_pattern), selector_format))

        # 값 (문자열, 색상 등)
        value_format = QTextCharFormat()
        value_format.setForeground(Qt.GlobalColor.darkGreen)
        value_pattern = r'[#][0-9a-fA-F]{3,6}|[0-9]+px|[0-9]+%|[0-9]+em|"[^"]*"|\'[^\']*\''
        self.highlighting_rules.append((re.compile(value_pattern), value_format))

        # 주석
        comment_format = QTextCharFormat()
        comment_format.setForeground(Qt.GlobalColor.gray)
        comment_format.setFontItalic(True)
        comment_pattern = r'/\*.*?\*/'
        self.highlighting_rules.append((re.compile(comment_pattern, re.DOTALL), comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format)

class ThemeEditorDialog(QDialog):
    """CSS 테마 편집 다이얼로그"""

    theme_changed = pyqtSignal(int)  # 테마가 변경되었을 때 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CSS 테마 편집기")
        self.setGeometry(200, 200, 1000, 700)
        self.setModal(True)

        self.current_theme_id = None
        self.themes = []
        self.setup_ui()
        self.load_themes()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout()

        # 상단 툴바
        toolbar_layout = QHBoxLayout()

        self.new_button = QPushButton("새 테마")
        self.save_button = QPushButton("저장")
        self.delete_button = QPushButton("삭제")
        self.set_default_button = QPushButton("기본으로 설정")

        self.new_button.clicked.connect(self.new_theme)
        self.save_button.clicked.connect(self.save_theme)
        self.delete_button.clicked.connect(self.delete_theme)
        self.set_default_button.clicked.connect(self.set_as_default)

        toolbar_layout.addWidget(self.new_button)
        toolbar_layout.addWidget(self.save_button)
        toolbar_layout.addWidget(self.delete_button)
        toolbar_layout.addWidget(self.set_default_button)
        toolbar_layout.addStretch()

        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.accept)
        toolbar_layout.addWidget(close_button)

        layout.addLayout(toolbar_layout)

        # 메인 영역 - 스플리터로 분할
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 왼쪽: 테마 목록
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        left_layout.addWidget(QLabel("테마 목록"))
        self.theme_list = QListWidget()
        self.theme_list.currentItemChanged.connect(self.on_theme_selected)
        left_layout.addWidget(self.theme_list)

        # 오른쪽: 편집 영역
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 테마 정보
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        info_layout = QVBoxLayout(info_frame)

        # 테마 이름
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("테마 이름:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        info_layout.addLayout(name_layout)

        # 테마 설명
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("설명:"))
        self.description_edit = QLineEdit()
        desc_layout.addWidget(self.description_edit)
        info_layout.addLayout(desc_layout)

        right_layout.addWidget(info_frame)

        # CSS 편집기
        right_layout.addWidget(QLabel("CSS 코드:"))
        self.css_editor = QTextEdit()
        self.css_editor.setFont(QFont("Consolas", 10))

        # CSS 구문 강조 적용
        self.highlighter = CSSHighlighter(self.css_editor.document())

        right_layout.addWidget(self.css_editor)

        # 미리보기 버튼
        preview_button = QPushButton("미리보기 적용")
        preview_button.clicked.connect(self.preview_theme)
        right_layout.addWidget(preview_button)

        # 스플리터에 위젯 추가
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 750])  # 왼쪽:오른쪽 비율

        layout.addWidget(splitter)
        self.setLayout(layout)

    def load_themes(self):
        """데이터베이스에서 테마 목록 로드"""
        try:
            from ePub_db import get_all_css_themes
            self.themes = get_all_css_themes()

            self.theme_list.clear()
            for theme in self.themes:
                theme_id, name, description, content, is_default = theme
                item = QListWidgetItem()
                display_text = name
                if is_default:
                    display_text += " (기본)"
                item.setText(display_text)
                item.setData(Qt.ItemDataRole.UserRole, theme_id)
                self.theme_list.addItem(item)

            # 첫 번째 항목 선택
            if self.theme_list.count() > 0:
                self.theme_list.setCurrentRow(0)

        except Exception as e:
            QMessageBox.critical(self, "오류", f"테마 로드 중 오류가 발생했습니다:\n{str(e)}")

    def on_theme_selected(self, current, previous):
        """테마 선택 시 호출"""
        if current is None:
            return

        theme_id = current.data(Qt.ItemDataRole.UserRole)
        self.current_theme_id = theme_id

        # 해당 테마 정보 로드
        for theme in self.themes:
            if theme[0] == theme_id:
                theme_id, name, description, content, is_default = theme
                self.name_edit.setText(name)
                self.description_edit.setText(description or "")
                self.css_editor.setPlainText(content)
                break

    def new_theme(self):
        """새 테마 생성"""
        self.current_theme_id = None
        self.name_edit.setText("새 테마")
        self.description_edit.setText("")
        self.css_editor.setPlainText(self.get_default_css_template())

    def get_default_css_template(self):
        """새 테마를 위한 기본 CSS 템플릿"""
        return """/* 새 CSS 테마 */
QMainWindow {
    background-color: #f5f5f5;
    color: #333;
    font-family: "Segoe UI", Arial, sans-serif;
}

QPushButton {
    background-color: #0078d4;
    border: none;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #106ebe;
}

/* 여기에 더 많은 스타일을 추가하세요 */"""

    def save_theme(self):
        """테마 저장"""
        name = self.name_edit.text().strip()
        description = self.description_edit.text().strip()
        content = self.css_editor.toPlainText()

        if not name:
            QMessageBox.warning(self, "경고", "테마 이름을 입력해주세요.")
            return

        if not content.strip():
            QMessageBox.warning(self, "경고", "CSS 내용을 입력해주세요.")
            return

        try:
            if self.current_theme_id:
                # 기존 테마 업데이트
                from ePub_db import update_css_theme
                update_css_theme(self.current_theme_id, name, description, content)
                QMessageBox.information(self, "성공", "테마가 업데이트되었습니다.")
            else:
                # 새 테마 생성
                from ePub_db import add_custom_css_theme
                theme_id = add_custom_css_theme(name, description, content)
                self.current_theme_id = theme_id
                QMessageBox.information(self, "성공", "새 테마가 생성되었습니다.")

            # 테마 목록 새로고침
            self.load_themes()
            self.theme_changed.emit(self.current_theme_id)

        except Exception as e:
            QMessageBox.critical(self, "오류", f"테마 저장 중 오류가 발생했습니다:\n{str(e)}")

    def delete_theme(self):
        """테마 삭제"""
        if not self.current_theme_id:
            QMessageBox.warning(self, "경고", "삭제할 테마를 선택해주세요.")
            return

        reply = QMessageBox.question(
            self, "확인", "선택한 테마를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                from ePub_db import delete_css_theme
                success, message = delete_css_theme(self.current_theme_id)

                if success:
                    QMessageBox.information(self, "성공", message)
                    self.load_themes()
                    self.theme_changed.emit(0)  # 테마 목록 새로고침 신호
                else:
                    QMessageBox.warning(self, "경고", message)

            except Exception as e:
                QMessageBox.critical(self, "오류", f"테마 삭제 중 오류가 발생했습니다:\n{str(e)}")

    def set_as_default(self):
        """선택한 테마를 기본으로 설정"""
        if not self.current_theme_id:
            QMessageBox.warning(self, "경고", "기본으로 설정할 테마를 선택해주세요.")
            return

        try:
            from ePub_db import set_default_css_theme
            set_default_css_theme(self.current_theme_id)
            QMessageBox.information(self, "성공", "기본 테마가 변경되었습니다.")
            self.load_themes()
            self.theme_changed.emit(self.current_theme_id)

        except Exception as e:
            QMessageBox.critical(self, "오류", f"기본 테마 설정 중 오류가 발생했습니다:\n{str(e)}")

    def preview_theme(self):
        """현재 편집 중인 테마를 미리보기로 적용"""
        content = self.css_editor.toPlainText()
        if self.parent():
            self.parent().setStyleSheet(content)

# 테스트용 실행 코드
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = ThemeEditorDialog()
    dialog.show()
    sys.exit(app.exec())
