#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
목차찾기 기능만 단독 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 필요한 임포트만 수행
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QCheckBox
from PyQt6.QtCore import Qt
from chapter_finder import ChapterFinderWorker

class SimpleTest:
    def __init__(self):
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["선택", "순서", "제목", "라인", "정규식"])
        self.table.show()
        self.found_count = 0

    def on_chapter_found(self, line_no, title, regex_name, pattern):
        print(f"[SIGNAL] on_chapter_found 호출됨: Line {line_no}, Title: '{title}', Regex: {regex_name}")

        row = self.table.rowCount()
        self.table.insertRow(row)

        # 체크박스
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        self.table.setCellWidget(row, 0, checkbox)

        # 데이터 설정
        self.table.setItem(row, 1, QTableWidgetItem(str(row + 1)))
        self.table.setItem(row, 2, QTableWidgetItem(title))
        self.table.setItem(row, 3, QTableWidgetItem(str(line_no)))
        self.table.setItem(row, 4, QTableWidgetItem(regex_name))

        self.found_count += 1
        print(f"[SIGNAL] 테이블 업데이트 완료. 현재 행 수: {self.table.rowCount()}")

    def on_finished(self, total_found):
        print(f"[SIGNAL] 검색 완료: {total_found}개 발견")
        print(f"[SIGNAL] 실제 추가된 항목: {self.found_count}개")
        print(f"[SIGNAL] 테이블 최종 행 수: {self.table.rowCount()}")

def main():
    print("=== 목차찾기 단독 테스트 ===")

    app = QApplication([])

    test = SimpleTest()

    # 테스트 텍스트
    test_text = """이것은 테스트 파일입니다.

제1장 시작하기
이것은 첫 번째 챕터의 내용입니다.

제2장 계속하기
이것은 두 번째 챕터의 내용입니다.

제3장 마무리하기
이것은 세 번째 챕터의 내용입니다."""

    # 패턴
    patterns = [(9, r"^제\d+장\s+.*")]

    print(f"테스트 패턴: {patterns}")
    print(f"텍스트 라인 수: {len(test_text.splitlines())}")

    # 워커 생성
    worker = ChapterFinderWorker(test_text, patterns)

    # 시그널 연결
    worker.chapter_found.connect(test.on_chapter_found)
    worker.finished.connect(test.on_finished)

    print("워커 시작...")
    worker.start()

    # 워커 완료까지 대기
    if worker.wait(5000):  # 5초 대기
        print("워커 정상 완료")
    else:
        print("워커 타임아웃!")

    print(f"최종 결과: 테이블 행 수 = {test.table.rowCount()}")

    # GUI 표시
    return app.exec()

if __name__ == "__main__":
    main()
