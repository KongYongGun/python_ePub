import os
import sqlite3
from PyQt6.QtWidgets import QComboBox

# DB 파일 경로 설정 (현재 실행 파일 기준)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "epub_config.db")

def get_connection():
    """SQLite DB 연결 객체 반환"""
    return sqlite3.connect(DB_FILE)

def load_stylesheet_list():
    """
    Stylesheet 테이블에서 QSS 테마 리스트 조회
    :return: [(id, name)]
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Stylesheet ORDER BY id")
        return cursor.fetchall()

def load_chapter_regex_list():
    """
    ChapterRegex 테이블에서 (id, name, example, pattern) 반환
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, example, pattern
            FROM ChapterRegex
            WHERE is_enabled = 1
            ORDER BY id
        """)
        return cursor.fetchall()

def load_punctuation_regex_list():
    """
    PunctuationRegex 테이블에서 괄호 정규식 조회
    :return: [(id, name, pattern)]
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, pattern
            FROM PunctuationRegex
            WHERE is_enabled = 1
            ORDER BY id
        """)
        return cursor.fetchall()

def load_text_styles(style_type):
    """
    TextStyle 테이블에서 주어진 타입(bracket, chapter 등)의 스타일 조회
    :param style_type: 'bracket' | 'chapter' | 'main'
    :return: [(id, name)]
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name
            FROM TextStyle
            WHERE type = ? AND is_enabled = 1
            ORDER BY id
        """, (style_type,))
        return cursor.fetchall()

def set_combobox_items(widget: QComboBox, data_list, display_column=1, user_data_column=0):
    """
    QComboBox 위젯에 항목들을 일괄 설정
    :param widget: QComboBox 객체
    :param data_list: [(id, name, ...)] 형태의 데이터
    :param display_column: 콤보박스에 표시할 텍스트가 있는 컬럼 인덱스
    :param user_data_column: userData로 저장할 값의 컬럼 인덱스
    """
    widget.clear()
    for row in data_list:
        display_text = row[display_column]
        user_data = row[user_data_column]
        widget.addItem(display_text, user_data)

def set_combobox_items_for_regex(widget: QComboBox, regex_list):
    """
    ChapterRegex 콤보박스에 정규식 이름 + 예시를 표시하고,
    실제 정규식 패턴은 userData로 저장
    :param widget: QComboBox
    :param regex_list: [(id, name, example, pattern)]
    """
    widget.clear()
    for row in regex_list:
        name = row[1]
        example = row[2] or ""
        pattern = row[3]
        display_text = f"{name} ({example})" if example else name
        widget.addItem(display_text, userData=pattern)

    """Stylesheet 테이블에서 기본 테마를 찾아 앱에 적용"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT content FROM Stylesheet
            WHERE is_default = 1
            LIMIT 1
        """)
        row = cursor.fetchone()
      #  if row:
      #      app.setStyleSheet(row[0])
