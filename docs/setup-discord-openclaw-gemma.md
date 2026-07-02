# Discord + OpenClaw + Gemma 12B Setup

이 문서는 OCP Town을 Discord에서 굴릴 때의 운영 기준이다.

## Recommended Shape

```text
Discord server
  @OCP-Town-Gemma  -> Python resident bot -> Ollama Gemma 12B
  @OpenClaw        -> OpenClaw agent      -> 검증, 조사, 장기 작업
```

- Gemma 주민은 세계관과 학습 대화를 맡는다.
- OpenClaw는 검증자/Michael 역할, 도구 호출, 긴 작업, 추후 자동화에 둔다.
- 같은 Discord 봇 토큰을 두 프로세스가 동시에 쓰면 Gateway 충돌이 날 수 있다. Discord 애플리케이션/봇을 두 개 만든다.

권장 봇 이름:

- `OCP Town Gemma`: Gemma4 주민
- `OpenClaw Michael`: OpenClaw 검증자

## Discord Bot

Discord Developer Portal에서 봇을 만든 뒤 Bot 페이지에서 다음 intent를 켠다.

- Message Content Intent: required
- Server Members Intent: OpenClaw allowlist/이름 매칭을 쓸 때 권장

OAuth2 URL Generator에서는 다음 scope/permission을 준다.

- Scopes: `bot`, `applications.commands`
- Permissions: View Channels, Send Messages, Read Message History, Embed Links, Attach Files
- Thread를 쓸 예정이면 Send Messages in Threads도 추가

Developer Mode를 켠 뒤 서버 ID, 채널 ID, 본인 User ID를 복사한다.

## Python Resident Bot

Gemma 주민 봇의 `.env` 예시:

```bash
OCP_TOWN_DISCORD_BOT_TOKEN=...
OCP_TOWN_DISCORD_CHANNEL_ID=
OCP_TOWN_REQUIRE_MENTION=false
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=gemma4:12b-it-qat
OCP_TOWN_PROMPT=prompts/ocp-resident.md
OCP_TOWN_MEMORY=data/memory.jsonl
```

채널 하나에서만 반응하게 하려면 `OCP_TOWN_DISCORD_CHANNEL_ID`에 `#ocp-town` 채널 ID를 넣는다.
OpenClaw와 같은 채널에 둘 거면 `OCP_TOWN_REQUIRE_MENTION=true`로 바꿔서 봇끼리 말이 겹치지 않게 한다.

실행:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
ocp-town-doctor --chat
ocp-town
```

## OpenClaw Gemma Provider

OpenClaw 봇 토큰은 프로젝트 `.env`가 아니라 OpenClaw 서비스가 읽는 환경에 둔다.

```bash
mkdir -p ~/.openclaw
printf 'DISCORD_BOT_TOKEN=replace-with-openclaw-discord-bot-token\n' >> ~/.openclaw/.env
```

OpenClaw는 Ollama의 OpenAI 호환 `/v1` URL이 아니라 네이티브 API 주소를 써야 한다.

```bash
ollama list
openclaw gateway status
openclaw config patch --file openclaw/ocp-town-gemma.patch.json5 --dry-run
openclaw config patch --file openclaw/ocp-town-gemma.patch.json5
openclaw models list --provider ollama
```

OCP Town 전용 agent를 만들 때:

```bash
openclaw agents add ocp-town \
  --workspace /Users/Shared/agent-projects/active/ocp-town-oc/openclaw-workspace \
  --model ollama/gemma4:12b-it-qat \
  --non-interactive
```

Discord 채널 라우팅은 봇을 분리한 뒤 적용한다.

```bash
openclaw agents bind --agent ocp-town --bind discord
```

민감한 명령을 Discord에서 승인하려면 `commands.ownerAllowFrom`에 본인 Discord user id를 명시한다.

```bash
openclaw config set commands.ownerAllowFrom '[ "discord:<your-user-id>" ]' --strict-json
```

## Safety Rules

- Secret, kubeconfig, token 값은 Discord에 붙여 넣지 않는다.
- Gemma 주민은 실제 클러스터 변경 명령을 자동 실행하지 않는다.
- OpenClaw는 공개/다인원 채널보다 allowlist가 걸린 개인 서버나 DM에서 먼저 테스트한다.
- OCP 실습 명령은 처음에는 `oc get`, `oc describe`, `oc explain`, `oc logs` 같은 read-only 명령 위주로 제한한다.
