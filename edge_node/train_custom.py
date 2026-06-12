import os
import random
import shutil
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

def split_dataset(dataset_dir, val_ratio=0.15, test_ratio=0.10):
    train_img_dir = os.path.join(dataset_dir, "train", "images")
    train_lbl_dir = os.path.join(dataset_dir, "train", "labels")
    
    val_img_dir = os.path.join(dataset_dir, "valid", "images")
    val_lbl_dir = os.path.join(dataset_dir, "valid", "labels")
    test_img_dir = os.path.join(dataset_dir, "test", "images")
    test_lbl_dir = os.path.join(dataset_dir, "test", "labels")

    if os.path.exists(val_img_dir) and len(os.listdir(val_img_dir)) > 0:
        print("[INFO] 검증 세트가 이미 존재하여 분할 과정을 스킵합니다.")
        return

    os.makedirs(val_img_dir, exist_ok=True)
    os.makedirs(val_lbl_dir, exist_ok=True)
    os.makedirs(test_img_dir, exist_ok=True)
    os.makedirs(test_lbl_dir, exist_ok=True)

    if not os.path.exists(train_img_dir):
        print(f"[ERROR] train/images 폴더 없음: {train_img_dir}")
        return

    images = [f for f in os.listdir(train_img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if len(images) == 0:
        return

    random.seed(42)
    random.shuffle(images)

    total_count = len(images)
    val_count = int(total_count * val_ratio)
    test_count = int(total_count * test_ratio)

    val_images = images[:val_count]
    test_images = images[val_count:val_count + test_count]
    
    print(f"[INFO] {total_count}개 파일 중 {val_count}개를 valid 세트로 이동")
    for img_name in val_images:
        src_img = os.path.join(train_img_dir, img_name)
        dst_img = os.path.join(val_img_dir, img_name)
        if os.path.exists(src_img):
            shutil.move(src_img, dst_img)
        
        lbl_name = os.path.splitext(img_name)[0] + ".txt"
        src_lbl = os.path.join(train_lbl_dir, lbl_name)
        dst_lbl = os.path.join(val_lbl_dir, lbl_name)
        if os.path.exists(src_lbl):
            shutil.move(src_lbl, dst_lbl)

    print(f"[INFO] {total_count}개 파일 중 {test_count}개를 test 세트로 이동")
    for img_name in test_images:
        src_img = os.path.join(train_img_dir, img_name)
        dst_img = os.path.join(test_img_dir, img_name)
        if os.path.exists(src_img):
            shutil.move(src_img, dst_img)
        
        lbl_name = os.path.splitext(img_name)[0] + ".txt"
        src_lbl = os.path.join(train_lbl_dir, lbl_name)
        dst_lbl = os.path.join(test_lbl_dir, lbl_name)
        if os.path.exists(src_lbl):
            shutil.move(src_lbl, dst_lbl)

    print("[INFO] 데이터셋 자동 분할 완료!")

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(current_dir, "dataset", "SmartFactory-3")
    data_yaml_path = os.path.join(dataset_dir, "data.yaml")
    
    if not os.path.exists(data_yaml_path):
        raise FileNotFoundError(f"data.yaml 파일을 찾을 수 없습니다: {data_yaml_path}")
        
    print(f"[INFO] 설정 파일 로드 성공: {data_yaml_path}")
    
    split_dataset(dataset_dir)
    
    device = check_device()
    
    print("[INFO] YOLOv8n 모델 로딩 중...")
    model = YOLO("yolov8n.pt")
    
    print("[INFO] 학습 시작...")
    model.train(
        data=data_yaml_path,
        epochs=80,
        imgsz=640,
        device=device,
        workers=2,
        patience=20,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        fliplr=0.5,
        project=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs", "detect", "factory_project"),
        name="custom_inspector",
        exist_ok=True,
        verbose=True
    )
    
    print("\n[✔] 학습이 완료되었습니다!")
    print("[✔] 결과 저장 경로: 'edge_node/runs/detect/factory_project/custom_inspector/weights/best.pt'")

if __name__ == "__main__":
    main()
