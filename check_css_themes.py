#!/usr/bin/env python3
"""
데이터베이스의 CSS 테마에서 font-size 설정을 확인하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ePub_db import get_all_css_themes

def check_css_themes():
    themes = get_all_css_themes()
    print(f"총 {len(themes)}개의 테마를 확인합니다.\n")

    for theme in themes:
        id, name, desc, content, is_default = theme
        print(f'테마 ID {id}: {name}')
        print(f'기본 테마: {is_default}')
        print(f'CSS 길이: {len(content)} 문자')

        # QLabel과 QLineEdit의 font 설정 확인
        if 'font-size' in content.lower():
            print('⚠️ CSS에 font-size 설정 발견!')
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'font-size' in line.lower():
                    print(f'  라인 {i+1}: {line.strip()}')
        else:
            print('✅ font-size 설정 없음')

        # font: inherit 설정 확인
        if 'font: inherit' in content:
            print('✅ font: inherit 설정 발견')
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'font: inherit' in line:
                    print(f'  라인 {i+1}: {line.strip()}')
        else:
            print('⚠️ font: inherit 설정 없음')

        print('-' * 50)

if __name__ == "__main__":
    check_css_themes()
