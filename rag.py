from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
import pandas as pd
import sqlite3

class RagEngine:
    def __init__(self, api_key):
        self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        self.llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=api_key, temperature=0)
        self.vector_db = None

    def db_to_vector(self, db_path):
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM logs", conn)
        conn.close()

        documents = []
        for _, row in df.iterrows():
            content = f"시간: {row['timestamp']}, 상태: {row['status']}, 탐지결과: {row['sensor_data']}"
            documents.append(Document(page_content=content, metadata={"id": row['timestamp']}))

        self.vector_db = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
        )
    
    def get_answer(self, query):
        if not self.vector_db:
            return "데이터가 없습니다."

        prompt_template = """
        너는 스마트 팩토리 데이터 분석 전문가야. 제공된 공정 로그를 기반으로 질문에 대답해줘. 대답은 거짓이 없어야해.
        오류는 status가 RED_DETECTED, ERROR_CONNECTION일 때 오류라고 해.

        [공정 로그]
        {context}

        질문: {question}
        AI 분석 전문가의 답변:
        """

        PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_db.as_retriever(search_kwargs={"k": len(self.vector_db)}),
            chain_type_kwargs={"prompt": PROMPT}
        )

        return chain.invoke(query)["result"]