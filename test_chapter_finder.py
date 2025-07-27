#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
실제 목차찾기 기능을 시뮬레이션하는 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chapter_finder import ChapterFinderWorker
from PyQt6.QtCore import QCoreApplication
import time

def test_chapter_finder():
    """ChapterFinderWorker 테스트"""
    print("=== ChapterFinderWorker 테스트 ===")

    # 테스트 텍스트
    test_text = """이것은 테스트 파일입니다.

제1장 시작하기
이것은 첫 번째 챕터의 내용입니다.
여러 줄의 텍스트가 있습니다.

제2장 계속하기
이것은 두 번째 챕터의 내용입니다.
더 많은 내용이 있습니다.

제3장 마무리하기
이것은 세 번째 챕터의 내용입니다.
마지막 챕터입니다.

끝"""

    # 테스트 패턴 (DB의 ID 9번 패턴)
    patterns = [(9, r"^제\d+장\s+.*")]

    print(f"테스트 패턴: {patterns}")
    print("텍스트 라인별 확인:")

    lines = test_text.splitlines()
    for i, line in enumerate(lines):
        print(f"Line {i+1}: '{line}'")
        if line.startswith('제') and '장' in line:
            import re
            pattern = re.compile(r"^제\d+장\s+.*")
            match = pattern.search(line)
            print(f"  -> 매칭 결과: {bool(match)}")

    app = QCoreApplication([])

    worker = ChapterFinderWorker(test_text, patterns)

    found_chapters = []

    def on_chapter_found(line_no, title, regex_name, pattern):
        found_chapters.append((line_no, title, regex_name, pattern))
        print(f"워커에서 찾은 챕터: Line {line_no}, Title: '{title}', Regex: {regex_name}")

    def on_finished(total_found):
        print(f"워커 완료: 총 {total_found}개 챕터 찾음")
        app.quit()

    worker.chapter_found.connect(on_chapter_found)
    worker.finished.connect(on_finished)

    worker.start()

    # 워커가 완료될 때까지 대기
    timeout = 5000  # 5초 타임아웃
    start_time = time.time()

    while worker.isRunning() and (time.time() - start_time) < timeout:
        app.processEvents()
        time.sleep(0.1)

    if worker.isRunning():
        print("타임아웃 발생")
        worker.terminate()
        worker.wait()

    return found_chapters

if __name__ == "__main__":
    chapters = test_chapter_finder()
    print(f"\n최종 결과: {len(chapters)}개 챕터 발견")
    for chapter in chapters:
        print(f"  {chapter}")
