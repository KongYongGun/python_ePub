#!/usr/bin/env python3
"""
정렬 콤보박스 초기화 테스트
"""

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel

def test_alignment_combo():
    """정렬 콤보박스 테스트"""
    app = QApplication(sys.argv)

    # 테스트 윈도우 생성
    window = QWidget()
    window.setWindowTitle("정렬 콤보박스 테스트")
    layout = QVBoxLayout()

    # 정렬 옵션 데이터
    alignment_options = [
        ("왼쪽 정렬", "Left"),
        ("가운데 정렬", "Center"),
        ("오른쪽 정렬", "Right"),
        ("들여쓰기1", "Indent1"),
        ("들여쓰기2", "Indent2"),
        ("들여쓰기3", "Indent3")
    ]

    # CharsAlign1 콤보박스 테스트
    chars_label = QLabel("문자 정렬 (CharsAlign1):")
    chars_combo = QComboBox()
    for display_text, code_value in alignment_options:
        chars_combo.addItem(display_text, code_value)

    layout.addWidget(chars_label)
    layout.addWidget(chars_combo)

    # BracketsAlign1 콤보박스 테스트
    brackets_label = QLabel("괄호 정렬 (BracketsAlign1):")
    brackets_combo = QComboBox()
    for display_text, code_value in alignment_options:
        brackets_combo.addItem(display_text, code_value)

    layout.addWidget(brackets_label)
    layout.addWidget(brackets_combo)

    # 선택 변경 시 출력 함수
    def on_chars_changed():
        current_data = chars_combo.currentData()
        current_text = chars_combo.currentText()
        print(f"문자 정렬 변경: '{current_text}' -> 코드: '{current_data}'")

    def on_brackets_changed():
        current_data = brackets_combo.currentData()
        current_text = brackets_combo.currentText()
        print(f"괄호 정렬 변경: '{current_text}' -> 코드: '{current_data}'")

    # 시그널 연결
    chars_combo.currentTextChanged.connect(on_chars_changed)
    brackets_combo.currentTextChanged.connect(on_brackets_changed)

    # 초기값 출력
    print("=== 정렬 콤보박스 초기화 테스트 ===")
    print(f"문자 정렬 초기값: '{chars_combo.currentText()}' -> 코드: '{chars_combo.currentData()}'")
    print(f"괄호 정렬 초기값: '{brackets_combo.currentText()}' -> 코드: '{brackets_combo.currentData()}'")
    print("\n콤보박스에서 다른 옵션을 선택해보세요.")

    window.setLayout(layout)
    window.resize(300, 200)
    window.show()

    return app.exec()

if __name__ == "__main__":
    test_alignment_combo()
