#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
목차찾기 기능 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ePub_loader import load_chapter_regex_list, set_combobox_items_for_regex
from PyQt6.QtWidgets import QApplication, QComboBox
from chapter_finder import ChapterFinderWorker
import re

def test_regex_loading():
    """정규식 로딩 테스트"""
    print("=== 정규식 로딩 테스트 ===")
    regex_list = load_chapter_regex_list()
    print(f"로드된 정규식 개수: {len(regex_list)}")

    for regex in regex_list[:5]:  # 처음 5개만 출력
        print(f"ID: {regex[0]}, Name: {regex[1]}, Example: {regex[2]}, Pattern: {regex[3]}")

    return regex_list

def test_combo_data():
    """콤보박스 데이터 테스트"""
    print("\n=== 콤보박스 데이터 테스트 ===")
    app = QApplication([])

    combo = QComboBox()
    regex_list = load_chapter_regex_list()
    set_combobox_items_for_regex(combo, regex_list)

    print(f"콤보박스 아이템 개수: {combo.count()}")
    for i in range(min(5, combo.count())):  # 처음 5개만 출력
        text = combo.itemText(i)
        data = combo.itemData(i)
        print(f"Index {i}: Text='{text}', Data='{data}'")

    app.quit()
    return combo

def test_regex_pattern():
    """정규식 패턴 테스트"""
    print("\n=== 정규식 패턴 테스트 ===")

    test_text = """이것은 테스트 파일입니다.

제1장 시작하기
이것은 첫 번째 챕터의 내용입니다.

제2장 계속하기
이것은 두 번째 챕터의 내용입니다.

제3장 마무리하기
이것은 세 번째 챕터의 내용입니다."""

    # 간단한 챕터 패턴
    test_pattern = r"제\d+장"

    print(f"테스트 패턴: {test_pattern}")
    print("테스트 텍스트에서 찾은 매치:")

    pattern = re.compile(test_pattern)
    lines = test_text.splitlines()

    for i, line in enumerate(lines):
        if pattern.search(line):
            print(f"Line {i+1}: {line.strip()}")

if __name__ == "__main__":
    test_regex_loading()
    test_combo_data()
    test_regex_pattern()
    print("\n테스트 완료!")
