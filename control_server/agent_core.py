import sqlite3
import base64
import os
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from config import OPENAI_API_KEY

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
LIMIT = 1000

@tool
def query_db_statistics(question: str) -> str:
    """
    정확한 숫자 정보 사용
    """
    try:
        conn = sqlite3.connect('factory_log.db')
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM logs")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM logs WHERE status='RED_DETECTED'")
        defect = cursor.fetchone()[0]

        df = pd.read_sql_query("SELECT * FROM logs ORDER BY timestamp DESC LIMIT {LIMIT}", conn)

        conn.close()

        defect_rate = round((defect / total * 100), 1) if total > 0 else 0
        return f"DB 조회 결과: 총 검사량 {total}개, 불량품 {defect}개, 현재 불량률 {defect_rate}% 입니다."
    except Exception as e:
        return f"DB 조회 중 오류 발생: {e}"

def encode_img(img_path):
    """
    base64 인코딩
    """
    with open(img_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

@tool
def analyze_defect_img(img_filename: str) -> str:
    """
    사용자가 사진 분석 요청 시 사용. 파일 이름은 'error_11.jpg와 같은 형식이여야합니다.
    """
    img_path = os.path.join("captured_imgs", img_filename)

    if not os.path.exists(img_path):
        return f"오류: {img_path} 경로에 일치하는 파일이 존재하지 않습니다."

    try:
        base64_img = encode_img(img_path)

        vision_llm = ChatOpenAI(model="gpt-4o", max_tokens=300)

        response = vision_llm.invoke([
            {"role": "system", "content": "당신은 공장의 품질 관리 전문가입니다. 주어진 사진을 보고 문제를 정확히 분석하고 5줄 안으로 간결히 정리한 보고서를 출력하세요."},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
            ]}
        ])
        return f"[Vision AI 분석 결과]: {response.content}"
    except Exception as e:
        return f"사진 분석 중 오류 발생: {e}"

def create_factory_agent():
    """
    필요에 따라 AI가 도구 선택
    """
    tools = [query_db_statistics, analyze_defect_img]

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    system_prompt = """
        너는 스마트 팩토리의 AI 관제 전문가야.
        사용자의 질문에 따라 적절한 응답을 생성해야해.
        1. 높은 수준의 분석을 요구하거나 사진에 관한 요청이 있다면 'analyze_defect_img'를 사용해.
        2. 그게 아니라 공정에 관한 질문이면 'query_db_statistics'를 사용해.
        3. 위 두가지에 속하지 않는 질문이면, 그냥 너의 전문 지식을 기반으로 대답해줘."""

    agent = create_react_agent(llm, tools, prompt=system_prompt)

    return agent

if __name__ == "__main__":
    agent = create_factory_agent()
    print("에이전트 연결 중...")

    while True:
        user_input = input("\n질문을 입력하세요.")
        if user_input.lower() == 'exit':
            break

        result = agent.invoke({"messages": [("user", user_input)]})
        print(f"\nAI의 답변: {result['messages'][-1].content}")