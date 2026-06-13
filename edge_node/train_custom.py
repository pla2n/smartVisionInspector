import os
import torch
from ultralytics import YOLO

def check_device():
    if torch.backends.mps.is_available():
        print("[INFO] Apple Silicon GPU (MPS) 사용")
        return "mps"
    elif torch.cuda.is_available():
        print("[INFO] Nvidia GPU (CUDA) 사용")
        return 0
    else:
        print("[INFO] CPU 사용")
        return "cpu"

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    runs_dir = os.path.join(os.path.dirname(current_dir), "runs", "detect", "factory_project")
    best_model_path = os.path.join(runs_dir, "custom_inspector", "weights", "best.pt")

    data_yaml_path = os.path.join(current_dir, "dataset", "SmartFactory-5", "data.yaml")
    if not os.path.exists(data_yaml_path):
        raise FileNotFoundError(
            f"데이터셋을 찾을 수 없습니다: {data_yaml_path}\n"
            f"Roboflow에서 다운로드한 폴더가 edge_node/ 안에 있는지 확인하세요."
        )

    if os.path.exists(best_model_path):
        base_model = best_model_path
        print(f"[INFO] 기존 best.pt에서 파인튜닝: {best_model_path}")
    else:
        base_model = "yolov8n.pt"
        print("[INFO] best.pt 없음 → yolov8n.pt에서 학습 시작")

    device = check_device()

    print(f"[INFO] 모델 로딩: {base_model}")
    model = YOLO(base_model)

    print("[INFO] 학습 시작...\n")
    model.train(
        data=data_yaml_path,
        epochs=40,
        imgsz=640,
        device=device,
        workers=2,
        patience=10,
        lr0=0.001,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        fliplr=0.5,
        project=runs_dir,
        name="custom_inspector_v2",
        exist_ok=True,
        verbose=True
    )

    result_path = os.path.join(runs_dir, "custom_inspector_v2", "weights", "best.pt")
    print(f"\n[✔] 학습 완료!")
    print(f"[✔] 가중치 저장 경로: {result_path}")

if __name__ == "__main__":
    main()
