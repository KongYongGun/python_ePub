#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
테이블 직접 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import MainWindow
from PyQt6.QtWidgets import QApplication, QTableWidgetItem, QCheckBox

def test_table_direct():
    """테이블에 직접 데이터 추가 테스트"""
    print("=== 테이블 직접 테스트 ===")

    app = QApplication([])
    window = MainWindow()
    window.show()

    # 테이블 참조
    table = window.ui.tableWidget_ChapterList
    print(f"초기 테이블 상태: 행수={table.rowCount()}, 열수={table.columnCount()}")

    # 컬럼 설정 확인
    if table.columnCount() < 5:
        table.setColumnCount(5)
        headers = ["선택", "순서", "제목", "라인", "정규식"]
        table.setHorizontalHeaderLabels(headers)

    # 직접 데이터 추가
    test_data = [
        (3, "제1장 시작하기", "정규식 09", "^제\\d+장\\s+.*"),
        (6, "제2장 계속하기", "정규식 09", "^제\\d+장\\s+.*"),
        (9, "제3장 마무리하기", "정규식 09", "^제\\d+장\\s+.*")
    ]

    for i, (line_no, title, regex_name, pattern) in enumerate(test_data):
        row = table.rowCount()
        table.insertRow(row)

        print(f"행 {row} 추가 중...")

        # 체크박스
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        table.setCellWidget(row, 0, checkbox)

        # 데이터 설정
        table.setItem(row, 1, QTableWidgetItem(str(row + 1)))
        table.setItem(row, 2, QTableWidgetItem(title))
        table.setItem(row, 3, QTableWidgetItem(str(line_no)))
        table.setItem(row, 4, QTableWidgetItem(regex_name))

        print(f"행 {row} 완료. 현재 행수: {table.rowCount()}")

    print(f"최종 테이블 상태: 행수={table.rowCount()}")

    # 테이블 업데이트 강제
    table.update()
    table.repaint()

    print("테스트 완료. 창을 수동으로 닫으세요.")
    return app.exec()

if __name__ == "__main__":
    test_table_direct()
