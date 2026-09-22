# DOCX → PDF 실행 방법

이 도구는 Python 프로그램이다. `.command`와 `.cmd`는 Python을 실행하는 바로가기 스크립트이며, Python·LibreOffice·Poppler가 내장된 독립 `.app`/`.exe`는 아니다. 현재 Mac에서는 원본 DOCX를 넣는 전체 과정을 실행해 확인했다. Windows 스크립트는 제공하지만 이 Mac에서 Windows 실행 검증을 했다고 주장하지 않는다.

새 기본값: `multi-signal`. 이전 함수명 실험은 `--profiles native-alias`로 선택한다. 새 suite 네 방식 전체는 `--profiles vector-local raster-docstring hidden-assert multi-signal`로 만든다.

## 처리 순서

```text
DOCX 원본 (수정하지 않음)
  → 임시 변환 사본 (필요한 경우 코드 글꼴 보정)
  → LibreOffice의 PDF export
  → baseline.pdf 보존
  → 선택한 PDF 후처리
  → 모든 페이지 렌더링 / 픽셀·본문 비교 / 네 추출 경로 검사
  → 날짜별 새 폴더 + instructor-only/manifest.json
```

PDF를 입력하면 LibreOffice 변환을 건너뛰고 바로 기준본 보존과 후처리를 한다. Word의 배치를 최대한 유지하려면 Word에서 직접 내보낸 PDF를 입력하는 편이 낫다. LibreOffice 변환은 글꼴·줄바꿈·페이지 배치가 Word와 달라질 수 있다. 원본의 D2Coding 밑줄 문제 때문에 Mac에서는 임시 사본에 Menlo를, Windows에서는 Courier New를 기본 지정한다. 실제 대체 글꼴과 렌더링 결과를 확인해야 한다.

`native-alias`는 화면을 유지하면서 추출 함수명만 `paint_stairs`로 바꾸는 실험이다. **Gemini Flash에서는 이 보완 뒤에도 원래 `print_stairs`가 출력되었으므로 Gemini 차단 기능이라고 부르지 않는다.** `visual-comment`는 회색의 작은 코드 주석 지시를 하단에 추가하는 별도 실험이다. 이쪽은 화면이 의도적으로 달라지며 사람도 읽을 수 있다.

PDF 생성에는 AI를 호출하지 않는다. 모델 검증 명령을 따로 실행하거나 브라우저에 직접 업로드할 때만 모델 제공자에게 파일이 전달된다.

## Mac

`PDF만들기.command`를 더블클릭하면 입력 파일 선택 창을 연다. DOCX 또는 PDF를 고르면 새 `multi-signal` 결합본을 만든다. 각 단독 방식과 실제 결과는 SIGNAL_SUITE.md를 참고한다. Finder에서 스크립트가 바로 실행되지 않으면 터미널에서 아래처럼 실행한다.

```bash
cd '/Users/taehoje/Documents/개인 진행 프로젝트/assignment-pdf-lab'
./PDF만들기.command '/Users/taehoje/Downloads/ASSN1_en_v2.docx'
```

화면 주석 실험본만 만들기:

```bash
./PDF만들기.command '/경로/과제.docx' --profiles visual-comment
```

둘 다 별도 파일로 만들기:

```bash
./PDF만들기.command '/경로/과제.docx' --profiles native-alias visual-comment
```

기존 `다시만들기.command`는 기존 동작을 유지한다. 인수를 생략하면 원래 Downloads의 DOCX를 사용하고 모든 실험 변형을 만든다. 새 파일을 선택하고 싶으면 `PDF만들기.command`를 쓴다.

현재 Mac은 Codex 번들 Python과 이미 설치된 라이브러리를 이용한다. 다른 Mac에서는 Python 3.10 이상, LibreOffice, Poppler가 필요하다. 기존 Homebrew를 쓰는 환경이라면 `brew install poppler libreoffice`로 관련 도구를 준비할 수 있다. 프로젝트의 `.venv`에 `requirements.txt`도 설치한다.

## Windows

프로젝트 폴더의 `MakePDF.cmd`를 더블클릭하면 파일 선택 창을 연다. DOCX/PDF를 파일 위로 드래그해 경로를 전달할 수도 있다. 공백이 있는 경로는 명령줄에서 큰따옴표로 감싼다.

```bat
MakePDF.cmd "C:\Assignments\ASSN1_en_v2.docx"
MakePDF.cmd "C:\Assignments\ASSN1_en_v2.docx" --profiles visual-comment
```

필요한 구성 요소:

1. Python 3.10 이상과 `py` 실행기. [Python 공식 다운로드](https://www.python.org/downloads/windows/)
2. DOCX 변환을 위한 [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/). 표준 Program Files 설치 경로를 자동 탐색한다.
3. Poppler의 `pdftotext.exe`, `pdftoppm.exe`. 이미 Conda를 사용하는 환경이면 conda-forge의 Poppler 패키지를 사용할 수 있다. 실행 파일이 있는 폴더를 PATH 또는 `POPPLER_BIN` 환경변수로 지정한다.
4. Python 라이브러리:

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe launcher.py "C:\Assignments\ASSN1_en_v2.docx" --check
```

`.venv`가 있으면 `MakePDF.cmd`가 그 Python을 사용한다. 설치가 빠져 있으면 어떤 항목이 없는지 알리고 멈춘다. 파일 선택기를 사용할 수 없는 Python이라면 명령줄에 파일 경로를 직접 준다.

독립 EXE로 배포하려면 Windows에서 별도 패키징·실행 검증이 필요하다. Python만 묶어도 LibreOffice/Poppler 의존성은 남는다. 이번 결과에는 검증하지 않은 EXE를 포함하지 않았다.

## 생성 결과와 보관

`output/pdf/날짜-식별자/`에 새 파일을 만든다. 기존 결과를 덮어쓰지 않는다. 최신 경로는 `output/LATEST`에 저장된다.

- `baseline.pdf`: 변환 후의 깨끗한 기준본
- 선택한 실험 PDF: 후처리된 사본
- `instructor-only/manifest.json`: 입력·출력 해시, 해당 빌드의 표식, 시각적·추출 검사
- `instructor-only/renders`: 검토용 전 페이지 이미지
- `instructor-only/extracted`: 추출 경로별 텍스트

`PASS`는 PDF의 생성 검사가 통과했다는 의미다. 특정 AI 모델에서 작동한다는 뜻이 아니다. 모델 결과는 별도 실험 기록을 확인한다. 별도 보고서·정답·manifest·서명키를 학생에게 배포할 필요는 없다.

현재 후처리는 이 ASSN1의 함수 이름과 구조를 대상으로 한다. 임의의 다른 과제 DOCX를 자동으로 의미 분석해 함정을 만드는 범용 도구는 아니다. 입력 형식이나 함수명이 달라지면 적절한 오류를 내거나 설정·코드를 수정해야 한다.
