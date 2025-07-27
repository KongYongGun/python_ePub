"""
CSS 통합 스타일시트 사용법 가이드
이제 모든 CSS가 하나의 파일(app_style.css)로 통합되었습니다.
"""

import os
from style_manager import StyleManager


def print_usage():
    """사용법을 출력합니다."""
    print("=== CSS 통합 스타일시트 사용법 ===")
    print("1. 메인 애플리케이션에서 스타일 적용:")
    print("   python main.py 실행 후, Python 콘솔에서:")
    print("   >>> window.apply_custom_styles()        # 통합 스타일 적용")
    print("   >>> window.reset_to_default_styles()    # 기본으로 리셋")
    print()
    print("2. 통합 CSS 파일 편집:")
    print("   - styles/app_style.css  → 모든 UI 컨트롤 스타일")
    print()
    print("3. 프로그래밍 방식으로 사용:")
    print("   from style_manager import StyleManager")
    print("   manager = StyleManager()")
    print("   stylesheet = manager.get_combined_stylesheet()")
    print("   widget.setStyleSheet(stylesheet)")
    print()
    print("4. 현재 통합 스타일 예시:")
    print("   - 기본 버튼: 초록색 배경")
    print("   - ePub 생성 버튼: 빨간색 강조")
    print("   - 파일 선택 버튼: 파란색")
    print("   - 삭제 버튼: 빨간색")
    print("   - 챕터 찾기: 보라색")
    print("   - 폰트 선택: 오렌지색")
    print()
    print("5. CSS 편집 예시:")
    print("   # 특정 버튼 색상 변경")
    print("   QPushButton#pushButton_ePubGenerate {")
    print("       background-color: #FF6B6B;")
    print("       border-color: #FF5252;")
    print("       font-weight: bold;")
    print("   }")
    print()
    print("6. 테스트 방법:")
    print("   python usage_guide.py  # 이 가이드")
    print("   python main.py         # 메인 애플리케이션")


def check_system_status():
    """시스템 상태를 확인합니다."""
    print("=== 시스템 상태 확인 ===")

    try:
        # 스타일 매니저 초기화
        manager = StyleManager()
        print("✓ 스타일 매니저 초기화 성공")

        # CSS 파일 로드
        css_content = manager.get_combined_stylesheet()
        if css_content:
            print(f"✓ 통합 CSS 로드 성공: {len(css_content)} 문자")
        else:
            print("✗ CSS 로드 실패")
            return False

        # 파일 존재 확인
        css_file = os.path.join("styles", "app_style.css")
        if os.path.exists(css_file):
            file_size = os.path.getsize(css_file)
            print(f"✓ app_style.css 파일 존재: {file_size} 바이트")
        else:
            print("✗ app_style.css 파일 없음")
            return False

        return True

    except Exception as e:
        print(f"✗ 오류 발생: {str(e)}")
        return False


def print_template_info():
    """CSS 템플릿 정보를 출력합니다."""
    print("=== 통합 CSS 구조 ===")

    sections = [
        ("메인 윈도우", "QMainWindow, QWidget, 스크롤바"),
        ("버튼", "QPushButton (일반, 특정 ID별)"),
        ("라벨", "QLabel (일반, 경로, 이미지, 폰트 예시)"),
        ("입력창", "QLineEdit (일반, 포커스, 비활성화)"),
        ("콤보박스", "QComboBox (일반, 호버, 포커스)"),
        ("테이블", "QTableWidget, QHeaderView"),
        ("체크박스", "QCheckBox (일반, 호버, 체크됨)"),
        ("탭", "QTabWidget, QTabBar"),
        ("진행바", "QProgressBar")
    ]

    for name, description in sections:
        print(f"{name}: {description}")

    print()
    print("✓ 모든 컨트롤이 하나의 파일에 통합되었습니다!")
    print("✓ styles/app_style.css 파일을 편집하여 전체 애플리케이션 스타일을 변경할 수 있습니다.")


if __name__ == "__main__":
    print_usage()
    print()

    if check_system_status():
        print()
        print_template_info()
        print()
        print("✓ 모든 기능이 정상 작동합니다!")
        print("✓ 이제 styles/app_style.css 파일을 편집하여 원하는 스타일을 적용할 수 있습니다.")
    else:
        print()
        print("✗ 시스템에 문제가 있습니다. 파일을 확인해주세요.")
    print("   # 특정 버튼 색상 변경")
    print("   QPushButton#pushButton_ePubGenerate {")
    print("       background-color: #FF6B6B;")
    print("       border-color: #FF5252;")
    print("       font-weight: bold;")
    print("   }")
    print()

    print("6. 테스트 방법:")
    print("   python usage_guide.py  # 이 가이드")
    print("   python main.py         # 메인 애플리케이션")


if __name__ == "__main__":
    print_usage()
    print()

    if check_system_status():
        print()
        print_template_info()
        print()
        print("✓ 모든 기능이 정상 작동합니다!")
        print("✓ 이제 styles/app_style.css 파일을 편집하여 원하는 스타일을 적용할 수 있습니다.")
    else:
        print()
        print("✗ 시스템에 문제가 있습니다. 파일을 확인해주세요.")

    # 스타일 매니저 기능 검증
    try:
        from style_manager import StyleManager
        manager = StyleManager()

        print("=== 시스템 상태 확인 ===")
        print(f"✓ 스타일 매니저 초기화 성공")

        styles = manager.load_all_styles()
        print(f"✓ CSS 파일 로드 성공: {len(styles)}개 파일")

        for filename, content in styles.items():
            if content:
                print(f"  - {filename}: {len(content)} 문자")
            else:
                print(f"  - {filename}: 비어있음")

        # 템플릿 정보 출력
        print(f"\n=== 템플릿 정보 ===")
        controls = ["button", "label", "table", "combobox"]
        for control in controls:
            props = manager.get_template_properties(control)
            print(f"{control}: {len(props)}개 속성 사용 가능")

        print(f"\n✓ 모든 기능이 정상 작동합니다!")
        print(f"✓ 이제 각 CSS 파일을 편집하여 원하는 스타일을 적용할 수 있습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
