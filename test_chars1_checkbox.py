#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
checkBox_Chars1 기능 테스트 스크립트
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# 현재 디렉토리를 모듈 검색 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import MainWindow

def test_chars1_checkbox():
    """checkBox_Chars1이 체크된 상태에서 스타일링이 적용되는지 테스트"""
    
    app = QApplication(sys.argv)
    window = MainWindow()
    
    print("=== checkBox_Chars1 기능 테스트 ===")
    
    # 1. checkBox_Chars1이 존재하는지 확인
    if hasattr(window.ui, 'checkBox_Chars1'):
        print("✓ checkBox_Chars1 위젯 존재")
        checkbox = window.ui.checkBox_Chars1
        
        # 2. 체크박스를 체크 상태로 설정
        checkbox.setChecked(True)
        print(f"✓ checkBox_Chars1 체크 상태: {checkbox.isChecked()}")
        
        # 3. 관련 lineEdit가 존재하는지 확인
        if hasattr(window.ui, 'lineEdit_Chars1'):
            print("✓ lineEdit_Chars1 위젯 존재")
            lineedit = window.ui.lineEdit_Chars1
            
            # 테스트용 텍스트 설정
            test_text = "테스트 문장"
            lineedit.setText(test_text)
            print(f"✓ lineEdit_Chars1에 테스트 텍스트 설정: '{test_text}'")
            
            # 4. 스타일 적용 함수 테스트
            test_line = "테스트 문장"
            styled_line = window.apply_single_character_style(test_line, 1)
            
            print(f"원본 텍스트: '{test_line}'")
            print(f"스타일 적용 후: '{styled_line}'")
            
            if styled_line != test_line:
                print("✓ 문자 스타일이 성공적으로 적용됨")
            else:
                print("⚠ 문자 스타일이 적용되지 않음 (추가 설정 필요할 수 있음)")
                
            # 5. 문자 스타일 정보 확인
            try:
                style_info = window.get_character_style_info(1)
                print(f"✓ 스타일 정보 수집: {style_info}")
            except Exception as e:
                print(f"⚠ 스타일 정보 수집 실패: {e}")
        else:
            print("✗ lineEdit_Chars1 위젯이 존재하지 않음")
    else:
        print("✗ checkBox_Chars1 위젯이 존재하지 않음")
    
    # 6. 전체 문자 스타일링 시스템 테스트
    test_lines = ["테스트 문장", "다른 텍스트", "세 번째 줄"]
    try:
        styled_lines = window.apply_character_styling_to_text(test_lines)
        print(f"✓ 전체 스타일링 시스템 테스트 완료")
        print(f"원본: {test_lines}")
        print(f"스타일 적용 후: {styled_lines}")
    except Exception as e:
        print(f"✗ 전체 스타일링 시스템 테스트 실패: {e}")
    
    print("\n=== 테스트 완료 ===")
    
    # GUI를 닫고 종료
    app.quit()
    return True

if __name__ == "__main__":
    try:
        test_chars1_checkbox()
    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {e}")
        sys.exit(1)
