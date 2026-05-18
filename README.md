# 🏭 Smart Vision Inspector

> **지능형 엣지 관제 및 멀티모달 AI 에이전트 시스템 (IT-OT 융합 아키텍처)**

</div>

---

## 📋 목차

1. [📖 프로젝트 개요](#-프로젝트-개요)
2. [✨ 주요 기능](#-주요-기능)
3. [🏗️ 시스템 아키텍처](#️-시스템-아키텍처)
4. [📁 리포지토리 구조](#-리포지토리-구조)
5. [🛠️ 기술 스택](#️-기술-스택)
6. [🚀 실행 가이드](#-실행-가이드)
7. [👨‍💻 제작자](#-제작자)

---

## 📖 프로젝트 개요
**Smart Vision Inspector**는 제조 현장의 객체 탐지 및 하드웨어 제어를 자동화하고, 이를 원격에서 통제 및 분석할 수 있는 양방향 지능형 관제 시스템입니다. 

기존 단방향 모니터링 시스템과 상시 구동되는 Vision AI의 컴퓨팅 부하 한계를 극복하기 위해, **이벤트 드리븐 기반의 센서 퓨전 기술**을 엣지 디바이스에 적용했습니다. 더불어 대형 언어 모델(LLM) 기반의 Multi-Tool(RAG) 에이전트를 도입하여, 관리자의 자연어 질의만으로 공정 통계 조회와 불량 원인 분석을 동시 수행합니다.

해당 프로젝트를 수행하기 위해선 아두이노와 웹캠, 컨베이어 벨트, 서보 모터, 모터, 초음파 센서가 필요합니다.
아두이노와 연결된 모터가 컨베이어 벨트를 직동시키고, 컨베이어 벨트 위에 설치된 초음파 센서가 물품을 감지하면 웹캠이 불량품 여부를 판단하고, 불량품일 경우 서보 모터가 작동되어 불량품을 컨베이어 벨트에서 제거합니다.

<div align="center">
  <img width="800" alt="제어 대시보드" src="https://github.com/user-attachments/assets/2f8b7f33-0cda-457f-9c43-ffd2c7faf374" />
  <p><b>제어 대시보드</b></p>
  <br>

  <img width="800" alt="실제 스마트 팩토리 데이터 시각화" src="https://github.com/user-attachments/assets/bae4c0e3-597c-4f47-a4ec-01c5d1a4418e" />
  <p><b>실제 스마트 팩토리 데이터 시각화</b></p>
  <br>

  <img width="800" alt="저장된 데이터 기반 보고서 생성" src="https://github.com/user-attachments/assets/c49acbeb-0e77-47b8-93b2-dee3b3b2f0cf" />
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
│   ├── api_server.py           # FastAPI 통합 백엔드 (로그 수신 및 설정 동기화)
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

> **네트워크 환경 설정:** 환경에 맞춰 `edge_node/edge_main.py` 내부의 서버 통신 URL(`API_URL`, `SERVER_URL`, `LOGS_URL`)과 `control_server/dashboard.py` 내부의 이미지 소스 IP를 관제 서버의 IP로 수정해야 합니다.

### 1. 관제 서버 실행 (Server)
메인 서버(공유기망 등)에서 다음 명령어를 실행합니다.
```bash
cd control_server

# 1-1. 백엔드 API 서버 백그라운드 실행
uvicorn api_server:app --host 0.0.0.0 --port 8000

# 1-2. 대시보드 실행 (새 터미널)
streamlit run dashboard.py

# 1-3. .env 파일 작성
control_server 폴더 안에 .env 파일을 만들고,
OPENAI_API_KEY= """ 실제 OPENAI API KEY를 입력하기! """
```

### 2. 현장 엣지 디바이스 실행 (Edge Node)
현장의 카메라 및 아두이노가 연결된 맥북(핫스팟망 등)에서 실행합니다.
```bash
cd edge_node
python edge_main.py

edge_node 폴더 안에 .env 파일을 만들고,
SERVER_IP= 127.0.0.1
를 입력해주세요! 만약 외부 환경의 서버와 통신을 한다면, 해당 망의 8000번 포트의 포트포워딩 설정을 마치고, SERVER_IP에 관제 서버 공인 IP 주소를 입력 해 주세요!
```

---

## 👨‍💻 제작자
이세용
