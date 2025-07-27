import sqlite3
from qt_material import build_stylesheet

# 테마 목록
qt_material_themes = [
    'dark_blue.xml',
    'light_blue.xml',
    'dark_teal.xml',
    'light_teal.xml',
    'dark_amber.xml',
    'light_cyan_500.xml'
]

# DB 경로
from pathlib import Path
DB_FILE = Path(__file__).parent / "epub_config.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# 기존 qt_material 테마 제거 (선택 사항)
cursor.execute("DELETE FROM Stylesheet WHERE name LIKE 'Material - %'")

for i, theme_name in enumerate(qt_material_themes):
    qss = build_stylesheet(theme=theme_name)
    display_name = f"Material - {theme_name.replace('.xml', '')}"

    cursor.execute("""
        INSERT INTO Stylesheet (name, description, content, is_default)
        VALUES (?, ?, ?, ?)
    """, (
        display_name,
        f"qt_material 테마: {theme_name}",
        qss,
        1 if i == 0 else 0  # 첫 번째 테마를 기본값으로
    ))

conn.commit()
conn.close()
print("✅ qt_material 테마들이 DB에 저장되었습니다.")
