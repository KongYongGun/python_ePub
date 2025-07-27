#!/usr/bin/env python3
"""
CSS의 모든 선택자를 분석하여 font: inherit가 필요한 곳을 찾는 스크립트
"""

import sqlite3
import re

def analyze_css_selectors():
    conn = sqlite3.connect('epub_config.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, content FROM Stylesheet WHERE is_default = 1')
    theme = cursor.fetchone()

    if theme:
        theme_id, name, content = theme
        print(f'=== 기본 테마 분석: {name} ===')

        # 모든 CSS 선택자 찾기
        selectors = []
        lines = content.split('\n')

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # CSS 선택자 패턴 (Q로 시작하는 것들)
            if re.match(r'^Q\w+', line_stripped) and '{' in line_stripped:
                selector = line_stripped.replace('{', '').strip()
                selectors.append((selector, i+1))

        print("발견된 Qt 위젯 선택자들:")
        for selector, line_num in selectors:
            print(f"  라인 {line_num}: {selector}")

        # font: inherit가 없는 선택자들 찾기
        print("\n=== font: inherit가 필요할 수 있는 선택자들 ===")

        widget_blocks = {}
        current_selector = ""
        current_block = []
        in_block = False

        for line in lines:
            line_stripped = line.strip()

            if re.match(r'^Q\w+', line_stripped) and '{' in line_stripped:
                # 이전 블록 저장
                if current_selector and current_block:
                    widget_blocks[current_selector] = current_block

                # 새 블록 시작
                current_selector = line_stripped.replace('{', '').strip()
                current_block = [line_stripped]
                in_block = True
            elif in_block:
                current_block.append(line_stripped)
                if line_stripped == '}':
                    widget_blocks[current_selector] = current_block
                    in_block = False
                    current_block = []

        # font: inherit가 없는 위젯들 찾기
        for selector, block in widget_blocks.items():
            has_font_inherit = any('font: inherit' in line for line in block)
            if not has_font_inherit and selector:
                print(f"  {selector} - font: inherit 없음")

    conn.close()

if __name__ == "__main__":
    analyze_css_selectors()
