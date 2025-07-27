# CSS 스타일 템플릿 사용 가이드

## 개요
이 프로젝트는 각 UI 컨트롤별로 개별적인 CSS 스타일을 적용할 수 있는 모듈화된 스타일 시스템을 제공합니다.

## 파일 구조
```
styles/
├── mainwindow_styles.css    # 메인 윈도우 및 스크롤바
├── button_styles.css        # 모든 버튼들
├── combobox_styles.css      # 콤보박스들
├── table_styles.css         # 테이블 위젯
├── label_styles.css         # 라벨들
├── lineedit_styles.css      # 입력창들
├── tab_styles.css           # 탭 위젯
├── checkbox_styles.css      # 체크박스들
└── progressbar_styles.css   # 진행바
```

## 사용 방법

### 1. 기본 사용법

```python
from style_manager import StyleManager

# 스타일 매니저 생성
manager = StyleManager()

# 모든 스타일 적용
stylesheet = manager.get_combined_stylesheet()
widget.setStyleSheet(stylesheet)

# 특정 스타일만 적용
manager.apply_styles_to_widget(widget, ["button_styles.css", "label_styles.css"])
```

### 2. 메인 애플리케이션에서 사용

```python
# main.py에서 선택적으로 사용 가능한 메서드들:

# 모든 스타일 적용
window.apply_custom_styles()

# 버튼 스타일만 적용
window.apply_button_styles_only()

# 테이블 스타일만 적용
window.apply_table_styles_only()

# 폼 관련 스타일만 적용
window.apply_form_styles_only()

# 필수 스타일만 적용
window.apply_essential_styles_only()

# 기본 상태로 리셋
window.reset_to_default_styles()
```

### 3. CSS 파일 편집 예시

#### button_styles.css
```css
/* 모든 버튼에 적용 */
QPushButton {
    background-color: #4CAF50;
    border: 2px solid #45a049;
    color: white;
    padding: 10px 24px;
    font-size: 14px;
    border-radius: 5px;
}

QPushButton:hover {
    background-color: #45a049;
}

QPushButton:pressed {
    background-color: #3d8b40;
}

/* 특정 버튼에만 적용 */
#pushButton_ePubGenerate {
    background-color: #FF6B6B;
    border-color: #FF5252;
}

#pushButton_ePubGenerate:hover {
    background-color: #FF5252;
}
```

#### label_styles.css
```css
/* 모든 라벨에 적용 */
QLabel {
    color: #333333;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}

/* 제목 라벨들 */
#label_Title, #label_Author, #label_Publisher {
    font-weight: bold;
    font-size: 14px;
    color: #2C3E50;
}

/* 경로 표시 라벨들 */
#label_CoverImagePath, #label_ChapterImagePath {
    color: #7F8C8D;
    font-style: italic;
    font-size: 10px;
}
```

## CSS 속성 참고

### 버튼 (QPushButton)
- `background-color`: 배경색
- `border`: 테두리
- `color`: 텍스트 색상
- `padding`: 내부 여백
- `border-radius`: 모서리 둥글기
- `font-weight`: 폰트 굵기
- `font-size`: 폰트 크기

### 라벨 (QLabel)
- `color`: 텍스트 색상
- `font-family`: 폰트 패밀리
- `font-size`: 폰트 크기
- `font-weight`: 폰트 굵기
- `background-color`: 배경색
- `border`: 테두리
- `padding`: 내부 여백

### 테이블 (QTableWidget)
- `background-color`: 배경색
- `alternate-background-color`: 교대 행 색상
- `gridline-color`: 격자선 색상
- `selection-background-color`: 선택된 행 배경색
- `border`: 테두리

### 콤보박스 (QComboBox)
- `border`: 테두리
- `background-color`: 배경색
- `color`: 텍스트 색상
- `padding`: 내부 여백
- `border-radius`: 모서리 둥글기

## 선택자 (Selector) 사용법

### 클래스 선택자
```css
QPushButton { /* 모든 버튼 */ }
QLabel { /* 모든 라벨 */ }
QTableWidget { /* 모든 테이블 */ }
```

### ID 선택자 (objectName 기반)
```css
#pushButton_ePubGenerate { /* 특정 버튼 */ }
#label_Title { /* 제목 라벨 */ }
#tableWidget_ChapterList { /* 챕터 리스트 테이블 */ }
```

### 상태 선택자
```css
QPushButton:hover { /* 마우스 오버 시 */ }
QPushButton:pressed { /* 클릭 시 */ }
QPushButton:disabled { /* 비활성화 시 */ }
QLineEdit:focus { /* 포커스 시 */ }
```

### 하위 요소 선택자
```css
QComboBox::drop-down { /* 콤보박스 드롭다운 화살표 */ }
QTableWidget::item { /* 테이블 아이템 */ }
QTabWidget::tab-bar { /* 탭 바 */ }
```

## 테스트 방법

```bash
# 스타일 테스트 실행
python test_styles.py

# 메인 애플리케이션에서 테스트
python main.py
# 그 후 Python 콘솔에서:
# window.apply_button_styles_only()
# window.get_style_template_info()
```

## 주의사항

1. **CSS 파일이 비어있음**: 템플릿 파일들은 빈 룰셋으로 되어 있으므로, 실제 스타일을 추가해야 합니다.

2. **선택자 우선순위**: ID 선택자(#objectName)가 클래스 선택자(QPushButton)보다 우선순위가 높습니다.

3. **objectName 확인**: UI 파일(.ui)에서 각 위젯의 objectName을 확인하여 정확한 ID 선택자를 사용하세요.

4. **스타일 충돌**: 여러 CSS 파일을 결합할 때 스타일이 충돌할 수 있으므로 주의하세요.

## 예시 워크플로우

1. **특정 버튼만 스타일링하고 싶을 때**:
   - `styles/button_styles.css` 파일을 편집
   - 해당 버튼의 objectName을 확인 (예: `pushButton_ePubGenerate`)
   - CSS 추가: `#pushButton_ePubGenerate { ... }`
   - `window.apply_button_styles_only()` 호출

2. **전체 폼을 일관성 있게 스타일링하고 싶을 때**:
   - 관련 CSS 파일들을 편집 (`label_styles.css`, `lineedit_styles.css` 등)
   - `window.apply_form_styles_only()` 호출

3. **특정 색상 테마를 적용하고 싶을 때**:
   - 모든 CSS 파일에 일관된 색상 체계 적용
   - `window.apply_custom_styles()` 호출

이제 각 컨트롤별로 개별적인 스타일을 적용할 수 있는 완전한 템플릿 시스템이 준비되었습니다!
