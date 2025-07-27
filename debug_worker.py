#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChapterFinderWorker 디버깅용 수정 버전
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtCore import QThread, pyqtSignal
import re

class DebugChapterFinderWorker(QThread):
    chapter_found = pyqtSignal(int, str, str, str)  # line_no, title, regex_name, pattern
    progress = pyqtSignal(int)
    finished = pyqtSignal(int)  # total found

    def __init__(self, text, patterns):
        super().__init__()
        self.text = text
        self.patterns = patterns  # [(idx, pattern)]

    def run(self):
        print(f"[DEBUG] 워커 시작. 패턴 개수: {len(self.patterns)}")

        lines = self.text.splitlines()
        total_lines = len(lines)
        total_found = 0

        print(f"[DEBUG] 총 라인 수: {total_lines}")

        for idx, pattern_str in self.patterns:
            print(f"[DEBUG] 패턴 처리 중: {idx}, {pattern_str}")

            try:
                pattern = re.compile(pattern_str)
                print(f"[DEBUG] 정규식 컴파일 성공")
            except re.error as e:
                print(f"[DEBUG] 정규식 컴파일 실패: {e}")
                continue  # skip invalid regex

            regex_name = f"정규식 {idx:02}"

            for i, line in enumerate(lines):
                if pattern.search(line):
                    total_found += 1
                    print(f"[DEBUG] 챕터 발견! Line {i+1}: {line.strip()}")
                    self.chapter_found.emit(i + 1, line.strip(), regex_name, pattern_str)

                if total_lines > 0 and i % 20 == 0:
                    percent = int((i / total_lines) * 100)
                    self.progress.emit(percent)

        print(f"[DEBUG] 워커 완료. 총 발견: {total_found}")
        self.progress.emit(100)
        self.finished.emit(total_found)


if __name__ == "__main__":
    from PyQt6.QtCore import QCoreApplication
    import time

    test_text = """이것은 테스트 파일입니다.

제1장 시작하기
이것은 첫 번째 챕터의 내용입니다.

제2장 계속하기
이것은 두 번째 챕터의 내용입니다.

제3장 마무리하기
이것은 세 번째 챕터의 내용입니다."""

    patterns = [(9, r"^제\d+장\s+.*")]

    app = QCoreApplication([])

    worker = DebugChapterFinderWorker(test_text, patterns)

    found_chapters = []

    def on_chapter_found(line_no, title, regex_name, pattern):
        found_chapters.append((line_no, title, regex_name, pattern))
        print(f"[SIGNAL] 챕터 발견: Line {line_no}, Title: '{title}'")

    def on_finished(total_found):
        print(f"[SIGNAL] 완료: {total_found}개")
        app.quit()

    worker.chapter_found.connect(on_chapter_found)
    worker.finished.connect(on_finished)

    print("워커 시작 중...")
    worker.start()

    # 워커가 완료될 때까지 대기
    timeout = 5
    start_time = time.time()

    while worker.isRunning() and (time.time() - start_time) < timeout:
        app.processEvents()
        time.sleep(0.1)

    if worker.isRunning():
        print("타임아웃!")
        worker.terminate()
        worker.wait()

    print(f"최종 결과: {len(found_chapters)}개 챕터")
