#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
시그널-슬롯 연결 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QCheckBox
from PyQt6.QtCore import Qt
from chapter_finder import ChapterFinderWorker

def test_signal_slot():
    """시그널-슬롯 연결 테스트"""
    print("=== 시그널-슬롯 연결 테스트 ===")

    app = QApplication([])

    # 테이블 위젯 생성
    table = QTableWidget()
    table.setColumnCount(5)
    table.setHorizontalHeaderLabels(["선택", "순서", "제목", "라인", "정규식"])
    table.show()

    test_text = """이것은 테스트 파일입니다.

제1장 시작하기
이것은 첫 번째 챕터의 내용입니다.

제2장 계속하기
이것은 두 번째 챕터의 내용입니다.

제3장 마무리하기
이것은 세 번째 챕터의 내용입니다."""

    patterns = [(9, r"^제\d+장\s+.*")]

    worker = ChapterFinderWorker(test_text, patterns)

    def on_chapter_found(line_no, title, regex_name, pattern):
        print(f"[SIGNAL] 챕터 발견: Line {line_no}, Title: '{title}'")

        row = table.rowCount()
        table.insertRow(row)

        # 체크박스
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        table.setCellWidget(row, 0, checkbox)

        # 데이터 설정
        table.setItem(row, 1, QTableWidgetItem(str(row + 1)))
        table.setItem(row, 2, QTableWidgetItem(title))
        table.setItem(row, 3, QTableWidgetItem(str(line_no)))
        table.setItem(row, 4, QTableWidgetItem(regex_name))

        print(f"[SIGNAL] 테이블 업데이트 완료. 현재 행 수: {table.rowCount()}")

    def on_finished(total_found):
        print(f"[SIGNAL] 완료: {total_found}개")
        print(f"[SIGNAL] 최종 테이블 행 수: {table.rowCount()}")

    # 시그널 연결
    worker.chapter_found.connect(on_chapter_found, Qt.ConnectionType.QueuedConnection)
    worker.finished.connect(on_finished, Qt.ConnectionType.QueuedConnection)

    print("워커 시작...")
    worker.start()

    return app.exec()

if __name__ == "__main__":
    test_signal_slot()
