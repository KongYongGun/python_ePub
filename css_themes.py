# CSS 테마 관리 모듈
# 기본 CSS 테마들을 정의하고 데이터베이스에 저장/로드하는 기능을 제공합니다.

# 기본 CSS 테마들
DEFAULT_CSS_THEMES = {
    "default": {
        "name": "기본 테마",
        "description": "기본 파란색 테마",
        "content": """/* ePub Python Application - 기본 테마 */
QMainWindow {
    background-color: #f5f5f5;
    color: #333;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

/* 버튼 스타일 */
QPushButton {
    background-color: #0078d4;
    border: none;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
    min-height: 20px;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

/* ePub 제작 버튼은 큰 폰트 유지 */
QPushButton#pushButton_ePubGenerate {
    font-size: 14pt;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

/* 콤보박스 스타일 */
QComboBox {
    border: 2px solid #e1e1e1;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: white;
    min-height: 20px;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

QComboBox:focus {
    border-color: #0078d4;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

/* 테이블 위젯 스타일 */
QTableWidget {
    alternate-background-color: #f9f9f9;
    background-color: white;
    gridline-color: #e1e1e1;
    border: 1px solid #d1d1d1;
    selection-background-color: #0078d4;
}

QTableWidget::item {
    padding: 4px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #0078d4;
    color: white;
}

QTableWidget QHeaderView::section {
    background-color: #f1f1f1;
    border: 1px solid #d1d1d1;
    padding: 4px 8px;
    font-weight: bold;
}

/* 라벨 스타일 */
QLabel {
    color: #333;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

/* 라인 에디트 스타일 */
QLineEdit {
    border: 2px solid #e1e1e1;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: white;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

QLineEdit:focus {
    border-color: #0078d4;
}

/* 탭 위젯 스타일 */
QTabWidget::pane {
    border: 1px solid #d1d1d1;
    background-color: white;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #f1f1f1;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid #d1d1d1;
    border-bottom: none;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

QTabBar::tab:selected {
    background-color: #0078d4;
    color: white;
}

QTabBar::tab:hover {
    background-color: #e3f2fd;
}

/* 체크박스 스타일 */
QCheckBox {
    spacing: 4px;
    color: #333;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:unchecked {
    border: 2px solid #d1d1d1;
    background-color: white;
    border-radius: 2px;
}

QCheckBox::indicator:checked {
    border: 2px solid #0078d4;
    background-color: #0078d4;
    border-radius: 2px;
}

/* 프로그레스 바 스타일 */
QProgressBar {
    border: 2px solid #d1d1d1;
    border-radius: 4px;
    text-align: center;
    background-color: #f5f5f5;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 2px;
}

/* 스크롤바 스타일 */
QScrollBar:vertical {
    background-color: #f5f5f5;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #d1d1d1;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #0078d4;
}

/* 메뉴 스타일 */
QMenu {
    background-color: white;
    border: 1px solid #d1d1d1;
    border-radius: 4px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 12px;
    border-radius: 2px;
}

QMenu::item:selected {
    background-color: #0078d4;
    color: white;
}

/* 메시지 박스 스타일 */
QMessageBox {
    background-color: white;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 6px 12px;
}"""
    },

    "dark": {
        "name": "다크 테마",
        "description": "어두운 배경의 테마",
        "content": """/* ePub Python Application - 다크 테마 */
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

/* 버튼 스타일 */
QPushButton {
    background-color: #0d7377;
    border: none;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
    min-height: 20px;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

/* ePub 제작 버튼은 큰 폰트 유지 */
QPushButton#pushButton_ePubGenerate {
    font-size: 14pt;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #14a085;
}

QPushButton:pressed {
    background-color: #0a5d61;
}

QPushButton:disabled {
    background-color: #555555;
    color: #888888;
}

/* 콤보박스 스타일 */
QComboBox {
    border: 2px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #3c3c3c;
    color: white;
    min-height: 20px;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

QComboBox:focus {
    border-color: #0d7377;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

/* 테이블 위젯 스타일 */
QTableWidget {
    alternate-background-color: #3c3c3c;
    background-color: #2b2b2b;
    gridline-color: #555555;
    border: 1px solid #555555;
    selection-background-color: #0d7377;
    color: white;
}

QTableWidget::item {
    padding: 4px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #0d7377;
    color: white;
}

QTableWidget QHeaderView::section {
    background-color: #404040;
    border: 1px solid #555555;
    padding: 4px 8px;
    font-weight: bold;
    color: white;
}

/* 라벨 스타일 */
QLabel {
    color: #ffffff;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

/* 라인 에디트 스타일 */
QLineEdit {
    border: 2px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #3c3c3c;
    color: white;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

QLineEdit:focus {
    border-color: #0d7377;
}

/* 탭 위젯 스타일 */
QTabWidget::pane {
    border: 1px solid #555555;
    background-color: #2b2b2b;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #404040;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid #555555;
    border-bottom: none;
    color: white;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

QTabBar::tab:selected {
    background-color: #0d7377;
    color: white;
}

QTabBar::tab:hover {
    background-color: #505050;
}

/* 체크박스 스타일 */
QCheckBox {
    spacing: 4px;
    color: #ffffff;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:unchecked {
    border: 2px solid #555555;
    background-color: #3c3c3c;
    border-radius: 2px;
}

QCheckBox::indicator:checked {
    border: 2px solid #0d7377;
    background-color: #0d7377;
    border-radius: 2px;
}

/* 프로그레스 바 스타일 */
QProgressBar {
    border: 2px solid #555555;
    border-radius: 4px;
    text-align: center;
    background-color: #3c3c3c;
    color: white;
}

QProgressBar::chunk {
    background-color: #0d7377;
    border-radius: 2px;
}

/* 스크롤바 스타일 */
QScrollBar:vertical {
    background-color: #3c3c3c;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #0d7377;
}

/* 메뉴 스타일 */
QMenu {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px;
    color: white;
}

QMenu::item {
    padding: 6px 12px;
    border-radius: 2px;
}

QMenu::item:selected {
    background-color: #0d7377;
    color: white;
}

/* 메시지 박스 스타일 */
QMessageBox {
    background-color: #2b2b2b;
    color: white;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 6px 12px;
}"""
    },

    "green": {
        "name": "초록 테마",
        "description": "자연스러운 초록색 테마",
        "content": """/* ePub Python Application - 초록 테마 */
QMainWindow {
    background-color: #f8f9fa;
    color: #2d3748;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

/* 버튼 스타일 */
QPushButton {
    background-color: #38a169;
    border: none;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
    min-height: 20px;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

/* ePub 제작 버튼은 큰 폰트 유지 */
QPushButton#pushButton_ePubGenerate {
    font-size: 14pt;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2f855a;
}

QPushButton:pressed {
    background-color: #276749;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

/* 콤보박스 스타일 */
QComboBox {
    border: 2px solid #e2e8f0;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: white;
    min-height: 20px;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

QComboBox:focus {
    border-color: #38a169;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

/* 테이블 위젯 스타일 */
QTableWidget {
    alternate-background-color: #f7fafc;
    background-color: white;
    gridline-color: #e2e8f0;
    border: 1px solid #e2e8f0;
    selection-background-color: #38a169;
}

QTableWidget::item {
    padding: 4px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #38a169;
    color: white;
}

QTableWidget QHeaderView::section {
    background-color: #edf2f7;
    border: 1px solid #e2e8f0;
    padding: 4px 8px;
    font-weight: bold;
}

/* 라벨 스타일 */
QLabel {
    color: #2d3748;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

/* 라인 에디트 스타일 */
QLineEdit {
    border: 2px solid #e2e8f0;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: white;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

QLineEdit:focus {
    border-color: #38a169;
}

/* 탭 위젯 스타일 */
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    background-color: white;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #edf2f7;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

QTabBar::tab:selected {
    background-color: #38a169;
    color: white;
}

QTabBar::tab:hover {
    background-color: #f0fff4;
}

/* 체크박스 스타일 */
QCheckBox {
    spacing: 4px;
    color: #2d3748;
    font-family: "맑은 고딕";
    font-size: 11pt;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:unchecked {
    border: 2px solid #e2e8f0;
    background-color: white;
    border-radius: 2px;
}

QCheckBox::indicator:checked {
    border: 2px solid #38a169;
    background-color: #38a169;
    border-radius: 2px;
}

/* 프로그레스 바 스타일 */
QProgressBar {
    border: 2px solid #e2e8f0;
    border-radius: 4px;
    text-align: center;
    background-color: #f8f9fa;
}

QProgressBar::chunk {
    background-color: #38a169;
    border-radius: 2px;
}

/* 스크롤바 스타일 */
QScrollBar:vertical {
    background-color: #f8f9fa;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #e2e8f0;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #38a169;
}

/* 메뉴 스타일 */
QMenu {
    background-color: white;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 12px;
    border-radius: 2px;
}

QMenu::item:selected {
    background-color: #38a169;
    color: white;
}

/* 메시지 박스 스타일 */
QMessageBox {
    background-color: white;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 6px 12px;
}"""
    }
}

def get_all_themes():
    """모든 기본 테마를 반환합니다."""
    return DEFAULT_CSS_THEMES

def get_theme_by_key(key):
    """키로 특정 테마를 반환합니다."""
    return DEFAULT_CSS_THEMES.get(key)

def get_default_theme():
    """기본 테마를 반환합니다."""
    return DEFAULT_CSS_THEMES["default"]
