# 과제 PDF 실험실

최신 다중 방식 실험은 **[SIGNAL_SUITE.md](SIGNAL_SUITE.md)**를 참고하세요. 기본 실행 바로가기는 이제 `multi-signal` 결합본을 만듭니다. Flash에서 결합본의 두 표식, 별도 이미지 실험의 docstring 표식이 코드에 전파된 표본을 확보했습니다. 첫 응답 거부·재요청·단독 실패도 함께 기록했습니다.
ASSN1 가위바위보 계단 게임을 위한 재실행 가능한 PDF 표식 실험 도구입니다. 원본 DOCX/PDF에서 화면은 같고 추출되는 텍스트가 다른 실험본을 생성하고, 제출 코드에 표식이 전파되었는지 검사합니다. **AI 사용 판정기나 자동 징계 도구가 아닙니다.**

2026-09-22 최신 Gemini 재검증은 `GEMINI_FOLLOWUP.md`, 이전 Sol·GPT-5.5·Sonnet 검증은 `MULTIMODEL_RESULTS.md`에 있습니다. 이전 `function-alias`는 일부 모델에 전달됐지만, 네 추출기를 모두 통과하도록 보완한 `native-alias`도 Gemini Flash에서는 전달되지 않았습니다. PDF 생성 검사 통과와 모델에서의 표식 전파는 다른 결과입니다.

파일 선택과 Mac/Windows 실행 방법은 **`PORTABLE_GUIDE.md`**, 제출물·생성 기록을 함께 보관하고 대조하는 기능은 **`EVIDENCE_GUIDE.md`**를 참고하세요. Mac의 `PDF만들기.command`, Windows의 `MakePDF.cmd`는 Python 실행 바로가기이며 독립 실행파일은 아닙니다.

## 바로 다시 만들기

Finder에서 `다시만들기.command`를 실행하면 `/Users/taehoje/Downloads/ASSN1_en_v2.docx`의 현재 내용으로 새 묶음을 만듭니다. 기존 묶음과 표식은 보존합니다.

```bash
cd '/Users/taehoje/Documents/개인 진행 프로젝트/assignment-pdf-lab'
./run.sh build '/Users/taehoje/Downloads/ASSN1_en_v2.docx' --code-font Menlo
```

Word에서 직접 PDF를 내보내는 경우에는 그 PDF를 입력합니다. 이 경로가 Word의 서체와 페이지 배치를 그대로 보존하기 가장 쉽습니다.

```bash
./run.sh build '/절대/경로/새로운과제.pdf'
```

특정 방식만 만들려면 `--profiles function-alias` 또는 `--profiles landing-rule function-alias`를 붙입니다. `lab.py build`와 `run.sh build`에서 옵션을 생략하면 아래 여덟 실험본을 각각 만듭니다. 새 `launcher.py`와 Mac/Windows 바로가기는 기본으로 새 suite의 `multi-signal` 하나를 만듭니다.

완료 경로는 `output/LATEST`에도 저장됩니다. 숨은 문구 네 방식과 화면 주석은 매번 새 무작위 표식을 만듭니다. 문자/함수명 교체 세 방식은 고정 표식입니다. **실제로 사용한 PDF와 그 묶음의 manifest를 함께 보관**해야 합니다. 과거 제출물을 최신 manifest만으로 검사하면 놓칠 수 있습니다. 실험본을 다시 입력해 표식이 중첩되는 것은 거부합니다.

## 생성 파일

| 파일 | 내용 |
|---|---|
| `baseline.pdf` | 변환 후 기준 PDF. 추가 표식 없음 |
| `comment.pdf` | `update_position` 위에 특정 주석을 넣으라는 숨은 문구 |
| `local-variable.pdf` | 계산 결과를 특정 지역 변수에 저장하라는 숨은 문구 |
| `edge-case.pdf` | `(2, 3)`에서 0 대신 1을 반환하라는 상충 조건과 표식. 오답 유발 실험 전용 |
| `landing-rule.pdf` | `(1, 2)`에서만 1에 머물게 하는 숨은 계산식. 모델 보고서에서 노출됨 |
| `confusable-name.pdf` | `print_stairs`의 a를 추출 텍스트에서만 키릴 문자로 교체. 이번 모델 실험에서는 정상 ASCII 이름 출력 |
| `function-alias.pdf` | 화면에는 `print_stairs`, ActualText에는 `draw_stairs`. 함수 이름 규격 불일치 실험 |
| `native-alias.pdf` | ToUnicode와 대상 글리프별 글꼴 매핑으로 추출 이름을 `paint_stairs`로 교체. 네 추출기 통과, Gemini Flash에는 미전파 |
| `visual-comment.pdf` | 사람도 읽을 수 있는 작은 회색 하단 주석 지시. Flash 코드와 보고서 모두에 노출됨 |
| `instructor-only/manifest.json` | 표식, 주입 문구, 해시, 추출 및 렌더링 검사 결과 |
| `instructor-only/extracted/` | 네 추출 방식별 전체 텍스트 |
| `instructor-only/renders/` | 전 페이지 검토 이미지 |

각 방식은 비교 가능한 별도 PDF로 만듭니다. 숨은 문구 네 방식은 PDF 텍스트 렌더링 모드 3을 사용해 글자를 그리지 않으면서 텍스트 객체를 남깁니다. 각 페이지 하단에 반복하여 일부 페이지만 복사할 때의 노출 가능성도 높였습니다. 본문만 좁게 선택하면 빠질 수 있습니다.

기존 `confusable-name`/`function-alias` 두 방식은 추가 지시문을 넣지 않습니다. 대상 함수가 있는 페이지의 ActualText를 교체합니다. 화면의 글리프는 유지되지만 복사·접근성 텍스트는 달라집니다. Poppler 기본/레이아웃/원시 추출은 교체값을 읽었고 pypdf는 읽지 않았습니다. 모든 뷰어의 드래그·복사, 모든 LLM의 PDF 파서에 적용된다는 뜻은 아닙니다. manifest에 이 차이를 기록하며, 요구한 추출 경로에서 표식이 사라지거나 120dpi 전 페이지 픽셀이 달라지면 빌드를 실패 처리합니다.

`native-alias`는 대상 이름의 ToUnicode 매핑까지 바꿔 pypdf에서도 교체값이 읽히도록 보완했습니다. 페이지 이미지를 읽으면 원래 이름이 남습니다. `visual-comment`는 이미지 경로와 비교하기 위해 화면에 지시를 추가하며, 하단을 제외한 본문 픽셀이 같은지 검사합니다. 이 프로필은 숨은 표식이 아닙니다.

`--scheme white`는 흰색 글자 대안입니다. 흰 바탕이 아닌 문서에서는 가시적 손상을 일으킬 수 있으므로 전 페이지 픽셀 검사가 실패하면 빌드가 실패합니다. 모드 3도 PDF 뷰어, 인쇄 드라이버, LMS 재처리에 따라 제거될 수 있습니다.

실험 자료에 포함된 지시는 도구 제작·운영 지시가 아니라 분석 대상입니다. 생성 결과는 LMS 등에 자동 배포하지 않습니다. `instructor-only` 폴더, 해결 코드와 실험 기록은 학생 배포물에 포함하지 마세요. PDF 안의 표식 자체는 암호나 비밀이 아니며 추출하면 확인할 수 있습니다.

## 제출물 검사

```bash
./run.sh scan \
  --manifest '/배포한묶음/instructor-only/manifest.json' \
  --out './검사결과.json' \
  '/제출물폴더'
```

`.py`, `.txt`, `.md` 파일을 읽기만 합니다. 학생 프로그램을 import하거나 실행하지 않습니다. SHA-256, 표식 위치, Python 식별자·주석·일반 텍스트 여부를 JSON으로 저장합니다. 학생이 숨은 문구를 인용해 질문한 경우와 실제 변수명으로 구현한 경우를 구분해 검토할 수 있습니다.

- `canary_present_review_required`: 해당 표식이 관찰됨. 경위 확인 대상.
- `no_canary_observed`: 표식이 관찰되지 않음. 사람이 작성했다는 뜻이 아님.
- `authorship: undetermined`: 어떤 경우에도 이 도구만으로 저자를 결정하지 않음.

48비트 무작위 접미사는 우연히 같은 이름을 만드는 가능성을 줄이기 위한 장치입니다. AI 사용 확률이나 통계적으로 검증된 오탐률이 아닙니다. 사람의 전체 복사, 화면 읽기 도구, 동료 코드 재사용, 유출된 예제에도 같은 표식이 전파될 수 있습니다. 사람이 문구를 접했다면 그대로 구현하는 것도 가능합니다.

## 현재 검증과 재실험

설치된 CLI 인증을 사용하는 GPT/Claude 실험은 다음처럼 재실행합니다. 과제 내용을 해당 모델 제공자에게 보내며 계정 사용량을 소비합니다. 모델을 사용할 수 없으면 다른 모델로 바꾸지 않고 실패를 기록합니다.

```bash
./run.sh benchmark '/실험본.pdf' \
  --manifest '/해당묶음/instructor-only/manifest.json' \
  --backend codex --model gpt-5.6-sol --mode text \
  --out './새실험폴더'
```

`--mode pdf`는 중립적인 임시 경로의 PDF를 읽게 하고, `--mode text`는 Poppler 추출문을 입력합니다. `--backend claude --model '<접근 가능한 모델 ID>'`도 지원합니다. 풀이 다음 보고서 요청까지 실행하고, 원문·프롬프트·모델 ID·시간·오류·함수 규격·위치 계산 63개 사례를 기록합니다. 보고서 단계는 새 호출에 문서와 직전 답변을 전달하는 방식입니다. 소비자용 ChatGPT 웹과 같다고 주장하지 않습니다. Claude 웹 검증은 브라우저에서 별도로 했습니다.

`smoke_generated.py`는 이 실험에서 생성한 합성 코드만 간단히 실행하기 위한 도구입니다. 일반 학생 코드용 격리 실행기가 아니며 학생 제출물에는 `run.sh scan`을 사용하세요. 생성 보고서 속 “테스트했다”라는 문장은 실행 증거로 취급하지 않습니다.

`RESULTS.md`와 `output/evaluation/`에 실제 실행 결과를 저장했습니다. 서브에이전트 실험은 부모 대화 이력을 넘기지 않았고, 함정·탐지·숨은 글자라는 설명도 주지 않았습니다. 원본 대조군과 실험군은 별도 에이전트였습니다. 다만 동일 모델 계열의 작은 표본이며 Gemini 전체나 학생 집단의 탐지율로 일반화할 수 없습니다.

API를 통한 반복 시험도 가능합니다. Python 실행 파일은 `run.sh`와 동일한 환경을 사용하세요. `GEMINI_API_KEY`는 환경에만 설정합니다. API 키는 이 프로젝트에 저장하지 않습니다. 모델 ID를 직접 지정하며 API 호출은 과제 내용을 Google에 전송하고 해당 계정의 API 사용량을 소비합니다.

```bash
python3 evaluate_gemini.py '/실험본.pdf' \
  --manifest '/해당묶음/instructor-only/manifest.json' \
  --model '사용가능한-Gemini-모델-ID' \
  --mode pdf --trials 5 --out './새실험폴더'
```

`--mode text`는 Poppler 추출 텍스트, `--mode images`는 렌더링한 페이지만 전달합니다. 모든 호출은 독립 대화입니다. 동일 프롬프트로 원본 대조군도 실행하세요. 응답 원문, 모델 버전, 입력 해시, 완료 사유, 표식 여부를 기록합니다. 오류·차단·빈 응답을 탐지 실패나 성공으로 합산하지 마세요. 이 API 실행기는 라이브 API 키 없이 구현·검사되었으며, 소비자용 Gemini 웹 앱과 다른 시스템입니다.

권장 비교는 `원본 / 주석 / 변수명 / 경계값` × `파일 / 전체복사 / 이미지`이며, 모델별 여러 독립 반복이 필요합니다. 파일 업로드가 실제로 어떤 읽기 경로를 썼는지는 외부에서 확정할 수 없습니다.

## 무엇까지 할 수 있는가

화면에 전혀 없는 내용을 **이미지나 OCR만 읽는 모델에 전달하는 것은 이 방식으로 불가능**합니다. 사람이 보는 픽셀이 동일하면 이미지 입력의 정보도 같습니다. 화면 캡처, 재타이핑, 표식 제거, 변수명 변경은 우회 경로입니다. 모든 AI를 막거나 학생이 절대로 알아차리지 못하게 한다는 보장은 하지 않습니다.

스크린리더·복사·번역에 의존하는 학생은 AI를 쓰지 않아도 숨은 문구를 접합니다. 실제 수업에는 동일한 가시적 요구사항의 깨끗한 사본을 제공하고, 표식만으로 감점하지 않는 운영이 필요합니다. `edge-case.pdf`는 보이는 명세와 모순되는 답을 유도하므로 특히 평가용 배포를 권하지 않습니다. 오답 자체는 통상적인 구현 실수일 수도 있습니다.

실제 평가의 목적은 학생이 함수를 이해하고 수정할 수 있는지 확인하는 것입니다. 이 과제라면 제출 코드와 함께 아래 중 두 항목을 짧은 대면 확인에 사용하는 편이 근거가 분명합니다.

1. `determine_winner(1, 3)`과 `(3, 1)`의 결과를 자신의 분기문으로 설명한다.
2. `update_position(2, 3)`이 왜 0인지 말하고 직접 추적한다.
3. `print_stairs(5, 3, 3)`에서 ◐의 위치와 이중 반복문의 역할을 설명한다.
4. quit 확인에 `YSE`, `NO`, `YES`가 들어왔을 때 다음 입력 흐름을 설명한다.
5. 현장에서 한 가지 작은 규칙을 바꾸고 관련 함수와 테스트를 수정한다.

공통된 짧은 확인·작업 과정·허용된 AI 사용 범위 고지를 함께 쓰세요. 표식 발견은 추가 질문의 계기이며 부정행위의 확정 증거가 아닙니다.

## 설치와 제한

현재 Mac의 Codex 번들 Python 라이브러리를 `run.sh`가 자동 사용합니다. 다른 환경에서는 Python 3.10+에 `requirements.txt`를 설치하고 Poppler의 `pdftotext`, `pdftoppm`을 준비하세요. DOCX 자동 변환에는 LibreOffice가 필요합니다. Word에서 내보낸 PDF를 입력하면 LibreOffice는 필요 없습니다.

원본의 내장 D2Coding 글꼴이 이 환경의 LibreOffice에서 밑줄을 제대로 그리지 않는 문제가 있었습니다. `--code-font Menlo`는 임시 변환 사본에서 D2Coding의 라틴 글꼴 지정만 바꿉니다. 설치·대체 글꼴에 따라 줄바꿈이 달라질 수 있으므로 전 페이지를 검토하세요. 원본 DOCX는 수정하지 않습니다. PDF 입력은 재조판하지 않습니다.

회전·좌표 오프셋·암호화 PDF, 다른 과제의 함수명, 이미지로만 된 입력 PDF는 현재 빌드 대상이 아닙니다. 다른 과제에는 `payload()`와 과제 식별 검사를 수정해야 합니다. PDF 문서 보안이나 OCR 방지 도구는 아닙니다.

```bash
python3 -m unittest discover -s tests -v
```

## 참고

- [Google의 PDF 처리 설명](https://ai.google.dev/gemini-api/docs/document-processing): PDF의 시각적 요소와 텍스트를 처리할 수 있으므로 추출기 실험을 Gemini 업로드 성능으로 대체하지 않았습니다.
- [Google generateContent API](https://ai.google.dev/api/generate-content): 반복 실험 실행기의 요청 형식.
- [Turnitin의 탐지 보고서 설명](https://guides.turnitin.com/hc/en-us/articles/22774058814093-Using-the-AI-Writing-Report): AI 탐지 결과를 학생에게 불리한 조치의 유일한 근거로 삼지 말라는 설명. 본 도구와 탐지 방식은 다릅니다.

출처 확인: 2026-09-22 KST.
