import cv2
import os
import argparse
import time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--class', dest='cls', required=True,
                        choices=['normal', 'broken', 'stained'],
                        help='촬영할 클래스 이름')
    args = parser.parse_args()

    save_dir = os.path.join('custom_data', args.cls)
    os.makedirs(save_dir, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("카메라 열기 실패")
        return

    count = len([f for f in os.listdir(save_dir) if f.endswith('.jpg')])
    print(f"\n[클래스: {args.cls}] 저장 경로: {save_dir}")
    print("스페이스바 = 저장 | Q = 종료\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display = frame.copy()
        cv2.putText(display, f"Class: {args.cls} | Saved: {count}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(display, "SPACE: save  Q: quit",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.imshow('Data Capture', display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            filename = os.path.join(save_dir, f"{args.cls}_{count:04d}.jpg")
            cv2.imwrite(filename, frame)
            count += 1
            print(f"  저장됨: {filename}")

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n완료. 총 {count}장 저장됨 → {save_dir}")

if __name__ == '__main__':
    main()
