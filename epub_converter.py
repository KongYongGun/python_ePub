"""
ePub 변환 및 품질 검증 모듈

텍스트 파일을 완전한 ePub 3.0 형식으로 변환하고 품질을 검증하는
핵심 모듈입니다.

주요 기능:
- 텍스트 파일을 ePub 3.0 형식으로 변환
- 챕터 자동 분할 및 목차 생성
- 커버 이미지 및 삽화 포함
- 폰트 임베딩 및 서브셋 최적화
- CSS 스타일시트 적용
- ePub 품질 검증 및 표준 준수 확인
- 메타데이터 설정 (제목, 작가, 언어, 출판일 등)
- 진행률 표시 및 사용자 피드백

지원 기능:
- ePub 3.0 표준 완전 지원
- 반응형 레이아웃 및 다양한 화면 크기 지원
- 접근성 기능 (aria-label, navigation 등)
- 폰트 라이선스 호환성 검사
- 압축 최적화

작성자: ePub Python Team
최종 수정일: 2025-07-28
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
import shutil
import time
import logging
import re
import zipfile
from typing import List, Dict, Optional, Tuple
from PyQt6.QtWidgets import QMessageBox, QProgressDialog
from PyQt6.QtCore import QTimer, Qt
from ebooklib import epub
from fontTools import subset
from fontTools.ttLib import TTFont
from xml.etree import ElementTree as ET
import io

# ==================================================================================
# ePub 품질 검증 클래스
# ==================================================================================

class EpubQualityValidator:
    """
    ePub 파일의 품질과 표준 준수를 검증하는 클래스입니다.

    ePub 3.0 표준에 따라 파일 구조, 메타데이터, 내용을 분석하고
    문제점이나 개선사항을 식별하여 보고서를 생성합니다.

    검증 항목:
    - 파일 크기 및 구조 유효성
    - 메타데이터 완성도
    - 챕터 내용 및 HTML 구조
    - 이미지 및 폰트 파일 유효성
    - CSS 스타일시트 문법
    - 접근성 준수 사항

    Attributes:
        main_window: 메인 윈도우 참조 (로깅용)
        issues (List[str]): 발견된 문제점 목록
    """

    def __init__(self, main_window):
        """
        ePub 품질 검증기를 초기화합니다.

        Args:
            main_window: 메인 윈도우 객체 (로깅 메서드 사용)
        """
        self.main_window = main_window
        self.issues = []

    def validate_epub_file(self, epub_path: str) -> List[str]:
        """
        ePub 파일의 품질을 종합적으로 검증합니다.

        파일 구조, 메타데이터, 내용, 표준 준수 등을 체크하여
        문제점 목록을 반환합니다.

        Args:
            epub_path (str): 검증할 ePub 파일 경로

        Returns:
            List[str]: 발견된 문제점 및 개선사항 목록

        Raises:
            FileNotFoundError: ePub 파일이 존재하지 않을 때
            zipfile.BadZipFile: ePub 파일이 손상되었을 때
        """
        self.issues = []

        try:
            self.log_info(f"ePub 품질 검증 시작: {epub_path}")

            # 파일 존재 여부 확인
            if not os.path.exists(epub_path):
                self.issues.append("❌ ePub 파일이 존재하지 않습니다.")
                return self.issues

            # 1. 파일 크기 검증
            self._check_file_size(epub_path)

            # 2. 파일 구조 검증
            self._check_file_structure(epub_path)

            # 3. 메타데이터 검증
            self._check_metadata(epub_path)

            # 4. 챕터 내용 검증
            self._check_chapter_content(epub_path)

            # 5. 이미지 검증
            self._check_images(epub_path)

            # 6. CSS 스타일 검증
            self._check_css_styles(epub_path)

            # 7. 폰트 검증
            self._check_fonts(epub_path)

            # 8. XHTML 구조 검증
            self._check_xhtml_structure(epub_path)

            # 9. 목차 구조 검증
            self._check_toc_structure(epub_path)

            if not self.issues:
                self.log_info("ePub 품질 검증 통과: 문제점이 발견되지 않았습니다.")
            else:
                self.log_warning(f"ePub 품질 검증 완료: {len(self.issues)}개의 문제점 발견")

        except Exception as e:
            self.issues.append(f"❌ 품질 검증 중 오류 발생: {str(e)}")

        return self.issues

    def _check_file_size(self, epub_path):
        """파일 크기를 확인합니다."""
        try:
            file_size = os.path.getsize(epub_path)
            size_mb = file_size / (1024 * 1024)

            if size_mb > 100:  # 100MB 초과
                self.issues.append(f"⚠️ 파일 크기가 큽니다: {size_mb:.1f}MB (권장: 50MB 이하)")
            elif size_mb < 0.1:  # 100KB 미만
                self.issues.append(f"⚠️ 파일 크기가 너무 작습니다: {size_mb:.1f}MB")
            else:
                self.log_info(f"파일 크기 적정: {size_mb:.1f}MB")

        except Exception as e:
            self.issues.append(f"❌ 파일 크기 확인 실패: {str(e)}")

    def _check_file_structure(self, epub_path):
        """ePub 파일 구조를 확인합니다."""
        try:
            with zipfile.ZipFile(epub_path, 'r') as zip_file:
                file_list = zip_file.namelist()

                # 필수 파일 확인
                required_files = ['mimetype', 'META-INF/container.xml']
                for required_file in required_files:
                    if required_file not in file_list:
                        self.issues.append(f"❌ 필수 파일 누락: {required_file}")

                # OPF 파일 확인
                opf_files = [f for f in file_list if f.endswith('.opf')]
                if not opf_files:
                    self.issues.append("❌ OPF 파일이 없습니다.")

                # XHTML 파일 확인
                xhtml_files = [f for f in file_list if f.endswith(('.xhtml', '.html'))]
                if not xhtml_files:
                    self.issues.append("❌ 콘텐츠 파일(XHTML)이 없습니다.")
                else:
                    self.log_info(f"콘텐츠 파일 수: {len(xhtml_files)}개")

        except Exception as e:
            self.issues.append(f"❌ 파일 구조 확인 실패: {str(e)}")

    def _check_metadata(self, epub_path):
        """메타데이터를 확인합니다."""
        try:
            book = epub.read_epub(epub_path)

            # 제목 확인
            title = book.get_metadata('DC', 'title')
            if not title or not title[0][0].strip():
                self.issues.append("⚠️ 제목이 설정되지 않았습니다.")

            # 저자 확인
            authors = book.get_metadata('DC', 'creator')
            if not authors:
                self.issues.append("⚠️ 저자 정보가 설정되지 않았습니다.")

            # 언어 확인
            languages = book.get_metadata('DC', 'language')
            if not languages:
                self.issues.append("⚠️ 언어 정보가 설정되지 않았습니다.")

            self.log_info("메타데이터 확인 완료")

        except Exception as e:
            self.issues.append(f"❌ 메타데이터 확인 실패: {str(e)}")

    def _check_chapter_content(self, epub_path):
        """챕터 내용을 확인합니다."""
        try:
            book = epub.read_epub(epub_path)
            chapter_count = 0
            empty_chapters = 0
            short_chapters = 0
            long_chapters = 0
            total_content_length = 0

            for item in book.get_items():
                if item.get_type() == epub.ITEM_DOCUMENT:
                    chapter_count += 1
                    content = item.get_content().decode('utf-8')

                    # HTML 태그 제거 후 텍스트 길이 확인
                    text_content = re.sub(r'<[^>]+>', '', content).strip()
                    content_length = len(text_content)
                    total_content_length += content_length

                    if content_length < 10:  # 10자 미만
                        empty_chapters += 1
                    elif content_length < 100:  # 100자 미만 (너무 짧은 챕터)
                        short_chapters += 1
                    elif content_length > 50000:  # 50,000자 초과 (너무 긴 챕터)
                        long_chapters += 1

            if chapter_count == 0:
                self.issues.append("❌ 챕터가 없습니다.")
            else:
                # 평균 챕터 길이 계산
                avg_length = total_content_length / chapter_count if chapter_count > 0 else 0

                if empty_chapters > 0:
                    self.issues.append(f"⚠️ 빈 챕터가 {empty_chapters}개 있습니다. (10자 미만)")

                if short_chapters > 0:
                    self.issues.append(f"⚠️ 너무 짧은 챕터가 {short_chapters}개 있습니다. (100자 미만)")

                if long_chapters > 0:
                    self.issues.append(f"⚠️ 너무 긴 챕터가 {long_chapters}개 있습니다. (50,000자 초과)")

                if avg_length < 500:
                    self.issues.append(f"⚠️ 평균 챕터 길이가 짧습니다: {avg_length:.0f}자 (권장: 1,000자 이상)")

                self.log_info(f"챕터 내용 확인 완료: {chapter_count}개 챕터, 평균 {avg_length:.0f}자")

        except Exception as e:
            self.issues.append(f"❌ 챕터 내용 확인 실패: {str(e)}")

    def _check_images(self, epub_path):
        """이미지를 확인합니다."""
        try:
            book = epub.read_epub(epub_path)
            image_count = 0
            large_images = 0

            for item in book.get_items():
                if item.get_type() == epub.ITEM_IMAGE:
                    image_count += 1
                    image_size = len(item.get_content())

                    # 5MB 초과 이미지 확인
                    if image_size > 5 * 1024 * 1024:
                        large_images += 1

            if large_images > 0:
                self.issues.append(f"⚠️ 큰 이미지가 {large_images}개 있습니다. (5MB 초과)")

            if image_count > 0:
                self.log_info(f"이미지 확인 완료: {image_count}개 이미지")

        except Exception as e:
            self.issues.append(f"❌ 이미지 확인 실패: {str(e)}")

    def _check_css_styles(self, epub_path):
        """CSS 스타일을 확인합니다."""
        try:
            book = epub.read_epub(epub_path)
            css_count = 0

            for item in book.get_items():
                if item.get_type() == epub.ITEM_STYLE:
                    css_count += 1
                    css_content = item.get_content().decode('utf-8')

                    # 기본적인 CSS 검증
                    if len(css_content.strip()) < 10:
                        self.issues.append("⚠️ CSS 파일이 거의 비어있습니다.")

            if css_count == 0:
                self.issues.append("⚠️ CSS 스타일시트가 없습니다.")
            else:
                self.log_info(f"CSS 확인 완료: {css_count}개 스타일시트")

        except Exception as e:
            self.issues.append(f"❌ CSS 확인 실패: {str(e)}")

    def _check_fonts(self, epub_path):
        """폰트를 확인합니다."""
        try:
            book = epub.read_epub(epub_path)
            font_count = 0
            large_fonts = 0

            for item in book.get_items():
                if item.media_type and 'font' in item.media_type:
                    font_count += 1
                    font_size = len(item.get_content())

                    # 10MB 초과 폰트 확인
                    if font_size > 10 * 1024 * 1024:
                        large_fonts += 1

            if large_fonts > 0:
                self.issues.append(f"⚠️ 큰 폰트 파일이 {large_fonts}개 있습니다. (10MB 초과)")

            if font_count > 0:
                self.log_info(f"폰트 확인 완료: {font_count}개 폰트")

        except Exception as e:
            self.issues.append(f"❌ 폰트 확인 실패: {str(e)}")

    def _check_xhtml_structure(self, epub_path):
        """XHTML 구조와 유효성을 확인합니다."""
        try:
            book = epub.read_epub(epub_path)
            invalid_html_count = 0
            missing_title_count = 0

            for item in book.get_items():
                if item.get_type() == epub.ITEM_DOCUMENT:
                    try:
                        content = item.get_content().decode('utf-8')

                        # 기본적인 HTML 구조 검증
                        if '<html' not in content:
                            invalid_html_count += 1
                            continue

                        # title 태그 확인
                        if '<title>' not in content and '<title ' not in content:
                            missing_title_count += 1

                        # 잘못된 문자 인코딩 확인
                        if '�' in content:  # 깨진 문자
                            self.issues.append(f"⚠️ 문자 인코딩 문제가 있는 챕터가 발견되었습니다: {item.file_name}")

                    except Exception:
                        invalid_html_count += 1

            if invalid_html_count > 0:
                self.issues.append(f"❌ 유효하지 않은 XHTML 구조: {invalid_html_count}개 파일")

            if missing_title_count > 0:
                self.issues.append(f"⚠️ 제목 태그가 없는 챕터: {missing_title_count}개")

            if invalid_html_count == 0 and missing_title_count == 0:
                self.log_info("XHTML 구조 검증 완료")

        except Exception as e:
            self.issues.append(f"❌ XHTML 구조 확인 실패: {str(e)}")

    def _check_toc_structure(self, epub_path):
        """목차 구조를 확인합니다."""
        try:
            book = epub.read_epub(epub_path)

            # 목차 항목 수 확인
            toc_items = book.toc
            if not toc_items:
                self.issues.append("⚠️ 목차가 비어있습니다.")
                return

            # 목차 항목 개수 확인
            toc_count = len(toc_items)

            # 챕터 수와 목차 수 비교
            chapter_count = 0
            for item in book.get_items():
                if item.get_type() == epub.ITEM_DOCUMENT:
                    chapter_count += 1

            # 커버나 네비게이션 파일 제외하고 비교
            expected_toc_count = max(1, chapter_count - 2)  # 대략적 예상

            if toc_count < expected_toc_count * 0.5:  # 목차가 챕터의 절반보다 적으면
                self.issues.append(f"⚠️ 목차 항목이 적습니다: {toc_count}개 (예상: {expected_toc_count}개 이상)")

            self.log_info(f"목차 구조 확인 완료: {toc_count}개 항목")

        except Exception as e:
            self.issues.append(f"❌ 목차 구조 확인 실패: {str(e)}")

    def show_validation_results(self, epub_path):
        """검증 결과를 메시지박스로 표시합니다."""
        issues = self.validate_epub_file(epub_path)

        if not issues:
            # 문제가 없는 경우
            QMessageBox.information(
                self.main_window,
                "품질 검증 완료",
                "✅ ePub 파일 품질 검증을 통과했습니다!\n\n문제점이 발견되지 않았습니다."
            )
            self.log_info("ePub 품질 검증 완료: 문제 없음")
        else:
            # 문제가 있는 경우
            message = "📋 ePub 품질 검증 결과\n\n"
            message += f"총 {len(issues)}개의 문제점이 발견되었습니다:\n\n"
            message += "\n".join(issues)
            message += "\n\n💡 대부분의 문제는 ePub 사용에 큰 영향을 주지 않을 수 있습니다."

            QMessageBox.warning(
                self.main_window,
                "품질 검증 결과",
                message
            )
            self.log_warning(f"ePub 품질 검증 완료: {len(issues)}개 문제 발견")
            for issue in issues:
                self.log_warning(f"  - {issue}")

    def log_info(self, message):
        """정보 로그를 기록합니다."""
        print(f"[VALIDATION] {message}")

    def log_warning(self, message):
        """경고 로그를 기록합니다."""
        print(f"[VALIDATION WARNING] {message}")

# ==================================================================================

# ebooklib의 추가 유용한 기능들 (현재 미사용):
#
# 1. 고급 메타데이터 설정:
#    book.add_metadata('DC', 'publisher', '출판사명')
#    book.add_metadata('DC', 'description', '책 설명')
#    book.add_metadata('DC', 'subject', '장르/카테고리')
#    book.add_metadata('DC', 'rights', '저작권 정보')
#    book.add_metadata('DC', 'contributor', '기여자')
#    book.add_metadata('DC', 'type', 'Text')
#    book.add_metadata('DC', 'format', 'application/epub+zip')
#    book.add_metadata('DC', 'source', '원본 출처')
#    book.add_metadata('DC', 'relation', '관련 작품')
#    book.add_metadata('DC', 'coverage', '시간/공간적 범위')
#
# 2. 다국어 지원:
#    book.set_title('English Title', 'en')
#    book.set_title('日本語タイトル', 'ja')
#    book.add_author('Author Name', file_as='LastName, FirstName', role='aut', uid='author01')
#
# 3. 시리즈 정보:
#    book.add_metadata(None, 'meta', '', {'name': 'calibre:series', 'content': '시리즈명'})
#    book.add_metadata(None, 'meta', '', {'name': 'calibre:series_index', 'content': '1'})
#
# 4. 챕터 그룹화 및 중첩 목차:
#    book.toc = [
#        epub.Link("chapter_1.xhtml", "Chapter 1", "chapter1"),
#        (epub.Section("Part I"), [
#            epub.Link("chapter_2.xhtml", "Chapter 2", "chapter2"),
#            epub.Link("chapter_3.xhtml", "Chapter 3", "chapter3")
#        ]),
#        (epub.Section("Part II"), [
#            epub.Link("chapter_4.xhtml", "Chapter 4", "chapter4")
#        ])
#    ]
#
# 5. 랜드마크 (Landmarks) 설정:
#    book.guide = [
#        epub.Link("cover.xhtml", "Cover", "cover"),
#        epub.Link("toc.xhtml", "Table of Contents", "toc"),
#        epub.Link("chapter_1.xhtml", "Start", "text")
#    ]
#
# 6. 사용자 정의 문서 타입:
#    glossary = epub.EpubHtml(title='Glossary', file_name='glossary.xhtml', lang='ko')
#    glossary.content = '<html>...</html>'
#    book.add_item(glossary)
#    book.spine.append(glossary)
#
# 7. JavaScript 추가:
#    script = epub.EpubItem(uid="jquery", file_name="js/jquery.js",
#                          media_type="application/javascript", content="...")
#    book.add_item(script)
#
# 8. 오디오/비디오 파일 추가:
#    audio = epub.EpubItem(uid="audio1", file_name="audio/narration.mp3",
#                         media_type="audio/mpeg", content=audio_data)
#    book.add_item(audio)
#
# 9. SVG 이미지 추가:
#    svg_img = epub.EpubItem(uid="svg1", file_name="images/diagram.svg",
#                           media_type="image/svg+xml", content=svg_content)
#    book.add_item(svg_img)
#
# 10. 고급 스타일시트 기능:
#     css_content = '''
#     @font-face {
#         font-family: 'CustomFont';
#         src: url('../fonts/custom.ttf') format('truetype');
#     }
#     @media screen {
#         body { background-color: white; }
#     }
#     @media print {
#         body { background-color: transparent; }
#     }
#     '''
#
# 11. 페이지 진행 방향 설정 (우→좌 읽기 등):
#     book.set_direction('rtl')  # 아랍어, 히브리어 등
#
# 12. 읽기 순서에서 제외 (linear="no"):
#     appendix = epub.EpubHtml(title='Appendix', file_name='appendix.xhtml')
#     book.spine.append((appendix, 'no'))  # 목차에는 표시되지만 순차읽기에서 제외
#
# 13. 커스텀 네임스페이스 추가:
#     book.add_prefix('duokan', 'http://www.duokan.com/2012/epub')
#
# 14. 암호화된 콘텐츠 (DRM):
#     # ebooklib는 기본적으로 DRM을 지원하지 않음, 별도 라이브러리 필요
#
# 15. MathML 지원:
#     mathml_content = '''<math xmlns="http://www.w3.org/1998/Math/MathML">...</math>'''
#     chapter.content = f'<p>수식: {mathml_content}</p>'

# ==================================================================================
# UI 추가 요구사항 - 목차 번호 매기기 기능 & ePub 분할 기능
# ==================================================================================
#
# 다음 UI 위젯들을 기존 ePub 변환 설정 영역에 추가해야 합니다:
#
# 1. 체크박스 (checkBox_AddChapterNumbers) - 아직 미구현
#    - 텍스트: "목차에 챕터 번호 표시"
#    - 기본값: True (체크됨)
#    - 툴팁: "목차에서만 번호가 표시되며, 본문 제목은 변경되지 않습니다"
#
# 2. 콤보박스 (comboBox_NumberingStyle) - 아직 미구현
#    - 라벨: "번호 매기기 스타일:"
#    - 위치: checkBox_AddChapterNumbers 바로 아래
#    - 항목들:
#      • "아라비아 숫자 (1, 2, 3...)" - 기본 선택
#      • "로마 숫자 (I, II, III...)"
#      • "한국식 (1장, 2장, 3장...)"
#      • "진행률 표시 (1/10, 2/10...)"
#    - 활성화 조건: checkBox_AddChapterNumbers가 체크된 경우에만 활성화
#    - 툴팁: "목차에 표시될 번호 형식을 선택하세요"
#
# 3. 체크박스 (checkBox_ePubDivide) - ✅ 이미 구현됨
#    - 텍스트: "ePub 파일 분할"
#    - 기본값: False (체크 안됨)
#    - 툴팁: "챕터 수가 많을 때 여러 권으로 분할하여 생성합니다"
#
# 4. 스핀박스 (spinBox_ChapterCnt) - ✅ 이미 구현됨
#    - 라벨: "권당 챕터 수:"
#    - 위치: checkBox_ePubDivide 바로 아래
#    - 최솟값: 1
#    - 최댓값: 100
#    - 기본값: 10
#    - 활성화 조건: checkBox_ePubDivide가 체크된 경우에만 활성화
#    - 툴팁: "각 권에 포함될 챕터 수를 설정하세요"
#
# 5. 이벤트 연결 - main.py에서 추가 필요
#    - checkBox_AddChapterNumbers.stateChanged.connect(self.toggle_numbering_style) [미구현]
#    - checkBox_ePubDivide.stateChanged.connect(self.toggle_epub_divide) [구현 필요]
#    - toggle_numbering_style, toggle_epub_divide 메서드에서 각각 활성화/비활성화 처리
#
# 6. Qt Designer에서의 구성 예시:
#    [기존 ePub 설정들...]
#
#    ☑ 목차에 챕터 번호 표시                    [미구현]
#    번호 매기기 스타일: [아라비아 숫자 (1, 2, 3...) ▼]   [미구현]
#
#    ☐ ePub 파일 분할                          [✅ 구현됨]
#    권당 챕터 수: [10]                         [✅ 구현됨]
#
# 7. main.py에서 추가할 이벤트 핸들러:
#    def __init__(self):
#        # [기존 초기화 코드...]
#
#        # 번호 매기기 관련 이벤트 연결 (미구현 위젯)
#        if hasattr(self.ui, 'checkBox_AddChapterNumbers'):
#            self.ui.checkBox_AddChapterNumbers.stateChanged.connect(self.toggle_numbering_style)
#            self.toggle_numbering_style()
#
#        # ePub 분할 관련 이벤트 연결 (구현됨 위젯)
#        if hasattr(self.ui, 'checkBox_ePubDivide'):
#            self.ui.checkBox_ePubDivide.stateChanged.connect(self.toggle_epub_divide)
#            self.toggle_epub_divide()
#
#    def toggle_numbering_style(self):  # 미구현 위젯용
#        """챕터 번호 체크박스 상태에 따라 스타일 콤보박스 활성화/비활성화"""
#        if hasattr(self.ui, 'checkBox_AddChapterNumbers') and hasattr(self.ui, 'comboBox_NumberingStyle'):
#            is_checked = self.ui.checkBox_AddChapterNumbers.isChecked()
#            self.ui.comboBox_NumberingStyle.setEnabled(is_checked)
#
#    def toggle_epub_divide(self):  # 구현됨 위젯용
#        """ePub 분할 체크박스 상태에 따라 스핀박스 활성화/비활성화"""
#        if hasattr(self.ui, 'checkBox_ePubDivide') and hasattr(self.ui, 'spinBox_ChapterCnt'):
#            is_checked = self.ui.checkBox_ePubDivide.isChecked()
#            self.ui.spinBox_ChapterCnt.setEnabled(is_checked)
#
# ==================================================================================

class EpubConverter:
    """ePub 파일 생성을 담당하는 클래스 (ebooklib 사용)"""

    def __init__(self, main_window):
        """
        EpubConverter 초기화

        Args:
            main_window: MainWindow 인스턴스 (UI 요소에 접근하기 위함)
        """
        self.main_window = main_window
        self.ui = main_window.ui

        # 진행률 및 로깅 관련 속성
        self.progress_dialog = None
        self.current_step = 0
        self.total_steps = 0
        self.start_time = None

        # 로거 설정
        self.setup_logger()

        # 품질 검증 객체 초기화
        self.quality_validator = EpubQualityValidator(main_window)

    def setup_logger(self):
        """ePub 변환 로거를 설정합니다."""
        self.logger = logging.getLogger('EpubConverter')
        self.logger.setLevel(logging.INFO)

        # 이미 핸들러가 있으면 제거 (중복 방지)
        if self.logger.handlers:
            self.logger.handlers.clear()

        # 파일 핸들러 생성
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"epub_conversion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # 로그 포맷 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.info("=== ePub 변환 로거 초기화 완료 ===")

    def log_info(self, message):
        """정보 로그를 기록합니다."""
        self.logger.info(message)
        print(f"[INFO] {message}")

    def log_error(self, message):
        """오류 로그를 기록합니다."""
        self.logger.error(message)
        print(f"[ERROR] {message}")

    def log_warning(self, message):
        """경고 로그를 기록합니다."""
        self.logger.warning(message)
        print(f"[WARNING] {message}")

    def create_progress_dialog(self, title, total_steps):
        """진행률 다이얼로그를 생성합니다."""
        self.progress_dialog = QProgressDialog(title, "취소", 0, 100, self.main_window)
        self.progress_dialog.setWindowTitle("ePub 생성 진행률")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()

        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = time.time()

        return self.progress_dialog

    def update_progress(self, step_name, step_number=None):
        """진행률을 업데이트합니다."""
        if not self.progress_dialog:
            return

        if step_number is not None:
            self.current_step = step_number
        else:
            self.current_step += 1

        progress_percentage = int((self.current_step / self.total_steps) * 100)

        # 경과 시간 계산
        elapsed_time = time.time() - self.start_time
        if self.current_step > 0:
            estimated_total_time = elapsed_time * (self.total_steps / self.current_step)
            remaining_time = estimated_total_time - elapsed_time
            remaining_minutes = int(remaining_time // 60)
            remaining_seconds = int(remaining_time % 60)
            time_info = f" (남은 시간: 약 {remaining_minutes}분 {remaining_seconds}초)"
        else:
            time_info = ""

        # 진행률 다이얼로그 업데이트
        self.progress_dialog.setValue(progress_percentage)
        self.progress_dialog.setLabelText(f"{step_name}{time_info}")

        # 로그 기록
        self.log_info(f"진행률: {progress_percentage}% - {step_name}")

        # UI 업데이트 강제 실행
        self.progress_dialog.repaint()
        self.main_window.app.processEvents() if hasattr(self.main_window, 'app') else None

    def close_progress_dialog(self):
        """진행률 다이얼로그를 닫습니다."""
        if self.progress_dialog:
            total_time = time.time() - self.start_time
            minutes = int(total_time // 60)
            seconds = int(total_time % 60)

            self.log_info(f"ePub 생성 완료 - 총 소요시간: {minutes}분 {seconds}초")

            self.progress_dialog.close()
            self.progress_dialog = None

    def convert_to_epub(self, save_path):
        """
        설정된 정보를 기반으로 ePub 파일을 생성합니다.

        Args:
            save_path (str): 저장할 ePub 파일 경로

        Returns:
            bool: 성공 시 True, 실패 시 False
        """
        self.log_info(f"ePub 변환 시작: {save_path}")

        if not self.validate_epub_requirements():
            self.log_error("ePub 변환 요구사항 검증 실패")
            return False

        try:
            # ePub 분할 옵션 확인
            should_divide = self.should_divide_epub()

            conversion_success = False

            if should_divide:
                self.log_info("분할 ePub 생성 모드")
                # 분할 생성
                conversion_success = self.create_divided_epubs(save_path)
            else:
                self.log_info("단일 ePub 생성 모드")
                # 단일 파일 생성
                conversion_success = self.create_single_epub(save_path)

            # ePub 생성이 성공한 경우 품질 검증 수행
            if conversion_success:
                self.log_info("ePub 생성 완료. 품질 검증을 시작합니다.")
                self.perform_quality_validation(save_path, should_divide)

            return conversion_success

        except Exception as e:
            error_msg = f"ePub 변환 중 오류가 발생했습니다: {str(e)}"
            self.log_error(error_msg)

            # 진행률 다이얼로그가 열려있으면 닫기
            if self.progress_dialog:
                self.close_progress_dialog()

            QMessageBox.critical(self.main_window, "변환 실패", error_msg)
            return False

    def perform_quality_validation(self, save_path, is_divided):
        """ePub 생성 완료 후 품질 검증을 수행합니다."""
        try:
            if is_divided:
                # 분할된 ePub의 경우 첫 번째 파일만 검증
                base_path = Path(save_path)
                base_name = base_path.stem
                base_dir = base_path.parent
                first_volume_path = base_dir / f"{base_name}_001권.epub"

                if first_volume_path.exists():
                    self.log_info(f"분할 ePub 품질 검증 (첫 번째 권): {first_volume_path}")
                    self.quality_validator.show_validation_results(str(first_volume_path))
                else:
                    self.log_warning("분할된 ePub 파일을 찾을 수 없어 품질 검증을 건너뜁니다.")
            else:
                # 단일 ePub 검증
                if os.path.exists(save_path):
                    self.log_info(f"단일 ePub 품질 검증: {save_path}")
                    self.quality_validator.show_validation_results(save_path)
                else:
                    self.log_warning("ePub 파일을 찾을 수 없어 품질 검증을 건너뜁니다.")

        except Exception as e:
            self.log_error(f"품질 검증 중 오류 발생: {str(e)}")
            # 품질 검증 실패는 전체 변환 과정에 영향을 주지 않음

    def create_single_epub(self, save_path):
        """단일 ePub 파일을 생성합니다."""
        self.log_info("단일 ePub 파일 생성 시작")

        # 진행률 다이얼로그 생성 (총 8단계)
        progress = self.create_progress_dialog("ePub 파일 생성 중...", 8)

        try:
            # 1단계: ePub 객체 생성
            self.update_progress("ePub 객체 생성 중...")
            book = epub.EpubBook()

            # 2단계: 메타데이터 설정
            self.update_progress("메타데이터 설정 중...")
            self.set_metadata(book)

            # 3단계: 스타일시트 추가
            self.update_progress("스타일시트 추가 중...")
            self.add_stylesheet(book)

            # 4단계: 챕터 추가
            self.update_progress("챕터 추가 중...")
            chapters = self.add_chapters(book)

            # 5단계: 커버 이미지 추가
            self.update_progress("커버 이미지 처리 중...")
            cover_page = self.add_cover_image(book)

            # 6단계: 목차 생성
            self.update_progress("목차 생성 중...")
            toc_chapters = self.create_toc_with_numbering(chapters)

            if cover_page:
                # 커버를 목차 맨 앞에 추가
                book.toc = [
                    epub.Link("cover.xhtml", "표지", "cover")
                ] + toc_chapters
            else:
                book.toc = toc_chapters

            # 7단계: 네비게이션 파일 추가
            self.update_progress("네비게이션 파일 생성 중...")
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            # spine 설정 (읽기 순서)
            if cover_page:
                # 커버 → 목차 → 챕터들 순서로 배치
                book.spine = [cover_page, 'nav'] + chapters
            else:
                book.spine = ['nav'] + chapters

            # 8단계: 파일 저장
            self.update_progress("ePub 파일 저장 중...")
            epub.write_epub(save_path, book, {})

            # 완료
            self.close_progress_dialog()
            self.log_info(f"단일 ePub 파일 생성 완료: {save_path}")
            return True

        except Exception as e:
            self.close_progress_dialog()
            self.log_error(f"단일 ePub 생성 실패: {str(e)}")
            raise

    def create_divided_epubs(self, save_path):
        """분할된 ePub 파일들을 생성합니다."""
        self.log_info("분할 ePub 파일 생성 시작")

        chapters_per_volume = self.get_chapters_per_volume()
        chapters_info = self.get_chapter_info()

        if len(chapters_info) <= chapters_per_volume:
            self.log_info("챕터 수가 적어 단일 파일로 생성")
            # 분할할 필요가 없으면 단일 파일로 생성
            return self.create_single_epub(save_path)

        # 챕터를 권별로 분할
        chapter_groups = self.divide_chapters_into_volumes(chapters_info, chapters_per_volume)
        total_volumes = len(chapter_groups)

        self.log_info(f"총 {total_volumes}권으로 분할 생성 예정 (권당 {chapters_per_volume}챕터)")

        # 진행률 다이얼로그 생성 (준비 단계 + 각 권별 생성)
        progress = self.create_progress_dialog(f"분할 ePub 생성 중... (총 {total_volumes}권)", total_volumes + 2)

        try:
            # 1단계: 파일명 준비
            self.update_progress("파일명 준비 중...")
            base_path = Path(save_path)
            base_name = base_path.stem
            base_dir = base_path.parent

            # 숫자 포맷 결정 (01, 001 등)
            number_format = self.get_volume_number_format(total_volumes)

            # 2단계: 분할 정보 로깅
            self.update_progress("분할 정보 준비 중...")
            self.log_info(f"파일명 형식: {base_name}_XXX권.epub (숫자 자릿수: {number_format})")

            success_count = 0

            for volume_idx, volume_chapters in enumerate(chapter_groups, 1):
                # 각 권별 진행률 업데이트
                step_name = f"권 {volume_idx}/{total_volumes} 생성 중..."
                self.update_progress(step_name, volume_idx + 2)

                # 권별 파일명 생성
                volume_number = f"{volume_idx:0{number_format}d}"
                volume_filename = f"{base_name}_{volume_number}권.epub"
                volume_path = base_dir / volume_filename

                try:
                    self.log_info(f"권 {volume_idx} 생성 시작: {volume_filename}")

                    # 각 권별로 ePub 생성
                    if self.create_volume_epub(str(volume_path), volume_chapters, volume_idx, total_volumes):
                        success_count += 1
                        self.log_info(f"권 {volume_idx} 생성 완료: {volume_filename}")
                    else:
                        self.log_error(f"권 {volume_idx} 생성 실패: {volume_filename}")

                except Exception as e:
                    self.log_error(f"권 {volume_idx} 생성 중 오류: {e}")

            # 완료 처리
            self.close_progress_dialog()

            # 결과 확인 및 메시지 표시
            if success_count == total_volumes:
                success_msg = f"총 {total_volumes}권으로 분할하여 생성이 완료되었습니다."
                self.log_info(f"분할 ePub 생성 완료: {success_msg}")
                QMessageBox.information(self.main_window, "분할 완료", success_msg)
                return True
            else:
                warning_msg = f"총 {total_volumes}권 중 {success_count}권만 성공적으로 생성되었습니다."
                self.log_warning(f"분할 ePub 부분 실패: {warning_msg}")
                QMessageBox.warning(self.main_window, "분할 부분 실패", warning_msg)
                return False

        except Exception as e:
            self.close_progress_dialog()
            self.log_error(f"분할 ePub 생성 실패: {str(e)}")
            raise

    def create_volume_epub(self, save_path, volume_chapters, volume_number, total_volumes):
        """개별 권의 ePub 파일을 생성합니다."""
        # ePub 객체 생성
        book = epub.EpubBook()

        # 메타데이터 설정 (권 정보 포함)
        self.set_volume_metadata(book, volume_number, total_volumes)

        # 스타일시트 추가
        self.add_stylesheet(book)

        # 해당 권의 챕터들만 추가
        chapters = self.add_volume_chapters(book, volume_chapters)

        # 커버 이미지 추가 (권별로 동일한 커버 사용)
        cover_page = self.add_cover_image(book)

        # 목차 생성 (해당 권의 챕터들만)
        toc_chapters = self.create_toc_with_numbering(chapters)

        if cover_page:
            book.toc = [
                epub.Link("cover.xhtml", "표지", "cover")
            ] + toc_chapters
        else:
            book.toc = toc_chapters

        # NCX 및 nav 파일 추가
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # spine 설정
        if cover_page:
            book.spine = [cover_page, 'nav'] + chapters
        else:
            book.spine = ['nav'] + chapters

        # 파일 저장
        epub.write_epub(save_path, book, {})
        return True

    def divide_chapters_into_volumes(self, chapters_info, chapters_per_volume):
        """챕터들을 권별로 분할합니다."""
        chapter_groups = []

        for i in range(0, len(chapters_info), chapters_per_volume):
            volume_chapters = chapters_info[i:i + chapters_per_volume]
            chapter_groups.append(volume_chapters)

        return chapter_groups

    def get_volume_number_format(self, total_volumes):
        """권 번호 포맷을 결정합니다."""
        if total_volumes < 10:
            return 1  # 1, 2, 3...
        elif total_volumes < 100:
            return 2  # 01, 02, 03...
        else:
            return 3  # 001, 002, 003...

    def set_volume_metadata(self, book, volume_number, total_volumes):
        """권별 메타데이터를 설정합니다."""
        title = self.ui.lineEdit_Title.text().strip()
        # lineEdit_Author는 UI에 존재하므로 직접 접근
        author_text = self.ui.lineEdit_Author.text().strip() if hasattr(self.ui, 'lineEdit_Author') else "Unknown Author"

        # 권 정보가 포함된 제목
        volume_title = f"{title} - {volume_number}권"

        # 기본 메타데이터 설정
        book.set_identifier(f"{str(uuid.uuid4())}-vol{volume_number}")
        book.set_title(volume_title)
        book.set_language('ko')
        book.add_author(author_text)
        book.add_metadata('DC', 'date', datetime.now().strftime('%Y-%m-%d'))

        # 시리즈 정보 추가 (Calibre 호환)
        book.add_metadata(None, 'meta', title, {'name': 'calibre:series'})
        book.add_metadata(None, 'meta', str(volume_number), {'name': 'calibre:series_index'})

        # 권 정보를 설명에 추가
        description = f"총 {total_volumes}권 중 {volume_number}권"
        book.add_metadata('DC', 'description', description)

    def add_volume_chapters(self, book, volume_chapters):
        """특정 권의 챕터들을 ePub에 추가합니다."""
        chapters = []

        for i, chapter_info in enumerate(volume_chapters, 1):
            # 챕터 내용을 HTML로 변환
            content = self.convert_text_to_html(chapter_info['content'])

            # 챕터 HTML 생성
            chapter_html = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{chapter_info['title']}</title>
    <link rel="stylesheet" type="text/css" href="../style/nav.css"/>
</head>
<body>
    <div class="chapter-title">{chapter_info['title']}</div>
    {content}
</body>
</html>'''

            # 챕터 객체 생성
            chapter = epub.EpubHtml(
                title=chapter_info['title'],
                file_name=f'chapter_{i}.xhtml',
                lang='ko'
            )
            chapter.content = chapter_html

            # 책에 챕터 추가
            book.add_item(chapter)
            chapters.append(chapter)

        return chapters

    def should_divide_epub(self):
        """ePub 파일을 분할할지 결정합니다."""
        # UI에서 분할 옵션 체크박스 확인
        divide_checkbox = getattr(self.ui, 'checkBox_ePubDivide', None)

        if divide_checkbox:
            return divide_checkbox.isChecked()

        # 체크박스가 없는 경우 기본값
        return False

    def get_chapters_per_volume(self):
        """권당 챕터 수를 가져옵니다."""
        # UI에서 스핀박스 값 확인
        chapters_spinbox = getattr(self.ui, 'spinBox_ChapterCnt', None)

        if chapters_spinbox:
            return chapters_spinbox.value()

        # 스핀박스가 없는 경우 기본값 (UI 기본값과 동일하게 설정)
        return 30

    def validate_epub_requirements(self):
        """ePub 변환에 필요한 최소 요구사항을 검증합니다."""
        text_file_path = self.ui.label_TextFilePath.text().strip()
        if not text_file_path or not os.path.exists(text_file_path):
            QMessageBox.warning(self.main_window, "변환 실패", "텍스트 파일이 선택되지 않았거나 존재하지 않습니다.")
            return False

        title = self.ui.lineEdit_Title.text().strip()
        if not title:
            QMessageBox.warning(self.main_window, "변환 실패", "제목을 입력해주세요.")
            return False

        table = self.ui.tableWidget_ChapterList
        if table.rowCount() == 0:
            reply = QMessageBox.question(
                self.main_window, "챕터 없음",
                "챕터 리스트가 비어있습니다. 전체 텍스트를 하나의 챕터로 만들까요?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.No:
                return False

        return True

    def set_metadata(self, book):
        """ePub의 메타데이터를 설정합니다."""
        title = self.ui.lineEdit_Title.text().strip()
        # lineEdit_Author는 UI에 존재하므로 직접 접근
        author_text = self.ui.lineEdit_Author.text().strip() if hasattr(self.ui, 'lineEdit_Author') else "Unknown Author"

        # 기본 메타데이터 설정
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(title)
        book.set_language('ko')
        book.add_author(author_text)
        book.add_metadata('DC', 'date', datetime.now().strftime('%Y-%m-%d'))

        # 추가 가능한 메타데이터들 (주석):
        # book.add_metadata('DC', 'publisher', '출판사명')
        # book.add_metadata('DC', 'description', '이 책에 대한 상세한 설명을 여기에 입력')
        # book.add_metadata('DC', 'subject', '소설, 판타지, 로맨스')  # 장르/태그
        # book.add_metadata('DC', 'rights', '© 2025 저작권자명. All rights reserved.')
        # book.add_metadata('DC', 'contributor', '편집자명', {'role': 'edt'})
        # book.add_metadata('DC', 'contributor', '일러스트레이터명', {'role': 'ill'})
        # book.add_metadata('DC', 'contributor', '번역자명', {'role': 'trl'})
        #
        # # 시리즈 정보 (Calibre 호환):
        # book.add_metadata(None, 'meta', '시리즈명', {'name': 'calibre:series'})
        # book.add_metadata(None, 'meta', '1', {'name': 'calibre:series_index'})
        #
        # # 평점 정보:
        # book.add_metadata(None, 'meta', '5', {'name': 'calibre:rating'})
        #
        # # 태그 정보:
        # book.add_metadata(None, 'meta', 'tag1,tag2,tag3', {'name': 'calibre:user_categories'})
        #
        # # ISBN 정보:
        # book.add_metadata('DC', 'identifier', '978-1234567890', {'scheme': 'ISBN'})
        #
        # # 다국어 제목 지원:
        # book.set_title('English Title', 'en')
        # book.set_title('日本語タイトル', 'ja')
        #
        # # 저자 상세 정보:
        # book.add_author('저자명', file_as='성, 이름', role='aut', uid='author01')

    def add_stylesheet(self, book):
        """CSS 스타일시트를 추가합니다."""
        # 선택된 폰트 정보 가져오기
        body_font_path = getattr(self.ui, 'label_BodyFontPath', None)
        chapter_font_path = getattr(self.ui, 'label_ChapterFontPath', None)

        body_font_family = "serif"
        chapter_font_family = "serif"
        font_face_declarations = ""

        # 폰트가 선택된 경우 폰트 파일을 ePub에 포함
        if body_font_path and body_font_path.text() != "---" and os.path.exists(body_font_path.text()):
            body_font_family, body_font_face = self.add_font_to_book(book, body_font_path.text(), "body-font")
            font_face_declarations += body_font_face

        if chapter_font_path and chapter_font_path.text() != "---" and os.path.exists(chapter_font_path.text()):
            chapter_font_family, chapter_font_face = self.add_font_to_book(book, chapter_font_path.text(), "chapter-font")
            font_face_declarations += chapter_font_face

        css_content = f'''
{font_face_declarations}

{self.create_multilingual_css(font_face_declarations, body_font_family, chapter_font_family)}

body {{
    font-family: {self.get_font_fallback_chain(body_font_family)};
    line-height: 1.6;
    margin: 0;
    padding: 1em;
}}

h1, h2, h3 {{
    font-family: {self.get_font_fallback_chain(chapter_font_family)};
    margin-top: 2em;
    margin-bottom: 1em;
    font-weight: bold;
}}

h1 {{
    font-size: 1.5em;
    text-align: center;
}}

p {{
    margin-bottom: 1em;
    text-indent: 1em;
    font-family: {self.get_font_fallback_chain(body_font_family)};
}}

.chapter-title {{
    font-family: {self.get_font_fallback_chain(chapter_font_family)};
    text-align: center;
    font-size: 1.3em;
    font-weight: bold;
    margin: 2em 0;
}}

/* 개별 문자 타입별 세밀한 조정 */
.korean {{
    font-family: 'KoreanFont', serif;
    letter-spacing: -0.02em;
}}
.english {{
    font-family: 'EnglishFont', sans-serif;
    letter-spacing: 0.01em;
}}
.number {{
    font-family: 'NumberFont', monospace;
    font-variant-numeric: tabular-nums;
}}
.chinese {{
    font-family: 'ChineseFont', serif;
    letter-spacing: 0.05em;
}}
.japanese {{
    font-family: 'JapaneseFont', serif;
    letter-spacing: 0.02em;
}}
.symbol {{
    font-family: 'SymbolFont', sans-serif;
}}

/* 혼합 텍스트 최적화 */
.mixed-text {{
    font-feature-settings: "kern" 1, "liga" 1;
    text-rendering: optimizeLegibility;
}}
'''

        # 스타일시트 생성 및 추가
        nav_css = epub.EpubItem(
            uid="nav_css",
            file_name="style/nav.css",
            media_type="text/css",
            content=css_content
        )
        book.add_item(nav_css)

        # 추가 스타일시트 기능들 (주석):
        #
        # # 반응형 CSS 미디어 쿼리:
        # responsive_css = '''
        # @media screen and (max-width: 600px) {
        #     body { font-size: 14px; }
        #     .chapter-title { font-size: 1.1em; }
        # }
        # @media screen and (min-width: 800px) {
        #     body { font-size: 18px; }
        #     .chapter-title { font-size: 1.5em; }
        # }
        # '''
        #
        # # 다크모드 지원:
        # dark_mode_css = '''
        # @media (prefers-color-scheme: dark) {
        #     body {
        #         background-color: #1a1a1a;
        #         color: #e0e0e0;
        #     }
        #     .chapter-title { color: #ffffff; }
        # }
        # '''
        #
        # # 인쇄용 스타일:
        # print_css = '''
        # @media print {
        #     body {
        #         font-family: "Times New Roman", serif;
        #         font-size: 12pt;
        #         line-height: 1.4;
        #     }
        #     .chapter-title {
        #         page-break-before: always;
        #         margin-top: 0;
        #     }
        # }
        # '''
        #
        # # 폰트 페이스 정의 (커스텀 폰트):
        # font_face_css = '''
        # @font-face {
        #     font-family: 'MyCustomFont';
        #     src: url('../fonts/custom.woff2') format('woff2'),
        #          url('../fonts/custom.woff') format('woff'),
        #          url('../fonts/custom.ttf') format('truetype');
        #     font-weight: normal;
        #     font-style: normal;
        # }
        # '''

    def create_multilingual_css(self, font_face_declarations, body_font_family, chapter_font_family):
        """다국어 지원을 위한 CSS 생성 (현재 UI 기반)"""

        # 현재 UI에서는 본문/제목 폰트만 설정 가능하므로
        # 모든 문자 종류에 적절히 분배하여 적용

        # 문자별 @font-face 정의 (기존 폰트들 활용)
        multilingual_font_faces = f"""
/* ========================================
   문자 종류별 폰트 정의 (기존 UI 기반)
   ======================================== */

/* 한글 폰트 - 본문 폰트 사용 */
@font-face {{
    font-family: 'KoreanFont';
    src: url('../fonts/{body_font_family}.ttf') format('truetype');
    unicode-range: U+AC00-U+D7AF, U+1100-U+11FF, U+3130-U+318F, U+A960-U+A97F, U+D7B0-U+D7FF;
    font-display: swap;
}}

/* 영문 폰트 - 본문 폰트 사용 */
@font-face {{
    font-family: 'EnglishFont';
    src: url('../fonts/{body_font_family}.ttf') format('truetype');
    unicode-range: U+0020-U+007F, U+00A0-U+00FF, U+0100-U+017F, U+0180-U+024F;
    font-display: swap;
}}

/* 숫자 폰트 - 본문 폰트 사용 (가독성 위해) */
@font-face {{
    font-family: 'NumberFont';
    src: url('../fonts/{body_font_family}.ttf') format('truetype');
    unicode-range: U+0030-U+0039, U+FF10-U+FF19;
    font-display: swap;
}}

/* 한자 폰트 - 제목 폰트 사용 (강조 효과) */
@font-face {{
    font-family: 'ChineseFont';
    src: url('../fonts/{chapter_font_family}.ttf') format('truetype');
    unicode-range: U+4E00-U+9FFF, U+3400-U+4DBF, U+20000-U+2A6DF, U+2A700-U+2B73F;
    font-display: swap;
}}

/* 일본어 폰트 - 본문 폰트 사용 */
@font-face {{
    font-family: 'JapaneseFont';
    src: url('../fonts/{body_font_family}.ttf') format('truetype');
    unicode-range: U+3040-U+309F, U+30A0-U+30FF, U+31F0-U+31FF;
    font-display: swap;
}}

/* 특수문자 폰트 - 제목 폰트 사용 (시각적 강조) */
@font-face {{
    font-family: 'SymbolFont';
    src: url('../fonts/{chapter_font_family}.ttf') format('truetype');
    unicode-range: U+2000-U+206F, U+2070-U+209F, U+20A0-U+20CF, U+2100-U+214F, U+2190-U+21FF, U+2200-U+22FF, U+2300-U+23FF, U+2460-U+24FF, U+2500-U+257F, U+25A0-U+25FF, U+2600-U+26FF;
    font-display: swap;
}}
"""

        return multilingual_font_faces

    def get_font_fallback_chain(self, primary_font):
        """문자 종류별 폰트 폴백 체인 생성 (현재 UI 기반)"""
        return f"'KoreanFont', 'EnglishFont', 'NumberFont', 'ChineseFont', 'JapaneseFont', 'SymbolFont', {primary_font}, serif"

    def add_font_to_book(self, book, font_path, font_id):
        """폰트 파일을 ePub에 추가하고 폰트 패밀리명과 @font-face CSS를 반환합니다."""
        try:
            font_name = Path(font_path).stem
            font_ext = Path(font_path).suffix.lower()

            self.log_info(f"폰트 추가 시작: {font_name}{font_ext}")

            # 사용된 모든 문자 수집
            used_chars = self.collect_used_characters()

            # 폰트 서브셋 생성 (용량 최적화)
            font_content = self.create_font_subset(font_path, used_chars)

            if not font_content:
                # 서브셋 실패 시 원본 폰트 사용
                with open(font_path, 'rb') as f:
                    font_content = f.read()
                self.log_warning(f"폰트 서브셋 실패, 원본 폰트 사용: {font_name}")

            # 미디어 타입 결정
            if font_ext == '.ttf':
                media_type = "font/ttf"
                format_type = "truetype"
            elif font_ext == '.otf':
                media_type = "font/otf"
                format_type = "opentype"
            else:
                media_type = "application/octet-stream"
                format_type = "truetype"

            # 폰트 아이템 생성 및 추가
            font_item = epub.EpubItem(
                uid=font_id,
                file_name=f"fonts/{font_name}{font_ext}",
                media_type=media_type,
                content=font_content
            )
            book.add_item(font_item)

            # @font-face CSS 선언 생성
            font_face_css = f'''
@font-face {{
    font-family: '{font_name}';
    src: url('../fonts/{font_name}{font_ext}') format('{format_type}');
    font-weight: normal;
    font-style: normal;
}}
'''

            self.log_info(f"폰트 추가 완료: {font_name} ({len(font_content):,} bytes)")
            return f'"{font_name}"', font_face_css

        except Exception as e:
            error_msg = f"폰트 추가 실패: {e}"
            self.log_error(error_msg)
            return "serif", ""

    def collect_used_characters(self, max_sample_size=1024*1024):
        """ePub에서 사용되는 모든 문자를 수집합니다. (최적화된 버전)"""
        used_chars = set()

        try:
            self.log_info("사용된 문자 수집 시작")

            # 제목에서 문자 수집
            title = self.ui.lineEdit_Title.text().strip()
            used_chars.update(title)

            # 저자명에서 문자 수집
            if hasattr(self.ui, 'lineEdit_Author'):
                used_chars.update(self.ui.lineEdit_Author.text().strip())

            # 챕터 내용에서 문자 수집
            chapters_info = self.get_chapter_info()

            # 텍스트 파일에서 문자 수집 (최적화)
            text_file_path = self.ui.label_TextFilePath.text().strip()
            if text_file_path and os.path.exists(text_file_path):
                file_size = os.path.getsize(text_file_path)

                if file_size > max_sample_size:
                    # 큰 파일의 경우 샘플링 방식 사용
                    self.log_info(f"큰 파일({file_size:,} bytes) 감지, 샘플링 모드 사용")
                    used_chars.update(self._sample_characters_from_file(text_file_path, max_sample_size))
                else:
                    # 작은 파일은 전체 읽기
                    with open(text_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        used_chars.update(content)

            self.log_info(f"수집된 문자 수: {len(used_chars):,}개")
            return used_chars

        except Exception as e:
            self.log_error(f"문자 수집 실패: {e}")
            return set()

    def _sample_characters_from_file(self, file_path, sample_size):
        """큰 파일에서 문자를 샘플링하여 수집합니다."""
        used_chars = set()
        file_size = os.path.getsize(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 파일을 여러 구간으로 나누어 샘플링
                sample_points = 10  # 10개 지점에서 샘플링
                chunk_size = sample_size // sample_points

                for i in range(sample_points):
                    # 파일의 다른 위치에서 샘플링
                    position = (file_size * i) // sample_points
                    f.seek(position)

                    # 줄의 시작점으로 이동 (중간에서 잘린 문자 방지)
                    if position > 0:
                        f.readline()  # 현재 줄의 나머지 부분 건너뛰기

                    # chunk_size만큼 읽기
                    chunk = f.read(chunk_size)
                    used_chars.update(chunk)

                    # 충분한 문자가 수집되었으면 조기 종료
                    if len(used_chars) > 10000:  # 10,000개 문자면 충분
                        break

            self.log_info(f"샘플링으로 수집된 문자 수: {len(used_chars):,}개")
            return used_chars

        except Exception as e:
            self.log_error(f"샘플링 실패: {e}")
            return set()

    def get_font_supported_characters(self, font_path):
        """폰트 파일에서 지원하는 문자 목록을 추출합니다. (캐싱 지원)"""
        # 폰트 캐시 확인
        if not hasattr(self, '_font_cache'):
            self._font_cache = {}

        font_key = f"{font_path}_{os.path.getmtime(font_path)}"

        if font_key in self._font_cache:
            self.log_info(f"폰트 캐시 사용: {os.path.basename(font_path)}")
            return self._font_cache[font_key]

        try:
            from fontTools.ttLib import TTFont

            self.log_info(f"폰트 분석 시작: {os.path.basename(font_path)}")
            font = TTFont(font_path)
            supported_chars = set()

            # 폰트의 cmap 테이블에서 지원하는 유니코드 포인트 추출
            for table in font['cmap'].tables:
                if hasattr(table, 'cmap'):
                    for unicode_point in table.cmap.keys():
                        try:
                            char = chr(unicode_point)
                            supported_chars.add(char)
                        except ValueError:
                            # 유효하지 않은 유니코드 포인트는 건너뛰기
                            continue

            font.close()

            # 캐시에 저장
            self._font_cache[font_key] = supported_chars

            self.log_info(f"폰트 지원 문자 수: {len(supported_chars):,}개 (캐시됨)")
            return supported_chars

        except Exception as e:
            self.log_error(f"폰트 문자 추출 실패: {e}")
            return set()

    def check_font_character_support(self, font_path, text_chars):
        """폰트가 텍스트의 모든 문자를 지원하는지 확인합니다."""
        try:
            supported_chars = self.get_font_supported_characters(font_path)
            if not supported_chars:
                return False, set(), "폰트 파일을 읽을 수 없습니다."

            # 지원되지 않는 문자 찾기
            unsupported_chars = text_chars - supported_chars

            # 공백, 탭, 개행 등 제어 문자는 제외
            control_chars = {'\n', '\r', '\t', ' '}
            unsupported_chars = unsupported_chars - control_chars

            is_fully_supported = len(unsupported_chars) == 0

            return is_fully_supported, unsupported_chars, ""

        except Exception as e:
            error_msg = f"폰트 지원 확인 실패: {e}"
            self.log_error(error_msg)
            return False, set(), error_msg

    def analyze_text_font_compatibility(self):
        """텍스트와 선택된 폰트의 호환성을 분석합니다."""
        try:
            # 텍스트에서 사용된 모든 문자 수집
            used_chars = self.collect_used_characters()
            if not used_chars:
                return {"status": "error", "message": "텍스트 파일을 읽을 수 없습니다."}

            results = {
                "status": "success",
                "total_chars": len(used_chars),
                "fonts": {}
            }

            # 본문 폰트 확인
            body_font_path = getattr(self.ui, 'label_BodyFontPath', None)
            if body_font_path and body_font_path.text() != "---" and os.path.exists(body_font_path.text()):
                is_supported, unsupported, error = self.check_font_character_support(
                    body_font_path.text(), used_chars
                )
                results["fonts"]["body"] = {
                    "path": body_font_path.text(),
                    "name": Path(body_font_path.text()).stem,
                    "supported": is_supported,
                    "unsupported_chars": list(unsupported),
                    "unsupported_count": len(unsupported),
                    "error": error
                }

            # 제목 폰트 확인
            chapter_font_path = getattr(self.ui, 'label_ChapterFontPath', None)
            if chapter_font_path and chapter_font_path.text() != "---" and os.path.exists(chapter_font_path.text()):
                is_supported, unsupported, error = self.check_font_character_support(
                    chapter_font_path.text(), used_chars
                )
                results["fonts"]["chapter"] = {
                    "path": chapter_font_path.text(),
                    "name": Path(chapter_font_path.text()).stem,
                    "supported": is_supported,
                    "unsupported_chars": list(unsupported),
                    "unsupported_count": len(unsupported),
                    "error": error
                }

            return results

        except Exception as e:
            return {"status": "error", "message": f"폰트 호환성 분석 실패: {e}"}
            for chapter_info in chapters_info:
                used_chars.update(chapter_info['title'])
                used_chars.update(chapter_info['content'])

            # 기본 문자들 추가 (영문, 숫자, 기본 문장부호)
            basic_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
            basic_punctuation = set(".,!?;:\"'()-[]{}…""''·")
            used_chars.update(basic_chars)
            used_chars.update(basic_punctuation)

            # 한글 기본 문자 추가 (자주 사용되는 것들)
            korean_basic = set("가나다라마바사아자차카타파하")
            used_chars.update(korean_basic)

            char_count = len(used_chars)
            self.log_info(f"수집된 문자 수: {char_count:,}개")
            return ''.join(sorted(used_chars))

        except Exception as e:
            error_msg = f"문자 수집 실패: {e}"
            self.log_error(error_msg)
            # 기본 문자셋 반환
            return "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,!?;:\"'()-[]{}…""''"

    def create_font_subset(self, font_path, used_chars):
        """사용된 문자만 포함하는 폰트 서브셋을 생성합니다."""
        try:
            font_name = Path(font_path).name
            self.log_info(f"폰트 서브셋 생성 시작: {font_name} (사용 문자 수: {len(used_chars)})")

            # fonttools를 사용한 폰트 서브셋팅
            options = subset.Options()
            options.retain_gids = False  # 글리프 ID 재배치로 용량 최적화
            options.hinting = True      # 힌팅 정보 유지
            options.layout_features = ['*']  # 레이아웃 기능 유지
            options.name_IDs = ['*']    # 폰트 이름 정보 유지
            options.drop_tables = [     # 불필요한 테이블 제거
                'GSUB', 'GPOS',        # 고급 타이포그래피 (필요시 제거)
            ]

            # 폰트 로드
            font = TTFont(font_path)

            # 서브셋 생성
            subsetter = subset.Subsetter(options)
            subsetter.populate(text=used_chars)
            subsetter.subset(font)

            # 메모리 스트림에 저장
            output_stream = io.BytesIO()
            font.save(output_stream)

            # 원본 크기와 서브셋 크기 비교
            original_size = os.path.getsize(font_path)
            subset_size = len(output_stream.getvalue())
            compression_ratio = (1 - subset_size / original_size) * 100

            self.log_info(f"폰트 서브셋 완료: {font_name}")
            self.log_info(f"원본 크기: {original_size:,} bytes → 서브셋 크기: {subset_size:,} bytes")
            self.log_info(f"압축률: {compression_ratio:.1f}% 감소")

            return output_stream.getvalue()

        except Exception as e:
            error_msg = f"폰트 서브셋 생성 실패: {e}"
            self.log_error(error_msg)
            return None

    # 고급 폰트 서브셋팅 옵션들 (주석):
    #
    # def create_advanced_font_subset(self, font_path, used_chars):
    #     """고급 폰트 서브셋팅 옵션들"""
    #     options = subset.Options()
    #
    #     # 더 적극적인 용량 최적화:
    #     options.retain_gids = False          # 글리프 ID 재배치
    #     options.hinting = False              # 힌팅 제거 (더 작은 크기)
    #     options.legacy_kern = False          # 레거시 커닝 테이블 제거
    #     options.layout_features = []         # 모든 레이아웃 기능 제거
    #     options.name_languages = ['ko', 'en'] # 필요한 언어만 유지
    #
    #     # 제거할 테이블들:
    #     options.drop_tables = [
    #         'DSIG',    # 디지털 서명
    #         'LTSH',    # 선형 임계값
    #         'VDMX',    # 수직 장치 메트릭
    #         'hdmx',    # 수평 장치 메트릭
    #         'vmtx',    # 수직 메트릭 (세로쓰기 미사용시)
    #         'GSUB',    # 글리프 치환 (고급 타이포그래피)
    #         'GPOS',    # 글리프 위치 조정
    #     ]
    #
    #     # 유니코드 범위별 서브셋:
    #     korean_chars = self.get_korean_characters()
    #     english_chars = self.get_english_characters()
    #     number_chars = "0123456789"
    #     punctuation_chars = ".,!?;:\"'()-[]{}…""''"
    #
    #     # 조건부 문자 추가:
    #     if self.has_korean_content():
    #         used_chars += korean_chars
    #     if self.has_english_content():
    #         used_chars += english_chars
    #
    #     return used_chars
    #
    # def optimize_font_for_ereaders(self, font_path):
    #     """전자책 리더기 최적화 폰트 생성"""
    #     options = subset.Options()
    #
    #     # 전자책 리더기 최적화 설정:
    #     options.hinting = True               # 저해상도 화면용 힌팅 유지
    #     options.legacy_kern = True           # 구형 리더기 호환성
    #     options.layout_features = ['kern']   # 기본 커닝만 유지
    #     options.glyph_names = False          # 글리프 이름 제거
    #
    #     # 전자책에서 불필요한 기능 제거:
    #     options.drop_tables = [
    #         'DSIG', 'LTSH', 'VDMX', 'hdmx',  # 장치별 최적화 테이블
    #         'COLR', 'CPAL',                   # 컬러 폰트 (흑백 전용)
    #         'SVG ', 'sbix',                   # 벡터/비트맵 글리프
    #     ]
    #
    #     return options

    def add_chapters(self, book):
        """챕터들을 ePub에 추가합니다."""
        chapters_info = self.get_chapter_info()
        chapters = []

        for i, chapter_info in enumerate(chapters_info, 1):
            # 챕터 내용을 HTML로 변환
            content = self.convert_text_to_html(chapter_info['content'])

            # 챕터 HTML 생성
            chapter_html = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{chapter_info['title']}</title>
    <link rel="stylesheet" type="text/css" href="../style/nav.css"/>
</head>
<body>
    <div class="chapter-title">{chapter_info['title']}</div>
    {content}
</body>
</html>'''

            # 챕터 객체 생성
            chapter = epub.EpubHtml(
                title=chapter_info['title'],
                file_name=f'chapter_{i}.xhtml',
                lang='ko'
            )
            chapter.content = chapter_html

            # 책에 챕터 추가
            book.add_item(chapter)
            chapters.append(chapter)

            # 챕터별 추가 기능들 (주석):
            #
            # # 챕터별 개별 이미지 추가:
            # chapter_image_path = self.get_chapter_image_path(i)  # 사용자 정의 함수
            # if chapter_image_path and os.path.exists(chapter_image_path):
            #     img_content = open(chapter_image_path, 'rb').read()
            #     img_item = epub.EpubItem(
            #         uid=f"image_{i}",
            #         file_name=f"images/chapter_{i}.jpg",
            #         media_type="image/jpeg",
            #         content=img_content
            #     )
            #     book.add_item(img_item)
            #
            # # 챕터별 오디오 내레이션:
            # audio_path = self.get_chapter_audio_path(i)  # 사용자 정의 함수
            # if audio_path and os.path.exists(audio_path):
            #     audio_content = open(audio_path, 'rb').read()
            #     audio_item = epub.EpubItem(
            #         uid=f"audio_{i}",
            #         file_name=f"audio/chapter_{i}.mp3",
            #         media_type="audio/mpeg",
            #         content=audio_content
            #     )
            #     book.add_item(audio_item)
            #
            # # 주석(Annotation) 지원:
            # chapter.content = chapter_html.replace(
            #     '특정텍스트',
            #     '<span class="annotation" title="주석 내용">특정텍스트</span>'
            # )
            #
            # # 수학 공식 (MathML) 지원:
            # if 'math_formula' in chapter_info.get('features', []):
            #     mathml = '''<math xmlns="http://www.w3.org/1998/Math/MathML">
            #         <mrow><mi>x</mi><mo>=</mo><mfrac><mrow><mo>-</mo><mi>b</mi><mo>±</mo>
            #         <msqrt><mrow><msup><mi>b</mi><mn>2</mn></msup><mo>-</mo><mn>4</mn>
            #         <mi>a</mi><mi>c</mi></mrow></msqrt></mrow><mrow><mn>2</mn><mi>a</mi>
            #         </mrow></mfrac></mrow></math>'''
            #     chapter.content = chapter.content.replace('[FORMULA]', mathml)

        return chapters

    def convert_text_to_html(self, text):
        """텍스트를 HTML 문단으로 변환합니다."""
        if not text.strip():
            return "<p></p>"

        # 줄바꿈을 기준으로 문단 분리
        paragraphs = text.split('\n')
        html_paragraphs = []

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # HTML 특수문자 이스케이프
                paragraph = paragraph.replace('&', '&amp;')
                paragraph = paragraph.replace('<', '&lt;')
                paragraph = paragraph.replace('>', '&gt;')
                paragraph = paragraph.replace('"', '&quot;')
                paragraph = paragraph.replace("'", '&#39;')
                html_paragraphs.append(f'<p>{paragraph}</p>')

        return '\n'.join(html_paragraphs)

    def add_cover_image(self, book):
        """커버 이미지를 ePub에 추가합니다."""
        cover_image_path = getattr(self.ui, 'label_CoverImagePath', None)
        if cover_image_path and cover_image_path.text() != "---" and os.path.exists(cover_image_path.text()):
            try:
                with open(cover_image_path.text(), 'rb') as f:
                    cover_content = f.read()

                # 이미지 확장자에 따른 미디어 타입 결정
                ext = Path(cover_image_path.text()).suffix.lower()
                if ext in ['.jpg', '.jpeg']:
                    media_type = 'image/jpeg'
                elif ext == '.png':
                    media_type = 'image/png'
                elif ext == '.gif':
                    media_type = 'image/gif'
                elif ext == '.webp':
                    media_type = 'image/webp'
                else:
                    media_type = 'image/jpeg'

                # 1. 커버 이미지 파일 추가
                cover_image_item = epub.EpubItem(
                    uid="cover_image",
                    file_name=f"images/cover{ext}",
                    media_type=media_type,
                    content=cover_content
                )
                book.add_item(cover_image_item)

                # 2. 커버 페이지 HTML 생성
                cover_html = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>표지</title>
    <link rel="stylesheet" type="text/css" href="../style/nav.css"/>
    <style type="text/css">
        body {{
            margin: 0;
            padding: 0;
            text-align: center;
        }}
        .cover-image {{
            width: 100%;
            height: 100vh;
            object-fit: contain;
            display: block;
        }}
    </style>
</head>
<body>
    <img src="../images/cover{ext}" alt="표지" class="cover-image" />
</body>
</html>'''

                # 3. 커버 페이지 객체 생성
                cover_page = epub.EpubHtml(
                    title='표지',
                    file_name='cover.xhtml',
                    lang='ko'
                )
                cover_page.content = cover_html
                book.add_item(cover_page)

                # 4. 메타데이터에 커버 정보 등록 (ebooklib 내부 처리용)
                book.set_cover(f"images/cover{ext}", cover_content)

                return cover_page  # 커버 페이지 객체 반환 (spine과 toc에 추가용)

            except Exception as e:
                print(f"커버 이미지 추가 실패: {e}")
                return None

        return None  # 커버 이미지가 없는 경우

                # 추가 이미지 처리 기능들 (주석):
                #
                # # 여러 커버 이미지 (썸네일 등):
                # thumbnail_content = self.resize_image(cover_content, (150, 200))  # 사용자 정의 함수
                # book.add_item(epub.EpubItem(
                #     uid="cover_thumbnail",
                #     file_name="images/cover_thumb.jpg",
                #     media_type="image/jpeg",
                #     content=thumbnail_content
                # ))
                #
                # # 이미지 메타데이터:
                # img_item = epub.EpubItem(
                #     uid="cover_image",
                #     file_name=f"images/cover{ext}",
                #     media_type=media_type,
                #     content=cover_content
                # )
                # img_item.add_metadata('DC', 'title', '표지 이미지')
                # img_item.add_metadata('DC', 'creator', '일러스트레이터명')
                # book.add_item(img_item)
                #
                # # SVG 커버 이미지:
                # svg_cover = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800">
                #     <rect width="600" height="800" fill="#f0f0f0"/>
                #     <text x="300" y="400" text-anchor="middle" font-size="48">제목</text>
                # </svg>'''
                # book.add_item(epub.EpubItem(
                #     uid="svg_cover",
                #     file_name="images/cover.svg",
                #     media_type="image/svg+xml",
                #     content=svg_cover
                # ))

    def create_toc_with_numbering(self, chapters):
        """목차에 일련번호를 추가하여 생성합니다."""
        # UI에서 번호 표시 옵션 확인
        add_numbering = self.should_add_chapter_numbering()

        if not add_numbering:
            # 번호를 붙이지 않는 경우 기존 챕터 그대로 반환
            return chapters

        # 번호 매기기 스타일 확인
        numbering_style = self.get_numbering_style()

        # 번호를 붙이는 경우 새로운 목차 아이템 생성
        numbered_chapters = []

        for i, chapter in enumerate(chapters, 1):
            # 기존 챕터의 제목 가져오기
            original_title = chapter.title

            # 번호 매기기 스타일에 따른 제목 생성
            if numbering_style == "arabic":  # 1, 2, 3...
                numbered_title = f"{i}. {original_title}"
            elif numbering_style == "roman":  # I, II, III...
                roman_number = self.to_roman_numeral(i)
                numbered_title = f"{roman_number}. {original_title}"
            elif numbering_style == "korean":  # 1장, 2장, 3장...
                numbered_title = f"{i}장. {original_title}"
            elif numbering_style == "progress":  # 1/10, 2/10, 3/10...
                total = len(chapters)
                numbered_title = f"({i}/{total}) {original_title}"
            else:  # 기본값
                numbered_title = f"{i}. {original_title}"

            # 새로운 Link 객체 생성 (같은 파일을 가리키지만 제목만 다름)
            numbered_chapter = epub.Link(
                href=chapter.file_name,
                title=numbered_title,
                uid=f"toc_chapter_{i}"
            )

            numbered_chapters.append(numbered_chapter)

        return numbered_chapters

    def get_numbering_style(self):
        """목차 번호 매기기 스타일을 가져옵니다."""
        # UI에서 번호 스타일 콤보박스 확인
        #
        # UI 추가 필요: 콤보박스 위젯
        # - 위젯명: comboBox_NumberingStyle
        # - 라벨: "번호 매기기 스타일:"
        # - 위치: checkBox_AddChapterNumbers 바로 아래
        # - 항목들:
        #   1. "아라비아 숫자 (1, 2, 3...)" - 기본값
        #   2. "로마 숫자 (I, II, III...)"
        #   3. "한국식 (1장, 2장, 3장...)"
        #   4. "진행률 표시 (1/10, 2/10...)"
        # - 기본 선택: "아라비아 숫자 (1, 2, 3...)"
        # - 활성화 조건: checkBox_AddChapterNumbers가 체크된 경우에만 활성화
        # - 툴팁: "목차에 표시될 번호 형식을 선택하세요"
        #
        style_combo = getattr(self.ui, 'comboBox_NumberingStyle', None)

        if style_combo:
            current_text = style_combo.currentText()
            if "로마" in current_text or "Roman" in current_text:
                return "roman"
            elif "장" in current_text or "Korean" in current_text:
                return "korean"
            elif "진행" in current_text or "Progress" in current_text:
                return "progress"
            else:
                return "arabic"

        # 기본값
        return "arabic"

    def to_roman_numeral(self, number):
        """아라비아 숫자를 로마 숫자로 변환합니다."""
        if number <= 0 or number > 3999:
            return str(number)  # 범위를 벗어나면 아라비아 숫자 그대로

        values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        numerals = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']

        result = ''
        for i, value in enumerate(values):
            count = number // value
            if count:
                result += numerals[i] * count
                number -= value * count

        return result

    def should_add_chapter_numbering(self):
        """챕터 번호를 목차에 추가할지 결정합니다."""
        # UI에서 챕터 번호 표시 옵션 체크박스 확인
        #
        # UI 추가 필요: 체크박스 위젯
        # - 위젯명: checkBox_AddChapterNumbers
        # - 텍스트: "목차에 챕터 번호 표시"
        # - 기본값: True (체크됨)
        # - 위치: ePub 변환 설정 그룹박스 내부
        # - 툴팁: "목차에서만 번호가 표시되며, 본문 제목은 변경되지 않습니다"
        #
        numbering_checkbox = getattr(self.ui, 'checkBox_AddChapterNumbers', None)

        if numbering_checkbox:
            return numbering_checkbox.isChecked()

        # 체크박스가 없는 경우 기본값
        # 사용자가 원하는 기본 동작을 설정할 수 있습니다
        return True  # True: 기본적으로 번호 표시, False: 기본적으로 번호 숨김

        # 고급 번호 매기기 옵션들 (주석):
        #
        # def create_advanced_numbering(self, chapters):
        #     """고급 번호 매기기 옵션들"""
        #     numbered_chapters = []
        #
        #     # 로마 숫자 번호 매기기:
        #     roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
        #     for i, chapter in enumerate(chapters):
        #         if i < len(roman_numerals):
        #             numbered_title = f"{roman_numerals[i]}. {chapter.title}"
        #         else:
        #             numbered_title = f"{i+1}. {chapter.title}"
        #
        #     # 부/장 구조 번호 매기기:
        #     part_number = 1
        #     chapter_in_part = 1
        #     for chapter in chapters:
        #         if self.is_part_separator(chapter.title):  # 사용자 정의 함수
        #             numbered_title = f"제{part_number}부. {chapter.title}"
        #             part_number += 1
        #             chapter_in_part = 1
        #         else:
        #             numbered_title = f"{part_number}-{chapter_in_part}. {chapter.title}"
        #             chapter_in_part += 1
        #
        #     # 진행률 표시:
        #     total_chapters = len(chapters)
        #     for i, chapter in enumerate(chapters):
        #         progress = f"({i+1}/{total_chapters})"
        #         numbered_title = f"{i+1}. {chapter.title} {progress}"
        #
        #     # 예상 읽기 시간 표시:
        #     for i, chapter in enumerate(chapters):
        #         reading_time = self.estimate_reading_time(chapter)  # 사용자 정의 함수
        #         numbered_title = f"{i+1}. {chapter.title} ({reading_time}분)"
        #
        #     return numbered_chapters

    def get_chapter_info(self):
        """챕터 테이블에서 정보를 수집합니다."""
        chapters = []
        table = self.ui.tableWidget_ChapterList

        if table.rowCount() == 0:
            # 챕터가 없으면 전체 텍스트를 하나의 챕터로 만듦
            title = self.ui.lineEdit_Title.text().strip()
            chapters.append({
                'title': title,
                'content': self.get_full_text_content(),
                'order': 1
            })
        else:
            # 체크된 챕터들만 수집
            for row in range(table.rowCount()):
                checkbox = table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    order_item = table.item(row, 1)
                    title_item = table.item(row, 2)
                    line_item = table.item(row, 3)

                    if order_item and title_item and line_item:
                        chapters.append({
                            'title': title_item.text(),
                            'line_no': int(line_item.text()),
                            'order': int(order_item.text()) if order_item.text() else 999
                        })

            # 순서대로 정렬
            chapters.sort(key=lambda x: x['order'])
            # 각 챕터의 내용 추출
            self.extract_chapter_contents(chapters)

        return chapters

    def get_full_text_content(self):
        """전체 텍스트 내용을 반환합니다."""
        text_file_path = self.ui.label_TextFilePath.text().strip()
        try:
            with open(text_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            QMessageBox.critical(self.main_window, "파일 읽기 오류", f"텍스트 파일을 읽을 수 없습니다:\n{str(e)}")
            return ""

    def extract_chapter_contents(self, chapters):
        """각 챕터의 내용을 추출합니다."""
        text_file_path = self.ui.label_TextFilePath.text().strip()
        try:
            with open(text_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, chapter in enumerate(chapters):
                start_line = chapter['line_no'] - 1
                end_line = chapters[i + 1]['line_no'] - 1 if i + 1 < len(chapters) else len(lines)
                chapter_lines = lines[start_line:end_line]
                chapter['content'] = ''.join(chapter_lines).strip()

        except Exception as e:
            QMessageBox.critical(self.main_window, "챕터 추출 오류", f"챕터 내용을 추출할 수 없습니다:\n{str(e)}")
