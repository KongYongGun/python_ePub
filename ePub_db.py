import os
import sqlite3
from datetime import datetime

# 항상 현재 파일 기준 경로에 생성
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "epub_config.db")

def table_exists(cursor, table_name):
    """테이블 존재 여부를 확인하는 함수"""
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def initialize_database():
    db_exists = os.path.exists(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if not db_exists:
        print("DB 파일이 존재하지 않아 새로 생성합니다...")
    else:
        print("기존 DB 파일이 존재합니다. 테이블 구조를 확인합니다...")

    # 각 테이블별로 존재 여부 확인 후 생성
    tables_created = []

    # Stylesheet 테이블: QSS 테마 스타일 저장
    if not table_exists(cursor, 'Stylesheet'):
        cursor.execute("""
        CREATE TABLE Stylesheet (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- 고유 ID
            name TEXT NOT NULL,                  -- 스타일 이름
            description TEXT,                    -- 설명
            content TEXT NOT NULL,               -- QSS 내용
            is_default INTEGER DEFAULT 0,        -- 기본 적용 여부
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 생성일시
        );
        """)
        tables_created.append('Stylesheet')

    # ChapterRegex 테이블: 챕터 구분용 정규식
    if not table_exists(cursor, 'ChapterRegex'):
        cursor.execute("""
        CREATE TABLE ChapterRegex (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- 고유 ID
            name TEXT NOT NULL,                   -- 정규식 이름
            example TEXT,                         -- 예시 텍스트
            pattern TEXT NOT NULL,                -- 정규식 패턴
            is_enabled INTEGER DEFAULT 1,         -- 활성화 여부
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        tables_created.append('ChapterRegex')

    # PunctuationRegex 테이블: 괄호/기호 추출용 정규식
    if not table_exists(cursor, 'PunctuationRegex'):
        cursor.execute("""
        CREATE TABLE PunctuationRegex (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- 고유 ID
            name TEXT NOT NULL,                   -- 정규식 이름
            pattern TEXT NOT NULL,                -- 정규식 패턴
            description TEXT,                     -- 설명
            is_enabled INTEGER DEFAULT 1,         -- 활성화 여부
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        tables_created.append('PunctuationRegex')

    # TextStyle 테이블: 텍스트 스타일 설정 (정렬, 굵기 등)
    if not table_exists(cursor, 'TextStyle'):
        cursor.execute("""
        CREATE TABLE TextStyle (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- 고유 ID
            name TEXT NOT NULL,                   -- 스타일 이름
            type TEXT NOT NULL,                   -- 구분 (chapter/main/bracket 등)
            is_enabled INTEGER DEFAULT 1,         -- 활성화 여부
            align TEXT DEFAULT 'left',            -- 정렬 (left/center/right)
            font_style TEXT DEFAULT 'normal',     -- 스타일 (normal/bold/italic 등)
            font_color TEXT DEFAULT '#000000',    -- 색상 (HEX)
            description TEXT,                     -- 설명
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        tables_created.append('TextStyle')

    # EpubHistory 테이블: ePub 생성 이력
    if not table_exists(cursor, 'EpubHistory'):
        cursor.execute("""
        CREATE TABLE EpubHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- 고유 ID
            file_name TEXT NOT NULL,              -- 출력 파일명
            output_path TEXT,                     -- 출력 경로
            title TEXT,                           -- 책 제목
            author TEXT,                          -- 작가명
            isbn TEXT,                            -- ISBN
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 생성일시
            chapter_count INTEGER,                -- 챕터 수
            duration_seconds REAL,                -- 생성 소요시간
            setting_id INTEGER,                   -- 사용된 설정 ID
            FOREIGN KEY(setting_id) REFERENCES EpubSetting(id)
        );
        """)
        tables_created.append('EpubHistory')

    # ChapterList 테이블: ePub별 목차 정보
    if not table_exists(cursor, 'ChapterList'):
        cursor.execute("""
        CREATE TABLE ChapterList (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- 고유 ID
            epub_id INTEGER NOT NULL,             -- EpubHistory 참조 ID
            chapter_index INTEGER NOT NULL,       -- 챕터 인덱스
            chapter_title TEXT NOT NULL,          -- 챕터 제목
            regex_used TEXT,                      -- 사용된 정규식
            FOREIGN KEY(epub_id) REFERENCES EpubHistory(id) ON DELETE CASCADE
        );
        """)
        tables_created.append('ChapterList')

    # EpubSetting 테이블: ePub 생성 시 사용한 전체 세팅 정보 저장
    if not table_exists(cursor, 'EpubSetting'):
        cursor.execute("""
        CREATE TABLE EpubSetting (
            id INTEGER PRIMARY KEY AUTOINCREMENT,     -- 고유 ID
            name TEXT NOT NULL,                       -- 세팅 이름
            description TEXT,                         -- 설명
            use_body_font INTEGER DEFAULT 0,          -- 본문 폰트 포함 여부
            use_chapter_font INTEGER DEFAULT 0,       -- 챕터 폰트 포함 여부
            body_font_path TEXT,                      -- 본문 폰트 경로
            chapter_font_path TEXT,                   -- 챕터 폰트 경로
            stylesheet_id INTEGER,                    -- Stylesheet 테이블 참조
            chapter_regex_id INTEGER,                 -- ChapterRegex 테이블 참조
            punctuation_regex_ids TEXT,               -- 쉼표로 연결된 정규식 ID 목록
            top_margin INTEGER DEFAULT 1,             -- 상단 여백
            bottom_margin INTEGER DEFAULT 4,          -- 하단 여백
            divide_by_chapter INTEGER DEFAULT 0,      -- 챕터별 분할 여부
            chapter_style_enabled INTEGER DEFAULT 1,  -- 챕터 스타일 적용 여부
            chapter_align TEXT DEFAULT 'center',      -- 챕터 정렬
            chapter_font_style TEXT DEFAULT 'bold',   -- 챕터 폰트 스타일
            chapter_font_color TEXT DEFAULT '#000000',-- 챕터 폰트 색상
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(stylesheet_id) REFERENCES Stylesheet(id),
            FOREIGN KEY(chapter_regex_id) REFERENCES ChapterRegex(id)
        );
        """)
        tables_created.append('EpubSetting')

    # AlignStyle 테이블: Left, Center, Right 정렬 스타일 저장
    if not table_exists(cursor, 'AlignStyle'):
        cursor.execute("""
        CREATE TABLE AlignStyle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,     -- 고유 ID
            name TEXT NOT NULL,                       -- 세팅 이름 Left, Center, Right
            description TEXT                          -- 설명 Left, Center, Right
        );
        """)
        tables_created.append('AlignStyle')

    # FontStyle 테이블: bold, italic, normal 폰트 스타일 저장
    if not table_exists(cursor, 'FontStyle'):
        cursor.execute("""
        CREATE TABLE FontStyle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,     -- 고유 ID
            name TEXT NOT NULL,                       -- 세팅 이름 bold, italic, normal
            description TEXT                          -- 설명 bold, italic, normal
        );
        """)
        tables_created.append('FontStyle')

    # 데이터 삽입 부분 - 테이블이 새로 생성된 경우에만 기본 데이터 삽입
    data_inserted = []

    # 기본 정규식 (ChapterRegex) - ChapterRegex 테이블이 비어있는 경우에만 삽입
    cursor.execute("SELECT COUNT(*) FROM ChapterRegex")
    if cursor.fetchone()[0] == 0:
        chapter_regex = [
            ("정규식 01", "[1화]", r"(.+\d+화.)"),
            ("정규식 02", "005. 가나다라 1", r"(^[0-9]{3,}[.]\s.*.[0-9]$)"),
            ("정규식 03", "0001 / 1050 ──────────", r"(^[0-9]{4,})(\s[/]\s[0-9]{4,}...........)"),
            ("정규식 04", "2화 가나다라 (1)", r"(^[0-9]+화.*)"),
            ("정규식 05", "< 가나다라 >", r"(<.*>)$"),
            ("정규식 06", "＃1화 가나다라", r"^#\d+.*"),
            ("정규식 07", "54. 가나다라", r"(\d+\.\s+.+)"),
            ("정규식 08", "#50. 가나다라(3)", r"(#+\d+\.\s+.+)"),
            ("정규식 09", "제1장 가나다라", r"^제\d+장\s+.*"),
            ("정규식 10", "1", r"^\d+$"),
            ("정규식 11", "제 1화", r"제\s*\d+화\.\s*[^\n]+"),
            ("정규식 12", "외전 1화 - 가나다라 (2)", r"외전\s*\d+화\s*[-–]\s*[^\n]+"),
            ("정규식 13", "=-=-=-=", r"=-=-=-="),
            ("정규식 14", "", r"\b\d{5}\b"),
            ("정규식 15", "00001 1화", r"\b\d{5}\s\d+화\b"),
            ("정규식 16", "00001 1화 닥터최태수", r"\b\d{5}\s*\d+화\b"),
            ("정규식 17", "1화 닥터최태수", r"\d+화\b"),
            ("정규식 18", "2부 123화 가나다라", r"[0-9]+부\s[0-9]+화\s[^\n]+"),
            ("정규식 19", "외전 1화", r"외전\s*\d+화"),
            ("정규식 20", "<1화> 미 국세청 범죄수사국의 검은머리 요원", r"^<\d+화>.+$"),
            ("정규식 21", "<천하제일 곤륜객잔 1권 1화>", r"<천하제일 곤륜객잔 \d+권 \d+화>"),
            ("정규식 22", "대한민국 절대 재벌! 1화", r"대한민국 절대 재벌! \d{1,3}화"),
            ("정규식 23", "< 001 : 프롤로그 >", r"< \d{3} : .+ >$"),
            ("정규식 24", "524 : 대한민국의 방패", r"^\d{3} : .+$"),
            ("정규식 25", "1편. 청동기 시대에서의 삶", r"^(?:외전\s*)?\d+편\.\s+.+$"),
            ("정규식 26", "천마는 조용히 살고싶다-1화", r"천마는 조용히 살고싶다-\d{1,3}화"),
            ("정규식 27", "01-천산의 객잔?", r"^\d{1,3}-(.*)$"),
            ("정규식 28", "외전-", r"외전-(.*)$"),
            ("정규식 29", "제1편", r"제\d+편\s+.*"),
            ("정규식 30", "우주재벌 막내아들-1화", r"우주재벌 막내아들-\d{1,3}화"),
            ("정규식 31", "만년만에 귀환한 플레이어 515화", r"만년만에\s귀환한\s플레이어\s(외전\s\(\d+\)|\d+)화"),
            ("정규식 32", "< Episode 1. 유료 서비스 시작 (1) >", r"< Episode \d+\. [^>]+ >"),
            ("정규식 33", "# [47화] 대장간", r"^# \[\d+화\] [^\(\r\n]+(?: \(\d+\))?$"),
            ("정규식 34", "< 진주만에 입항 하다 >", r"^<[^>]+>(?!\s*끝)$"),
            ("정규식 35", "048 - 비상 계엄 (7)", r"^\d{3} - .+ \(\d+\)$"),
            ("정규식 36", "002 - 대혼란", r"^\d{3} - .+$"),
            ("정규식 37", "1화", r"\b\d{1,3}화\b"),
        ]

        cursor.executemany("""
            INSERT INTO ChapterRegex (name, example, pattern) VALUES (?, ?, ?)
        """, chapter_regex)
        data_inserted.append('ChapterRegex 기본 데이터')

    # 정렬 스타일 (AlignStyle) - AlignStyle 테이블이 비어있는 경우에만 삽입
    cursor.execute("SELECT COUNT(*) FROM AlignStyle")
    if cursor.fetchone()[0] == 0:
        align_Style = [
            ("Left", "Left"),
            ("Center", "Center"),
            ("Right", "Right")
        ]
        cursor.executemany("""
            INSERT INTO AlignStyle (name, description) VALUES (?, ?)
        """, align_Style)
        data_inserted.append('AlignStyle 기본 데이터')

    # 폰트 스타일 (FontStyle) - FontStyle 테이블이 비어있는 경우에만 삽입
    cursor.execute("SELECT COUNT(*) FROM FontStyle")
    if cursor.fetchone()[0] == 0:
        font_Style = [
            ("Bold", "Bold"),
            ("Italic", "Italic"),
            ("Normal", "Normal")
        ]
        cursor.executemany("""
            INSERT INTO FontStyle (name, description) VALUES (?, ?)
        """, font_Style)
        data_inserted.append('FontStyle 기본 데이터')

    # 기본 괄호 정규식 (PunctuationRegex) - PunctuationRegex 테이블이 비어있는 경우에만 삽입
    cursor.execute("SELECT COUNT(*) FROM PunctuationRegex")
    if cursor.fetchone()[0] == 0:
        punctuation_regex = [
            ("'...'", r"[‘'](.*?)[’']", "작은 따옴표 감지"),
            ('"..."', r'[“"](.*?)[”"]', "큰 따옴표 감지"),
            ("(...) 괄호", r"\((.*?)\)", "소괄호 내용"),
            ("[...] 괄호", r"\[(.*?)\]", "대괄호 내용")
        ]
        cursor.executemany("""
            INSERT INTO PunctuationRegex (name, pattern, description) VALUES (?, ?, ?)
        """, punctuation_regex)
        data_inserted.append('PunctuationRegex 기본 데이터')

    # 기본 스타일시트 (Stylesheet) - Stylesheet 테이블이 비어있는 경우에만 삽입
    cursor.execute("SELECT COUNT(*) FROM Stylesheet")
    if cursor.fetchone()[0] == 0:
        # 기본 스타일시트
        default_style = """

/*
    * Available at: https://github.com/GTRONICK/QSS/blob/master/Ubuntu.qss
    * https://github.com/Abdulrahmantommy/StyleSheets-for-PyQt5/blob/main/MacOS.qss
    * https://github.com/GTRONICK/QSS/blob/master/Aqua.qss
    * https://www.pythonguis.com/faq/built-in-qicons-pyqt/ 아이콘
*/

/* QMainWindow */
    QMainWindow {
            background-color:#ffffff;

            /* border: 1px solid #000000; 테두리 스타일 (1px 실선, 검정색) */
            /* border-radius: 8px; 테두리 둥글기 설정 */
            /* margin: 10px; 외부 여백 */
            /* padding: 10px; 내부 여백 */
            /* color: #ffffff; 기본 텍스트 색상 */
            /* font-family: Arial, Helvetica, sans-serif; 폰트 패밀리 설정 */
            /* font-size: 14px; 폰트 크기 */
            /* min-width: 500px; 최소 너비 설정 */
            /* min-height: 400px; 최소 높이 설정 */
            /* opacity: 0.1; 창의 투명도 설정 (95% 불투명) */
        }
/* QCheckBox */
    QCheckBox {
            color: #000000; /* 체크박스의 기본 텍스트 색상 */
            padding: 2px;   /* 체크박스와 텍스트 사이의 여백 */
        }

    QCheckBox:disabled {
            color: rgb(81,72,65); /* 비활성화된 상태에서의 텍스트 색상 */
            padding: 2px;         /* 비활성화 상태에서의 체크박스와 텍스트 사이의 여백 */
        }

    QCheckBox:hover {
            border-radius: 4px;        /* 마우스 오버 시 체크박스의 테두리 둥글기 */
            border-style: solid;       /* 마우스 오버 시 테두리의 스타일을 solid로 설정 */
            padding-left: 1px;         /* 왼쪽 패딩 */
            padding-right: 1px;        /* 오른쪽 패딩 */
            padding-bottom: 1px;       /* 아래쪽 패딩 */
            padding-top: 1px;          /* 위쪽 패딩 */
            border-width: 1px;         /* 마우스 오버 시 테두리의 두께 */
            border-color: transparent; /* 마우스 오버 시 테두리 색상 투명 처리 */
        }

    QCheckBox::indicator:checked {
            height: 10px; /* 체크박스 크기 - 높이 */
            width: 10px;  /* 체크박스 크기 - 너비 */
            border-style: solid; /* 체크박스의 테두리 스타일 */
            border-width: 1px;   /* 체크박스의 테두리 두께 */
            border-color: qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(246, 134, 86, 255), stop:1 rgba(246, 134, 86, 100));
            /* 체크된 상태에서의 테두리 색상: 색상 변화가 있는 선형 그라디언트 */

            color: #000000; /* 체크된 상태에서의 텍스트 색상 */
            background-color: qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(246, 134, 86, 255), stop:1 rgba(246, 134, 86, 100));
            /* 체크된 상태에서의 배경 색상: 색상 변화가 있는 선형 그라디언트 */
        }

    QCheckBox::indicator:unchecked {
            height: 10px; /* 체크되지 않은 상태에서의 체크박스 높이 */
            width: 10px;  /* 체크되지 않은 상태에서의 체크박스 너비 */
            border-style: solid; /* 체크되지 않은 상태에서의 테두리 스타일 */
            border-width: 1px;   /* 체크되지 않은 상태에서의 테두리 두께 */
            border-color: qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(246, 134, 86, 255), stop:1 rgba(246, 134, 86, 100));
            /* 체크되지 않은 상태에서의 테두리 색상: 색상 변화가 있는 선형 그라디언트 */

            color: #000000; /* 체크되지 않은 상태에서의 텍스트 색상 */
        }
    QCheckBox::indicator:pressed {
            background-color: rgba(200, 100, 50, 150); /* 눌렸을 때의 체크박스 배경색 */
            border-color: rgba(100, 50, 25, 150);      /* 눌렸을 때의 테두리 색상 */
        }

    QCheckBox::indicator:hover {
            background-color: rgba(255, 150, 100, 200); /* 마우스를 올렸을 때의 체크박스 배경색 */
            border-color: rgba(100, 50, 25, 200);       /* 마우스를 올렸을 때의 테두리 색상 */
        }

    QCheckBox::indicator:disabled {
            background-color: rgb(200, 200, 200); /* 비활성화 상태에서의 배경색 */
            border-color: rgb(150, 150, 150);     /* 비활성화 상태에서의 테두리 색상 */
        }

    QColorDialog{
            background-color:#f0f0f0;
        }
/* QComboBox */
    QComboBox {
            font-size: 14px;           /* 콤보박스 내부 텍스트의 글꼴 크기 */
            color: rgb(81,72,65);      /* 콤보박스 텍스트 색상 */
            background: #ffffff;       /* 콤보박스의 배경 색상 */
            border: 1px solid #b0b0b0; /* 콤보박스의 테두리 색상 및 두께 */
            padding: 2px;              /* 콤보박스 내부 여백 */
            font-family: '맑은 고딕', Arial, sans-serif; /* 폰트 패밀리 설정 */
        }

    QComboBox:editable {
            selection-color: rgb(81,72,65);          /* 편집 가능한 콤보박스에서 선택된 텍스트의 색상 */
            selection-background-color: #ffffff;     /* 편집 가능한 콤보박스에서 선택된 항목의 배경 색상 */
            font-size: 14px;                         /* 편집 가능한 콤보박스에서의 글꼴 크기 */
        }

    QComboBox QAbstractItemView {
            selection-color: #ffffff;                /* 콤보박스 드롭다운에서 선택된 항목의 텍스트 색상 */
            selection-background-color: rgb(246, 134, 86); /* 콤보박스 드롭다운에서 선택된 항목의 배경 색상 */
            font-size: 14px;                         /* 드롭다운 항목의 글꼴 크기 */
            color: rgb(81,72,65);                    /* 드롭다운 항목의 텍스트 색상 */
        }

    QComboBox:!editable:on, QComboBox::drop-down:editable:on {
            color:  #1e1d23;   /* 편집 불가능한 콤보박스 및 드롭다운 버튼을 눌렀을 때의 텍스트 색상 */
            font-size: 14px;   /* 편집 불가능한 콤보박스에서의 글꼴 크기 */
        }

    QComboBox::drop-down {
            subcontrol-origin: padding;        /* 드롭다운 버튼의 위치 */
            subcontrol-position: top right;    /* 드롭다운 버튼을 콤보박스의 오른쪽 상단에 위치시킴 */
            width: 25px;                       /* 드롭다운 버튼의 너비 */
            border-left-width: 1px;            /* 드롭다운 버튼의 왼쪽 테두리 두께 */
            border-left-color: darkgray;       /* 드롭다운 버튼의 왼쪽 테두리 색상 */
            border-left-style: solid;          /* 드롭다운 버튼의 왼쪽 테두리 스타일 */
        }

    QComboBox::down-arrow {
            image: url("resource/dropdown.png");        /* 드롭다운 화살표 이미지 */
            width: 10px;                       /* 화살표의 너비 */
            height: 10px;                      /* 화살표의 높이 */
        }

    QComboBox::item {
            padding: 5px;                      /* 드롭다운 메뉴 항목의 패딩 */
            background-color: #f0f0f0;         /* 드롭다운 메뉴 항목의 배경 색상 */
            color: rgb(81,72,65);              /* 드롭다운 메뉴 항목의 텍스트 색상 */
            font-size: 14px;                   /* 드롭다운 메뉴 항목의 글꼴 크기 */
            font-family:'맑은 고딕', Arial, sans-serif;    /* 드롭다운 메뉴 항목의 폰트 패밀리 */
        }

    QComboBox::item:selected {
            background-color: rgb(246, 134, 86); /* 선택된 항목의 배경 색상 */
            color: #ffffff;                      /* 선택된 항목의 텍스트 색상 */
        }

    QComboBox::hover {
            border: 1px solid #555;              /* 콤보박스 위로 마우스를 올렸을 때의 테두리 색상 */
            background-color: #eaeaea;           /* 콤보박스 위로 마우스를 올렸을 때의 배경 색상 */
        }

    QDateTimeEdit, QDateEdit, QDoubleSpinBox, QFontComboBox {
        color:rgb(81,72,65);
        background-color: #ffffff;
    }

    QDialog {
        background-color:#ffffff;
    }

/* QLabel */
    QLabel {
        color: rgb(17, 17, 17);          /* 글자 색상을 어두운 회색으로 설정 */
        font-size: 14px;                 /* 글자 크기를 14px로 설정 */
        font-family: "맑은 고딕", "Arial", sans-serif;/* 글꼴을 Arial로 설정 */
        padding: 5px;                    /* 레이블 안쪽 여백을 5px로 설정 */
        text-align: left;              /* 텍스트를 중앙 정렬 */
        /* background-color: #ffffff;       배경 색상을 흰색으로 설정 */
        /* font-weight: bold;               글자 두께를 굵게 설정 */
        /* font-style: italic;              글자에 이탤릭 스타일을 적용 */
        /* border: 1px solid #d3d3d3;       테두리를 회색으로 설정 */
        /* border-radius: 5px;              테두리를 둥글게 설정 */
        /* min-width: 100px;                레이블의 최소 너비를 100px로 설정 */
        /* min-height: 30px;                레이블의 최소 높이를 30px로 설정 */
        /* margin: 5px;                     레이블 외부 여백을 5px로 설정 */
        /* text-shadow: 1px 1px 2px rgba(0, 0,255, 0.5); 텍스트 그림자 효과 */
    }
    QWidget#convert_tab QLabel#title_font_info_label,  QWidget#convert_tab QLabel#font_info_label{
        color: rgb(0, 0, 0);          /* 글자 색상 설정 */
        font-size: 16px;                /*  글자 크기를 14px로 설정 */
        text-align: left;              /* 텍스트 정렬 */

    }
    QWidget#metadata_tab QLabel#cover_label, QWidget#metadata_tab QLabel#chapter_label {
        border: 1px solid #0b8657;     /*  빨간색 테두리를 설정 */
        /* color: rgb(255, 0, 0);           글자 색상을 빨간색으로 설정 */
        /* background-color: #f0f0f0;       배경 색상을 밝은 회색으로 설정 */
        /* font-size: 16px;                 글자 크기를 16px로 설정 */
        /* font-family: "Verdana", sans-serif; 글꼴을 Verdana로 설정 */
        /* font-weight: normal;             글자 두께를 기본값으로 설정 */
        /* border-radius: 10px;             테두리를 더 둥글게 설정 */
        /* padding: 10px;                   내부 여백을 넉넉하게 설정 */
        /* text-align: right;               텍스트를 오른쪽으로 정렬 */
    }
    /* 특정 레이블 (cover_label, chapter_label) 마우스 hover 시 스타일 */
    QWidget#metadata_tab QLabel#cover_label:hover, QWidget#metadata_tab QLabel#chapter_label:hover {
        border: 2px solid #ff0000;       /* 마우스 hover 시 테두리를 빨간색으로 설정 */
        background-color: #f5f5f5;       /* 마우스 hover 시 배경 색상을 밝은 회색으로 설정 */
        color: rgb(0, 0, 255);           /* 마우스 hover 시 글자 색상을 파란색으로 설정 */
    }

/* QLineEdit */
    QLineEdit {
        color: rgb(17, 17, 17);                  /* 글자 색상을 어두운 회색으로 설정 */
        background-color: rgb(255, 255, 255);    /* 배경 색상을 흰색으로 설정 */
        border: 1px solid rgb(200, 200, 200);    /* 테두리 색상을 연한 회색으로 설정 */
        border-radius: 5px;                      /* 테두리를 둥글게 설정 (5px 반지름) */
        padding: 5px;                            /* 내부 여백을 5px로 설정 */
        font-size: 14px;                         /* 글자 크기를 14px로 설정 */
        font-family: "맑은 고딕", "Arial", sans-serif; /* 글꼴을 Arial로 설정 */
        selection-background-color: rgb(236, 116, 64); /* 선택된 텍스트의 배경 색상을 오렌지색으로 설정 */
        selection-color: rgb(255, 255, 255);     /* 선택된 텍스트의 글자 색상을 흰색으로 설정 */
    }

    /* QLineEdit 마우스 hover 시 스타일 */
    QLineEdit:hover {
        border: 2px solid rgb(236, 116, 64);     /* 마우스 hover 시 테두리를 오렌지색으로 설정 */
        background-color: rgb(245, 245, 245);    /* 마우스 hover 시 배경 색상을 밝은 회색으로 설정 */
    }

    /* QLineEdit 활성화된 상태 (focus) 시 스타일 */
    QLineEdit:focus {
        border: 2px solid rgb(236, 116, 64);     /* 입력 상태일 때 테두리 두께를 더 두껍게 설정하고 오렌지색으로 설정 */
        background-color: rgb(255, 255, 255);    /* 입력 상태일 때 배경 색상을 흰색으로 설정 */
        color: rgb(0, 0, 0);                    /* 입력 상태일 때 글자 색상을 검은색으로 설정 */
        font-weight: bold;                       /* 입력 상태일 때 글자 두께를 굵게 설정 */
        outline: none;                           /* 기본 포커스 아웃라인 제거 */
    }

    /* QLineEdit 비활성화 (disabled) 상태일 때 스타일 */
    QLineEdit:disabled {
        background-color: rgb(230, 230, 230);    /* 비활성화 시 배경 색상을 연한 회색으로 설정 */
        color: rgb(150, 150, 150);               /* 비활성화 시 글자 색상을 흐린 회색으로 설정 */
        border: 1px solid rgb(200, 200, 200);    /* 비활성화 시 테두리를 연한 회색으로 설정 */
    }

    /* QLineEdit 읽기 전용 (read-only) 상태일 때 스타일 */
    QLineEdit[readOnly="true"] {
        background-color: rgb(240, 240, 240);    /* 읽기 전용일 때 배경 색상을 밝은 회색으로 설정 */
        color: rgb(100, 100, 100);               /* 읽기 전용일 때 글자 색상을 중간 회색으로 설정 */
        border: 1px solid rgb(200, 200, 200);    /* 읽기 전용일 때 테두리를 연한 회색으로 설정 */
        font-style: italic;                      /* 읽기 전용일 때 글자를 이탤릭체로 설정 */
    }


    QMenuBar {
        color:rgb(223,219,210);
        background-color:rgb(65,64,59);
    }
    QMenuBar::item {
        padding-top:4px;
        padding-left:4px;
        padding-right:4px;
        color:rgb(223,219,210);
        background-color:rgb(65,64,59);
    }
    QMenuBar::item:selected {
        color:rgb(255,255,255);
        padding-top:2px;
        padding-left:2px;
        padding-right:2px;
        border-top-width:2px;
        border-left-width:2px;
        border-right-width:2px;
        border-top-right-radius:4px;
        border-top-left-radius:4px;
        border-style:solid;
        background-color:rgb(65,64,59);
        border-top-color: rgb(47,47,44);
        border-right-color: qlineargradient(spread:pad, x1:0, y1:1, x2:1, y2:0, stop:0 rgba(90, 87, 78, 255), stop:1 rgba(47,47,44, 255));
        border-left-color:  qlineargradient(spread:pad, x1:1, y1:0, x2:0, y2:0, stop:0 rgba(90, 87, 78, 255), stop:1 rgba(47,47,44, 255));
    }
    QMenu {
        color:rgb(223,219,210);
        background-color:rgb(65,64,59);
    }
    QMenu::item {
        color:rgb(223,219,210);
        padding:4px 10px 4px 20px;
    }
    QMenu::item:selected {
        color:rgb(255,255,255);
        background-color: qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(225, 108, 54, 255), stop:1 rgba(246, 134, 86, 255));
        border-style:solid;
        border-width:3px;
        padding:4px 7px 4px 17px;
        border-bottom-color:qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(175,85,48,255), stop:1 rgba(236,114,67, 255));
        border-top-color:qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(253,156,113,255), stop:1 rgba(205,90,46, 255));
        border-right-color:qlineargradient(spread:pad, x1:0, y1:0.5, x2:1, y2:0.5, stop:0 rgba(253,156,113,255), stop:1 rgba(205,90,46, 255));
        border-left-color:qlineargradient(spread:pad, x1:1, y1:0.5, x2:0, y2:0.5, stop:0 rgba(253,156,113,255), stop:1 rgba(205,90,46, 255));
    }

    QPlainTextEdit {
        border: 1px solid transparent;
        color:rgb(17,17,17);
        selection-background-color:rgb(236,116,64);
        background-color: #FFFFFF;
    }

    QProgressBar {
        text-align: center;
        color: rgb(0, 0, 0);
        border: 1px inset rgb(150,150,150);
        border-radius: 10px;
        background-color:rgb(221,221,219);
    }
    QProgressBar::chunk:horizontal {
        background-color: qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(225, 108, 54, 255), stop:1 rgba(246, 134, 86, 255));
        border:1px solid;
        border-radius:8px;
        border-bottom-color:qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(175,85,48,255), stop:1 rgba(236,114,67, 255));
        border-top-color:qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(253,156,113,255), stop:1 rgba(205,90,46, 255));
        border-right-color:qlineargradient(spread:pad, x1:0, y1:0.5, x2:1, y2:0.5, stop:0 rgba(253,156,113,255), stop:1 rgba(205,90,46, 255));
        border-left-color:qlineargradient(spread:pad, x1:1, y1:0.5, x2:0, y2:0.5, stop:0 rgba(253,156,113,255), stop:1 rgba(205,90,46, 255));
    }
    QPushButton{
        color:rgb(17,17,17);
        border-width: 1px;
        border-radius: 6px;
        border-bottom-color: rgb(150,150,150);
        border-right-color: rgb(165,165,165);
        border-left-color: rgb(165,165,165);
        border-top-color: rgb(180,180,180);
        border-style: solid;
        padding: 4px;
        background-color: qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(220, 220, 220, 255), stop:1 rgba(255, 255, 255, 255));
    }
    QPushButton:hover{
        color:rgb(17,17,17);
        border-width: 1px;
        border-radius:6px;
        border-top-color: rgb(255,150,60);
        border-right-color: qlineargradient(spread:pad, x1:0, y1:1, x2:1, y2:0, stop:0 rgba(200, 70, 20, 255), stop:1 rgba(255,150,60, 255));
        border-left-color:  qlineargradient(spread:pad, x1:1, y1:0, x2:0, y2:0, stop:0 rgba(200, 70, 20, 255), stop:1 rgba(255,150,60, 255));
        border-bottom-color: rgb(200,70,20);
        border-style: solid;
        padding: 2px;
        background-color: qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(220, 220, 220, 255), stop:1 rgba(255, 255, 255, 255));
    }
    QPushButton:default{
        color:rgb(17,17,17);
        border-width: 1px;
        border-radius:6px;
        border-top-color: rgb(255,150,60);
        border-right-color: qlineargradient(spread:pad, x1:0, y1:1, x2:1, y2:0, stop:0 rgba(200, 70, 20, 255), stop:1 rgba(255,150,60, 255));
        border-left-color:  qlineargradient(spread:pad, x1:1, y1:0, x2:0, y2:0, stop:0 rgba(200, 70, 20, 255), stop:1 rgba(255,150,60, 255));
        border-bottom-color: rgb(200,70,20);
        border-style: solid;
        padding: 2px;
        background-color: qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(220, 220, 220, 255), stop:1 rgba(255, 255, 255, 255));
    }

    QPushButton:pressed{
        color:rgb(17,17,17);
        border-width: 1px;
        border-radius: 6px;
        border-width: 1px;
        border-top-color: rgba(255,150,60,200);
        border-right-color: qlineargradient(spread:pad, x1:0, y1:1, x2:1, y2:0, stop:0 rgba(200, 70, 20, 255), stop:1 rgba(255,150,60, 200));
        border-left-color:  qlineargradient(spread:pad, x1:1, y1:0, x2:0, y2:0, stop:0 rgba(200, 70, 20, 255), stop:1 rgba(255,150,60, 200));
        border-bottom-color: rgba(200,70,20,200);
        border-style: solid;
        padding: 2px;
        background-color: qlineargradient(spread:pad, x1:0.5, y1:0, x2:0.5, y2:1, stop:0 rgba(220, 220, 220, 255), stop:1 rgba(255, 255, 255, 255));
    }
    QPushButton:disabled{
        color:rgb(174,167,159);
        border-width: 1px;
        border-radius: 6px;
        background-color: qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(200, 200, 200, 255), stop:1 rgba(230, 230, 230, 255));
    }
    QRadioButton {
        padding: 1px;
    }
    QRadioButton::indicator:checked {
        height: 10px;
        width: 10px;
        border-style:solid;
        border-radius:5px;
        border-width: 1px;
        border-color: rgba(246, 134, 86, 255);
        color: #a9b7c6;
        background-color:rgba(246, 134, 86, 255);
    }
    QRadioButton::indicator:!checked {
        height: 10px;
        width: 10px;
        border-style:solid;
        border-radius:5px;
        border-width: 1px;
        border-color: rgb(246, 134, 86);
        color: #a9b7c6;
        background-color: transparent;
    }
    QScrollArea {
        color: white;
        background-color:#f0f0f0;
    }
    QSlider::groove {
        border-style: solid;
        border-width: 1px;
        border-color: rgb(207,207,207);
    }
    QSlider::groove:horizontal {
        height: 5px;
        background: rgb(246, 134, 86);
    }
    QSlider::groove:vertical {
        width: 5px;
        background: rgb(246, 134, 86);
    }
    QSlider::handle:horizontal {
        background: rgb(253,253,253);
        border-style: solid;
        border-width: 1px;
        border-color: rgb(207,207,207);
        width: 12px;
        margin: -5px 0;
        border-radius: 7px;
    }
    QSlider::handle:vertical {
        background: rgb(253,253,253);
        border-style: solid;
        border-width: 1px;
        border-color: rgb(207,207,207);
        height: 12px;
        margin: 0 -5px;
        border-radius: 7px;
    }
    QSlider::add-page:horizontal, QSlider::add-page:vertical {
        background: white;
    }
    QSlider::sub-page:horizontal, QSlider::sub-page:vertical {
        background: rgb(246, 134, 86);
    }
    QStatusBar {
        color:rgb(81,72,65);
    }

/* QSpinBox, QDoubleSpinBox */
    /* General QSpinBox and QDoubleSpinBox styling */
    QSpinBox, QDoubleSpinBox {
        background-color: #ffffff;              /* White background */
        color: rgb(17, 17, 17);                 /* Text color */
        border: 1px solid rgb(200, 200, 200);   /* Border color */
        border-radius: 5px;                     /* Rounded corners */
        padding-right: 18px;                    /* Space for the up and down buttons */
        font-size: 14px;                        /* Font size */
        font-family: "맑은 고딕", "Arial", sans-serif; /* Font family */
        min-width: 60px;                        /* Minimum width */
    }

    /* Up and down button positions */
    QSpinBox::up-button, QDoubleSpinBox::up-button {
        subcontrol-origin: padding;              /* Align the button within the padding */
        subcontrol-position: top right;          /* Place the up button in the top right */
        width: 16px;                             /* Width of the up button */
        border-left: 1px solid rgb(200, 200, 200); /* Add a separator for the up button */
        background-color: rgb(245, 245, 245);    /* Button background color */
        border-top-right-radius: 5px;            /* Rounded top right corner */
    }

    QSpinBox::down-button, QDoubleSpinBox::down-button {
        subcontrol-origin: padding;              /* Align the button within the padding */
        subcontrol-position: bottom right;       /* Place the down button in the bottom right */
        width: 16px;                             /* Width of the down button */
        border-left: 1px solid rgb(200, 200, 200); /* Add a separator for the down button */
        background-color: rgb(245, 245, 245);    /* Button background color */
        border-bottom-right-radius: 5px;         /* Rounded bottom right corner */
    }

    /* Arrow icons */
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
        image: url("resource/arrow-up.png");     /* Up arrow icon */
        width: 10px;                             /* Icon width */
        height: 10px;                            /* Icon height */
    }

    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
        image: url("resource/arrow-down.png");   /* Down arrow icon */
        width: 10px;                             /* Icon width */
        height: 10px;                            /* Icon height */
    }

    /* Hover effect */
    QSpinBox:hover, QDoubleSpinBox:hover {
        border: 1px solid rgb(236, 116, 64);     /* Orange border on hover */
    }

    /* Focus effect */
    QSpinBox:focus, QDoubleSpinBox:focus {
        border: 2px solid rgb(236, 116, 64);     /* Thicker border when focused */
        background-color: rgb(255, 255, 255);    /* White background when focused */
    }

    /* Disabled state */
    QSpinBox:disabled, QDoubleSpinBox:disabled {
        background-color: rgb(230, 230, 230);    /* Light gray background when disabled */
        color: rgb(150, 150, 150);               /* Gray text when disabled */
        border: 1px solid rgb(200, 200, 200);    /* Gray border when disabled */
    }

    QScrollBar:horizontal {
        max-height: 20px;
        border: 1px transparent;
        margin: 0px 20px 0px 20px;
    }
    QScrollBar::handle:horizontal {
        background: rgb(253,253,253);
        border: 1px solid rgb(207,207,207);
        border-radius: 7px;
        min-width: 25px;
    }
    QScrollBar::handle:horizontal:hover {
        background: rgb(253,253,253);
        border: 1px solid rgb(255,150,60);
        border-radius: 7px;
        min-width: 25px;
    }
    QScrollBar::add-line:horizontal {
        border: 1px solid rgb(207,207,207);
        border-top-right-radius: 7px;
        border-top-left-radius: 7px;
        border-bottom-right-radius: 7px;
        background: rgb(255, 255, 255);
        width: 20px;
        subcontrol-position: right;
        subcontrol-origin: margin;
    }
    QScrollBar::add-line:horizontal:hover {
        border: 1px solid rgb(255,150,60);
        border-top-right-radius: 7px;
        border-top-left-radius: 7px;
        border-bottom-right-radius: 7px;
        background: rgb(255, 255, 255);
        width: 20px;
        subcontrol-position: right;
        subcontrol-origin: margin;
    }
    QScrollBar::add-line:horizontal:pressed {
        border: 1px solid grey;
        border-top-left-radius: 7px;
        border-top-right-radius: 7px;
        border-bottom-right-radius: 7px;
        background: rgb(231,231,231);
        width: 20px;
        subcontrol-position: right;
        subcontrol-origin: margin;
    }
    QScrollBar::sub-line:horizontal {
        border: 1px solid rgb(207,207,207);
        border-top-right-radius: 7px;
        border-top-left-radius: 7px;
        border-bottom-left-radius: 7px;
        background: rgb(255, 255, 255);
        width: 20px;
        subcontrol-position: left;
        subcontrol-origin: margin;
    }
    QScrollBar::sub-line:horizontal:hover {
        border: 1px solid rgb(255,150,60);
        border-top-right-radius: 7px;
        border-top-left-radius: 7px;
        border-bottom-left-radius: 7px;
        background: rgb(255, 255, 255);
        width: 20px;
        subcontrol-position: left;
        subcontrol-origin: margin;
    }
    QScrollBar::sub-line:horizontal:pressed {
        border: 1px solid grey;
        border-top-right-radius: 7px;
        border-top-left-radius: 7px;
        border-bottom-left-radius: 7px;
        background: rgb(231,231,231);
        width: 20px;
        subcontrol-position: left;
        subcontrol-origin: margin;
    }
    QScrollBar::left-arrow:horizontal {
        border: 1px transparent grey;
        border-top-left-radius: 3px;
        border-bottom-left-radius: 3px;
        width: 6px;
        height: 6px;
        background: rgb(230,230,230);
    }
    QScrollBar::right-arrow:horizontal {
        border: 1px transparent grey;
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
        width: 6px;
        height: 6px;
        background: rgb(230,230,230);
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
    QScrollBar:vertical {
        max-width: 20px;
        border: 1px transparent grey;
        margin: 20px 0px 20px 0px;
    }
    QScrollBar::add-line:vertical {
        border: 1px solid;
        border-color: rgb(207,207,207);
        border-bottom-right-radius: 7px;
        border-bottom-left-radius: 7px;
        border-top-left-radius: 7px;
        background: rgb(255, 255, 255);
        height: 20px;
        subcontrol-position: bottom;
        subcontrol-origin: margin;
    }
    QScrollBar::add-line:vertical:hover {
        border: 1px solid;
        border-color: rgb(255,150,60);
        border-bottom-right-radius: 7px;
        border-bottom-left-radius: 7px;
        border-top-left-radius: 7px;
        background: rgb(255, 255, 255);
        height: 20px;
        subcontrol-position: bottom;
        subcontrol-origin: margin;
    }
    QScrollBar::add-line:vertical:pressed {
        border: 1px solid grey;
        border-bottom-left-radius: 7px;
        border-bottom-right-radius: 7px;
        border-top-left-radius: 7px;
        background: rgb(231,231,231);
        height: 20px;
        subcontrol-position: bottom;
        subcontrol-origin: margin;
    }
    QScrollBar::sub-line:vertical {
        border: 1px solid rgb(207,207,207);
        border-top-right-radius: 7px;
        border-top-left-radius: 7px;
        border-bottom-left-radius: 7px;
        background: rgb(255, 255, 255);
        height: 20px;
        subcontrol-position: top;
        subcontrol-origin: margin;
    }
    QScrollBar::sub-line:vertical:hover {
        border: 1px solid rgb(255,150,60);
        border-top-right-radius: 7px;
        border-top-left-radius: 7px;
        border-bottom-left-radius: 7px;
        background: rgb(255, 255, 255);
        height: 20px;
        subcontrol-position: top;
        subcontrol-origin: margin;
    }
    QScrollBar::sub-line:vertical:pressed {
        border: 1px solid grey;
        border-top-left-radius: 7px;
        border-top-right-radius: 7px;
        background: rgb(231,231,231);
        height: 20px;
        subcontrol-position: top;
        subcontrol-origin: margin;
    }
    QScrollBar::handle:vertical {
        background: rgb(253,253,253);
        border: 1px solid rgb(207,207,207);
        border-radius: 7px;
        min-height: 25px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgb(253,253,253);
        border: 1px solid rgb(255,150,60);
        border-radius: 7px;
        min-height: 25px;
    }
    QScrollBar::up-arrow:vertical {
        border: 1px transparent grey;
        border-top-left-radius: 3px;
        border-top-right-radius: 3px;
        width: 6px;
        height: 6px;
        background: rgb(230,230,230);
    }
    QScrollBar::down-arrow:vertical {
        border: 1px transparent grey;
        border-bottom-left-radius: 3px;
        border-bottom-right-radius: 3px;
        width: 6px;
        height: 6px;
        background: rgb(230,230,230);
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }

/* QTabWidget */
    QTabWidget {
        color:rgb(0,0,0);
        background-color:rgb(247,246,246);
    }
    QTabWidget::pane {
        border-color: rgba(136, 136, 136, 255);
        background-color:rgb(247,246,246);
        border-style: solid;
        border-width: 1px;
        border-radius: 6px;
    }
    QTabBar::tab {
        padding-left:4px;
        padding-right:4px;
        padding-bottom:2px;
        padding-top:2px;
        color:rgb(81,72,65);
        background-color: qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(221,218,217,255), stop:1 rgba(240,239,238,255));
        border-style: solid;
        border-width: 1px;
        border-top-right-radius:4px;
        border-top-left-radius:4px;
        border-top-color: rgb(180,180,180);
        border-left-color: rgb(180,180,180);
        border-right-color: rgb(180,180,180);
        border-bottom-color: transparent;
    }
    QTabBar::tab:selected, QTabBar::tab:last:selected, QTabBar::tab:hover {
        font-weight: bold;
        background-color:rgba(99, 214, 109, 255);
        margin-left: 0px;
        margin-right: 1px;
    }
    QTabBar::tab:!selected {
        margin-top: 1px;
        margin-right: 1px;
    }

/* QTextEdit */
    QTextEdit {
        border-width: 1px;
        border-style: solid;
        border-color:t rgb(180,180,180);
        color:rgb(17,17,17);
        selection-background-color:rgb(236,116,64);
    }
    QTextEdit:hover {
        border-width: 1px;
        border-style: solid;
        border-color:rgb(180,180,180);
        color:rgb(17,17,17);
        selection-background-color:rgb(236,116,64);
    }
    QTextEdit:focus {
        border-width: 1px;
        border-style: solid;
        border-color:rgb(180,180,180);
        color:rgb(17,17,17);
        selection-background-color:rgb(236,116,64);
    }

    QTimeEdit, QToolBox, QToolBox::tab, QToolBox::tab:selected {
        color:rgb(81,72,65);
        background-color: #ffffff;
    }

    QToolTip
        {
            background-color: #f7ff8d;        /* 툴팁의 배경색을 어두운 회색으로 설정 */
            color: #000000;                   /* 툴팁의 글자색을 흰색으로 설정 */
            border: 1px solid #ffee00;        /* 테두리를 주황색으로 설정 */
            border-radius: 3px;               /* 테두리를 둥글게 설정 */
            padding: 5px;                     /* 툴팁 내부 여백 설정 */
            font-size: 12px;                  /* 툴팁의 글자 크기를 12px로 설정 */
            font-family: "맑은 고딕", "Arial", sans-serif; /* 툴팁의 글꼴을 Arial로 설정 */
            /* font-weight: bold;                글자 굵기를 볼드체로 설정 */
            /* font-style: italic;               글자에 이탤릭 스타일을 적용 */
            /* letter-spacing: 1px;              글자 간격을 넓힘 */
            /* text-shadow: 1px 1px 2px rgba(0, 0, 0, 150); 툴팁 텍스트에 그림자 효과 적용 */
            /* box-shadow: 3px 3px 6px rgba(0, 0, 0, 150);  툴팁 자체에 그림자 효과 적용 */
            opacity: 220;                     /* 툴팁의 투명도 설정 (0-255) */
        }
/* QGroupBox */
    /* QGroupBox 기본 스타일 */

    QGroupBox {
        border: 2px solid #8f8f91;              /* 테두리 설정 */
        border-radius: 5px;                     /* 테두리를 둥글게 설정 */
        background-color: #ffffff;              /* 배경 색상을 흰색으로 설정 */
        padding: 10px;                          /* QGroupBox 내부 패딩 */
        margin-top: 10px;                       /* QGroupBox 상단 여백 설정 */

        /* 3D 효과를 위한 입체 테두리 */
        border-top-color: #d3d3d3;              /* 상단 테두리 색상 (밝은 색) */
        border-left-color: #d3d3d3;             /* 왼쪽 테두리 색상 (밝은 색) */
        border-right-color: #5c5c5c;            /* 오른쪽 테두리 색상 (어두운 색) */
        border-bottom-color: #5c5c5c;           /* 하단 테두리 색상 (어두운 색) */

        /* 그림자 효과 추가 */
        box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.3); /* 그림자 효과 (X축, Y축, 흐림 정도, 색상) */
    }

    /* QGroupBox 제목에 3D 효과 적용 */
    QGroupBox::title {
        subcontrol-origin: margin;                /* 제목 위치를 테두리 안쪽으로 설정 */
        subcontrol-position: top left;            /* 제목 위치: 상단 왼쪽 */
        padding: 0 5px;                           /* 제목의 좌우 여백 */
        color: #333333;                           /* 제목 글자 색상 */
        background-color: rgba(255, 255, 255, 0.8);                /* 제목의 배경 색상 */
        font-size: 14px;                          /* 제목 글자 크기 */
        font-weight: bold;                        /* 제목 글자 두께 설정 */
        font-family: "맑은 고딕", "Arial", sans-serif; /* 제목 폰트 설정 */

        /* 제목에도 약간의 그림자 효과 추가 */
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2); /* 제목 텍스트에 그림자 추가 */
    }

    /* QGroupBox의 hover(마우스를 올렸을 때) 상태 */
    QGroupBox:hover {
        border-color: #f28f43;            /* 마우스를 올렸을 때 테두리 색상을 변경 */
    }

    /* QGroupBox가 비활성화된 경우 */
    QGroupBox:disabled {
        border-color: #d3d3d3;            /* 비활성화 상태일 때 테두리 색상 */
        color: #a0a0a0;                   /* 비활성화 상태일 때 텍스트 색상 */
    }

    /* QGroupBox의 내부 레이아웃에 적용할 스타일 */
    QGroupBox QLineEdit, QGroupBox QPushButton {
        margin: 3px;                      /* 내부 위젯들 간의 간격을 설정 */
        padding: 5px;                     /* 내부 위젯의 패딩 */
    }

    /* QGroupBox 제목 hover 시 효과 */
    QGroupBox::title:hover {
        color: #ff6600;                   /* 마우스를 올렸을 때 제목 글자 색상 */
        background-color: #e6e6e6;        /* 제목의 배경색을 변경 */
    }

    /* QGroupBox 내부의 QCheckBox 스타일 */
    QGroupBox QCheckBox {
        color: #333333;                   /* 체크박스의 기본 글자 색상 */
        padding-left: 5px;                /* 체크박스 텍스트 왼쪽 여백 */
    }

    /* QGroupBox 내부 QComboBox 스타일 */
    QGroupBox QComboBox {
        color: #333333;                   /* 콤보박스의 기본 글자 색상 */
        background-color: #ffffff;        /* 콤보박스의 배경 색상 */
        border: 1px solid #cccccc;        /* 콤보박스의 테두리 색상 */
        border-radius: 3px;               /* 콤보박스의 테두리 둥근 정도 */
    }

    /* QGroupBox 내부 QComboBox가 비활성화되었을 때 */
    QGroupBox QComboBox:disabled {
        background-color: #f0f0f0;        /* 콤보박스가 비활성화되었을 때의 배경색 */
        color: #a0a0a0;                   /* 비활성화 상태의 글자 색상 */
        border: 1px solid #cccccc;        /* 비활성화 상태일 때 테두리 */
    }

        """
        default_style2 = """
/*Copyright (c) DevSec Studio. All rights reserved.

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

/*-----QWidget-----*/
QWidget
{
	background-color: #e4e4e4;
	color: #000;
	selection-background-color: #46a2da;
	selection-color: #fff;

}


/*-----QLabel-----*/
QLabel
{
	background-color: transparent;
	color: #000;

}


/*-----QMenuBar-----*/
QMenuBar
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(227, 227, 227, 255),stop:1 rgba(187, 187, 187, 255));
	border: 1px solid #f1f1f1;
	color: #000;

}


QMenuBar::item
{
	background-color: transparent;

}


QMenuBar::item:selected
{
	background-color: rgba(70,162,218,50%);
	border: 1px solid #46a2da;
	color: #000;

}


QMenuBar::item:pressed
{
	background-color: #46a2da;
	border: 1px solid #46a2da;
	color: #fff;

}


/*-----QMenu-----*/
QMenu
{
    background-color: #d6d6d6;
    border: 1px solid #222;
    padding: 4px;
	color: #000;

}


QMenu::item
{
    background-color: transparent;
    padding: 2px 20px 2px 20px;

}


QMenu::separator
{
   	background-color: #46a2da;
	height: 1px;

}


QMenu::item:disabled
{
    color: #555;
    background-color: transparent;
    padding: 2px 20px 2px 20px;

}


QMenu::item:selected
{
	background-color: rgba(70,162,218,50%);
	border: 1px solid #46a2da;
	color: #000;

}


/*-----QToolBar-----*/
QToolBar
{
	background-color: #d6d6d6;
	border-top: none;
	border-bottom: 1px solid #f1f1f1;
	border-left: 1px solid #f1f1f1;
	border-right: 1px solid #f1f1f1;

}


QToolBar::separator
{
	background-color: #2e2e2e;
	width: 1px;

}


/*-----QToolButton-----*/
QToolButton
{
	background-color: transparent;
	color: #fff;
	padding: 3px;
	margin-left: 1px;
}


QToolButton:hover
{
	background-color: rgba(70,162,218,50%);
	border: 1px solid #46a2da;
	color: #000;

}


QToolButton:pressed
{
	background-color: #727272;
	border: 1px solid #46a2da;

}


QToolButton:checked
{
	background-color: #727272;
	border: 1px solid #222;
}


/*-----QPushButton-----*/
QPushButton
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(184, 184, 184, 255),stop:1 rgba(159, 159, 159, 255));
	color: #000;
	min-width: 80px;
	border-style: solid;
	border-width: 1px;
	border-color: #051a39;
	padding: 5px;

}


QPushButton::flat
{
	background-color: transparent;
	border: none;
	color: #000;

}


QPushButton::disabled
{
	background-color: #606060;
	color: #959595;
	border-color: #051a39;

}


QPushButton::hover
{
	background-color: rgba(70,162,218,50%);
	border: 1px solid #46a2da;

}


QPushButton::pressed
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(174, 174, 174, 255),stop:1 rgba(149, 149, 149, 255));
	border: 1px solid #46a2da;

}


QPushButton::checked
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(174, 174, 174, 255),stop:1 rgba(149, 149, 149, 255));
	border: 1px solid #222;

}


/*-----QLineEdit-----*/
QLineEdit
{
	background-color: #f6f6f6;
	color : #000;
	border: 1px solid #343434;
	padding: 3px;
	padding-left: 5px;

}


/*-----QPlainTExtEdit-----*/
QPlainTextEdit
{
	background-color: #f6f6f6;
	color : #000;
	border: 1px solid #343434;
	padding: 3px;
	padding-left: 5px;

}


/*-----QTabBar-----*/
QTabBar::tab
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(227, 227, 227, 255),stop:1 rgba(187, 187, 187, 255));
	color: #000;
	border-style: solid;
	border-width: 1px;
	border-color: #666;
	border-bottom: none;
	padding: 5px;
	padding-left: 15px;
	padding-right: 15px;

}


QTabWidget::pane
{
	background-color: red;
	border: 1px solid #666;
	top: 1px;

}


QTabBar::tab:last
{
	margin-right: 0;

}


QTabBar::tab:first:!selected
{
	background-color: #666666;
	margin-left: 0px;

}


QTabBar::tab:!selected
{
	color: #b1b1b1;
	border-bottom-style: solid;
	background-color: #666666;

}


QTabBar::tab:selected
{
	margin-top: 0px;

}


QTabBar::tab:!selected:hover
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(127, 127, 127, 255),stop:1 rgba(87, 87, 87, 255));
	color: #000;

}


/*-----QComboBox-----*/
QComboBox
{
    background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(184, 184, 184, 255),stop:1 rgba(159, 159, 159, 255));
    border: 1px solid #000;
    padding-left: 6px;
    color: #000;
    height: 20px;

}


QComboBox::disabled
{
	background-color: #404040;
	color: #656565;
	border-color: #051a39;

}


QComboBox:on
{
    background-color: #46a2da;
	color: #000;

}


QComboBox QAbstractItemView
{
    background-color: #383838;
    color: #000;
    border: 1px solid black;
    selection-background-color: #46a2da;
    outline: 0;

}


QComboBox::drop-down
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(157, 157, 157, 255),stop:1 rgba(150, 150, 150, 255));
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border-left-width: 1px;
    border-left-color: black;
    border-left-style: solid;

}


QComboBox::down-arrow
{
    image: url(://arrow-down.png);
    width: 8px;
    height: 8px;
}


/*-----QSpinBox & QDateTimeEdit-----*/
QSpinBox,
QDateTimeEdit
{
    background-color: #f6f6f6;
	color : #000;
	border: 1px solid #000;
	padding: 3px;
	padding-left: 5px;

}


QSpinBox::up-button,
QDateTimeEdit::up-button
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(184, 184, 184, 255),stop:1 rgba(159, 159, 159, 255));
    width: 16px;
    border-width: 1px;
	border-color: #000;

}


QSpinBox::up-button:hover,
QDateTimeEdit::up-button:hover
{
	background-color: #585858;

}


QSpinBox::up-button:pressed,
QDateTimeEdit::up-button:pressed
{
	background-color: #252525;
    width: 16px;
    border-width: 1px;

}


QSpinBox::up-arrow,
QDateTimeEdit::up-arrow
{
    image: url(://arrow-up.png);
    width: 7px;
    height: 7px;

}


QSpinBox::down-button,
QDateTimeEdit::down-button
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(184, 184, 184, 255),stop:1 rgba(159, 159, 159, 255));
    width: 16px;
    border-width: 1px;
	border-color: #000;

}


QSpinBox::down-button:hover,
QDateTimeEdit::down-button:hover
{
	background-color: #585858;

}


QSpinBox::down-button:pressed,
QDateTimeEdit::down-button:pressed
{
	background-color: #252525;
    width: 16px;
    border-width: 1px;

}


QSpinBox::down-arrow,
QDateTimeEdit::down-arrow
{
    image: url(://arrow-down.png);
    width: 7px;
    height: 7px;

}


/*-----QGroupBox-----*/
QGroupBox
{
    border: 1px solid;
    border-color: #666666;
    margin-top: 23px;

}


QGroupBox::title
{
    background-color: #a0a2a4;
    color: #000;
	subcontrol-position: top left;
    subcontrol-origin: margin;
    padding: 5px;
	border: 1px solid #000;
	border-bottom: none;

}




/*-----QHeaderView-----*/
QHeaderView::section
{
    background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(227, 227, 227, 255),stop:1 rgba(187, 187, 187, 255));
	border: 1px solid #000;
    color: #000;
    text-align: left;
	padding: 4px;

}


QHeaderView::section:disabled
{
    background-color: #525251;
    color: #656565;

}


QHeaderView::section:checked
{
    background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(227, 227, 227, 255),stop:1 rgba(187, 187, 187, 255));
    color: #000;

}


QHeaderView::section::vertical::first,
QHeaderView::section::vertical::only-one
{
    border-top: 1px solid #353635;

}


QHeaderView::section::vertical
{
    border-top: 1px solid #353635;

}


QHeaderView::section::horizontal::first,
QHeaderView::section::horizontal::only-one
{
    border-left: 1px solid #353635;

}


QHeaderView::section::horizontal
{
    border-left: 1px solid #353635;

}


QTableCornerButton::section
{
    background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(227, 227, 227, 255),stop:1 rgba(187, 187, 187, 255));
	border: 1px solid #000;
    color: #fff;

}


/*-----QTreeWidget-----*/
QTreeView
{
	show-decoration-selected: 1;
	alternate-background-color: #c6c6c6;
	selection-color: #fff;
	background-color: #f6f6f6;
	border: 1px solid gray;
	padding-top : 5px;
	color: #000;
	font: 8pt;

}


QTreeView::item:selected
{
	color:#fff;
	background-color: #46a2da;
	border-radius: 0px;

}


QTreeView::item:!selected:hover
{
    background-color: #5e5e5e;
    border: none;
    color: white;

}


QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings
{
	image: url(://tree-closed.png);

}


QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings
{
	image: url(://tree-open.png);

}


/*-----QListView-----*/
QListView
{
	background-color: #f6f6f6;
    border : none;
    color: #000;
    show-decoration-selected: 1;
    outline: 0;
	border: 1px solid gray;

}


QListView::disabled
{
	background-color: #656565;
	color: #1b1b1b;
    border: 1px solid #656565;

}


QListView::item
{
	background-color: #f6f6f6;
    padding: 1px;

}


QListView::item:alternate
{
    background-color: #c6c6c6;

}


QListView::item:alternate:selected
{
    background-color: red;

}


QListView::item:selected
{
	background-color: #b78620;
	border: 1px solid #b78620;
	color: #fff;

}


QListView::item:selected:!active
{
	background-color: #46a2da;
	border: 1px solid #46a2da;
	color: #fff;

}


QListView::item:selected:active
{
	background-color: #46a2da;
	border: 1px solid #46a2da;
	color: #fff;

}


QListView::item:hover {
    background-color: #5e5e5e;
    border: none;
    color: #000;

}


/*-----QCheckBox-----*/
QCheckBox
{
	background-color: transparent;
    color: #000;
	border: none;

}


QCheckBox::indicator
{
    background-color: lightgray;
    border: 1px solid #000;
    width: 12px;
    height: 12px;

}


QCheckBox::indicator:checked
{
    image:url("./ressources/check.png");
	background-color: #46a2da;
    border: 1px solid #3a546e;

}


QCheckBox::indicator:unchecked:hover
{
	border: 1px solid #46a2da;

}


QCheckBox::disabled
{
	color: #656565;

}


QCheckBox::indicator:disabled
{
	background-color: #656565;
	color: #656565;
    border: 1px solid #656565;

}


/*-----QRadioButton-----*/
QRadioButton
{
	color: #000;
	background-color: transparent;

}


QRadioButton::indicator::unchecked:hover
{
	background-color: darkgray;
	border: 2px solid #46a2da;
	border-radius: 6px;
}


QRadioButton::indicator::checked
{
	border: 2px solid #52beff;
	border-radius: 6px;
	background-color: #0088da;
	width: 9px;
	height: 9px;

}


/*-----QSlider-----*/
QSlider::groove:horizontal
{
	background-color: transparent;
	height: 3px;

}


QSlider::sub-page:horizontal
{
	background-color: #46a2da;

}


QSlider::add-page:horizontal
{
	background-color: #5d5d5d;

}


QSlider::handle:horizontal
{
	background-color: #46a2da;
	width: 14px;
	margin-top: -6px;
	margin-bottom: -6px;
	border-radius: 6px;

}


QSlider::handle:horizontal:hover
{
	background-color: #0088da;
	border-radius: 6px;

}


QSlider::sub-page:horizontal:disabled
{
	background-color: #bbb;
	border-color: #999;

}


QSlider::add-page:horizontal:disabled
{
	background-color: #eee;
	border-color: #999;

}


QSlider::handle:horizontal:disabled
{
	background-color: #eee;
	border: 1px solid #aaa;
	border-radius: 3px;

}


/*-----QScrollBar-----*/
QScrollBar:horizontal
{
    border: 1px solid #222222;
    background-color: #9d9d9d;
    height: 13px;
    margin: 0px 16px 0 16px;

}


QScrollBar::handle:horizontal
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(227, 227, 227, 255),stop:1 rgba(187, 187, 187, 255));
	border: 1px solid #2d2d2d;
    min-height: 20px;

}


QScrollBar::add-line:horizontal
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(227, 227, 227, 255),stop:1 rgba(187, 187, 187, 255));
	border: 1px solid #2d2d2d;
    width: 15px;
    subcontrol-position: right;
    subcontrol-origin: margin;

}


QScrollBar::sub-line:horizontal
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(227, 227, 227, 255),stop:1 rgba(187, 187, 187, 255));
	border: 1px solid #2d2d2d;
    width: 15px;
    subcontrol-position: left;
    subcontrol-origin: margin;

}


QScrollBar::right-arrow:horizontal
{
    image: url(://arrow-right.png);
    width: 6px;
    height: 6px;

}


QScrollBar::left-arrow:horizontal
{
    image: url(://arrow-left.png);
    width: 6px;
    height: 6px;

}


QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal
{
    background: none;

}


QScrollBar:vertical
{
    background-color: #9d9d9d;
    width: 13px;
	border: 1px solid #2d2d2d;
    margin: 16px 0px 16px 0px;

}


QScrollBar::handle:vertical
{
    background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(227, 227, 227, 255),stop:1 rgba(187, 187, 187, 255));
	border: 1px solid #2d2d2d;
    min-height: 20px;

}


QScrollBar::add-line:vertical
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(227, 227, 227, 255),stop:1 rgba(187, 187, 187, 255));
	border: 1px solid #2d2d2d;
    height: 15px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;

}


QScrollBar::sub-line:vertical
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(227, 227, 227, 255),stop:1 rgba(187, 187, 187, 255));
	border: 1px solid #2d2d2d;
    height: 15px;
    subcontrol-position: top;
    subcontrol-origin: margin;

}


QScrollBar::up-arrow:vertical
{
    image: url(://arrow-up.png);
    width: 6px;
    height: 6px;

}


QScrollBar::down-arrow:vertical
{
    image: url(://arrow-down.png);
    width: 6px;
    height: 6px;

}


QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical
{
    background: none;

}


/*-----QProgressBar-----*/
QProgressBar
{
	background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(227, 227, 227, 255),stop:1 rgba(187, 187, 187, 255));
    border: 1px solid #666666;
    text-align: center;
	color: #000;
	font-weight: bold;

}


QProgressBar::chunk
{
    background-color: #46a2da;
    width: 5px;
    margin: 0.5px;

}


"""

        cursor.execute("""
            INSERT INTO Stylesheet (name, description, content, is_default)
            VALUES (?, ?, ?, 1)
        """, ("기본 스타일", "기본 폰트 및 버튼 패딩", default_style))
        cursor.execute("""
            INSERT INTO Stylesheet (name, description, content, is_default)
            VALUES (?, ?, ?, 1)
        """, ("기본 스타일 2", "기본 폰트 및 버튼 패딩", default_style2))
        data_inserted.append('Stylesheet 기본 데이터')

    # 기본 텍스트 스타일 설정 (TextStyle) - TextStyle 테이블이 비어있는 경우에만 삽입
    cursor.execute("SELECT COUNT(*) FROM TextStyle")
    if cursor.fetchone()[0] == 0:
        # 기본 텍스트 스타일 설정
        text_styles = [
            ("Chapter Title", "chapter", 1, "center", "bold", "#000000", "챕터 제목"),
            ("Main Text", "main", 1, "left", "normal", "#000000", "본문 내용"),
            ("Bracket 1", "bracket", 1, "left", "normal", "#888888", "괄호 스타일 1")
        ]
        cursor.executemany("""
            INSERT INTO TextStyle (name, type, is_enabled, align, font_style, font_color, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, text_styles)
        data_inserted.append('TextStyle 기본 데이터')

    # 변경사항 커밋
    conn.commit()

    # 결과 출력
    if tables_created or data_inserted:
        print("=== DB 초기화 결과 ===")
        if tables_created:
            print(f"생성된 테이블: {', '.join(tables_created)}")
        if data_inserted:
            print(f"삽입된 데이터: {', '.join(data_inserted)}")
        print("DB 초기화 완료.")
    else:
        print("모든 테이블과 데이터가 이미 존재합니다. 초기화 생략.")

    # CSS 테마 초기화
    initialize_css_themes()

    conn.close()

# CSS 테마 관리 함수들
def initialize_css_themes():
    """CSS 테마 데이터베이스 초기화 및 기본 테마 삽입"""
    from css_themes import get_all_themes

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 기존 테마 개수 확인
    cursor.execute("SELECT COUNT(*) FROM Stylesheet")
    theme_count = cursor.fetchone()[0]

    if theme_count == 0:
        print("기본 CSS 테마들을 데이터베이스에 삽입 중...")
        themes = get_all_themes()

        for key, theme_data in themes.items():
            is_default = 1 if key == "default" else 0
            cursor.execute("""
                INSERT INTO Stylesheet (name, description, content, is_default)
                VALUES (?, ?, ?, ?)
            """, (theme_data["name"], theme_data["description"], theme_data["content"], is_default))

        conn.commit()
        print(f"{len(themes)}개의 기본 CSS 테마가 삽입되었습니다.")
    else:
        print(f"CSS 테마 {theme_count}개가 이미 존재합니다.")

    conn.close()

def get_all_css_themes():
    """모든 CSS 테마를 데이터베이스에서 가져오기"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, description, content, is_default
        FROM Stylesheet
        ORDER BY is_default DESC, name ASC
    """)

    themes = cursor.fetchall()
    conn.close()

    return themes

def get_css_theme_by_id(theme_id):
    """ID로 특정 CSS 테마 가져오기"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, description, content, is_default
        FROM Stylesheet
        WHERE id = ?
    """, (theme_id,))

    theme = cursor.fetchone()
    conn.close()

    return theme

def get_default_css_theme():
    """기본 CSS 테마 가져오기"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, description, content, is_default
        FROM Stylesheet
        WHERE is_default = 1
        LIMIT 1
    """)

    theme = cursor.fetchone()
    conn.close()

    return theme

def set_default_css_theme(theme_id):
    """기본 CSS 테마 설정"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 모든 테마의 기본 설정 해제
    cursor.execute("UPDATE Stylesheet SET is_default = 0")

    # 선택한 테마를 기본으로 설정
    cursor.execute("UPDATE Stylesheet SET is_default = 1 WHERE id = ?", (theme_id,))

    conn.commit()
    conn.close()

def add_custom_css_theme(name, description, content):
    """사용자 정의 CSS 테마 추가"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Stylesheet (name, description, content, is_default)
        VALUES (?, ?, ?, 0)
    """, (name, description, content))

    theme_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return theme_id

def update_css_theme(theme_id, name, description, content):
    """CSS 테마 업데이트"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Stylesheet
        SET name = ?, description = ?, content = ?
        WHERE id = ?
    """, (name, description, content, theme_id))

    conn.commit()
    conn.close()

def delete_css_theme(theme_id):
    """CSS 테마 삭제 (기본 테마가 아닌 경우에만)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 기본 테마인지 확인
    cursor.execute("SELECT is_default FROM Stylesheet WHERE id = ?", (theme_id,))
    result = cursor.fetchone()

    if result and result[0] == 1:
        conn.close()
        return False, "기본 테마는 삭제할 수 없습니다."

    cursor.execute("DELETE FROM Stylesheet WHERE id = ?", (theme_id,))

    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return True, "테마가 삭제되었습니다."
    else:
        conn.close()
        return False, "테마를 찾을 수 없습니다."

def save_font_folder(folder_path):
    """폰트 폴더 경로를 저장합니다. (1개만 유지)"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # FontFolder 테이블이 없으면 생성
        if not table_exists(cursor, 'FontFolder'):
            cursor.execute("""
            CREATE TABLE FontFolder (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

        # 기존 데이터 모두 삭제 (1개만 유지)
        cursor.execute("DELETE FROM FontFolder")

        # 새 폴더 경로 삽입
        cursor.execute("""
            INSERT INTO FontFolder (folder_path, updated_at)
            VALUES (?, CURRENT_TIMESTAMP)
        """, (folder_path,))

        conn.commit()
        conn.close()
        return True, "폰트 폴더가 저장되었습니다."
    except Exception as e:
        return False, f"폰트 폴더 저장 중 오류: {str(e)}"

def get_font_folder():
    """저장된 폰트 폴더 경로를 반환합니다."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # FontFolder 테이블이 없으면 None 반환
        if not table_exists(cursor, 'FontFolder'):
            conn.close()
            return None

        cursor.execute("SELECT folder_path FROM FontFolder ORDER BY updated_at DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
        return None
    except Exception as e:
        print(f"폰트 폴더 조회 중 오류: {str(e)}")
        return None

if __name__ == "__main__":
    initialize_database()
    initialize_css_themes()