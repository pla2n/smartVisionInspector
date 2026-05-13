from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sqlite3
import pandas as pd
import asyncio

app = FastAPI(title="Smart Factory API")

global_frame = None

def get_db_connection():
    try:
        conn = sqlite3.connect('factory_log.db', check_same_thread=False)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB Connection Error: {e}")
    
@app.get("/api/stats")
def get_factory_stats():
    """대시보드 상단 지표를 위한 API"""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT status FROM logs", conn)
        total = len(df)
        defect = len(df[df['status'] == 'RED_DETECTED'])
        normal = total - defect
        rate = (defect / total * 100) if total > 0 else 0

        return {
            "total_count": total,
            "normal_count": normal,
            "defect_count": defect,
            "defect_rate": round(rate, 1)
        }
    finally:
        conn.close()

@app.get("/api/logs")
def get_factory_logs(limit: int = 500):
    """실시간 공정 로그 데이터 API"""
    conn = get_db_connection()
    try:
        query = f"SELECT timestamp, status, sensor_data FROM logs ORDER BY timestamp ASC LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        return df.to_dict(orient="records")
    finally:
        conn.close()

class SettingUpdate(BaseModel):
    confidence: float
    is_running: int

def init_settings():
    conn = get_db_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, confidence REAL, is_running INTEGER)")
    df = pd.read_sql_query("SELECT * FROM settings", conn)
    if df.empty:
        conn.execute("INSERT INTO settings (id, confidence, is_running) VALUES (1, 0.3, 1)")
        conn.commit()
    conn.close()

init_settings()

@app.get("/api/settings")
def get_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT confidence, is_running FROM settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return {"confidence": row[0], "is_running": row[1]}

@app.post("/api/settings")
def update_settings(settings: SettingUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET confidence = ?, is_running = ? WHERE id = 1",
                    (settings.confidence, settings.is_running))
    conn.commit()
    conn.close()
    return {"message": "설정이 성공적으로 업데이트 되었습니다."}

@app.post("/predict")
async def receive_defect(
    defect_type: str = Form(...),
    confidence: float = Form(...),
    file: UploadFile = File(...)
):
    """Edge 디바이스(Server.py)로부터 불량 감지 이미지와 정보를 수신하는 API"""
    try:
        file_location = f"received_{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())
            
        print(f"[{defect_type}] 수신 완료! (정확도: {confidence:.2f}, 파일명: {file_location})")
                
        return {
            "status": "success",
            "message": "서버 수신 완료",
            "saved_file": file_location,
            "defect_type": defect_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload_frame")
async def upload_frame(request: Request):
    """Edge 디바이스에서 전송하는 실시간 JPEG 프레임 바이트 수신"""
    global global_frame
    global_frame = await request.body()
    return {"status": "ok"}

async def frame_generator():
    global global_frame
    while True:
        if global_frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + global_frame + b'\r\n')
        await asyncio.sleep(0.05)

@app.get("/video_feed")
async def video_feed():
    """대시보드를 위한 MJPEG 스트리밍 송출"""
    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")