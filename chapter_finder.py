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

        텍스트의 각 줄을 순차적으로 검사하여 선택된 모든 정규식 패턴과 매치를 시도합니다.
        이 방식으로 챕터가 문서에 나타나는 순서대로 정확하게 찾을 수 있습니다.
        
        매칭 처리 방식:
        1. 모든 정규식 패턴을 미리 컴파일
        2. 각 줄마다 모든 정규식 패턴을 순차적으로 검사
        3. 첫 번째로 매치되는 패턴을 해당 줄의 챕터로 인식
        4. 줄의 앞뒤 공백을 제거한 후 줄 시작부터 패턴 매칭
        5. 챕터 발견 시 즉시 신호 발생으로 문서 순서 보장

        Returns:
            None

        Emits:
            chapter_found: 챕터 발견 시 라인 정보 (문서 순서대로)
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

            # 정규식 패턴들을 미리 컴파일
            compiled_patterns = []
            for idx, pattern_str in self.patterns:
                try:
                    pattern = re.compile(pattern_str, re.MULTILINE)
                    regex_name = f"정규식 {idx:02}"
                    compiled_patterns.append((idx, pattern, regex_name, pattern_str))
                    logging.debug(f"정규식 패턴 컴파일 완료: {regex_name} - {pattern_str}")
                except re.error as e:
                    logging.error(f"잘못된 정규식 패턴 (인덱스 {idx}): {pattern_str} - {e}")
                    continue  # 잘못된 정규식은 건너뛰기

            if not compiled_patterns:
                logging.warning("사용 가능한 정규식 패턴이 없습니다.")
                self.finished.emit(0)
                return

            # 각 줄에 대해 모든 정규식 패턴을 순차적으로 검사
            for i, line in enumerate(lines):
                # 줄의 앞뒤 공백 제거 (탭, 스페이스 등 모든 공백 문자)
                line_stripped = line.strip()

                # 빈 줄은 건너뛰기
                if not line_stripped:
                    # 진행률 업데이트 (빈 줄도 포함하여 계산)
                    if total_lines > 0 and i % 20 == 0:
                        percent = min(int((i / total_lines) * 100), 100)
                        self.progress.emit(percent)
                    continue

                # 현재 줄에 대해 모든 정규식 패턴 검사
                chapter_found_in_line = False
                for idx, pattern, regex_name, pattern_str in compiled_patterns:
                    # 정규식 매치 검사 - 공백이 제거된 줄이 패턴과 줄 시작부터 일치하는지 확인
                    if pattern.match(line_stripped):
                        total_found += 1
                        logging.debug(f"챕터 발견: 라인 {i+1} - 원본: '{line}' -> 처리됨: '{line_stripped[:50]}...' (패턴: {regex_name})")
                        self.chapter_found.emit(i + 1, line_stripped, regex_name, pattern_str)
                        chapter_found_in_line = True
                        break  # 한 줄에서 첫 번째로 매치된 패턴만 사용

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
