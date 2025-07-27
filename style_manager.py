"""
스타일 매니저 모듈
각 컨트롤별로 CSS 스타일을 개별적으로 로드하고 적용하는 기능을 제공합니다.
"""

import os
from typing import Dict, List, Optional


class StyleManager:
    """각 컨트롤별 CSS 스타일을 관리하는 클래스"""

    def __init__(self, styles_dir: str = "styles"):
        """
        스타일 매니저 초기화

        Args:
            styles_dir: CSS 파일들이 있는 디렉토리 경로
        """
        self.styles_dir = styles_dir
        self.loaded_styles: Dict[str, str] = {}

    def load_style_file(self, filename: str) -> Optional[str]:
        """
        CSS 파일을 로드합니다.

        Args:
            filename: CSS 파일명 (예: "button_styles.css")

        Returns:
            CSS 내용 문자열 또는 None (로드 실패 시)
        """
        try:
            file_path = os.path.join(self.styles_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.loaded_styles[filename] = content
                    return content
            else:
                print(f"[WARNING] 스타일 파일을 찾을 수 없습니다: {file_path}")
                return None
        except Exception as e:
            print(f"[ERROR] 스타일 파일 로드 실패: {filename}, {str(e)}")
            return None

    def load_all_styles(self) -> Dict[str, str]:
        """
        통합 CSS 파일을 로드합니다.

        Returns:
            파일명을 키로 하는 CSS 내용 딕셔너리
        """
        # 통합된 app_style.css 파일만 로드
        self.load_style_file("app_style.css")
        return self.loaded_styles.copy()

    def get_combined_stylesheet(self, include_files: Optional[List[str]] = None) -> str:
        """
        통합된 스타일시트를 반환합니다.

        Args:
            include_files: 사용하지 않음 (호환성을 위해 유지)

        Returns:
            통합된 CSS 문자열
        """
        # app_style.css 파일 로드
        app_css = self.load_style_file("app_style.css")
        return app_css if app_css else ""

    def apply_styles_to_widget(self, widget, style_files: List[str]):
        """
        위젯에 특정 스타일 파일들을 적용합니다.

        Args:
            widget: PyQt6 위젯 객체
            style_files: 적용할 CSS 파일명 리스트
        """
        stylesheet = self.get_combined_stylesheet(style_files)
        widget.setStyleSheet(stylesheet)

    def get_template_properties(self, control_type: str) -> List[str]:
        """
        특정 컨트롤 타입에 대한 CSS 속성 템플릿을 반환합니다.

        Args:
            control_type: 컨트롤 타입 ("button", "label", "table" 등)

        Returns:
            CSS 속성 리스트
        """
        templates = {
            "button": [
                "background-color", "border", "color", "padding",
                "border-radius", "font-weight", "font-size", "font-family"
            ],
            "label": [
                "color", "font-family", "font-size", "font-weight",
                "background-color", "border", "padding"
            ],
            "combobox": [
                "border", "background-color", "color", "padding",
                "font-family", "font-size", "border-radius"
            ],
            "table": [
                "background-color", "alternate-background-color", "gridline-color",
                "border", "selection-background-color", "font-family", "font-size"
            ],
            "lineedit": [
                "border", "background-color", "color", "padding",
                "font-family", "font-size", "border-radius"
            ],
            "checkbox": [
                "color", "font-family", "font-size", "spacing",
                "background-color"
            ],
            "tab": [
                "background-color", "border", "padding", "color",
                "font-family", "font-size", "border-radius"
            ],
            "progressbar": [
                "background-color", "border", "border-radius",
                "text-align", "color", "font-size"
            ]
        }

        return templates.get(control_type, [])


# 사용 예시 함수들
def create_basic_stylesheet() -> str:
    """기본 스타일시트를 생성합니다."""
    manager = StyleManager()
    return manager.get_combined_stylesheet()


def apply_button_styles_only(widget) -> None:
    """버튼 스타일만 적용합니다."""
    manager = StyleManager()
    manager.apply_styles_to_widget(widget, ["button_styles.css"])


def apply_table_styles_only(widget) -> None:
    """테이블 스타일만 적용합니다."""
    manager = StyleManager()
    manager.apply_styles_to_widget(widget, ["table_styles.css"])


if __name__ == "__main__":
    # 테스트 코드
    manager = StyleManager()

    # 모든 스타일 로드 테스트
    styles = manager.load_all_styles()
    print(f"로드된 스타일 파일 수: {len(styles)}")

    # 결합된 스타일시트 생성 테스트
    combined = manager.get_combined_stylesheet(["button_styles.css", "label_styles.css"])
    print(f"결합된 CSS 길이: {len(combined)} 문자")

    # 템플릿 속성 확인
    button_props = manager.get_template_properties("button")
    print(f"버튼 CSS 속성들: {button_props}")
