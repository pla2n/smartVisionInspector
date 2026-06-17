# 🏭 Smart Vision Inspector

> 아두이노 + YOLOv8 기반 엣지 비전 관제 및 AI 에이전트 시스템

---

## 📋 목차

1. [프로젝트 개요](#-프로젝트-개요)
2. [주요 기능](#-주요-기능)
3. [커스텀 모델 학습 및 성능](#-커스텀-모델-학습-및-성능)
4. [보안 설계](#-보안-설계)
5. [시스템 아키텍처](#️-시스템-아키텍처)
6. [리포지토리 구조](#-리포지토리-구조)
7. [기술 스택](#️-기술-스택)
8. [실행 가이드](#-실행-가이드)

---

## 📖 프로젝트 개요

**Smart Vision Inspector**는 컨베이어 벨트 위를 지나는 제품의 불량 여부를 실시간으로 판정하고, 불량품을 자동 배출하는 스마트 팩토리 시스템입니다. 공장 현장(엣지)과 관제 센터(서버)를 분리된 물리 환경으로 가정하고 설계했습니다.

아두이노에 연결된 스테퍼 모터가 컨베이어 벨트를 구동하고, 초음파 센서가 제품을 감지하면 웹캠의 YOLOv8이 불량 판정을 수행합니다. 불량으로 판정되면 서보 모터가 작동해 해당 제품을 벨트 밖으로 밀어냅니다. 모든 판정 이력은 관제 서버 DB에 쌓이고, AI 에이전트를 통해 자연어로 공정 통계를 조회하거나 불량 이미지를 분석할 수 있습니다.

<div align="center">
  
  <img width="368" height="654" alt="KakaoTalk_Photo_2026-06-14-00-14-03 003" src="https://github.com/user-attachments/assets/e78ebaff-e4f2-435b-92f5-5d0649b98942" />
  <p><b>정상 제품 처리 예시</b></p>
  <br>

  <img width="368" height="654" alt="KakaoTalk_Photo_2026-06-14-00-14-02 001" src="https://github.com/user-attachments/assets/3f469dc8-6d29-4e43-b095-42a2a667c78d" />
  <p><b>오염 제품(Stained) 처리 예시</b></p>
  <br>

  <img width="368" height="654" alt="KakaoTalk_Photo_2026-06-14-00-14-03 002" src="https://github.com/user-attachments/assets/a0041232-15ac-4cd2-910d-911528b074bf" />
  <p><b>손상 제품(Broken) 처리 예시</b></p>
  <br>
  
  <img width="867" height="1294" alt="image" src="https://github.com/user-attachments/assets/f6500777-1336-4d9d-aa4a-fbf1d59e93c9" />
  <p><b>실제 스마트 팩토리 데이터 시각화</b></p>
  <br>

  <img width="694" height="764" alt="image" src="https://github.com/user-attachments/assets/520b8d91-d4b3-4caa-8e72-8fa67d4e7bf5" />
  <p><b>RAG 챗봇</b></p>
  
  <img width="587" height="755" alt="image" src="https://github.com/user-attachments/assets/d9ccc2e0-c416-4920-9514-71c6965a19ed" />
  <p><b>저장된 데이터 기반 보고서 생성</b></p>
</div>

---

## ✨ 주요 기능

### 🏭 엣지 컴퓨팅 기반 실시간 불량 탐지

- 초음파 센서 감지 시에만 카메라가 켜지고 YOLO 추론을 시작하는 **이벤트 드리븐 구조**로 엣지 디바이스 부하 최소화
- **멀티프레임 버스트 분석**: 단일 프레임 오탐을 줄이기 위해 센서 감지 시점 기준 2초 전 6장 + 1초 전 6장 + 현재 6장, 총 최대 18장을 연속으로 추론해 최고 신뢰도 결과를 채택
- 불량 판정 시 해당 프레임 이미지를 저장하고 관제 서버로 전송, 정상/불량 여부에 따라 서보 모터 및 경광등(PASS/RED) 자동 작동

### 🌐 분산 아키텍처 및 실시간 관제

- 공장 현장(Edge)과 관제 센터(Server)의 물리적 망 분리 지원
- 엣지 디바이스에서 서버로 영상을 밀어 올리는 Edge-Push 방식의 실시간 스트리밍
- Streamlit 대시보드를 통한 실시간 생산 통계 및 불량률 모니터링
- 대시보드에서 AI 민감도 및 시스템 가동 상태를 원격으로 제어하면 엣지 노드가 2초 주기로 동기화

### 🤖 멀티모달 RAG AI 에이전트

- LangGraph 기반의 반응형 AI 에이전트 구조
- 자연어로 공정 통계를 물어보면 SQLite DB를 직접 조회해 답변
- 불량 이미지를 첨부하면 GPT-4o Vision으로 시각적 원인 분석 수행
- ChromaDB 기반 RAG로 제조 도메인 지식을 검색해 답변 품질 보완

---

## 📊 커스텀 모델 파인튜닝

초기 구축한 자체 데이터셋(SmartFactory-3, 425장)으로 학습한 모델을 실제 환경에서 테스트해본 결과, 조명과 카메라 각도 등의 차이(도메인 갭)로 인해 성능 저하가 발생했습니다.
이를 해결하기 위해 현장의 실제 컨베이어 벨트 환경에서 추가 이미지(Normal 18장, Broken 28장, Stained 30장)를 직접 촬영하고, 데이터 증강(Rotation, Brightness, Blur)을 거친 새 데이터셋(SmartFactory-5, 557장)으로 추가 파인튜닝을 진행했습니다.

### 학습 설정

| 항목        | 설정값                                             |
| ----------- | -------------------------------------------------- |
| 베이스 모델 | 기존에 학습된 `best.pt` (YOLOv8n 기반)             |
| 데이터셋    | 추가 촬영 및 증강한 자체 데이터셋 (SmartFactory-5) |
| 분할 비율   | Train 60% / Val 20% / Test 20%                     |
| 학습 옵션   | 40 Epochs, lr0=0.001 (Early Stopping patience=10)  |
| 데이터 증강 | Rotation(±15°), Brightness(±15%), Blur(1.5px)      |
| 하드웨어    | Apple M3 Pro 32GB (MPS)                            |

### 평가 결과

18 Epoch에서 수렴하며 과적합 없이 안정적인 성능을 확보했습니다.

| 클래스   | Precision | Recall | mAP@50    | mAP@50-95 |
| -------- | --------- | ------ | --------- | --------- |
| **전체** | 0.964     | 0.891  | **0.931** | **0.920** |
| Broken   | 0.949     | 0.922  | 0.920     | 0.915     |
| Normal   | 0.955     | 0.750  | 0.878     | 0.860     |
| Stained  | 0.990     | 1.000  | 0.995     | 0.985     |

```bash
cd edge_node
python train_custom.py
# 학습 완료 후 가중치: runs/detect/factory_project/custom_inspector_v2/weights/best.pt
```

---

## 🔒 보안 설계

본 시스템은 외부 네트워크에서 접근 가능한 환경(포트 포워딩)을 전제로 운영됩니다. 프로토타입 완성 후 운영 환경 배포 전에 코드 수준의 보안 점검을 직접 수행했습니다.

### 환경 변수(`.env`) 구성

| 변수명           | 위치                                | 역할                                                    |
| ---------------- | ----------------------------------- | ------------------------------------------------------- |
| `OPENAI_API_KEY` | control_server                      | GPT API 호출 인증                                       |
| `API_SECRET_KEY` | control_server, edge_node (동일 값) | 외부망 노출 API 무단 호출 차단. 불일치 시 즉시 403 반환 |
| `ADMIN_PW_HASH`  | control_server                      | SHA-256 단방향 해시로만 저장, 원본 비밀번호 역산 불가   |
| `API_BASE_URL`   | control_server                      | 대시보드가 바라보는 API 서버 주소                       |
| `SERVER_IP`      | edge_node                           | 엣지 노드가 데이터를 전송할 관제 서버 IP                |

---

## 🏗️ 시스템 아키텍처

<div align="center">
  <img src="https://img.shields.io/badge/Edge_Node-(Factory)-orange?style=for-the-badge" />
     ➡️ HTTP POST (Streaming & Logs) ➡️   
  <img src="https://img.shields.io/badge/Control_Server-(Cloud/Local)-blue?style=for-the-badge" />
</div>

- **Edge Node (현장):** 카메라 스트리밍, 아두이노 제어, YOLOv8 추론을 담당하며 관제 서버로 데이터를 전송
- **Control Server (관제):** FastAPI 백엔드, SQLite DB, AI 에이전트, Streamlit 대시보드로 현장 전체를 관제

---

## 📁 리포지토리 구조

<details>
<summary><b>📂 상세 폴더 구조 보기</b></summary>

```text
smartVisionInspector/
├── README.md
├── control_server/             # 관제 서버 (백엔드 / 프론트엔드 / AI)
│   ├── api_server.py           # FastAPI 통합 백엔드 (인증, 로그 수신, 설정 동기화)
│   ├── dashboard.py            # Streamlit 기반 통합 관제 대시보드
│   ├── agent_core.py           # LangGraph 기반 AI 에이전트 핵심 로직
│   ├── rag.py                  # RAG 엔진 (문서 임베딩 및 검색)
│   ├── setup_db.py             # SQLite 데이터베이스 스키마 초기화
│   ├── config.py               # 환경 변수 및 설정 관리
│   └── chroma_db/              # RAG용 벡터 데이터베이스 (런타임 생성)
│
└── edge_node/                  # 현장 엣지 디바이스 (비전 AI / 하드웨어)
    ├── edge_main.py            # 엣지 메인 루프 (카메라, 아두이노, 서버 통신)
    ├── train_custom.py         # 커스텀 모델 학습 스크립트 (데이터 분할 + YOLOv8 파인튜닝)
    ├── dataset/                # 학습 데이터셋 (Roboflow, .gitignore 처리)
    ├── detect/
    │   └── detect.ino          # 아두이노 센서 및 모터 제어 코드
    └── captured_imgs/          # 불량 발생 시 저장 이미지 (런타임 생성)
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

# 백엔드 API 서버
uvicorn api_server:app --host 0.0.0.0 --port 8000

# 대시보드 (새 터미널)
streamlit run dashboard.py
```

### 2. 현장 엣지 디바이스 실행 (Edge Node)

```bash
cd edge_node
python edge_main.py

# macOS에서 실시간 스트리밍 관제 기능 사용 시
# OPENCV_AVFOUNDATION_SKIP_AUTH=1 python edge_main.py
```

> 외부 서버와 통신하는 경우, 관제 서버의 8000번 포트를 포트포워딩한 뒤 `SERVER_IP`에 공인 IP를 입력 필요.

---

## 👨‍💻 제작자

이세용
