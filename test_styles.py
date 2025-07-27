"""
스타일 테스트 파일
CSS 템플릿 사용 예시를 보여줍니다.
"""

import sys
import os

# PyQt6 import
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt

# 스타일 매니저 import
from style_manager import StyleManager


class StyleTestWindow(QMainWindow):
    """스타일 테스트를 위한 간단한 윈도우"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.style_manager = StyleManager()

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("CSS 템플릿 테스트")
        self.setGeometry(100, 100, 400, 300)

        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 레이아웃 생성
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # 테스트용 위젯들
        self.label = QLabel("스타일 테스트 라벨")
        self.button1 = QPushButton("기본 버튼")
        self.button2 = QPushButton("스타일 적용 버튼")
        self.button3 = QPushButton("다른 스타일 버튼")

        # 레이아웃에 위젯 추가
        layout.addWidget(self.label)
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)

        # 버튼 이벤트 연결
        self.button1.clicked.connect(self.apply_basic_style)
        self.button2.clicked.connect(self.apply_button_style)
        self.button3.clicked.connect(self.apply_custom_style)

    def apply_basic_style(self):
        """기본 스타일 적용"""
        self.setStyleSheet("")
        print("기본 스타일 적용됨")

    def apply_button_style(self):
        """버튼 스타일만 적용"""
        try:
            # button_styles.css에서 스타일 로드
            button_css = self.style_manager.load_style_file("button_styles.css")
            if button_css:
                # 예시 스타일 추가 (실제 CSS 파일에 내용이 있어야 함)
                custom_css = """
                QPushButton {
                    background-color: #4CAF50;
                    border: 2px solid #45a049;
                    color: white;
                    padding: 10px 24px;
                    text-align: center;
                    font-size: 14px;
                    border-radius: 5px;
                }

                QPushButton:hover {
                    background-color: #45a049;
                }

                QPushButton:pressed {
                    background-color: #3d8b40;
                }
                """
                self.setStyleSheet(custom_css)
                print("버튼 스타일 적용됨")
        except Exception as e:
            print(f"스타일 적용 실패: {e}")

    def apply_custom_style(self):
        """커스텀 스타일 적용"""
        custom_css = """
        QMainWindow {
            background-color: #f0f0f0;
        }

        QLabel {
            color: #333;
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            background-color: #e8e8e8;
            border: 1px solid #ccc;
            border-radius: 3px;
        }

        QPushButton {
            background-color: #2196F3;
            border: 2px solid #1976D2;
            color: white;
            padding: 8px 16px;
            font-size: 12px;
            border-radius: 4px;
            min-width: 100px;
        }

        QPushButton:hover {
            background-color: #1976D2;
            border-color: #1565C0;
        }

        QPushButton:pressed {
            background-color: #1565C0;
        }
        """
        self.setStyleSheet(custom_css)
        print("커스텀 스타일 적용됨")


def test_style_manager():
    """스타일 매니저 기능 테스트"""
    print("=== 스타일 매니저 테스트 ===")

    manager = StyleManager()

    # 1. 템플릿 속성 확인
    print("\n1. 버튼 템플릿 속성:")
    button_props = manager.get_template_properties("button")
    print(f"   {button_props}")

    # 2. CSS 파일 로드 테스트
    print("\n2. CSS 파일 로드 테스트:")
    styles_dir = "styles"
    if os.path.exists(styles_dir):
        css_files = [f for f in os.listdir(styles_dir) if f.endswith('.css')]
        print(f"   발견된 CSS 파일: {css_files}")

        for css_file in css_files[:3]:  # 처음 3개만 테스트
            content = manager.load_style_file(css_file)
            if content is not None:
                print(f"   {css_file}: 로드 성공 ({len(content)} 문자)")
            else:
                print(f"   {css_file}: 로드 실패")
    else:
        print(f"   styles 디렉토리가 없습니다: {styles_dir}")

    # 3. 결합된 스타일시트 테스트
    print("\n3. 결합된 스타일시트 테스트:")
    try:
        combined = manager.get_combined_stylesheet(["button_styles.css", "label_styles.css"])
        print(f"   결합된 CSS 길이: {len(combined)} 문자")
    except Exception as e:
        print(f"   결합 실패: {e}")


if __name__ == "__main__":
    # 스타일 매니저 테스트
    test_style_manager()

    print("\n" + "="*50)
    print("PyQt6 스타일 테스트 윈도우 실행...")

    # PyQt6 애플리케이션 실행
    app = QApplication(sys.argv)
    window = StyleTestWindow()
    window.show()

    sys.exit(app.exec())
