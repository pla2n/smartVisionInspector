import serial
import sqlite3
import time
import cv2
import os
from datetime import datetime
from ultralytics import YOLO
import requests
import threading
from flask import Flask, Response

ARDUINO_PORT = '/dev/cu.usbmodem1101'
BAUD_RATE = 9600

IMAGE_DIR = "captured_imgs"
os.makedirs(IMAGE_DIR, exist_ok=True)

API_URL = "http://localhost:8000/api/settings"
CONFIDENCE_THRESHOLD = 0.3
IS_RUNNING = True
latest_frame = None

print("YOLO모델 로딩중...")
model = YOLO('yolov8n.pt')

# --- 1. 설정 동기화 ---
def sync_settings():
    global CONFIDENCE_THRESHOLD, IS_RUNNING
    try:
        resp = requests.get(API_URL).json()
        CONFIDENCE_THRESHOLD = resp['confidence']
        IS_RUNNING = bool(resp['is_running'])
    except Exception:
        pass
    threading.Timer(2.0, sync_settings).start()

# --- 2. 대시보드 영상 스트리밍 (Flask) ---
app = Flask(__name__)

def generate_frames():
    global latest_frame
    while True:
        if latest_frame is None:
            time.sleep(0.01)
            continue
        ret, buffer = cv2.imencode('.jpg', latest_frame)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def run_streaming_server():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# --- 3. [스레드 1] 웹캠 전담 루프 ---
def camera_streaming_loop():
    global latest_frame
    cap = cv2.VideoCapture(0)
    print("카메라 구동 시작 (스레드 분리 완료)")
    
    while True:
        ret, frame = cap.read()
        if ret:
            latest_frame = frame.copy()
        time.sleep(0.03) # CPU 점유율 최적화 (약 30fps)

# --- 4. [메인] AI 추론 및 아두이노 제어 ---
def ai_inference_loop():
    global latest_frame
    print(f"엣지 디바이스({ARDUINO_PORT}) 연결 시도 중...")
    
    # DB 연결 (스레드 충돌 방지 옵션 추가)
    conn = sqlite3.connect('factory_log.db', check_same_thread=False)
    
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print("엣지 통신 완료. 스마트 팩토리 관제 시작!")
        
        while True:
            if not IS_RUNNING: # 대시보드에서 시스템 정지 시
                time.sleep(0.1)
                continue
                
            if ser.in_waiting > 0:
                raw_data = ser.readline().decode('utf-8').strip()
                
                # 아두이노에서 물체 감지 신호가 왔을 때
                if raw_data == "DETECTED" and latest_frame is not None:
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[알림] {now} | 물체 감지! 최신 프레임 1장만 낚아채서 분석 시작")
                    
                    frame_to_analyze = latest_frame.copy()
                    current_results = model(frame_to_analyze, verbose=False)
                    
                    is_defective = False
                    detected_items = []
                    
                    for r in current_results:
                        for box in r.boxes:
                            class_name = model.names[int(box.cls[0])]
                            confidence = float(box.conf[0])
                            detected_items.append(class_name)
                            
                            # 대시보드에서 설정한 임계값(CONFIDENCE_THRESHOLD) 적용
                            if class_name in ['pizza', 'toilet', 'chair', 'person', 'bed'] and confidence > CONFIDENCE_THRESHOLD:
                                is_defective = True
                                
                    print(f"탐지 결과: {detected_items}")
                    
                    img_filename = "-"
                    if is_defective:
                        print("불량 발견! 컨베이어 일시 정지 후 불량품 제거 시도")
                        ser.write(b"RED\n")
                        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                        img_filename = f"error_{current_time}.jpg"
                        cv2.imwrite(os.path.join(IMAGE_DIR, img_filename), frame_to_analyze)
                        status = "RED_DETECTED"
                    else:
                        print("정상 제품. 통과")
                        ser.write(b"PASS\n")
                        status = "PASS"
                        
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO logs (timestamp, status, sensor_data, img_filename) VALUES (?, ?, ?, ?)",
                                (now, status, f"YOLO: {str(detected_items)}", img_filename))
                    conn.commit()
                        
            time.sleep(0.01)

    except serial.SerialException:
        print(f"장애 발생! {ARDUINO_PORT} 포트를 찾을 수 없습니다.")
    except KeyboardInterrupt:
        print("서버를 안전하게 종료합니다.")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    # 1. 설정 동기화 백그라운드 시작
    sync_settings()
    # 2. Flask 영상 스트리밍 스레드 시작
    threading.Thread(target=run_streaming_server, daemon=True).start()
    # 3. 카메라 전용 스레드 시작
    threading.Thread(target=camera_streaming_loop, daemon=True).start()
    
    # 4. 메인 스레드에서는 AI 및 하드웨어 로직 실행
    ai_inference_loop()