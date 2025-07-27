# 시스템 기본 폰트 정보를 확인하는 스크립트
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtGui import QFont

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 시스템 기본 폰트 정보
    default_font = app.font()
    print(f"시스템 기본 폰트:")
    print(f"  패밀리: {default_font.family()}")
    print(f"  크기: {default_font.pointSize()}")
    print(f"  픽셀 크기: {default_font.pixelSize()}")
    print(f"  스타일: {default_font.styleName()}")
    print(f"  굵기: {default_font.weight()}")

    # 메인 윈도우 생성 후 폰트
    window = QMainWindow()
    window_font = window.font()
    print(f"\nQMainWindow 기본 폰트:")
    print(f"  패밀리: {window_font.family()}")
    print(f"  크기: {window_font.pointSize()}")
    print(f"  픽셀 크기: {window_font.pixelSize()}")
    print(f"  스타일: {window_font.styleName()}")
    print(f"  굵기: {window_font.weight()}")

    # CSS 적용 전후 폰트 비교
    label = QLabel("테스트 라벨", window)
    label_font_before = label.font()
    print(f"\nQLabel CSS 적용 전:")
    print(f"  패밀리: {label_font_before.family()}")
    print(f"  크기: {label_font_before.pointSize()}")

    # CSS 적용 (기본 테마와 동일)
    window.setStyleSheet("""
    QMainWindow {
        background-color: #f5f5f5;
        color: #333;
    }
    """)

    label_font_after = label.font()
    print(f"\nQLabel CSS 적용 후:")
    print(f"  패밀리: {label_font_after.family()}")
    print(f"  크기: {label_font_after.pointSize()}")

    # 다크 테마 CSS 적용
    window.setStyleSheet("""
    QMainWindow {
        background-color: #2b2b2b;
        color: #ffffff;
    }
    """)

    label_font_dark = label.font()
    print(f"\nQLabel 다크 테마 적용 후:")
    print(f"  패밀리: {label_font_dark.family()}")
    print(f"  크기: {label_font_dark.pointSize()}")

    app.quit()
