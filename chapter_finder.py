from PyQt6.QtCore import QThread, pyqtSignal
import re

class ChapterFinderWorker(QThread):
    chapter_found = pyqtSignal(int, str, str, str)  # line_no, title, regex_name, pattern
    progress = pyqtSignal(int)
    finished = pyqtSignal(int)  # total found

    def __init__(self, text, patterns):
        super().__init__()
        self.text = text
        self.patterns = patterns  # [(idx, pattern)]

    def run(self):
        lines = self.text.splitlines()
        total_lines = len(lines)
        total_found = 0

        for idx, pattern_str in self.patterns:
            try:
                pattern = re.compile(pattern_str)
            except re.error:
                continue  # skip invalid regex

            regex_name = f"정규식 {idx:02}"

            for i, line in enumerate(lines):
                if pattern.search(line):
                    total_found += 1
                    self.chapter_found.emit(i + 1, line.strip(), regex_name, pattern_str)

                if total_lines > 0 and i % 20 == 0:
                    percent = int((i / total_lines) * 100)
                    self.progress.emit(percent)

        self.progress.emit(100)
        self.finished.emit(total_found)
