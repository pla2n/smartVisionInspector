from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import sqlite3
import pandas as pd
import asyncio
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Smart Factory API")

API_KEY = os.getenv("API_SECRET_KEY", "change-me")
api_key_header = APIKeyHeader(name='X-API-Key', auto_error=False)

async def verify_api_key(key: str = Depends(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="인가되지 않은 접근입니다.")

UPLOAD_DIR = Path("received_imgs")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

global_frame = None

class LogEntry(BaseModel):
    timestamp: str
    status: str
    sensor_data: str
    img_filename: str

def get_db_connection():
    try:
        conn = sqlite3.connect('factory_log.db', check_same_thread=False)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB Connection Error: {e}")
    
@app.get("/api/stats", dependencies=[Depends(verify_api_key)])
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

@app.get("/api/logs", dependencies=[Depends(verify_api_key)])
def get_factory_logs(limit: int = 500):
    limit = max(1, min(limit, 1000))
    """실시간 공정 로그 데이터 API"""
    conn = get_db_connection()
    try:
        query = "SELECT * FROM (SELECT timestamp, status, sensor_data FROM logs ORDER BY timestamp DESC LIMIT ?) ORDER BY timestamp ASC"
        df = pd.read_sql_query(query, conn, params=(limit,))
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

@app.get("/api/settings", dependencies=[Depends(verify_api_key)])
def get_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT confidence, is_running FROM settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return {"confidence": row[0], "is_running": row[1]}

@app.post("/api/settings", dependencies=[Depends(verify_api_key)])
def update_settings(settings: SettingUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET confidence = ?, is_running = ? WHERE id = 1",
                    (settings.confidence, settings.is_running))
    conn.commit()
    conn.close()
    return {"message": "설정이 성공적으로 업데이트 되었습니다."}

@app.post("/predict", dependencies=[Depends(verify_api_key)])
async def receive_defect(
    defect_type: str = Form(...),
    confidence: float = Form(...),
    file: UploadFile = File(...)
):
    """Edge 디바이스(Server.py)로부터 불량 감지 이미지와 정보를 수신하는 API"""
    try:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다. JPG, JPEG, PNG만 가능합니다.")

        safe_filename = f"received_{uuid.uuid4().hex}{suffix}"
        file_location = UPLOAD_DIR / safe_filename

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

@app.post("/api/upload_frame", dependencies=[Depends(verify_api_key)])
async def upload_frame(request: Request):
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
    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.post("/api/logs", dependencies=[Depends(verify_api_key)])
def add_log(entry: LogEntry):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO logs (timestamp, status, sensor_data, img_filename) VALUES (?, ?, ?, ?)",
                       (entry.timestamp, entry.status, entry.sensor_data, entry.img_filename))
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return {"status": "ok"}