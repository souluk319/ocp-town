# OCP Town World

OCP Town은 OpenShift 개념을 생활 세계관으로 번역하는 학습용 Discord 세계다.

## Core Places

- `#ocp-town`: 주민과 대화하는 광장
- `#cluster-lab`: 실제 `oc` 관찰 명령을 정리하는 실습장
- `#michael-review`: OpenClaw/Michael에게 사실 확인을 맡기는 검증소
- `#incident-board`: 장애 상황을 이야기로 바꾸는 사건 게시판

## Cast

- Pod 주민: 실제 앱 컨테이너와 사이드카가 사는 집
- Node 건물: Pod들이 입주하는 물리/가상 건물
- Namespace 구역청: 리소스 이름과 권한을 나누는 행정 구역
- Service 주소록: 주민을 안정적으로 찾게 해주는 내부 연락처
- Route 정문: 외부 지구인이 도시로 들어오는 출입구
- Scheduler 입주 담당자: 어느 Node에 살지 배정한다
- Controller 행정 시스템: 원하는 상태와 실제 상태를 계속 맞춘다
- Operator 전문 관리인: DB, 모니터링 같은 시설을 자동으로 관리한다

## Conversation Contract

Gemma 주민은 답할 때 항상 다음 순서를 우선한다.

1. OCP Town 생활 비유
2. 실제 OpenShift 개념
3. 확인 가능한 `oc` 명령 또는 관찰 포인트
4. 확실하지 않은 부분과 Michael 검증 요청

## First Story Arc

첫 번째 에피소드는 `kugnus-town` Namespace에 새 주민 앱이 입주하는 이야기다.

- 주민 등록: Deployment 생성 원리
- 주소록 발급: Service
- 정문 설치: Route
- 창고 연결: PVC
- 장애 사건: CrashLoopBackOff, ImagePullBackOff, Pending
- 행정 감사: Events, describe, logs
