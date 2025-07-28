"""
ePub 데이터베이스 로더 모듈

SQLite 데이터베이스에서 ePub 변환기의 설정 데이터를 조회하고
PyQt6 UI 컴포넌트에 로드하는 기능을 제공합니다.

주요 기능:
- 스타일시트(QSS) 테마 목록 조회
- 챕터 정규식 패턴 목록 조회
- 구두점 정규식 패턴 목록 조회
- 콤보박스 위젯에 데이터 로드
- 데이터베이스 연결 관리

작성자: ePub Python Team
최종 수정일: 2025-07-28
"""

import os
import sqlite3
import logging
from typing import List, Tuple, Optional
from PyQt6.QtWidgets import QComboBox

# DB 파일 경로 설정 (현재 실행 파일 기준)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "epub_config.db")

def get_connection():
    """
    SQLite 데이터베이스 연결 객체를 반환합니다.

    Returns:
        sqlite3.Connection: SQLite 데이터베이스 연결 객체

    Raises:
        sqlite3.Error: 데이터베이스 연결 실패 시
        FileNotFoundError: 데이터베이스 파일이 존재하지 않을 시
    """
    try:
        if not os.path.exists(DB_FILE):
            raise FileNotFoundError(f"데이터베이스 파일을 찾을 수 없습니다: {DB_FILE}")
        return sqlite3.connect(DB_FILE)
    except sqlite3.Error as e:
        logging.error(f"데이터베이스 연결 중 오류 발생: {e}")
        raise

def load_stylesheet_list():
    """
    Stylesheet 테이블에서 QSS 테마 목록을 조회합니다.

    Returns:
        List[Tuple[int, str]]: (id, name) 형태의 튜플 리스트

    Raises:
        sqlite3.Error: 데이터베이스 쿼리 실행 중 오류 발생 시
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM Stylesheet ORDER BY id")
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"스타일시트 목록 조회 중 오류 발생: {e}")
        return []

def load_chapter_regex_list():
    """
    ChapterRegex 테이블에서 활성화된 챕터 정규식 패턴 목록을 조회합니다.

    Returns:
        List[Tuple[int, str, str, str]]: (id, name, example, pattern) 형태의 튜플 리스트

    Raises:
        sqlite3.Error: 데이터베이스 쿼리 실행 중 오류 발생 시
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, example, pattern
                FROM ChapterRegex
                WHERE is_enabled = 1
                ORDER BY id
            """)
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"챕터 정규식 목록 조회 중 오류 발생: {e}")
        return []

def load_punctuation_regex_list():
    """
    PunctuationRegex 테이블에서 활성화된 구두점 정규식 패턴 목록을 조회합니다.

    Returns:
        List[Tuple[int, str, str]]: (id, name, pattern) 형태의 튜플 리스트

    Raises:
        sqlite3.Error: 데이터베이스 쿼리 실행 중 오류 발생 시
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, pattern
                FROM PunctuationRegex
                WHERE is_enabled = 1
                ORDER BY id
            """)
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"구두점 정규식 목록 조회 중 오류 발생: {e}")
        return []

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
