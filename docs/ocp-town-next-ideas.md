# OCP Town Next Ideas

OCP Town의 다음 개발 방향은 "개념 설명 봇"보다 "살다 보면 OCP 개념이 몸에 들어오는 동네"에 가깝게 잡는다.

## 1. Daily Town Walk

매일 한 번 `C`가 짧은 산책 코스를 제안한다.

- 오늘의 집: Pod 하나를 고르고 상태를 본다.
- 오늘의 건물: Node 하나를 골라 누가 사는지 본다.
- 오늘의 주소록: Service 하나가 누구를 가리키는지 본다.
- 오늘의 정문: Route/Ingress가 어디로 이어지는지 본다.

예시:

```text
성욱, 오늘은 주소록(Service) 산책하자.
`oc get svc -n kugnus-town`로 마을 전화번호부부터 펼쳐봐.
```

## 2. Incident Story Mode

장애를 사건처럼 다룬다.

- `Pending`: 입주 대기 사건
- `CrashLoopBackOff`: 집에 들어오자마자 계속 뛰쳐나오는 사건
- `ImagePullBackOff`: 이삿짐 트럭 이미지를 못 찾는 사건
- `OOMKilled`: 집 안 메모리 공기가 부족해서 쓰러진 사건
- `Evicted`: 건물 사정 때문에 쫓겨난 사건

각 사건은 이 흐름으로 진행한다.

1. C가 마을 소문으로 사건을 설명한다.
2. 실제 OCP 상태로 번역한다.
3. read-only `oc` 명령 하나만 제안한다.
4. 성욱이 결과를 붙이면 다음 단서를 푼다.
5. 필요하면 Michael에게 검증을 넘긴다.

## 3. OCP Town Map

`docs/ocp-town-world.md`를 확장해서 마을 지도로 만든다.

- Namespace: 구역
- Node: 건물
- Pod: 집 또는 주민 몸
- Deployment: 주민 모집 공고와 복제 규칙
- ReplicaSet: 현재 유지 중인 주민 수 조정반
- Service: 주소록
- Route: 외부 정문
- PVC: 창고
- ConfigMap: 공개 생활 규칙표
- Secret: 신분증과 열쇠 보관함
- Operator: 전문 자동 관리인

나중에는 `/ocp-map` 같은 명령으로 현재 세계관 지도를 출력하게 할 수 있다.

## 4. Quest System

학습을 퀘스트로 만든다.

- Quest 1: `kugnus-town` 구역에 누가 사는지 보기
- Quest 2: Pod 하나의 Events 읽기
- Quest 3: Service가 어떤 Pod를 찾는지 따라가기
- Quest 4: Route가 외부에서 내부로 들어오는 길 이해하기
- Quest 5: ConfigMap과 Secret의 차이 말로 설명하기
- Quest 6: CrashLoopBackOff 사건 보고서 쓰기

각 퀘스트는 "마을 표현 -> 실제 개념 -> 확인 명령 -> 성욱의 한 줄 회고"로 저장한다.

## 5. Resident Memory

지금 JSONL memory는 최근 대화 위주다. 나중에는 장기 기억을 따로 둔다.

- 성욱이 헷갈렸던 개념
- 성욱이 이미 해결한 사건
- 자주 쓰는 Namespace
- 자주 보는 리소스
- Michael이 검증한 정정 내용

예시 저장 항목:

```json
{"type":"learned_concept","concept":"Service","earth_note":"Pod IP는 바뀌니까 Service가 안정 주소 역할을 한다."}
```

## 6. Michael Review Channel

OpenClaw/Michael은 C의 설명을 빼앗는 존재가 아니라 검증소로 둔다.

- C: 마을 감각, 첫 설명, 비유
- Michael: 실제 명령어 검증, 위험 경고, 장애 원인 좁히기
- Sung-uk: 관찰 결과를 가져오는 외부 지구인

패턴:

```text
C: 마을에서는 이런 사건 같아.
Michael: 실제 OCP로는 이 가능성이 높고, 이 명령부터 봐.
Sung-uk: 결과 붙임.
C: 그럼 마을 기록으로 이렇게 이해하면 돼.
```

## 7. Shorter Gemma Replies

Gemma 12B는 느릴 수 있으므로 C는 기본적으로 짧게 답한다.

- 일상 대화: 3-6문장
- OCP 설명: 명령어 1-2개
- 긴 분석: Michael에게 넘기거나 성욱이 "자세히"라고 할 때만 확장

나중에 `OLLAMA_NUM_PREDICT` 같은 설정을 추가해서 답변 길이를 제한할 수 있다.

## 8. Town Journal

하루 마지막에 C가 오늘 배운 내용을 마을 일지로 요약한다.

예시:

```text
오늘 성욱은 Pending이 "입주 대기"라는 걸 배웠다.
진짜 원인은 Events를 봐야 한다.
다음에는 Service 주소록을 따라가 보기로 했다.
```

이 일지는 `data/journal.jsonl` 또는 `outputs/town-journal.md`로 저장할 수 있다.

## 9. First Next Build

다음에 바로 만들기 좋은 순서:

1. `ocp-town`에 `--dry-run "메시지"` CLI 추가
2. 프롬프트에 사건별 예시 3개 추가
3. `/ocp-map` 또는 `!map` 명령 추가
4. `!journal`로 오늘 대화 요약 저장
5. Michael 검증 요청을 감지하면 안내 문구를 더 짧게 정리
