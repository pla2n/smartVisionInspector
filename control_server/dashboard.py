import time
import streamlit as st
import pandas as pd
import requests
from openai import OpenAI
from rag import RagEngine
from agent_core import create_factory_agent
from config import OPENAI_API_KEY, API_BASE_URL

client = OpenAI(api_key=OPENAI_API_KEY)
GPT_MODEL = "gpt-4o-mini"
rag_engine = RagEngine(OPENAI_API_KEY)

st.set_page_config(page_title="Factory HQ", page_icon="default", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e117;}
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4253;}
    .chat-panel { border-left: 2px solid #3e3253; padding-left: 20px; height: 100%; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important;}
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'show_chat' not in st.session_state:
    st.session_state['show_chat'] = False
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [{"role": "assistant", "content": "안녕하세요! 불량 탐지 AI 어시스턴트입니다. 무엇을 도와드릴까요?"}]
    

def login():
    st.title("인프라 관제 시스템 로그인")

    with st.form("login_form"):
        username = st.text_input("관리자 ID")
        password = st.text_input("비밀번호", type="password")
        submit = st.form_submit_button("로그인")

        if submit:
            if username == "admin" and password == "1234":
                st.session_state['logged_in'] = True
                st.success("인증 성공!")
                st.rerun()
            else:
                st.error("비인가 접근 시도입니다.")

def highlight_status(val):
    if val == 'RED_DETECTED': return 'background-color: #ff4b4b'
    elif val == 'ERROR_CONNECTION' : return 'background-color: #ff9900'
    elif val == 'PASS': return 'background-color: #00cc66'
    return ''

def generate_ai_report(df, stats):
    if df.empty or stats['defect_count'] == 0:
        return "데이터에 오류가 있습니다. 다시 확인해주세요."

    recent_defects = df[df['status'] == 'RED_DETECTED'].head(15)
    defect_items = recent_defects['sensor_data'].tolist()

    system_prompt = f"""
    """

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "현재까지의 공정 데이터를 바탕으로 AI 분석 보고서 작성해 줘."}
        ],
        temperature=0.5
    )

    return response.choices[0].message.content

def run_dashboard():
    st.title("엣지 인프라 통합 모니터링")
    st.markdown("---")

    try:
        stats_response = requests.get(f"{API_BASE_URL}/stats")
        logs_response = requests.get(f"{API_BASE_URL}/logs?limit=500")

        stats_response.raise_for_status()
        logs_response.raise_for_status()

        stats_data = stats_response.json()
        logs_data = logs_response.json()

        df = pd.DataFrame(logs_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        if not df.empty:
            start_time = df['timestamp'].min()
            end_time = df['timestamp'].max()
            up_time = end_time - start_time

            total = int(up_time.total_seconds())
            hour, remain = divmod(total, 3600)
            mins, sec = divmod(remain, 60)
            up_time_str = f"{hour:02}:{mins:02}:{sec:02}"
        else:
            up_time_str = "00:00:00"
    
    except Exception as e:
        st.error(f"백엔드 API 서버 응답이 없습니다. 에러 : {e}")
        return

    if st.session_state['show_chat']:
        col_main, col_chat = st.columns([3, 1.2])
    else:
        col_main, col_chat = st.columns([1, 0.001])

    with col_main:
        head1, head2 = st.columns([4, 1])
        with head1:
            st.title("스마트 팩토리")
        with head2:
            button_label = "챗봇 닫기" if st.session_state['show_chat'] else "AI 어시스턴트 열기"
            if st.button(button_label, use_container_width=True):
                st.session_state['show_chat'] = not st.session_state['show_chat']
                st.rerun()
        

        st.subheader("실시간 상태")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(label="총 검사량", value=f"{stats_data['total_count']} 개", delta="Edge Sync Ok")
        col2.metric(label="정상 제품", value=f"{stats_data['normal_count']} 개", delta="Stable", delta_color="normal")
        col3.metric(label="불량품", value=f"{stats_data['defect_count']} 개", delta=f"불량률: {stats_data['defect_rate']}%", delta_color="inverse")
        col4.metric(label="총 가동 시간", value=up_time_str, delta="hh:mm:ss")

        st.markdown("---")
        st.subheader("엣지 인프라 원격 제어 및 관제")

        col_cctv, col_control = st.columns([2, 1])

        with col_cctv:
            st.markdown("Edge Vision 실시간 스트리밍")

            stream_html = f'''
            <div style="border: 2px solid #3e4253; border-radius: 10px; overflow: hidden; display: flex; justify-content: center; background-color: #000;">
                <img src="{API_BASE_URL.replace('/api', '')}/video_feed" width="100%" alt="Edge Camera Offline">
            </div>
            '''
            st.markdown(stream_html, unsafe_allow_html=True)
        with col_control:
            st.markdown("시스템 파라미터 제어")

            try:
                current_settings = requests.get(f"{API_BASE_URL}/settings").json()
                curr_conf = current_settings['confidence']
                curr_run = bool(current_settings['is_running'])
            except:
                curr_conf = 0.3
                curr_run = True

            with st.form("control_form"):
                new_conf = st.slider("YOLO 민감도 (Confidence Threshold)",
                                    min_value=0.1, max_value=0.9, value=curr_conf, step=0.05,
                                    help="값이 높을수록 확실한 불량 검출 정확도가 높아집니다.")

                is_running = st.toggle("컨베이어 및 비전 시스템 가동", value=curr_run)

                submitted = st.form_submit_button("설정 적용", use_container_width=True)

                if submitted:
                    payload = {"confidence": new_conf, "is_running": 1 if is_running else 0}
                    requests.post(f"{API_BASE_URL}/settings", json=payload)
                    st.success("현장 엣지 노드에 설정이 전송되었습니다!")
                    time.sleep(1)
                    st.rerun()

        st.markdown("---")
        st.subheader(" OT 공정 이상 탐지 로그 (DB 데이터)")

        if not df.empty:

            st.dataframe(df.style.map(highlight_status, subset=['status']), use_container_width=True)

            st.subheader("인프라 상태 및 이상 탐지 통계")
            status_counts = df['status'].value_counts()
            st.bar_chart(status_counts)

            df['elapsed_time'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds() / 60

            df['is_error'] = df['status'].apply(lambda x: 1 if x == 'RED_DETECTED' else 0)

            df['cumulative_error'] = df['is_error'].cumsum() 

            chart_data = df[['elapsed_time', 'cumulative_error']].copy()
            chart_data = chart_data.set_index('elapsed_time')

            st.line_chart(chart_data)
            st.caption("X축: 가동 경과 시간 (분) / Y축: 누적 불량 발생 건수")
        else:
            st.info("수집된 로그 데이터가 없습니다.")
    
    if st.session_state['show_chat']:
        with col_chat:
            st.markdown("<div class='chat-panel'>", unsafe_allow_html=True)
            st.subheader("AI 분석 어이스턴트")

            if st.button("AI 분석 보고서 생성", use_container_width=True, type="primary"):
                
                with st.spinner("벡터 DB 동기화 및 RAG 동작 중..."):
                    rag_engine.db_to_vector('factory_log.db')
                    report = rag_engine.get_answer("현재까지의 전체 공정 불량 패턴을 분석하고 개선 방안을 마크다운 형식으로 정리해서 보고서 형태로 만들어줘.")
                st.session_state['chat_history'].append({"role": "assistant", "content": report})
                st.rerun()
            
            st.markdown("----------------")

            chat_container = st.container(height=500)
            with chat_container:
                for msg in st.session_state['chat_history']:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            if prompt := st.chat_input("공정에 대해 질문해 보세요."):
                st.session_state['chat_history'].append({"role": "user", "content": prompt})

                with st.spinner("ChatGPT가 답변을 생성 중..."):
                    agent = create_factory_agent()
                    ai_response = agent.invoke({"messages": [("user", prompt)]})

                st.session_state['chat_history'].append({"role": "assistant", "content": ai_response['messages'][-1].content})
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state['logged_in']:
    login()
else:
    run_dashboard()

    st.markdown("---")
    if st.button("로그아웃"):
        st.session_state['logged_in'] = False
        st.rerun()