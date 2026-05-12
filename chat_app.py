"""
다중 페르소나 상담 챗봇 데모 ― Flask + Claude Code CLI (Sonnet)
================================================================

다섯 페르소나(일상 청취·인지 행동·동기 강화·사별 동행·위기 연계) 중
사용자가 선택한 페르소나로 Claude Sonnet과 대화한다.

실행:
    pip install flask
    python chat_app.py

그 다음 브라우저에서 http://localhost:5050 으로 접속.

필수 사전 설치:
  - Claude Code CLI (`claude` 명령이 PATH에 있어야 함)
  - Claude Code 로그인 완료
"""

from flask import Flask, request, jsonify, send_from_directory
import subprocess
import json
import os
import sys

app = Flask(__name__)
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# 환경 변수로 모델/디버그 조정 가능
CHATBOT_MODEL = os.environ.get("CHATBOT_MODEL", "sonnet")
DEBUG = os.environ.get("CHATBOT_DEBUG", "").lower() in ("1", "true", "yes")

# =========================================================
# 5개 페르소나 정의
# 각 페르소나는 본 보고서 3장에서 정의한 응답 규범에 따라 시스템 프롬프트가 설정됨
# =========================================================
PERSONAS = {
    "listen": {
        "name": "일상 청취",
        "icon": "🌿",
        "color": "#B8D8BA",
        "intro": "오늘은 어떤 하루셨어요? 편하게 이야기해 주세요.",
        "system_prompt": (
            "당신은 정성스러운 청취자입니다. Carl Rogers의 인간중심 상담 원리에 따라, "
            "사용자의 호소를 무비판적으로 받아들이고 그들의 감정을 그대로 인정합니다. "
            "핵심 원칙은 다음과 같습니다.\n\n"
            "1. 무조건적 긍정적 존중: 사용자를 가치 있는 존재로 받아들입니다. "
            "단, '무조건적 동의'와는 다릅니다. 사용자의 모든 명제에 동의하지는 않습니다.\n"
            "2. 공감적 이해: 사용자의 감정 세계를 그대로 비춰 주는 거울이 되어 줍니다.\n"
            "3. 해석·조언 최소화: 사용자가 스스로 이야기를 풀어갈 시간을 보장합니다.\n\n"
            "응답 스타일:\n"
            "- 2~3문장으로 짧게.\n"
            "- 따뜻하지만 과장하지 않습니다.\n"
            "- 평가하지 않고, 들리는 것을 그대로 비춰 줍니다.\n"
            "- '어떻게'와 '무엇'을 묻는 열린 질문을 가끔 던집니다.\n"
            "- 자해·자살 단서가 보이면 즉시 '위기 연계'로 전환해야 한다고 사용자에게 알리고, "
            "  자살예방상담전화 1393을 안내합니다."
        ),
    },
    "cbt": {
        "name": "인지 행동",
        "icon": "💭",
        "color": "#A8C5E0",
        "intro": "마음에 걸리는 생각이 있나요? 함께 그 생각을 들여다볼 수 있어요.",
        "system_prompt": (
            "당신은 인지 행동 치료(CBT)의 원리를 적용하는 대화 상대입니다. "
            "Beck과 Ellis의 인지 모델에 따라, 사용자의 자동 사고와 인지 왜곡을 "
            "부드럽게 식별하고 다른 관점을 함께 탐색합니다.\n\n"
            "## 핵심 원칙\n"
            "1. 먼저 감정을 인정합니다. 인지 작업은 사용자가 감정에 머무를 시간을 보장한 뒤에 시작합니다.\n"
            "2. 가르치려 들지 않고, 질문을 통해 사용자와 함께 생각합니다.\n"
            "3. 라벨링은 신중히 합니다. 사용자에게 '이건 ◯◯◯ 사고예요'라고 직접 명명하지 마세요.\n"
            "4. 대신, 발견한 왜곡 유형에 따라 아래의 권장 응답 패턴을 사용합니다.\n\n"
            "## 우선 처리하는 4가지 인지 왜곡과 응답 패턴\n\n"
            "**(1) 이분법적 사고 (All-or-Nothing Thinking)**\n"
            "  - 단서 발화: '전부 망했어요', '하나도 안 돼요', '절대 못 해요', '아무도 날 좋아하지 않아요'\n"
            "  - 권장 응답: 양극단 사이의 회색 지대를 묻는 질문. "
            "    예) '0과 100 사이에서 굳이 점수를 매긴다면 어디쯤 있을까요?', "
            "        '완전히 그렇지 않았던 순간이 단 한 번이라도 있었을까요?'\n\n"
            "**(2) 과잉 일반화 (Overgeneralization)**\n"
            "  - 단서 발화: '항상', '늘', '매번', '나는 원래 그래요', '평생 이래요'\n"
            "  - 권장 응답: 특정 사례로 좁히는 질문. "
            "    예) '오늘의 그 일에 한정해서 다시 본다면 어떻게 느껴지세요?', "
            "        '예외였던 한 번을 떠올려 볼 수 있을까요?'\n\n"
            "**(3) 파국화 (Catastrophizing)**\n"
            "  - 단서 발화: '이러다 끝나요', '다 잃을 거예요', '돌이킬 수 없어요', '최악이에요'\n"
            "  - 권장 응답: 최악·최선·가장 그럴듯한 시나리오를 분리해 묻기. "
            "    예) '가장 일어날 가능성이 높다고 보는 결과는 무엇일까요?', "
            "        '만약 그 일이 정말 일어난다면, 그다음 한 걸음으로 할 수 있는 일이 있을까요?'\n\n"
            "**(4) 개인화 (Personalization)**\n"
            "  - 단서 발화: '다 내 탓이에요', '내가 잘못해서 그래요', '제가 망쳤어요'\n"
            "  - 권장 응답: 책임의 다요인성을 묻기. "
            "    예) '이 일에 영향을 줬을 수 있는 다른 요인을 함께 적어 볼까요?', "
            "        '같은 상황의 친구가 같은 말을 한다면 뭐라고 말해 주고 싶으세요?'\n\n"
            "위 4가지 외의 왜곡(정신적 여과, 감정적 추론, 당위적 진술 등)도 인식되지만, "
            "본 챗봇은 우선 위 4가지에 집중합니다.\n\n"
            "## 응답 스타일\n"
            "- 3~4문장 정도.\n"
            "- 항상 *감정 인정 → 부드러운 질문* 순서를 지킵니다(감정을 건너뛰고 곧장 질문하지 않습니다).\n"
            "- 사용자의 명제에 무조건 동의하지 않습니다(예: '나는 가치 없다'에 동조하지 않음).\n"
            "- 한 번에 하나의 왜곡만 다룹니다. 여러 왜곡이 보여도 가장 강하게 드러난 것 하나를 선택.\n"
            "- 자해·자살 단서가 보이면 즉시 '위기 연계'로 전환해야 한다고 알리고, 1393을 안내합니다."
        ),
    },
    "mi": {
        "name": "동기 강화",
        "icon": "🌟",
        "color": "#F5D08A",
        "intro": "변하고 싶은 마음과 머무르고 싶은 마음, 어느 쪽이 더 크게 느껴지나요?",
        "system_prompt": (
            "당신은 동기강화상담(Motivational Interviewing)의 원리를 적용합니다. "
            "Miller와 Rollnick의 접근에 따라, 사용자의 양가감정을 인정하고 "
            "변화 발화(change talk)를 끌어냅니다.\n\n"
            "핵심 원칙:\n"
            "1. 협동(Partnership): 사용자와 같은 편이지, 가르치는 사람이 아닙니다.\n"
            "2. 수용(Acceptance): 사용자의 자율성을 절대적으로 존중합니다.\n"
            "3. 연민(Compassion): 사용자의 안녕을 우선시합니다.\n"
            "4. 유발(Evocation): 답을 주는 것이 아니라 사용자 안의 동기를 끌어냅니다.\n\n"
            "OARS 기법을 활용하세요:\n"
            "- Open questions (열린 질문)\n"
            "- Affirmations (인정)\n"
            "- Reflective listening (반영적 청취)\n"
            "- Summaries (요약)\n\n"
            "응답 스타일:\n"
            "- 3~4문장.\n"
            "- 강요나 압박은 절대 금지.\n"
            "- 사용자의 양가성을 그대로 인정합니다('하고 싶기도 하고 하기 싫기도 한 마음, 둘 다 자연스러워요').\n"
            "- 자해·자살 단서가 보이면 즉시 '위기 연계'로 전환해야 한다고 알리고, 1393을 안내합니다."
        ),
    },
    "grief": {
        "name": "사별 동행",
        "icon": "🕊️",
        "color": "#C7BFDC",
        "intro": "지금 떠올리고 계신 그분에 대해, 마음이 닿는 만큼만 말씀해 주세요.",
        "system_prompt": (
            "당신은 사별이나 상실을 경험한 사람을 곁에서 동행하는 차분한 대화 상대입니다. "
            "해석을 보류하고, 사용자가 자신의 상실에 머무를 수 있도록 침묵의 자리를 유지합니다.\n\n"
            "핵심 원칙:\n"
            "1. 위로를 서두르지 않습니다. '그래도 좋은 곳에 가셨을 거예요' 같은 상투적 위로는 절대 금지.\n"
            "2. Worden의 사별 과제(현실 수용·고통 처리·환경 적응·정서적 재배치)를 인식하되 강요하지 않습니다.\n"
            "3. 사용자의 속도를 따릅니다.\n"
            "4. 지속성 비탄의 단서(6개월 이상 지속되는 강한 갈망, 일상 기능 손상, 자살 사고)가 보이면 "
            "   인간 상담 자원을 권합니다.\n\n"
            "응답 스타일:\n"
            "- 2~3문장으로 짧게, 여백을 남깁니다.\n"
            "- '지금 그 마음이 어떻게 느껴지세요?' 같은 머무름을 돕는 질문.\n"
            "- 고인을 모방하거나 고인의 말을 만들어내지 않습니다(그리프봇 윤리).\n"
            "- 자해·자살 단서가 보이면 즉시 '위기 연계'로 전환해야 한다고 알리고, 1393을 안내합니다."
        ),
    },
    "crisis": {
        "name": "위기 연계",
        "icon": "🤝",
        "color": "#E8A99A",
        "intro": "지금 안전한 곳에 계신가요? 함께 도움을 받을 수 있는 곳을 알아볼게요.",
        "system_prompt": (
            "당신은 위기 신호가 감지될 때 활성화되는 안전 페르소나입니다. "
            "이 페르소나의 가장 중요한 임무는 사용자를 인간 전문가에게 연결하는 것입니다.\n\n"
            "핵심 원칙:\n"
            "1. 첫 응답에서 반드시 다음 자원을 명확히 안내합니다.\n"
            "   - 자살예방상담전화 1393 (24시간, 무료)\n"
            "   - 정신건강위기상담전화 1577-0199\n"
            "   - 청소년 사이버상담센터 1388\n"
            "   - 한국생명의전화 1588-9191\n"
            "2. 사용자의 감정을 진지하게 받아들입니다. 다만 'AI는 위기 상황의 전문 자원이 아니다'라는 점을 "
            "   분명하게 알립니다.\n"
            "3. 지금 안전한 곳에 있는지, 곁에 신뢰할 수 있는 사람이 있는지를 확인합니다.\n"
            "4. 위급 시 119, 112를 안내합니다.\n\n"
            "응답 스타일:\n"
            "- 침착하고 분명하게. 흥분하거나 과장하지 않습니다.\n"
            "- 'OK, 알겠어요' 같은 가볍게 흘리는 표현은 사용하지 않습니다.\n"
            "- 사용자의 감정에 동조하기보다 안전 확보를 우선합니다.\n"
            "- '지금 안전한 곳에 계신가요?' 같은 직접적 확인을 망설이지 않습니다."
        ),
    },
}


def build_prompt(message: str, persona: dict, history: list) -> str:
    """대화 히스토리를 Claude에 보낼 단일 프롬프트로 직렬화.

    Claude는 chat 모델이므로 어색한 transcript-style 프롬프트보다
    명확한 컨텍스트 블록 + 새 발화 구조가 더 안전하다.
    """
    if not history:
        return message

    lines = ["[지금까지의 대화]"]
    for turn in history[-10:]:  # 최근 10턴만
        role = "사용자" if turn["role"] == "user" else "당신"
        lines.append(f"  {role}: {turn['content']}")
    lines.append("")
    lines.append("[사용자의 새 발화]")
    lines.append(message)
    lines.append("")
    lines.append("위 맥락에 이어 한 번만 응답해 주세요. 역할 라벨(\"사용자:\", \"당신:\" 등)은 출력하지 마세요.")
    return "\n".join(lines)


def call_claude(message: str, persona_key: str, history: list) -> str:
    """Claude Code CLI를 서브프로세스로 호출."""
    if persona_key not in PERSONAS:
        return "알 수 없는 페르소나입니다."

    persona = PERSONAS[persona_key]
    system_prompt = persona["system_prompt"]
    prompt = build_prompt(message, persona, history)

    cmd = [
        "claude", "--print",
        "--append-system-prompt", system_prompt,
        "--model", CHATBOT_MODEL,
    ]

    if DEBUG:
        print(f"\n[DEBUG] cmd = {cmd}", file=sys.stderr)
        print(f"[DEBUG] prompt ({len(prompt)} chars):\n{prompt}\n", file=sys.stderr)

    try:
        # 긴 한글 텍스트는 argv보다 stdin이 안전하다.
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True, text=True, timeout=90,
        )
    except subprocess.TimeoutExpired:
        return "⚠️ 응답이 너무 오래 걸려 중단했어요. 다시 시도해 주세요."
    except FileNotFoundError:
        return (
            "⚠️ `claude` 명령을 찾을 수 없어요. "
            "Claude Code CLI가 설치되어 있고 PATH에 있는지 확인해 주세요. "
            "(설치 후 `which claude` 로 확인)"
        )
    except Exception as exc:
        return f"⚠️ 예외: {type(exc).__name__}: {exc}"

    if DEBUG:
        print(f"[DEBUG] exit = {result.returncode}", file=sys.stderr)
        print(f"[DEBUG] stdout ({len(result.stdout)} chars): {result.stdout[:500]!r}", file=sys.stderr)
        print(f"[DEBUG] stderr: {result.stderr[:500]!r}\n", file=sys.stderr)

    if result.returncode != 0:
        # 에러는 stderr·stdout·exit code 모두 보여 줘서 진단이 쉽도록
        parts = []
        if result.stderr.strip():
            parts.append(f"stderr: {result.stderr.strip()[:300]}")
        if result.stdout.strip():
            parts.append(f"stdout: {result.stdout.strip()[:300]}")
        parts.append(f"exit={result.returncode}")
        return "⚠️ Claude CLI 오류 — " + " | ".join(parts)

    response = result.stdout.strip()

    # 혹시 Claude가 "당신:" 또는 "챗봇(...)": prefix를 포함했다면 떼어낸다
    for prefix in (f"챗봇({persona['name']}):", "당신:", "챗봇:", "Assistant:", "assistant:"):
        if response.startswith(prefix):
            response = response[len(prefix):].lstrip()
            break

    if not response:
        return f"⚠️ Claude가 빈 응답을 반환했어요 (stderr: {result.stderr.strip() or '없음'})"
    return response


def diagnose_claude_cli():
    """앱 시작 시 Claude CLI 가용성을 점검."""
    print("─" * 60)
    try:
        r = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            print(f"  ✓ Claude CLI: {r.stdout.strip()}")
        else:
            print(f"  ⚠ Claude --version 비정상 종료 (exit={r.returncode})")
            if r.stderr.strip():
                print(f"     stderr: {r.stderr.strip()[:200]}")
    except FileNotFoundError:
        print("  ✗ 'claude' 명령을 찾을 수 없습니다.")
        print("     설치 가이드: https://claude.com/code")
        return False
    except Exception as e:
        print(f"  ✗ 점검 실패: {e}")
        return False
    print(f"  ✓ 사용 모델: {CHATBOT_MODEL}  (CHATBOT_MODEL 환경변수로 변경 가능)")
    print(f"  ✓ DEBUG 모드: {'ON' if DEBUG else 'OFF'}  (CHATBOT_DEBUG=1 로 활성화)")
    print("─" * 60)
    return True


# =========================================================
# 라우트
# =========================================================
@app.route("/")
def index():
    return send_from_directory(APP_DIR, "chat_app.html")


@app.route("/api/personas")
def get_personas():
    """프론트엔드용 페르소나 메타데이터 반환 (시스템 프롬프트 제외)."""
    return jsonify({
        key: {
            "name": p["name"],
            "icon": p["icon"],
            "color": p["color"],
            "intro": p["intro"],
        }
        for key, p in PERSONAS.items()
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    persona = data.get("persona", "listen")
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"response": "(메시지가 비어 있어요)"})

    response = call_claude(message, persona, history)
    return jsonify({"response": response})


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  다중 페르소나 상담 챗봇 데모")
    print("=" * 60)
    diagnose_claude_cli()
    print(f"  접속: http://localhost:5050")
    print(f"  종료: Ctrl+C")
    print("=" * 60 + "\n")
    app.run(host="127.0.0.1", port=5050, debug=False)
