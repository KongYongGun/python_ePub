#!/usr/bin/env python3
"""
정렬 콤보박스 빠른 테스트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 필요한 모듈들이 있는지 확인
try:
    from PyQt6.QtWidgets import QApplication
    print("✓ PyQt6 사용 가능")
except ImportError:
    print("❌ PyQt6 없음")
    sys.exit(1)

try:
    from main import MainWindow
    print("✓ MainWindow 임포트 성공")
except ImportError as e:
    print(f"❌ MainWindow 임포트 실패: {e}")
    sys.exit(1)

try:
    from ePub_db import initialize_database
    print("✓ DB 모듈 사용 가능")
except ImportError as e:
    print(f"❌ DB 모듈 없음: {e}")

def quick_test():
    """빠른 정렬 콤보박스 테스트"""
    print("\n=== 정렬 콤보박스 빠른 테스트 ===")

    app = QApplication(sys.argv)

    try:
        # DB 초기화 (선택적)
        try:
            initialize_database()
        except:
            pass

        # 메인 윈도우 생성
        window = MainWindow()

        print("\n=== 콤보박스 존재 확인 ===")
        chars_count = 0
        brackets_count = 0
        chars_weight_count = 0
        brackets_weight_count = 0
        chars_style_count = 0
        brackets_style_count = 0
        chars_color_count = 0
        brackets_color_count = 0

        for i in range(1, 8):
            chars_name = f'comboBox_CharsAlign{i}'
            brackets_name = f'comboBox_BracketsAlign{i}'
            chars_weight_name = f'comboBox_CharsWeight{i}'
            brackets_weight_name = f'comboBox_BracketsWeight{i}'
            chars_style_name = f'comboBox_CharsStyle{i}'
            brackets_style_name = f'comboBox_BracketsStyle{i}'
            chars_color_name = f'lineEdit_CharsColor{i}'
            brackets_color_name = f'lineEdit_BracketsColor{i}'
            brackets_style_name = f'comboBox_BracketsStyle{i}'

            if hasattr(window.ui, chars_name):
                chars_count += 1
                combo = getattr(window.ui, chars_name)
                print(f"✓ {chars_name}: {combo.count()}개 아이템")
            else:
                print(f"❌ {chars_name}: 없음")

            if hasattr(window.ui, brackets_name):
                brackets_count += 1
                combo = getattr(window.ui, brackets_name)
                print(f"✓ {brackets_name}: {combo.count()}개 아이템")
            else:
                print(f"❌ {brackets_name}: 없음")

            if hasattr(window.ui, chars_weight_name):
                chars_weight_count += 1
                combo = getattr(window.ui, chars_weight_name)
                print(f"✓ {chars_weight_name}: {combo.count()}개 아이템")
            else:
                print(f"❌ {chars_weight_name}: 없음")

            if hasattr(window.ui, brackets_weight_name):
                brackets_weight_count += 1
                combo = getattr(window.ui, brackets_weight_name)
                print(f"✓ {brackets_weight_name}: {combo.count()}개 아이템")
            else:
                print(f"❌ {brackets_weight_name}: 없음")

            if hasattr(window.ui, chars_style_name):
                chars_style_count += 1
                combo = getattr(window.ui, chars_style_name)
                print(f"✓ {chars_style_name}: {combo.count()}개 아이템")
            else:
                print(f"❌ {chars_style_name}: 없음")

            if hasattr(window.ui, brackets_style_name):
                brackets_style_count += 1
                combo = getattr(window.ui, brackets_style_name)
                print(f"✓ {brackets_style_name}: {combo.count()}개 아이템")
            else:
                print(f"❌ {brackets_style_name}: 없음")

            if hasattr(window.ui, chars_color_name):
                chars_color_count += 1
                lineedit = getattr(window.ui, chars_color_name)
                print(f"✓ {chars_color_name}: 색상 '{lineedit.text()}'")
            else:
                print(f"❌ {chars_color_name}: 없음")

            if hasattr(window.ui, brackets_color_name):
                brackets_color_count += 1
                lineedit = getattr(window.ui, brackets_color_name)
                print(f"✓ {brackets_color_name}: 색상 '{lineedit.text()}'")
            else:
                print(f"❌ {brackets_color_name}: 없음")

        print(f"\n총 {chars_count}/7 개의 CharsAlign 콤보박스 초기화됨")
        print(f"총 {brackets_count}/7 개의 BracketsAlign 콤보박스 초기화됨")
        print(f"총 {chars_weight_count}/7 개의 CharsWeight 콤보박스 초기화됨")
        print(f"총 {brackets_weight_count}/7 개의 BracketsWeight 콤보박스 초기화됨")
        print(f"총 {chars_style_count}/7 개의 CharsStyle 콤보박스 초기화됨")
        print(f"총 {brackets_style_count}/7 개의 BracketsStyle 콤보박스 초기화됨")
        print(f"총 {chars_color_count}/7 개의 CharsColor LineEdit 초기화됨")
        print(f"총 {brackets_color_count}/7 개의 BracketsColor LineEdit 초기화됨")

        # 첫 번째 콤보박스의 옵션들 확인
        if chars_count > 0:
            combo = getattr(window.ui, 'comboBox_CharsAlign1')
            print(f"\n=== CharsAlign1 옵션 목록 ===")
            for i in range(combo.count()):
                text = combo.itemText(i)
                data = combo.itemData(i)
                print(f"  {i}: '{text}' -> '{data}'")

        # 첫 번째 Weight 콤보박스의 옵션들 확인
        if chars_weight_count > 0:
            combo = getattr(window.ui, 'comboBox_CharsWeight1')
            print(f"\n=== CharsWeight1 옵션 목록 ===")
            for i in range(combo.count()):
                text = combo.itemText(i)
                data = combo.itemData(i)
                print(f"  {i}: '{text}' -> '{data}'")

        # 첫 번째 Style 콤보박스의 옵션들 확인
        if chars_style_count > 0:
            combo = getattr(window.ui, 'comboBox_CharsStyle1')
            print(f"\n=== CharsStyle1 옵션 목록 ===")
            for i in range(combo.count()):
                text = combo.itemText(i)
                data = combo.itemData(i)
                print(f"  {i}: '{text}' -> '{data}'")

        print("\n✅ 빠른 테스트 완료!")
        return True

    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    if not success:
        sys.exit(1)
