import sqlite3

conn = sqlite3.connect('epub_config.db')
cursor = conn.cursor()
cursor.execute('SELECT id, name, content FROM Stylesheet ORDER BY id')
themes = cursor.fetchall()

for theme_id, name, content in themes:
    print(f'=== 테마 ID: {theme_id}, 이름: {name} ===')
    # 폰트 관련 설정만 찾기
    lines = content.split('\n')
    font_lines = [line.strip() for line in lines if 'font' in line.lower()]
    if font_lines:
        print('폰트 관련 설정:')
        for line in font_lines:
            print(f'  {line}')
    else:
        print('폰트 관련 설정 없음')
    print()

conn.close()
