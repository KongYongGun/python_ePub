#!/usr/bin/env python3
"""CSS 테마를 강제 업데이트하는 스크립트"""

import sqlite3
from css_themes import DEFAULT_CSS_THEMES

def update_themes():
    """CSS 테마들을 강제로 업데이트합니다."""
    conn = sqlite3.connect('epub_config.db')
    cursor = conn.cursor()

    # 기존 테마들 삭제
    cursor.execute("DELETE FROM Stylesheet")
    print("기존 CSS 테마들이 삭제되었습니다.")

    # 새 테마들 추가
    for theme_key, theme_data in DEFAULT_CSS_THEMES.items():
        is_default = 1 if theme_key == "default" else 0
        cursor.execute("""
            INSERT INTO Stylesheet (name, description, content, is_default)
            VALUES (?, ?, ?, ?)
        """, (
            theme_data["name"],
            theme_data["description"],
            theme_data["content"],
            is_default
        ))
        print(f"테마 '{theme_data['name']}'가 추가되었습니다.")

    conn.commit()
    conn.close()
    print("CSS 테마 업데이트가 완료되었습니다.")

if __name__ == "__main__":
    update_themes()
