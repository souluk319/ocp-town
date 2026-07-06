# OCP Town OC

Gemma 12B를 OpenShift 인프라 안에 사는 "OCP 주민"으로 굴리는 학습용 대화 봇 뼈대.

목표는 Gemma를 GPT 대체재로 쓰는 것이 아니라, OpenShift 개념을 생활 세계관으로 계속 재번역해주는 로컬 상주 학습 동료로 쓰는 것이다.

## Roles

- Sung-uk: 학습자이자 OCP Town의 외부 지구인
- Gemma 12B: OpenShift 클러스터 안에 사는 주민
- Michael / GPT: 실제 개념, 명령어, 장애 분석을 검증하는 고성능 검증자

## MVP Flow

```text
Discord #ocp-town
  -> Python bot
  -> Ollama Gemma 12B
  -> prompts/ocp-resident.md
  -> data/memory.jsonl
```

Telegram도 같은 `ocp-town` 프로세스에서 long-polling 방식으로 같이 붙일 수 있다.
SWEET12와 같은 Tailscale tailnet 안에서 Ollama를 직접 열어둔 경우에는 Ollama Tailscale IP를 쓴다.

```env
OCP_TOWN_LLM_BACKEND=ollama
OLLAMA_HOST=http://100.99.152.52:11434
OLLAMA_MODEL=gemma4:12b-it-qat
```

KUGNUS 게이트웨이처럼 OpenAI 호환 `/v1/chat/completions` endpoint를 쓰는 경우에는 gateway backend를 쓴다.

```env
OCP_TOWN_LLM_BACKEND=openai
KUGNUS_GATEWAY_BASE_URL=http://gateway-host:port
KUGNUS_GATEWAY_API_KEY=replace-with-api-key-if-required
KUGNUS_GATEWAY_MODEL=gemma4:12b-it-qat
```

## For Codex / Agents

If another coding agent is helping, read these first:

- `AGENTS.md`
- `docs/codex-brief.md`
- `prompts/ocp-resident.md`

The key requirement is a three-party learning environment, not a generic bot:

```text
Sung-uk learns OCP
  <-> Gemma 4 12B plays an OCP resident through Discord
  <-> Michael/GPT verifies facts, commands, and design decisions
```

## Quickstart

1. Ollama에서 Gemma 모델을 준비한다.

```bash
ollama pull gemma4:12b-it-qat
```

2. Python 환경을 만든다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

3. 환경 파일을 만든다.

```bash
cp .env.example .env
```

`.env`에는 실제 Gemma 주민용 Discord bot token과 채널 ID를 넣는다. 토큰 값은 커밋하거나 공유하지 않는다.

4. 봇을 실행한다.

먼저 안전 점검을 할 수 있다. 이 명령은 토큰이나 `.env` 값을 출력하지 않는다.

```bash
ocp-town-check
```

더 자세한 진단은 doctor를 쓴다. Discord 토큰, 채널 ID 형식, Ollama 연결, 모델 존재 여부를 확인한다.

```bash
ocp-town-doctor
ocp-town-doctor --chat
```

문제가 없으면 봇을 실행한다. Telegram token도 설정되어 있으면 같은 명령에서 Telegram도 같이 켜진다.

```bash
ocp-town
```

Telegram만 따로 디버깅하려면:

```bash
ocp-town-telegram
```

현재 개발 순서는 다음이 좋다.

1. `ocp-town-check`로 Ollama와 프롬프트 경로를 확인한다.
2. `ocp-town-doctor`로 Discord 설정까지 확인한다.
3. `OCP_TOWN_DISCORD_BOT_TOKEN`을 넣은 뒤 `ocp-town`을 실행한다.
4. Discord 채널에서 Gemma 주민 응답을 확인한다.

## Environment

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `OCP_TOWN_DISCORD_BOT_TOKEN` | yes | | Gemma 주민용 Discord bot token |
| `OCP_TOWN_DISCORD_CHANNEL_ID` | no | | 지정하면 해당 채널에서만 반응 |
| `OCP_TOWN_REQUIRE_MENTION` | no | `false` | `true`면 봇이 멘션된 메시지에만 반응 |
| `OCP_TOWN_TELEGRAM_BOT_TOKEN` | no | | Telegram BotFather token |
| `OCP_TOWN_TELEGRAM_CHAT_ID` | no | | 지정하면 해당 chat에서만 반응 |
| `OCP_TOWN_TELEGRAM_REQUIRE_MENTION` | no | `false` | 그룹에서 `@botname` 멘션된 메시지에만 반응 |
| `OCP_TOWN_LLM_BACKEND` | no | `ollama` | `ollama`, SWEET12 legacy gateway용 `home-server`, OpenAI 호환 gateway용 `openai` |
| `OCP_TOWN_HOME_SERVER_BASE_URL` | no | | `home-server` 또는 `openai` backend일 때 base URL |
| `OCP_TOWN_HOME_SERVER_API_KEY` | no | | 게이트웨이에 API key를 걸었을 때만 설정 |
| `KUGNUS_GATEWAY_BASE_URL` | no | | OpenAI 호환 gateway base URL. 설정되면 `OCP_TOWN_HOME_SERVER_BASE_URL`보다 우선 |
| `KUGNUS_GATEWAY_API_KEY` | no | | OpenAI 호환 gateway API key. 설정되면 `OCP_TOWN_HOME_SERVER_API_KEY`보다 우선 |
| `KUGNUS_GATEWAY_MODEL` | no | `gemma4:12b-it-qat` | OpenAI 호환 gateway에 전달할 model alias |
| `OLLAMA_HOST` | no | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | no | `gemma4:12b-it-qat` | 사용할 로컬 모델 |
| `LLM_BASE_URL` | no | | `OLLAMA_HOST`가 없을 때 쓰는 호환 alias |
| `LLM_MODEL` | no | | `OLLAMA_MODEL`이 없을 때 쓰는 호환 alias |
| `OCP_TOWN_OLLAMA_NUM_PREDICT` | no | `320` | 답변 최대 생성량. 낮추면 빠르고 짧아짐 |
| `OCP_TOWN_OLLAMA_TEMPERATURE` | no | `0.35` | 답변 변동성. 낮을수록 덜 샘 |
| `OCP_TOWN_MEMORY` | no | `data/memory.jsonl` | 대화 메모리 파일 |
| `OCP_TOWN_PROMPT` | no | `prompts/ocp-resident.md` | 주민 페르소나 프롬프트 |

## Interaction

- 일반 메시지: Gemma OCP 주민이 생활 비유와 실제 OCP 개념을 같이 답한다.
- `@Michael`, `검증`, `실제 명령어` 같은 말이 나오면 지금은 Gemma가 검증 요청을 권한다.
- 다음 단계에서 OpenClaw/Michael 자동 라우팅을 붙일 수 있다.

## OpenClaw

OpenClaw 봇과 Gemma 주민 봇은 Discord 애플리케이션/봇을 분리하는 구성이 안전하다.
권장 구성은 `#ocp-town`은 Gemma 주민 봇, `#michael-review`는 OpenClaw 검증자로 나누는 것이다.
자세한 설정은 [Discord + OpenClaw + Gemma 12B Setup](docs/setup-discord-openclaw-gemma.md)을 본다.

다음 개발 아이디어는 [OCP Town Next Ideas](docs/ocp-town-next-ideas.md)에 모아둔다.

## Safety

- Gemma는 모르는 내용을 지어내지 않고 확인 절차를 제안해야 한다.
- 실제 클러스터 변경 명령은 자동 실행하지 않는다.
- 토큰, kubeconfig, Secret 값은 대화 로그에 저장하지 않는다.
