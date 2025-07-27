#!/usr/bin/env python3
"""
CSS 테마에서 font: inherit를 명시적인 폰트 설정으로 변경하는 스크립트
"""

import re

def update_css_fonts():
    with open('css_themes.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # font: inherit를 명시적 폰트 설정으로 변경
    patterns = [
        (r'font: inherit; /\* UI에서 설정한 폰트 유지 \*/', 'font-family: "맑은 고딕";\n    font-size: 11pt;'),
    ]

    for old_pattern, new_text in patterns:
        content = re.sub(old_pattern, new_text, content)

    with open('css_themes.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("CSS 테마의 font: inherit를 명시적 폰트 설정으로 변경했습니다.")

if __name__ == "__main__":
    update_css_fonts()
