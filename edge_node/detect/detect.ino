#include <Servo.h>
#include <Stepper.h>

const int stepsPerRevolution = 2048;
Stepper myStepper(stepsPerRevolution, 8, 10, 9, 11);

const int trigPin = 3;
const int echoPin = 2;

// 서보모터
Servo ejectServo;
const int servoPin = 4;
const int idleAngle = 90;
const int ejectAngle = 0;

unsigned long lastHeartbeat = 0;

void setup() {
  myStepper.setSpeed(15);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  ejectServo.attach(servoPin);
  ejectServo.write(idleAngle);

  Serial.begin(9600);
}

void loop() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  long distance = duration * 0.034 / 2;

  if (distance > 1 && distance < 5) {
    Serial.println("DETECTED");

    unsigned long waitStart = millis();
    bool serverResponded = false;
    String response = "";

    while (millis() - waitStart < 5000) {
      if (Serial.available() > 0) {
        response = Serial.readStringUntil('\n');
        response.trim();
        serverResponded = true;
        break;
      }
    }

    if (!serverResponded) {
      Serial.println("ERROR_CONNECTION");
      while (true)
        ;
    } else {
      if (response == "RED") {
        Serial.println("RED_DETECTED");

        // 컨베이어 정지 후 서보로 불량품 배출
        ejectServo.write(ejectAngle);
        delay(800);
        ejectServo.write(idleAngle);
        delay(800);

        // 배출된 물건이 센서 구역을 완전히 벗어날 때까지 벨트 이동
        for (int i = 0; i < 200; i++) {
          myStepper.step(10);
        }
      } else {
        Serial.println("PASS");

        // 정상품: 벨트를 충분히 이동시켜 센서 구역 통과
        for (int i = 0; i < 300; i++) {
          myStepper.step(10);
        }
      }
    }
  } else {
    for (int i = 0; i < 100; i++) {
      myStepper.step(10);
    }

    if (millis() - lastHeartbeat > 3000) {
      Serial.println("PASS");
      lastHeartbeat = millis();
    }
  }
}