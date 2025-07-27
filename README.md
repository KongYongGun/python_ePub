# ePub Python Editor

ePub 파일을 생성하고 편집하는 PyQt6 기반 GUI 애플리케이션입니다.

## 주요 기능

- 텍스트 파일을 ePub 형식으로 변환
- 커버 이미지 및 챕터 이미지 관리
- 폰트 선택 및 미리보기
- 정규식을 이용한 챕터 자동 감지
- 텍스트 정렬, 스타일, 색상 설정
- 인코딩 자동 감지 및 변환

## 시스템 요구사항

- Python 3.10 이상
- PyQt6
- 기타 의존성은 requirements.txt 참조

## 설치 및 실행

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

2. 애플리케이션 실행:
```bash
python main.py
```

## UI 파일 빌드

UI 파일을 수정한 경우:
```bash
pyuic6 -o ePub_ui.py 250714.ui
```

## 주요 파일 구조

- `main.py`: 메인 애플리케이션 로직
- `ePub_ui.py`: PyQt6 UI 정의 (자동 생성)
- `250714.ui`: Qt Designer UI 파일
- `ePub_db.py`: 데이터베이스 관리
- `ePub_loader.py`: 데이터 로딩 유틸리티
- `encoding_worker.py`: 인코딩 감지 워커
- `chapter_finder.py`: 챕터 찾기 워커
- `font_checker_worker.py`: 폰트 호환성 검사 워커

## 기능 설명

### 폰트 관리
- 폰트 폴더 설정을 통한 일괄 폰트 로딩
- 실제 폰트로 미리보기 제공
- 폰트 호환성 자동 검사

### 챕터 관리
- 정규식 패턴을 이용한 자동 챕터 감지
- 수동 챕터 순서 조정
- 챕터별 삽화 이미지 설정

### 텍스트 포맷팅
- 다양한 정렬 옵션 (좌, 중앙, 우, 들여쓰기)
- 폰트 굵기 및 스타일 설정
- 색상 선택기를 통한 텍스트 색상 설정

## 라이센스

이 프로젝트는 오픈소스 프로젝트입니다.
