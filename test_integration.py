#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
목차찾기 기능 통합 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from main import MainWindow

def test_chapter_finding():
    """실제 애플리케이션에서 목차찾기 테스트"""
    print("=== 목차찾기 통합 테스트 ===")

    app = QApplication([])
    window = MainWindow()

    # 테스트 파일 경로 설정
    test_file = os.path.join(os.path.dirname(__file__), "test_chapter.txt")
    window.ui.label_TextFilePath.setText(test_file)

    # 첫 번째 체크박스를 선택하고 적절한 정규식 설정
    try:
        checkbox1 = window.ui.checkBox_RegEx1
        combo1 = window.ui.comboBox_RegEx1

        # 체크박스 활성화
        checkbox1.setChecked(True)

        # 콤보박스에서 "제1장" 패턴 찾기
        for i in range(combo1.count()):
            item_text = combo1.itemText(i)
            item_data = combo1.itemData(i)
            print(f"콤보 아이템 {i}: '{item_text}' -> '{item_data}'")

            if item_data and "제" in item_data and "장" in item_data:
                combo1.setCurrentIndex(i)
                print(f"선택된 패턴: {item_data}")
                break

        # 목차찾기 실행
        print("목차찾기 실행 중...")
        window.find_chapter_list()

        # 잠시 대기 (실제 사용에서는 사용자가 기다림)
        app.processEvents()

        # 결과 확인
        table = window.ui.tableWidget_ChapterList
        print(f"테이블 행 수: {table.rowCount()}")

        for row in range(table.rowCount()):
            title_item = table.item(row, 2)
            line_item = table.item(row, 3)
            if title_item and line_item:
                print(f"Row {row}: '{title_item.text()}' (Line {line_item.text()})")

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

    # 애플리케이션 종료하지 않고 대기
    print("테스트 완료. 애플리케이션을 수동으로 종료하세요.")
    return app.exec()

if __name__ == "__main__":
    test_chapter_finding()
