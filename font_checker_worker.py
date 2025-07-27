from PyQt6.QtCore import QThread, pyqtSignal
import os
import chardet
from fontTools.ttLib import TTFont

class FontCheckerWorker(QThread):
    """폰트 호환성 검사를 백그라운드에서 수행하는 워커"""

    # 시그널 정의
    progress = pyqtSignal(int)  # 진행률 (0-100)
    status_update = pyqtSignal(str)  # 상태 메시지
    result_ready = pyqtSignal(dict)  # 결과
    error_occurred = pyqtSignal(str)  # 에러

    def __init__(self, font_path, text_file_path, title="", author=""):
        super().__init__()
        self.font_path = font_path
        self.text_file_path = text_file_path
        self.title = title
        self.author = author
        self.should_stop = False
        self._font_cache = {}

    def run(self):
        """백그라운드에서 폰트 호환성 검사 실행"""
        try:
            self.status_update.emit("폰트 분석 시작...")
            self.progress.emit(10)

            if self.should_stop:
                return

            # 1. 폰트에서 지원하는 문자 수집
            supported_chars = self._get_font_supported_characters()
            if not supported_chars:
                self.error_occurred.emit("폰트 파일을 읽을 수 없습니다.")
                return

            self.progress.emit(40)

            if self.should_stop:
                return

            # 2. 텍스트에서 사용된 문자 수집
            self.status_update.emit("텍스트 문자 수집 중...")
            used_chars = self._collect_text_characters()

            self.progress.emit(80)

            if self.should_stop:
                return

            # 3. 호환성 분석
            self.status_update.emit("호환성 분석 중...")
            result = self._analyze_compatibility(supported_chars, used_chars)

            self.progress.emit(100)
            self.result_ready.emit(result)

        except Exception as e:
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
            return used_chars

        file_size = os.path.getsize(self.text_file_path)

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
        except Exception:
            return 'utf-8'

    def _sample_characters(self, sample_size, encoding):
        """큰 파일에서 문자 샘플링"""
        used_chars = set()
        file_size = os.path.getsize(self.text_file_path)

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
