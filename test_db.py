import sqlite3

# FontStyle 테이블 삭제
conn = sqlite3.connect("epub_config.db")
cursor = conn.cursor()

# FontStyle 테이블 삭제
cursor.execute("DROP TABLE IF EXISTS FontStyle")

# AlignStyle 테이블의 데이터만 삭제 (테이블은 유지)
cursor.execute("DELETE FROM AlignStyle")

conn.commit()
conn.close()

print("FontStyle 테이블 삭제 및 AlignStyle 데이터 삭제 완료")
