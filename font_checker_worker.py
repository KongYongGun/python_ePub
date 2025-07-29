"""
폰트 호환성 검사 워커 모듈

텍스트 파일과 폰트 파일의 호환성을 백그라운드에서 분석하는
QThread 워커 클래스를 제공합니다.

주요 기능:
- 폰트 파일에서 지원하는 문자셋 추출 (fontTools 사용)
- 텍스트 파일에서 사용된 문자 수집 (인코딩 자동 감지)
- 폰트-텍스트 간 호환성 분석 및 보고서 생성
- 누락된 문자 및 대체 문자 제안
- 실시간 진행률 및 상태 업데이트
- 비동기 처리로 GUI 블로킹 방지

지원 폰트 형식:
- TrueType (.ttf)
- OpenType (.otf)
- TrueType Collection (.ttc)

작성자: ePub Python Team
최종 수정일: 2025-07-28
"""

from PyQt6.QtCore import QThread, pyqtSignal
import os
import chardet
import logging
from typing import Set, Dict, List, Optional
from fontTools.ttLib import TTFont

class FontCheckerWorker(QThread):
    """
    폰트 호환성 검사를 백그라운드에서 수행하는 워커 스레드입니다.

    fontTools 라이브러리를 사용하여 폰트 파일에서 지원하는 문자셋을 추출하고,
    텍스트 파일에서 사용된 문자들과 비교하여 호환성을 분석합니다.

    Signals:
        progress (int): 작업 진행률 (0-100%)
        status_update (str): 현재 작업 상태 메시지
        result_ready (dict): 분석 완료 시 결과 데이터
        error_occurred (str): 오류 발생 시 오류 메시지

    Attributes:
        font_path (str): 분석할 폰트 파일 경로
        text_file_path (str): 분석할 텍스트 파일 경로
        title (str): ePub 제목 (선택사항)
        author (str): ePub 작가 (선택사항)
        should_stop (bool): 작업 중단 플래그
        _font_cache (dict): 폰트 분석 결과 캐시
    """

    # PyQt6 신호 정의
    progress = pyqtSignal(int)          # 진행률 (0-100)
    status_update = pyqtSignal(str)     # 상태 메시지
    result_ready = pyqtSignal(dict)     # 분석 결과
    error_occurred = pyqtSignal(str)    # 오류 메시지

    def __init__(self, font_path: str, text_file_path: str, title: str = "", author: str = ""):
        """
        폰트 호환성 검사 워커를 초기화합니다.

        Args:
            font_path (str): 분석할 폰트 파일의 경로
            text_file_path (str): 분석할 텍스트 파일의 경로
            title (str, optional): ePub 제목. 기본값은 빈 문자열.
            author (str, optional): ePub 작가. 기본값은 빈 문자열.
        """
        super().__init__()
        self.font_path = font_path
        self.text_file_path = text_file_path
        self.title = title
        self.author = author
        self.should_stop = False
        self._font_cache = {}

    def run(self):
        """
        워커 스레드의 메인 실행 함수입니다.

        폰트 호환성 검사를 단계별로 수행하고 각 단계마다 진행률을 업데이트합니다:
        1. 폰트 파일에서 지원하는 문자셋 추출
        2. 텍스트 파일에서 사용된 문자 수집
        3. 호환성 분석 및 보고서 생성

        Returns:
            None

        Emits:
            progress: 각 단계별 진행률
            status_update: 현재 작업 상태
            result_ready: 분석 완료 시 결과
            error_occurred: 오류 발생 시 오류 메시지
        """
        try:
            logging.info(f"폰트 호환성 검사 시작: {self.font_path}")
            self.status_update.emit("폰트 분석 시작...")
            self.progress.emit(10)

            # 중단 확인
            if self.should_stop:
                logging.info("폰트 호환성 검사가 사용자에 의해 중단되었습니다.")
                return

            # 1. 폰트에서 지원하는 문자 수집
            supported_chars = self._get_font_supported_characters()
            if not supported_chars:
                error_msg = "폰트 파일을 읽을 수 없거나 지원하는 문자가 없습니다."
                logging.error(error_msg)
                self.error_occurred.emit(error_msg)
                return

            self.progress.emit(40)
            logging.info(f"폰트에서 {len(supported_chars)}개의 문자 지원 확인")

            # 중단 확인
            if self.should_stop:
                return

            # 2. 텍스트에서 사용된 문자 수집
            self.status_update.emit("텍스트 문자 수집 중...")
            used_chars = self._collect_text_characters()

            if not used_chars:
                error_msg = "텍스트 파일을 읽을 수 없거나 내용이 없습니다."
                logging.error(error_msg)
                self.error_occurred.emit(error_msg)
                return

            self.progress.emit(80)
            logging.info(f"텍스트에서 {len(used_chars)}개의 고유 문자 발견")

            # 중단 확인
            if self.should_stop:
                return

            # 3. 호환성 분석
            self.status_update.emit("호환성 분석 중...")
            result = self._analyze_compatibility(supported_chars, used_chars)

            self.progress.emit(100)
            logging.info("폰트 호환성 검사 완료")
            self.result_ready.emit(result)

        except Exception as e:
            error_msg = f"폰트 호환성 검사 중 예상치 못한 오류 발생: {e}"
            logging.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.error_occurred.emit(f"폰트 검사 실패: {str(e)}")

    def stop(self):
        """작업 중단"""
        self.should_stop = True

    def _get_font_supported_characters(self):
        """폰트에서 지원하는 문자 수집 (캐싱 포함)"""
        font_key = f"{self.font_path}_{os.path.getmtime(self.font_path)}"

        if font_key in self._font_cache:
            return self._font_cache[font_key]

        try:
            font = TTFont(self.font_path)
            supported_chars = set()

            for table in font['cmap'].tables:
                if hasattr(table, 'cmap'):
                    for unicode_point in table.cmap.keys():
                        if self.should_stop:
                            font.close()
                            return set()

                        try:
                            char = chr(unicode_point)
                            supported_chars.add(char)
                        except ValueError:
                            continue

            font.close()
            self._font_cache[font_key] = supported_chars
            return supported_chars

        except Exception as e:
            raise Exception(f"폰트 분석 실패: {e}")

    def _collect_text_characters(self, max_sample_size=1024*1024):
        """텍스트에서 사용된 문자 수집 (샘플링 지원)"""
        used_chars = set()

        # 제목과 저자명 추가
        used_chars.update(self.title)
        used_chars.update(self.author)

        if not os.path.exists(self.text_file_path):
            logging.warning(f"텍스트 파일이 존재하지 않음: {self.text_file_path}")
            return used_chars

        try:
            file_size = os.path.getsize(self.text_file_path)
        except (OSError, IOError) as e:
            logging.error(f"텍스트 파일 크기 확인 실패: {self.text_file_path}, 오류: {e}")
            return used_chars

        try:
            # 파일 인코딩 자동 감지
            encoding = self._detect_file_encoding()

            if file_size > max_sample_size:
                # 큰 파일은 샘플링
                used_chars.update(self._sample_characters(max_sample_size, encoding))
            else:
                # 작은 파일은 전체 읽기 (안전한 방식)
                try:
                    with open(self.text_file_path, 'r', encoding=encoding) as f:
                        chunk_size = 8192  # 8KB씩 읽기
                        while True:
                            if self.should_stop:
                                break

                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            used_chars.update(chunk)
                except UnicodeDecodeError as e:
                    # 인코딩 오류 시 다른 인코딩들 시도
                    for fallback_encoding in ['euc-kr', 'cp949', 'latin1', 'utf-8']:
                        if fallback_encoding != encoding:
                            try:
                                with open(self.text_file_path, 'r', encoding=fallback_encoding) as f:
                                    content = f.read()
                                    used_chars.update(content)
                                break
                            except UnicodeDecodeError:
                                continue
                    else:
                        raise Exception(f"파일 인코딩을 인식할 수 없습니다. 원본 오류: {e}")

            return used_chars

        except Exception as e:
            raise Exception(f"텍스트 분석 실패: {e}")

    def _detect_file_encoding(self):
        """파일의 인코딩을 자동 감지합니다."""
        if not os.path.exists(self.text_file_path):
            logging.warning(f"인코딩 감지할 텍스트 파일이 존재하지 않음: {self.text_file_path}")
            return 'utf-8'
            
        try:
            with open(self.text_file_path, 'rb') as f:
                # 더 큰 샘플로 정확성 향상
                sample = f.read(32768)  # 32KB
                if sample:
                    result = chardet.detect(sample)
                    encoding = result.get('encoding', 'utf-8')
                    confidence = result.get('confidence', 0)

                    # 일반적인 한국어 인코딩 우선 시도
                    if confidence < 0.8:
                        # 한국어 파일 가능성이 높은 경우 특정 인코딩들 시도
                        for test_encoding in ['euc-kr', 'cp949', 'utf-8', 'latin-1']:
                            try:
                                with open(self.text_file_path, 'r', encoding=test_encoding) as test_f:
                                    test_f.read(1024)  # 작은 샘플로 테스트
                                    return test_encoding
                            except UnicodeDecodeError:
                                continue

                    return encoding if encoding else 'utf-8'
                else:
                    return 'utf-8'
        except Exception as e:
            logging.error(f"파일 인코딩 감지 실패: {self.text_file_path}, 오류: {e}")
            return 'utf-8'

    def _sample_characters(self, sample_size, encoding):
        """큰 파일에서 문자 샘플링"""
        used_chars = set()
        
        if not os.path.exists(self.text_file_path):
            logging.warning(f"샘플링할 텍스트 파일이 존재하지 않음: {self.text_file_path}")
            return used_chars
            
        try:
            file_size = os.path.getsize(self.text_file_path)
        except (OSError, IOError) as e:
            logging.error(f"샘플링용 파일 크기 확인 실패: {self.text_file_path}, 오류: {e}")
            return used_chars

        try:
            with open(self.text_file_path, 'r', encoding=encoding) as f:
                sample_points = 10
                chunk_size = sample_size // sample_points

                for i in range(sample_points):
                    if self.should_stop:
                        break

                    position = (file_size * i) // sample_points
                    f.seek(position)

                    if position > 0:
                        f.readline()  # 줄 경계 맞추기

                    chunk = f.read(chunk_size)
                    used_chars.update(chunk)

                    # 충분한 문자가 수집되면 조기 종료
                    if len(used_chars) > 10000:
                        break

            return used_chars

        except UnicodeDecodeError as e:
            # 샘플링 중 인코딩 오류 시 다른 인코딩들 시도
            for fallback_encoding in ['euc-kr', 'cp949', 'latin1', 'utf-8']:
                if fallback_encoding != encoding:
                    try:
                        with open(self.text_file_path, 'r', encoding=fallback_encoding) as f:
                            # 더 안전한 샘플링 - 파일 시작부분만
                            chunk = f.read(min(sample_size, 100000))  # 최대 100KB
                            used_chars.update(chunk)
                        return used_chars
                    except UnicodeDecodeError:
                        continue

            raise Exception(f"샘플링 중 인코딩 오류: {e}")
        except Exception as e:
            raise Exception(f"샘플링 실패: {e}")

    def _analyze_compatibility(self, supported_chars, used_chars):
        """폰트 호환성 분석"""
        # 지원되지 않는 문자 찾기
        unsupported_chars = used_chars - supported_chars

        # 제어 문자 제외
        control_chars = {'\n', '\r', '\t', ' ', '\u200b', '\ufeff'}
        unsupported_chars = unsupported_chars - control_chars

        # 결과 생성
        result = {
            'font_path': self.font_path,
            'font_name': os.path.basename(self.font_path),
            'total_used_chars': len(used_chars),
            'total_supported_chars': len(supported_chars),
            'unsupported_count': len(unsupported_chars),
            'unsupported_chars': list(unsupported_chars)[:50],  # 최대 50개만
            'is_compatible': len(unsupported_chars) == 0,
            'compatibility_rate': ((len(used_chars) - len(unsupported_chars)) / len(used_chars) * 100) if used_chars else 100
        }

        return result
