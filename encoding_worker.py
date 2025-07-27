from PyQt6.QtCore import QThread, pyqtSignal
import chardet

class EncodingDetectWorker(QThread):
    finished = pyqtSignal(str, str)  # file_path, encoding
    error = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            with open(self.file_path, 'rb') as f:
                sample = f.read(8192)  # 처음 8KB만 읽기
                result = chardet.detect(sample)
                encoding = result.get('encoding')
                if not encoding:
                    self.error.emit("인코딩을 감지할 수 없습니다.")
                    return
                self.finished.emit(self.file_path, encoding)
        except Exception as e:
            self.error.emit(str(e))
