# 🏭 Smart Vision Inspector

> **지능형 엣지 관제 및 멀티모달 AI 에이전트 시스템 (IT-OT 융합 아키텍처)**

</div>

---

## 📋 목차

1. [📖 프로젝트 개요](#-프로젝트-개요)
2. [✨ 주요 기능](#-주요-기능)
3. [🔒 보안 설계 및 조치](#-보안-설계-및-조치)
4. [🏗️ 시스템 아키텍처](#️-시스템-아키텍처)
5. [📁 리포지토리 구조](#-리포지토리-구조)
6. [🛠️ 기술 스택](#️-기술-스택)
7. [🚀 실행 가이드](#-실행-가이드)
8. [👨‍💻 제작자](#-제작자)

---

## 📖 프로젝트 개요

**Smart Vision Inspector**는 제조 현장의 객체 탐지 및 하드웨어 제어를 자동화하고, 이를 원격에서 통제 및 분석할 수 있는 양방향 지능형 관제 시스템입니다.

기존 단방향 모니터링 시스템을 구현하면서 가장 먼저 부딪힌 문제는 **리소스**였습니다. 24시간 내내 YOLOv8를 돌리면 엣지 디바이스에 심각한 부하가 걸립니다. 이를 해결하기 위해 초음파 센서가 물체를 감지한 순간에만 카메라가 켜지고 추론을 시작하는 이벤트 기반 제어 로직을 구현해 불필요한 CPU 사용을 줄였습니다. 여기에 LLM 기반 Multi-Tool(RAG) 에이전트를 더해, 관리자가 자연어로 질문하면 공정 통계 조회와 불량 원인 분석을 동시에 수행할 수 있도록 했습니다.

해당 프로젝트를 수행하기 위해선 아두이노와 웹캠, 컨베이어 벨트, 서보 모터, 모터, 초음파 센서가 필요합니다.
아두이노와 연결된 모터가 컨베이어 벨트를 직동시키고, 컨베이어 벨트 위에 설치된 초음파 센서가 물품을 감지하면 웹캠이 불량품 여부를 판단하고, 불량품일 경우 서보 모터가 작동되어 불량품을 컨베이어 벨트에서 제거합니다.

<div align="center">
  <img width="800" alt="제어 대시보드" src="https://github.com/user-attachments/assets/2f8b7f33-0cda-457f-9c43-ffd2c7faf374" />
  <p><b>제어 대시보드</b></p>
  <br>

  <img width="800" alt="실제 스마트 팩토리 데이터 시각화" src="https://github.com/user-attachments/assets/bae4c0e3-597c-4f47-a4ec-01c5d1a4418e" />
  <p><b>실제 스마트 팩토리 데이터 시각화</b></p>
  <br>

  <img width="800" alt="저장된 데이터 기반 보고서 생성" src="https://github.com/user-attachments/assets/c97bc69f-1c26-4807-9d51-eafd9a4e6166" />
  <p><b>저장된 데이터 기반 보고서 생성</b></p>
  <br>

  <img width="800" alt="간단한 챗봇" src="https://github.com/user-attachments/assets/c97bc69f-1c26-4807-9d51-eafd9a4e6166" />
  <p><b>간단한 챗봇</b></p>
</div>

---

## ✨ 주요 기능

### 🏭 엣지 컴퓨팅 기반 실시간 불량 탐지

- 아두이노 센서와 카메라 연동을 통한 **이벤트 드리븐 객체 탐지** (센서 감지 시에만 YOLO 추론하여 부하 최소화, 오류 이미지 별도 저장)
- YOLOv8 모델을 활용한 제품 불량(스크래치, 형태 불량 등) 실시간 판독
- 컨베이어 벨트 모터 제어 및 경고등(PASS/RED) 자동 작동

### 🌐 분산 아키텍처(MSA) 및 실시간 관제

- 공장 현장(Edge)과 관제 센터(Server)의 물리적 망 분리 완벽 지원
- 엣지 디바이스에서 서버로 영상을 밀어 올리는 방식의 지연 없는 실시간 네트워크 스트리밍
- Streamlit 대시보드를 통한 실시간 생산 통계 및 불량률 모니터링
- 대시보드에서 엣지 디바이스의 AI 민감도 및 시스템 가동 상태 원격 제어

### 🤖 멀티모달 RAG AI 에이전트

- LangGraph 기반의 반응형 AI 에이전트 아키텍처 통합
- 자연어로 공정 통계 조회, 불량 내역 질문 시 데이터베이스와 연동된 답변 생성
- 불량 이미지를 인식하여 사용자에게 시각적/맥락적 원인 분석 제공

---

## 🔒 보안 설계 및 조치

본 시스템은 외부 네트워크에서 접근 가능한 환경(포트 포워딩)을 전제로 운영됩니다. 초기 프로토타입 완성 후, 운영 환경 배포 전 코드 수준의 보안 점검을 직접 수행하여 아래 취약점들을 식별하고 조치했습니다.

### 발견 및 조치한 취약점

| 구분            | 취약점                                                                            | 조치 내용                                                                                                                                |
| --------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **인증**        | 모든 REST API 엔드포인트에 인증 체계 부재                                         | FastAPI `APIKeyHeader` 기반 API Key 인증 미들웨어 도입, 전 엔드포인트 적용                                                               |
| **인증**        | 관리자 계정 비밀번호 소스 코드 내 평문 하드코딩                                   | SHA-256 해시 기반 비밀번호 정책으로 전환, `.env` 환경 변수 분리 관리                                                                     |
| **인젝션**      | 대시보드 API의 `limit` 파라미터가 f-string으로 SQL에 직접 삽입되어 외부 조작 가능 | f-string 방식의 쿼리 조립을 전면 금지하고, `params=(limit,)` 튜플을 이용한 파라미터 바인딩으로 리팩토링하여 데이터 변조 가능성 원천 차단 |
| **파일 업로드** | 업로드 파일명 검증 없이 경로 직접 사용 (Path Traversal)                           | 확장자 화이트리스트 검증 및 UUID 기반 안전 파일명 재생성                                                                                 |
| **코드 관리**   | API 키 등 민감 정보의 환경 변수화 미흡                                            | 전체 설정값을 `.env`로 분리, `.gitignore`를 통한 형상 관리 제외 처리                                                                     |

### 보안 설계 원칙

- **최소 권한**: Edge 노드는 서버로 데이터를 전송하는 단방향 권한만 보유
- **인증 일관성**: 서버-서버(Edge→Control) 간 통신과 사용자-서버(Dashboard→API) 간 통신 모두 동일한 API Key 인증 체계 적용
- **민감 정보 분리**: 모든 민감 정보는 `.env` 파일에서만 관리하며, `.gitignore`를 통해 형상 관리 대상에서 제외

### 환경 변수(`.env`) 구성

각 변수가 보안 상 어떤 역할을 하는지 정리했습니다.

| 변수명           | 위치                                | 역할                                                                                                      |
| ---------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `OPENAI_API_KEY` | control_server                      | GPT API 호출 인증. 코드에 직접 삽입하지 않고 환경 변수로 분리                                             |
| `API_SECRET_KEY` | control_server, edge_node (동일 값) | 포트포워딩으로 외부망에 노출된 API에 대한 무단 호출을 막기 위한 인터셉터 인증 키. 미일치 시 즉시 403 차단 |
| `ADMIN_PW_HASH`  | control_server                      | 소스 코드나 `.env` 탈취 시에도 원본 비밀번호를 역산할 수 없도록 SHA-256 단방향 해시로만 저장              |
| `API_BASE_URL`   | control_server                      | 대시보드가 바라보는 API 서버 주소. 환경(로컬/외부)에 따라 분리 관리                                       |
| `SERVER_IP`      | edge_node                           | 엣지 노드가 데이터를 전송할 관제 서버 IP. 코드 수정 없이 변경 가능                                        |

---

## 🏗️ 시스템 아키텍처

<div align="center">
  <img src="https://img.shields.io/badge/Edge_Node-(Factory)-orange?style=for-the-badge" /> 
     ➡️ HTTP POST API (Streaming & Logs) ➡️   
  <img src="https://img.shields.io/badge/Control_Server-(Cloud/Local)-blue?style=for-the-badge" />
</div>

- **Edge Node (현장 장비):** 카메라, 아두이노 제어 및 YOLOv8 엣지 추론을 수행하며 관제 서버로 데이터를 쏘아 올림
- **Control Server (관제 서버):** FastAPI 백엔드, SQLite 통합 DB, AI 에이전트, Streamlit 프론트엔드 대시보드를 통해 현장을 관제

---

## 📁 리포지토리 구조

<details>
<summary><b>📂 상세 폴더 구조 보기</b></summary>

```text
smartVisionInspector/
├── README.md                   # 프로젝트 설명서
├── control_server/             # 관제 서버 (백엔드/프론트엔드/AI)
│   ├── api_server.py           # FastAPI 통합 백엔드 (인증, 로그 수신 및 설정 동기화)
│   ├── dashboard.py            # Streamlit 기반 통합 관제 대시보드
│   ├── agent_core.py           # LangGraph 기반 AI 에이전트 핵심 로직
│   ├── rag.py                  # RAG 엔진 (문서 임베딩 및 검색)
│   ├── setup_db.py             # SQLite 데이터베이스 스키마 초기화
│   ├── config.py               # 환경 변수 및 설정 관리 모듈
│   ├── factory_log.db          # 공정 로그 및 설정 저장 DB
│   └── chroma_db/              # RAG를 위한 벡터 데이터베이스
│
└── edge_node/                  # 현장 엣지 디바이스 (비전 AI 및 하드웨어)
    ├── edge_main.py            # 엣지 메인 루프 (카메라, 아두이노, 서버 통신)
    ├── yolov8n.pt              # YOLOv8 사전 학습 모델 가중치 파일
    ├── detect/
    │   └── detect.ino          # 아두이노 센서 및 모터 제어 소스코드
    └── captured_imgs/          # 불량 발생 시 저장 및 전송되는 이미지 디렉토리
```

</details>

---

## 🛠️ 기술 스택

### Frontend & Dashboard

<img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white">

### Backend & API

<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white">
<img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white">

### Edge Vision & Hardware

<img src="https://img.shields.io/badge/YOLOv8-FFCC00?style=for-the-badge&logo=yolo&logoColor=black">
<img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white">
<img src="https://img.shields.io/badge/Arduino-00979D?style=for-the-badge&logo=arduino&logoColor=white">

### AI Agent

<img src="https://img.shields.io/badge/OpenAI_API-412991?style=for-the-badge&logo=openai&logoColor=white">
<img src="https://img.shields.io/badge/LangGraph-000000?style=for-the-badge">
<img src="https://img.shields.io/badge/ChromaDB-FC5200?style=for-the-badge">

---

## 🚀 실행 가이드

### 사전 준비: 환경 변수 설정

보안 운영을 위해 두 노드 모두 `.env` 파일 작성이 필수입니다.

**`control_server/.env`**

```bash
OPENAI_API_KEY=<OpenAI API 키>
API_SECRET_KEY=<API 통신 인증 키 — Edge 노드와 동일하게 설정>
ADMIN_PW_HASH=<SHA-256 해시값 — 아래 명령어로 생성>
API_BASE_URL=http://localhost:8000/api
```

> `ADMIN_PW_HASH` 생성:
>
> ```bash
> python3 -c "import hashlib; print(hashlib.sha256(b'설정할비밀번호'.encode()).hexdigest())"
> ```

**`edge_node/.env`**

```bash
SERVER_IP=<관제 서버 IP>
API_SECRET_KEY=<control_server/.env의 API_SECRET_KEY와 동일한 값>
```

### 1. 관제 서버 실행 (Control Server)

```bash
cd control_server

# 백엔드 API 서버 실행
uvicorn api_server:app --host 0.0.0.0 --port 8000

# 대시보드 실행 (새 터미널)
streamlit run dashboard.py
```

### 2. 현장 엣지 디바이스 실행 (Edge Node)

현장의 카메라 및 아두이노가 연결된 장비에서 실행합니다.

```bash
cd edge_node
python edge_main.py
# 맥 실행 시 실시간 스트리밍 관제 기능 사용을 위해서는 아래 명령어로 edge_main.py 실행
# OPENCV_AVFOUNDATION_SKIP_AUTH=1 python edge_main.py
```

> 외부 서버와 통신하는 경우, 관제 서버의 8000번 포트 포트포워딩 설정 후 `SERVER_IP`에 공인 IP를 입력하세요.

---

## 👨‍💻 제작자

이세용
