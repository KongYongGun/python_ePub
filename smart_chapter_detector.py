from PyQt6.QtCore import QThread, pyqtSignal
import re
from typing import List, Dict, Tuple

class SmartChapterDetector(QThread):
    """의미적 챕터 감지를 위한 스마트 감지기"""

    chapter_found = pyqtSignal(int, str, str, float)  # line_no, title, method, confidence
    progress = pyqtSignal(int)
    finished = pyqtSignal(int)

    def __init__(self, text: str, options: Dict):
        super().__init__()
        self.text = text
        self.options = options
        self.lines = text.splitlines()

    def run(self):
        """스마트 챕터 감지 실행"""
        candidates = []

        # 1. 기존 정규식 패턴 (높은 신뢰도)
        regex_candidates = self.find_regex_chapters()
        candidates.extend(regex_candidates)

        # 2. 구조적 패턴 감지 (중간 신뢰도)
        structure_candidates = self.find_structure_chapters()
        candidates.extend(structure_candidates)

        # 3. 의미적 패턴 감지 (낮은 신뢰도)
        semantic_candidates = self.find_semantic_chapters()
        candidates.extend(semantic_candidates)

        # 4. 결과 통합 및 중복 제거
        final_chapters = self.merge_and_validate(candidates)

        # 5. 결과 emit
        for chapter in final_chapters:
            self.chapter_found.emit(
                chapter['line_no'],
                chapter['title'],
                chapter['method'],
                chapter['confidence']
            )

        self.finished.emit(len(final_chapters))

    def find_structure_chapters(self) -> List[Dict]:
        """구조적 패턴으로 챕터 감지"""
        candidates = []

        for i, line in enumerate(self.lines, 1):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # ✅ 대화문 형태 배제 (우선 검사)
            if self.is_dialogue_line(line_stripped):
                continue

            # ✅ 너무 긴 문장 배제 (챕터 제목은 보통 짧음)
            if len(line_stripped) > 100:  # 100자 이상이면 제외
                continue

            confidence = 0.0
            detection_reasons = []

            # 1. 짧은 줄 (제목 특성)
            if len(line_stripped) < 50:
                confidence += 0.2
                detection_reasons.append("짧은 줄")

            # 2. 앞뒤로 빈 줄이 있는지 확인
            prev_empty = i == 1 or not self.lines[i-2].strip()
            next_empty = i >= len(self.lines) or not self.lines[i].strip()

            if prev_empty and next_empty:
                confidence += 0.3
                detection_reasons.append("빈 줄로 둘러쌈")
            elif prev_empty or next_empty:
                confidence += 0.15
                detection_reasons.append("한쪽에 빈 줄")

            # 3. 특수 문자나 이모지 포함
            special_chars = ['◆', '★', '※', '■', '□', '▲', '▼', '◇', '○', '●']
            if any(char in line_stripped for char in special_chars):
                confidence += 0.2
                detection_reasons.append("특수 문자")

            # 4. 대문자나 특별한 서식
            if line_stripped.isupper() and len(line_stripped) > 2:
                confidence += 0.25
                detection_reasons.append("대문자")

            # 5. 시간/장소 표현
            time_patterns = [
                r'\d+년\s*\d*월?\s*\d*일?',
                r'(아침|점심|저녁|밤|새벽)',
                r'(월요일|화요일|수요일|목요일|금요일|토요일|일요일)',
                r'(봄|여름|가을|겨울)',
            ]

            for pattern in time_patterns:
                if re.search(pattern, line_stripped):
                    confidence += 0.15
                    detection_reasons.append("시간 표현")
                    break

            # 6. 장소 표현
            place_keywords = ['에서', '에게', '로부터', '까지', '집', '학교', '회사', '카페']
            if any(keyword in line_stripped for keyword in place_keywords):
                confidence += 0.1
                detection_reasons.append("장소 표현")

            # 7. 센트리컬 정렬 (중앙 정렬) 추정
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces > 10:  # 앞에 공백이 많으면 중앙 정렬 가능성
                confidence += 0.2
                detection_reasons.append("중앙 정렬")

            # 8. 내용과 길이 차이 분석
            confidence += self.analyze_content_break(i)

            # 신뢰도가 임계값 이상인 경우만 후보로 추가
            if confidence >= 0.4:  # 40% 이상
                candidates.append({
                    'line_no': i,
                    'title': line_stripped,
                    'method': f"구조적 감지 ({', '.join(detection_reasons)})",
                    'confidence': confidence
                })

        return candidates

    def find_semantic_chapters(self) -> List[Dict]:
        """의미적 패턴으로 챕터 감지"""
        candidates = []

        # 챕터 제목에 자주 나오는 키워드들
        chapter_keywords = [
            # 감정/상태
            '시작', '끝', '마지막', '처음', '새로운', '다시', '또다시',
            '만남', '이별', '결정', '선택', '기회', '위기', '변화',

            # 행동
            '떠나다', '도착', '출발', '돌아오다', '찾아가다', '만나다',
            '싸우다', '도전', '시도', '실패', '성공', '깨달음',

            # 시간/상황
            '그날', '오늘', '내일', '어제', '나중에', '드디어', '마침내',
            '갑자기', '결국', '하지만', '그러나', '한편', '이때',

            # 대화/관계
            '대화', '약속', '계획', '비밀', '진실', '거짓', '오해',
            '화해', '고백', '결혼', '이혼', '친구', '적', '동료'
        ]

        for i, line in enumerate(self.lines, 1):
            line_stripped = line.strip()
            if not line_stripped or len(line_stripped) > 100:  # 너무 긴 줄은 제외
                continue

            confidence = 0.0
            found_keywords = []

            # 키워드 매칭
            for keyword in chapter_keywords:
                if keyword in line_stripped:
                    confidence += 0.1
                    found_keywords.append(keyword)
                    if confidence >= 0.3:  # 키워드 점수 상한선
                        break

            # 명사로 끝나는 패턴 (제목 특성)
            if re.search(r'[가-힣]+$', line_stripped):
                confidence += 0.1

            # 감탄사나 의문문
            if line_stripped.endswith(('!', '?', '.')):
                confidence += 0.05

            # 단어 수가 적은 경우 (제목 특성)
            word_count = len(line_stripped.split())
            if 1 <= word_count <= 8:
                confidence += 0.1

            if confidence >= 0.3 and found_keywords:  # 30% 이상이고 키워드가 있는 경우
                candidates.append({
                    'line_no': i,
                    'title': line_stripped,
                    'method': f"의미적 감지 (키워드: {', '.join(found_keywords)})",
                    'confidence': confidence
                })

        return candidates

    def analyze_content_break(self, line_index: int) -> float:
        """앞뒤 문단의 내용 변화를 분석"""
        confidence = 0.0

        # 이전/이후 몇 줄의 평균 길이와 비교
        window = 3
        current_line = self.lines[line_index - 1].strip()

        # 이전 줄들의 평균 길이
        prev_lengths = []
        for i in range(max(0, line_index - window - 1), line_index - 1):
            if i < len(self.lines):
                prev_lengths.append(len(self.lines[i].strip()))

        # 이후 줄들의 평균 길이
        next_lengths = []
        for i in range(line_index, min(len(self.lines), line_index + window)):
            next_lengths.append(len(self.lines[i].strip()))

        if prev_lengths and next_lengths:
            prev_avg = sum(prev_lengths) / len(prev_lengths)
            next_avg = sum(next_lengths) / len(next_lengths)
            current_len = len(current_line)

            # 현재 줄이 앞뒤보다 현저히 짧으면 제목일 가능성
            if current_len < prev_avg * 0.3 and current_len < next_avg * 0.3:
                confidence += 0.2

            # 앞뒤 문단의 길이가 비슷하면서 현재 줄이 짧으면
            if abs(prev_avg - next_avg) < 20 and current_len < min(prev_avg, next_avg) * 0.5:
                confidence += 0.15

        return confidence

    def is_dialogue_line(self, line: str) -> bool:
        """대화문 형태인지 감지"""
        # 1. 기본 따옴표로 시작하거나 끝나는 경우
        if (line.startswith('"') and line.endswith('"')) or \
           (line.startswith("'") and line.endswith("'")):
            return True

        # 2. 유니코드 따옴표 검사
        unicode_quotes = ['"', '"', ''', ''']
        for quote in unicode_quotes:
            if line.startswith(quote) and line.endswith(quote):
                return True

        # 3. 대화문 시작 패턴들
        dialogue_patterns = [
            r'^"[^"]*"',  # "말하는 내용"
            r"^'[^']*'",  # '말하는 내용'
            r'[가-힣]+\s*:\s*"',  # 이름: "대사"
            r"[가-힣]+\s*:\s*'",  # 이름: '대사'
            r'[가-힣]+이\s*말했다',  # 누가 말했다
            r'[가-힣]+이\s*대답했다',  # 누가 대답했다
            r'[가-힣]+이\s*물었다',  # 누가 물었다
            r'[가-힣]+이\s*외쳤다',  # 누가 외쳤다
        ]

        for pattern in dialogue_patterns:
            try:
                if re.search(pattern, line):
                    return True
            except re.error:
                continue

        # 4. 대화문 중간/끝 패턴들
        dialogue_endings = [
            '라고 말했다', '라고 대답했다', '라고 물었다', '라고 외쳤다',
            '고 말했다', '고 대답했다', '고 물었다', '고 외쳤다',
            '하며 말했다', '하며 웃었다', '하며 고개를'
        ]

        if any(phrase in line for phrase in dialogue_endings):
            return True

        # 5. 따옴표가 포함된 일반적인 대화문
        quote_chars = ['"', "'", '"', '"', ''', ''']
        quote_count = sum(line.count(char) for char in quote_chars)
        if quote_count >= 2:  # 따옴표가 2개 이상이면 대화문 가능성 높음
            return True

        return False

    def find_regex_chapters(self) -> List[Dict]:
        """기존 정규식 패턴으로 감지 (참고용)"""
        # 이 부분은 기존 시스템과 동일하게 구현
        # 여기서는 예시로 간단히 처리
        return []

    def merge_and_validate(self, candidates: List[Dict]) -> List[Dict]:
        """후보들을 통합하고 검증"""
        # 같은 라인의 중복 제거 (높은 신뢰도 우선)
        line_dict = {}
        for candidate in candidates:
            line_no = candidate['line_no']
            if line_no not in line_dict or candidate['confidence'] > line_dict[line_no]['confidence']:
                line_dict[line_no] = candidate

        # ✅ 줄 번호순 정렬 (텍스트 파일의 순서대로)
        final_candidates = sorted(line_dict.values(), key=lambda x: x['line_no'])

        # 너무 가까운 챕터들 필터링 (최소 5줄 간격)
        filtered = []
        last_line = 0

        for candidate in final_candidates:
            if candidate['line_no'] - last_line >= 5:
                filtered.append(candidate)
                last_line = candidate['line_no']

        return filtered
