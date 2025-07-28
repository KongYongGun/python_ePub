"""
챕터 검색 워커 모듈

텍스트에서 정규식 패턴을 사용하여 챕터를 백그라운드에서 검색하는
QThread 워커 클래스를 제공합니다.

주요 기능:
- 다중 정규식 패턴을 사용한 챕터 검색
- 실시간 진행률 업데이트
- 비동기 처리로 GUI 블로킹 방지
- 잘못된 정규식 패턴 예외 처리
- 검색 결과를 신호로 실시간 전달

작성자: ePub Python Team
최종 수정일: 2025-07-28
"""

from PyQt6.QtCore import QThread, pyqtSignal
import re
import logging
from typing import List, Tuple

class ChapterFinderWorker(QThread):
    """
    텍스트에서 정규식 패턴을 사용하여 챕터를 검색하는 워커 스레드입니다.

    여러 정규식 패턴을 순차적으로 적용하여 텍스트의 각 줄을 검사하고,
    매치되는 줄을 챕터로 인식하여 실시간으로 결과를 전달합니다.

    Signals:
        chapter_found (int, str, str, str): 챕터 발견 시 (라인번호, 제목, 정규식명, 패턴) 전달
        progress (int): 진행률 업데이트 (0-100%)
        finished (int): 검색 완료 시 총 발견된 챕터 수 전달

    Attributes:
        text (str): 검색 대상 텍스트
        patterns (List[Tuple[int, str]]): (인덱스, 정규식패턴) 튜플 리스트
    """

    # PyQt6 신호 정의
    chapter_found = pyqtSignal(int, str, str, str)  # line_no, title, regex_name, pattern
    progress = pyqtSignal(int)                      # progress_percent
    finished = pyqtSignal(int)                      # total_found_count

    def __init__(self, text: str, patterns: List[Tuple[int, str]]):
        """
        챕터 검색 워커를 초기화합니다.

        Args:
            text (str): 챕터를 검색할 대상 텍스트
            patterns (List[Tuple[int, str]]): (인덱스, 정규식패턴) 형태의 튜플 리스트
        """
        super().__init__()
        self.text = text
        self.patterns = patterns

    def run(self):
        """
        워커 스레드의 메인 실행 함수입니다.

        각 정규식 패턴을 텍스트의 모든 줄에 적용하여 챕터를 검색하고,
        매치되는 줄을 찾을 때마다 chapter_found 신호를 발생시킵니다.
        진행률은 progress 신호로, 완료 시에는 finished 신호를 발생시킵니다.

        Returns:
            None

        Emits:
            chapter_found: 챕터 발견 시 라인 정보
            progress: 검색 진행률 (20줄마다 업데이트)
            finished: 검색 완료 시 총 발견 챕터 수
        """
        try:
            lines = self.text.splitlines()
            total_lines = len(lines)
            total_found = 0

            if total_lines == 0:
                logging.warning("검색할 텍스트가 비어있습니다.")
                self.finished.emit(0)
                return

            # 각 정규식 패턴에 대해 검색 수행
            for idx, pattern_str in self.patterns:
                try:
                    # 정규식 컴파일 시도
                    pattern = re.compile(pattern_str, re.MULTILINE)
                    regex_name = f"정규식 {idx:02}"

                    logging.debug(f"정규식 패턴 적용 중: {regex_name} - {pattern_str}")

                except re.error as e:
                    logging.error(f"잘못된 정규식 패턴 (인덱스 {idx}): {pattern_str} - {e}")
                    continue  # 잘못된 정규식은 건너뛰기

                # 각 줄에 대해 패턴 매치 검사
                for i, line in enumerate(lines):
                    line_stripped = line.strip()

                    # 빈 줄은 건너뛰기
                    if not line_stripped:
                        continue

                    # 정규식 매치 검사
                    if pattern.search(line):
                        total_found += 1
                        logging.debug(f"챕터 발견: 라인 {i+1} - {line_stripped[:50]}...")
                        self.chapter_found.emit(i + 1, line_stripped, regex_name, pattern_str)

                    # 진행률 업데이트 (20줄마다)
                    if total_lines > 0 and i % 20 == 0:
                        percent = min(int((i / total_lines) * 100), 100)
                        self.progress.emit(percent)

            # 검색 완료
            self.progress.emit(100)
            logging.info(f"챕터 검색 완료: 총 {total_found}개 발견")
            self.finished.emit(total_found)

        except Exception as e:
            logging.error(f"챕터 검색 중 예상치 못한 오류 발생: {e}")
            self.finished.emit(0)
