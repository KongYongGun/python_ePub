import sqlite3
import os

# 현재 데이터베이스의 모든 CSS 테마를 추출해서 분석
db_path = 'epub_config.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT id, name, content FROM Stylesheet ORDER BY id')
    themes = cursor.fetchall()

    for theme_id, name, content in themes:
        print(f'=== 테마 ID: {theme_id}, 이름: {name} ===')

        # QMainWindow 부분만 추출
        lines = content.split('\n')
        in_qmainwindow = False
        qmainwindow_content = []

        for line in lines:
            if 'QMainWindow' in line and '{' in line:
                in_qmainwindow = True
                qmainwindow_content.append(line)
            elif in_qmainwindow:
                qmainwindow_content.append(line)
                if '}' in line and line.strip() == '}':
                    break

        if qmainwindow_content:
            print('QMainWindow CSS:')
            for line in qmainwindow_content:
                print(f'  {line}')
        print()

    conn.close()
else:
    print("데이터베이스 파일이 존재하지 않습니다.")
