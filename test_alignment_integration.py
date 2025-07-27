#!/usr/bin/env python3
"""
정렬 기능 통합 테스트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from main import MainWindow

def test_alignment_functionality():
    """정렬 기능을 테스트합니다."""
    app = QApplication(sys.argv)

    try:
        # 메인 윈도우 생성
        window = MainWindow()

        print("=== 정렬 콤보박스 초기화 테스트 ===")

        # 각 정렬 옵션을 테스트
        alignment_codes = ["Left", "Center", "Right", "Indent1", "Indent2", "Indent3"]

        print("\n=== 정렬 적용 테스트 ===")
        test_text = "이것은 테스트 텍스트입니다."

        for i, code in enumerate(alignment_codes):
            # 문자 정렬 콤보박스에서 해당 인덱스 선택
            if hasattr(window.ui, 'comboBox_CharsAlign1'):
                window.ui.comboBox_CharsAlign1.setCurrentIndex(i)
                formatted = window.get_formatted_text_with_alignment(test_text, use_chars_align=True)
                print(f"  {code}: {formatted}")

        print("\n=== 현재 설정값 확인 ===")
        window.print_alignment_settings()

        print("\n=== 모든 정렬, 굵기, 스타일, 색상 설정 가져오기 테스트 ===")
        all_chars = window.get_all_chars_alignments()
        all_brackets = window.get_all_brackets_alignments()
        all_chars_weights = window.get_all_chars_weights()
        all_brackets_weights = window.get_all_brackets_weights()
        all_chars_styles = window.get_all_chars_styles()
        all_brackets_styles = window.get_all_brackets_styles()
        all_chars_colors = window.get_all_chars_colors()
        all_brackets_colors = window.get_all_brackets_colors()
        print(f"문자 정렬 설정: {all_chars}")
        print(f"괄호 정렬 설정: {all_brackets}")
        print(f"문자 굵기 설정: {all_chars_weights}")
        print(f"괄호 굵기 설정: {all_brackets_weights}")
        print(f"문자 스타일 설정: {all_chars_styles}")
        print(f"괄호 스타일 설정: {all_brackets_styles}")
        print(f"문자 색상 설정: {all_chars_colors}")
        print(f"괄호 색상 설정: {all_brackets_colors}")

        print("\n=== 개별 인덱스 접근 테스트 ===")
        for i in range(1, 8):
            chars_align = window.get_chars_alignment_by_index(i)
            brackets_align = window.get_brackets_alignment_by_index(i)
            chars_weight = window.get_chars_weight_by_index(i)
            brackets_weight = window.get_brackets_weight_by_index(i)
            print(f"  인덱스 {i}: CharsAlign='{chars_align}', BracketsAlign='{brackets_align}', CharsWeight='{chars_weight}', BracketsWeight='{brackets_weight}'")        # 실제 콤보박스 내용 확인
        print("\n=== 콤보박스 아이템 확인 ===")

        # CharsAlign 콤보박스들 확인 (1-7)
        for i in range(1, 8):
            combo_name = f'comboBox_CharsAlign{i}'
            if hasattr(window.ui, combo_name):
                combo = getattr(window.ui, combo_name)
                print(f"{combo_name} 아이템 수: {combo.count()}")
                for j in range(combo.count()):
                    text = combo.itemText(j)
                    data = combo.itemData(j)
                    print(f"  {j}: '{text}' -> '{data}'")
            else:
                print(f"{combo_name}: 존재하지 않음")

        # BracketsAlign 콤보박스들 확인 (1-7)
        for i in range(1, 8):
            combo_name = f'comboBox_BracketsAlign{i}'
            if hasattr(window.ui, combo_name):
                combo = getattr(window.ui, combo_name)
                print(f"{combo_name} 아이템 수: {combo.count()}")
                for j in range(combo.count()):
                    text = combo.itemText(j)
                    data = combo.itemData(j)
                    print(f"  {j}: '{text}' -> '{data}'")
            else:
                print(f"{combo_name}: 존재하지 않음")

        # CharsWeight 콤보박스들 확인 (1-7)
        for i in range(1, 8):
            combo_name = f'comboBox_CharsWeight{i}'
            if hasattr(window.ui, combo_name):
                combo = getattr(window.ui, combo_name)
                print(f"{combo_name} 아이템 수: {combo.count()}")
                for j in range(combo.count()):
                    text = combo.itemText(j)
                    data = combo.itemData(j)
                    print(f"  {j}: '{text}' -> '{data}'")
            else:
                print(f"{combo_name}: 존재하지 않음")

        # BracketsWeight 콤보박스들 확인 (1-7)
        for i in range(1, 8):
            combo_name = f'comboBox_BracketsWeight{i}'
            if hasattr(window.ui, combo_name):
                combo = getattr(window.ui, combo_name)
                print(f"{combo_name} 아이템 수: {combo.count()}")
                for j in range(combo.count()):
                    text = combo.itemText(j)
                    data = combo.itemData(j)
                    print(f"  {j}: '{text}' -> '{data}'")
            else:
                print(f"{combo_name}: 존재하지 않음")

        # CharsStyle 콤보박스들 확인 (1-7)
        for i in range(1, 8):
            combo_name = f'comboBox_CharsStyle{i}'
            if hasattr(window.ui, combo_name):
                combo = getattr(window.ui, combo_name)
                print(f"{combo_name} 아이템 수: {combo.count()}")
                for j in range(combo.count()):
                    text = combo.itemText(j)
                    data = combo.itemData(j)
                    print(f"  {j}: '{text}' -> '{data}'")
            else:
                print(f"{combo_name}: 존재하지 않음")

        # BracketsStyle 콤보박스들 확인 (1-7)
        for i in range(1, 8):
            combo_name = f'comboBox_BracketsStyle{i}'
            if hasattr(window.ui, combo_name):
                combo = getattr(window.ui, combo_name)
                print(f"{combo_name} 아이템 수: {combo.count()}")
                for j in range(combo.count()):
                    text = combo.itemText(j)
                    data = combo.itemData(j)
                    print(f"  {j}: '{text}' -> '{data}'")
            else:
                print(f"{combo_name}: 존재하지 않음")

        print("\n=== 테스트 완료 ===")
        print("콤보박스 초기화가 성공적으로 완료되었습니다!")

        # 간단한 메시지박스로 성공 알림
        QMessageBox.information(None, "테스트 완료",
                               "정렬 콤보박스 초기화가 성공적으로 완료되었습니다!\n"
                               "콘솔 출력을 확인해주세요.")

        return True

    except Exception as e:
        print(f"[ERROR] 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_alignment_functionality()
    if success:
        print("✅ 모든 테스트 통과!")
    else:
        print("❌ 테스트 실패!")
        sys.exit(1)
