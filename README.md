# 마음 곁에 (Maeum Gyeote) — 다중 페르소나 상담 챗봇 데모

> A multi-persona counseling chatbot demo (Korean).
> Five clinically-inspired personas (Rogerian listening, CBT, MI, bereavement, crisis)
> routed dynamically through Claude Sonnet via the Claude Code CLI.
> Built as the companion artifact for the AI Ethics report *"The Empathy of a Thin Agent"* (2026).

본 보고서 「얇은 행위자의 공감」이 제안한 다섯 페르소나(일상 청취·인지 행동·동기 강화·사별 동행·위기 연계)를
실제로 작동하는 챗봇으로 구현한 데모.

- **License:** MIT (see `LICENSE`)
- **Stack:** Python 3 · Flask · Claude Code CLI (`claude -p`, Sonnet) · Vanilla HTML/CSS/JS

**아키텍처:**

```
브라우저 (HTML)
    ↓ fetch /api/chat
Flask 서버 (chat_app.py)
    ↓ subprocess
claude -p (Claude Code CLI)
    ↓
Claude Sonnet
```

각 페르소나는 본 보고서 3장에서 정의한 응답 규범을 따르는 별도의 시스템 프롬프트를 갖는다.

---

## 사전 준비

1. **Claude Code CLI 설치** ― `claude` 명령이 PATH에 있어야 함.
   미설치 상태라면 https://claude.com/code 참고.
2. **Claude Code 로그인 완료** ― 터미널에서 `claude` 한 번 실행해 로그인되어 있는지 확인.
3. **Python 3 + Flask** ― `pip install flask`

---

## 실행

```bash
cd 페르소나_챗봇_데모
python chat_app.py
```

콘솔에 다음 안내가 뜬다.

```
============================================================
  다중 페르소나 상담 챗봇 데모
============================================================
  접속: http://localhost:5050
  종료: Ctrl+C
============================================================
```

브라우저에서 `http://localhost:5050` 접속.

---

## 사용 흐름

1. **페르소나 선택 화면**에서 5개 카드 중 하나를 클릭
   - 🌿 일상 청취 — 무비판적 청취가 필요할 때
   - 💭 인지 행동 — 부정적 생각의 패턴을 들여다보고 싶을 때
   - 🌟 동기 강화 — 변화에 대한 양가감정이 있을 때
   - 🕊️ 사별 동행 — 상실을 경험한 직후
   - 🤝 위기 연계 — 자해·자살 사고가 있을 때 (인간 자원 연계 우선)

2. **채팅 화면**에서 메시지 입력 → Enter (Shift+Enter는 줄바꿈)

3. 상단 우측 **↻ 페르소나 바꾸기** 버튼으로 언제든 다른 페르소나로 전환 가능

---

## 구성 파일

| 파일 | 역할 |
|---|---|
| `chat_app.py` | Flask 서버 + 페르소나별 시스템 프롬프트 + claude -p 서브프로세스 호출 |
| `chat_app.html` | 단일 파일 프런트엔드 (HTML/CSS/JS, 외부 의존 없음) |
| `README.md` | 본 문서 |

---

## 페르소나별 시스템 프롬프트 핵심

| 페르소나 | 핵심 원칙 | 응답 톤 |
|---|---|---|
| 일상 청취 | Rogers UPR, 거울처럼 비춤, 조언 최소화 | 짧고 따뜻하게 (2~3문장) |
| 인지 행동 | 인지 왜곡 부드러운 식별, 소크라테스적 질문 | 부드러운 직면 (3~4문장) |
| 동기 강화 | OARS, 양가성 인정, 자율성 존중 | 압박 없는 유도 (3~4문장) |
| 사별 동행 | Worden 사별 과제, 상투적 위로 금지, 그리프봇 윤리 | 여백 있는 짧은 응답 |
| 위기 연계 | 1393 / 1577-0199 즉시 안내, AI 한계 명시 | 침착하고 분명하게 |

전체 시스템 프롬프트는 `chat_app.py` 상단 `PERSONAS` 딕셔너리에서 확인·수정 가능.

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| "`claude` 명령을 찾을 수 없어요" | Claude Code CLI 미설치. `which claude` 로 확인 |
| 응답이 안 옴 / 타임아웃 | `claude` 명령으로 직접 한 번 테스트. 로그인 만료일 수 있음 |
| 포트 충돌 | `chat_app.py` 마지막 줄의 `port=5050` 다른 값으로 변경 |
| 한글 깨짐 | 브라우저는 영향 없음. 터미널 출력은 `LANG=ko_KR.UTF-8` 설정 권장 |

---

## GitHub에 올리기 (gh CLI 사용)

[GitHub CLI(`gh`)](https://cli.github.com/)가 설치되어 있다면 한 번에 처리할 수 있다.

```bash
cd 페르소나_챗봇_데모

# (선택) 이전에 시도한 .git 흔적이 있다면 깨끗이 시작:
rm -rf .git

# 한 번에 (가장 간단):
./setup_repo.sh

# 또는 수동:
git init -b main
git add -A
git commit -m "Initial commit: 마음 곁에 챗봇 데모"
gh auth login                                            # 처음 한 번만
gh repo create maeum-gyeote-chatbot --public --source=. --remote=origin --push
```

`gh repo create` 옵션 의미:
- `--public` — 공개 저장소 (비공개로 만들려면 `--private`)
- `--source=.` — 현재 폴더를 소스로
- `--remote=origin` — `origin` 이름으로 리모트 자동 연결
- `--push` — 생성 직후 첫 커밋 자동 푸시

### `.gitignore`로 보호되는 항목

이미 제외되어 있으므로 안심하고 푸시 가능하다.

- `__pycache__/`, `.venv/` 등 빌드·환경 파일
- `.env`, `*.key`, `*.pem` 등 비밀
- `.claude/`, `.anthropic/` 등 Claude Code CLI의 로컬 상태
- `data/`, `responses/`, `*.csv` 등 사용자 응답 데이터 (샘플은 `sample_*.csv` 형태로만 허용)

### 푸시 전 마지막 점검

```bash
git status                                    # 추적되는 파일 확인
grep -rE "(API_KEY|SECRET|PASSWORD|TOKEN)" .  # 비밀 문자열이 남아 있지 않은지 확인
```

---

## 윤리적 사용 안내

본 데모는 보고서의 다중 페르소나 아키텍처를 시연하기 위한 학술 목적의 산출물이다.
다음을 반드시 인식한 상태에서 사용해야 한다.

- 이 챗봇은 **전문 상담을 대체하지 않는다**. 임상적 도움이 필요하면 전문가를 찾아야 한다.
- 위급한 상황에서는 즉시 **자살예방상담전화 1393** 또는 **정신건강위기상담전화 1577-0199**로 연락한다.
- 응답은 Claude Sonnet의 통계적 산출이며, *진심*이 아니라 *모델의 통계*이다.
- 대화 내용은 Claude Code CLI를 통해 Anthropic 서버로 전송된다. 민감한 개인 정보 입력은 신중히.
- 미성년자의 사용은 보호자 동의 하에서만 권장된다.
