import serial
import sqlite3
import time
import cv2
import os
from datetime import datetime
from ultralytics import YOLO
import requests
import threading

ARDUINO_PORT = '/dev/cu.usbmodem1101'
BAUD_RATE = 9600

IMAGE_DIR = "captured_imgs"
os.makedirs(IMAGE_DIR, exist_ok=True)

API_URL = "http://YOUR_SERVER_IP:8000/api/settings"
SERVER_URL = "http://YOUR_SERVER_IP:8000/predict"
CONFIDENCE_THRESHOLD = 0.3
IS_RUNNING = True
latest_frame = None

print("YOLO모델 로딩중...")
model = YOLO('yolov8n.pt')

def sync_settings():
    global CONFIDENCE_THRESHOLD, IS_RUNNING
    try:
        resp = requests.get(API_URL).json()
        CONFIDENCE_THRESHOLD = resp['confidence']
        IS_RUNNING = bool(resp['is_running'])
    except Exception:
        pass
    threading.Timer(2.0, sync_settings).start()

def camera_streaming_loop():
    global latest_frame
    cap = cv2.VideoCapture(0)
    print("카메라 구동 시작 (Edge-Push 스트리밍 스레드)")
    
    upload_url = "http://192.168.219.103:8000/api/upload_frame"
    
    while True:
        ret, frame = cap.read()
        if ret:
            latest_frame = frame.copy()
            
            ret_encode, buffer = cv2.imencode('.jpg', latest_frame)
            if ret_encode:
                try:
                    requests.post(upload_url, data=buffer.tobytes(), headers={'Content-Type': 'image/jpeg'}, timeout=0.5)
                except requests.exceptions.RequestException:
                    pass
                    
        time.sleep(0.06)

def ai_inference_loop():
    global latest_frame
    print(f"엣지 디바이스({ARDUINO_PORT}) 연결 시도 중...")
    
    conn = sqlite3.connect('factory_log.db', check_same_thread=False)
    
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print("엣지 통신 완료. 스마트 팩토리 관제 시작!")
        
        while True:
            if not IS_RUNNING:
                time.sleep(0.1)
                continue
                
            if ser.in_waiting > 0:
                raw_data = ser.readline().decode('utf-8').strip()
                
                if raw_data == "DETECTED" and latest_frame is not None:
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[알림] {now} | 물체 감지! 최신 프레임 1장만 낚아채서 분석 시작")
                    
                    frame_to_analyze = latest_frame.copy()
                    current_results = model(frame_to_analyze, verbose=False)
                    
                    is_defective = False
                    detected_items = []
                    defect_class = "Unknown"
                    defect_conf = 0.0
                    
                    for r in current_results:
                        for box in r.boxes:
                            class_name = model.names[int(box.cls[0])]
                            confidence = float(box.conf[0])
                            detected_items.append(class_name)
                            
                            if class_name in ['pizza', 'toilet', 'chair', 'person', 'bed'] and confidence > CONFIDENCE_THRESHOLD:
                                is_defective = True
                                defect_class = class_name
                                defect_conf = float(confidence)
                                
                    print(f"탐지 결과: {detected_items}")
                    
                    img_filename = "-"
                    if is_defective:
                        print(f"불량 발견({defect_class})! 컨베이어 일시 정지 후 불량품 제거 시도")
                        ser.write(b"RED\n")
                        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                        img_filename = f"error_{current_time}.jpg"
                        img_filepath = os.path.join(IMAGE_DIR, img_filename)
                        
                        cv2.imwrite(img_filepath, frame_to_analyze)

                        threading.Thread(target=send_defect_to_server, args=(defect_class, defect_conf, img_filepath), daemon=True).start()
                        
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

def send_defect_to_server(defect_type, confidence, image_path):
    print(f"{defect_type} 불량 감지! 서버 전송 시작")

    try:
        payload = {
            "defect_type": defect_type,
            "confidence": confidence
        }

        with open(image_path, "rb") as f:
            files = {"file": f}

            response = requests.post(SERVER_URL, data=payload, files=files)

        if response.status_code == 200:
            print("서버 전송 성공! 서버 응답:", response.json())
        else:
            print(f"전송 실패 {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("에러 : 서버 연결 불가.")

if __name__ == "__main__":
    sync_settings()
    threading.Thread(target=camera_streaming_loop, daemon=True).start()
    
    ai_inference_loop()