"""
텍스트 파일 인코딩 감지 워커 모듈

텍스트 파일의 인코딩을 백그라운드에서 감지하는 QThread 워커 클래스를 제공합니다.
GUI 블로킹 없이 파일 인코딩을 자동으로 감지하여 사용자에게 알려줍니다.

주요 기능:
- 비동기 인코딩 감지 (chardet 라이브러리 사용)
- PyQt6 신호를 통한 결과 전달
- 오류 처리 및 예외 상황 관리
- GUI 메인 스레드 블로킹 방지

작성자: ePub Python Team
최종 수정일: 2025-07-28
"""

from PyQt6.QtCore import QThread, pyqtSignal
import chardet
import logging
from typing import Optional

class EncodingDetectWorker(QThread):
    """
    텍스트 파일의 인코딩을 백그라운드에서 감지하는 워커 스레드입니다.

    chardet 라이브러리를 사용하여 파일의 첫 8KB를 분석하고
    가장 가능성이 높은 인코딩을 감지합니다.

    Signals:
        finished (str, str): 감지 완료 시 (파일경로, 인코딩) 전달
        error (str): 오류 발생 시 오류 메시지 전달

    Attributes:
        file_path (str): 인코딩을 감지할 파일의 경로
    """

    # PyQt6 신호 정의
    finished = pyqtSignal(str, str)  # file_path, encoding
    error = pyqtSignal(str)         # error_message

    def __init__(self, file_path: str):
        """
        인코딩 감지 워커를 초기화합니다.

        Args:
            file_path (str): 인코딩을 감지할 텍스트 파일의 경로
        """
        super().__init__()
        self.file_path = file_path

    def run(self):
        """
        워커 스레드의 메인 실행 함수입니다.

        파일의 첫 8KB를 읽어 chardet으로 인코딩을 감지하고
        결과를 finished 신호로 전달하거나 오류 시 error 신호를 발생시킵니다.

        Returns:
            None

        Emits:
            finished: 인코딩 감지 성공 시 (파일경로, 인코딩)
            error: 인코딩 감지 실패 또는 오류 발생 시 오류 메시지
        """
        try:
            # 파일 존재 여부 확인
            import os
            if not os.path.exists(self.file_path):
                self.error.emit(f"파일을 찾을 수 없습니다: {self.file_path}")
                return

            # 파일 인코딩 감지
            with open(self.file_path, 'rb') as f:
                sample = f.read(8192)  # 처음 8KB만 읽어서 성능 향상

                if not sample:
                    self.error.emit("파일이 비어있거나 읽을 수 없습니다.")
                    return

                result = chardet.detect(sample)
                encoding = result.get('encoding')
                confidence = result.get('confidence', 0)

                if not encoding:
                    self.error.emit("인코딩을 감지할 수 없습니다.")
                    return

                # 신뢰도가 너무 낮으면 경고
                if confidence < 0.7:
                    logging.warning(f"인코딩 감지 신뢰도가 낮습니다: {confidence:.2f}")

                logging.info(f"인코딩 감지 완료: {encoding} (신뢰도: {confidence:.2f})")
                self.finished.emit(self.file_path, encoding)

        except PermissionError:
            error_msg = f"파일 접근 권한이 없습니다: {self.file_path}"
            logging.error(error_msg)
            self.error.emit(error_msg)
        except UnicodeDecodeError as e:
            error_msg = f"파일 읽기 중 인코딩 오류 발생: {e}"
            logging.error(error_msg)
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"인코딩 감지 중 예상치 못한 오류 발생: {e}"
            logging.error(error_msg)
            self.error.emit(error_msg)
