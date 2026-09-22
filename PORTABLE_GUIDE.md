# 원본 과제를 다시 PDF로 만드는 방법

현재 기본 프로필은 `native-hidden`이다. 함수명 치환과 숨은 검사 문자열만 사용하고 사람이 볼 수 있는 새 예시는 넣지 않는다. 기존 문서를 고칠 때는 수정한 DOCX 또는 그 문서에서 새로 내보낸 깨끗한 PDF를 선택한다. 이미 표식이 들어간 PDF를 입력하면 중복 삽입을 거부한다.

## 기준본 선택

PDF를 입력하면 그 파일을 바이트 단위로 복사해 `baseline.pdf`로 보관하고 후처리한다. Word 화면의 배치를 기준으로 삼으려면 Word에서 PDF로 내보낸 결과를 입력한다. 이 경로는 글꼴 교체나 재조판을 하지 않는다.

DOCX를 입력하면 현재 자동 경로는 LibreOffice가 PDF를 만든 뒤 그 결과를 기준으로 삼는다. DOCX의 글꼴 지정을 자동으로 바꾸지 않는다. 변환기와 설치 글꼴에 따라 Word와 다른 줄바꿈이나 글리프 문제가 생길 수 있으므로 새 환경에서는 기준본을 눈으로 확인해야 한다. 이번 원본에서도 LibreOffice의 D2Coding 밑줄 표현 문제가 관찰됐다. Word의 내보내기와 후처리 경로를 별도로 확인한 이유다. 전후 픽셀 검사는 PDF 후처리의 보존을 검증하며 서로 다른 변환기의 조판이 같다는 뜻은 아니다.

## Mac

`PDF만들기.command`를 더블클릭하면 파일 선택 창이 열린다. `다시만들기.command`도 같은 경로를 실행한다. 특정 사용자의 Downloads 파일이나 모든 이전 실험본을 자동 선택하지 않는다.

```bash
./PDF만들기.command '/경로/과제.docx'
./PDF만들기.command '/경로/깨끗한과제.pdf'
```

프로젝트의 `.venv`가 있으면 그 Python을 사용하고, 없으면 설치된 Codex 번들 Python 또는 `python3`를 찾는다. 일반 환경에는 Python 3.10 이상과 `requirements.txt`의 라이브러리, Poppler의 `pdftotext`와 `pdftoppm`이 필요하다. DOCX 자동 변환에는 LibreOffice가 필요하며, 설치된 Mac 앱과 Codex 번들 경로를 탐색한다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python launcher.py '/경로/과제.docx' --check
```

## Windows

`MakePDF.cmd`를 더블클릭하거나 DOCX/PDF를 그 파일 위로 끌어놓으면 된다. Python 실행기 `py`, Python 라이브러리, Poppler가 필요하다. DOCX 자동 변환에는 LibreOffice를 설치한다. 표준 Program Files 경로와 PATH를 탐색하며, Poppler 실행 파일 폴더는 PATH 또는 `POPPLER_BIN`으로 지정한다.

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
MakePDF.cmd "C:\Assignments\assignment.docx"
```

Windows용 바로가기는 제공하지만 이번 작업은 Mac에서 실행했다. Windows 실기 검증이나 독립 EXE 패키징을 완료한 것으로 표시하지 않는다. 파일 선택기가 없는 Python에서는 명령줄 인수로 경로를 전달한다.

## 보관과 실패 처리

성공하면 매번 새 폴더에 `assignment.pdf`, `baseline.pdf`, `instructor-only/manifest.json`을 남긴다. 함수 별칭 `paint_stairs`는 고정값이고 `probe_…`는 실행마다 바뀐다. 실제 사용한 PDF와 같은 폴더의 manifest로 검사해야 한다. 성공한 폴더만 `output/LATEST`에 기록된다.

현재 후처리는 마지막 페이지의 빈 공간을 요구하지 않는다. 페이지 수가 늘거나 하단에 원문이 있어도 모든 픽셀이 같은지 검사한다. 회전·좌표 오프셋·암호화 PDF, 이미지뿐인 PDF, 해석할 수 없는 대상 글꼴, 필수 함수명이 없는 다른 과제는 자동 보정하지 않고 중단할 수 있다.

과거 실험은 다음처럼 명시적으로 실행한다. 가시적 예시나 규칙 변경이 포함될 수 있으므로 현재 배포본과 구별해야 한다. 글꼴 교체 옵션도 이 실험 경로에서만 허용한다.

```bash
./PDF만들기.command '/경로/과제.pdf' --experimental --profiles multi-signal
./run.sh legacy build '/경로/과제.pdf' --experimental --profiles native-alias
```

PDF 생성과 Git 저장은 AI 호출을 포함하지 않는다. 별도 모델 검증 명령 또는 웹 업로드를 실행해야 해당 제공자에게 과제가 전달된다.
