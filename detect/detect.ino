#include <Stepper.h>
#include <Servo.h>

const int stepsPerRevolution = 2048;
Stepper myStepper(stepsPerRevolution, 8, 10, 9, 11);

const int trigPin = 3;
const int echoPin = 2;

//서보모터
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
    digitalWrite(trigPin, LOW); delayMicroseconds(2);
    digitalWrite(trigPin, HIGH); delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    long duration = pulseIn(echoPin, HIGH);
    long distance = duration * 0.034 / 2;

    if (distance > 1 && distance < 10) {
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
            while(true);
        } else {
            if (response == "RED") {
                Serial.println("RED_DETECTED");
                
                ejectServo.write(ejectAngle);
                delay(800);
                ejectServo.write(idleAngle);
                delay(800);
            } else {
                Serial.println("PASS");
                delay(1000);
            }
        }
    } else {
        for (int i=0; i<100; i++) {
            myStepper.step(10);
            digitalWrite(trigPin, LOW); delayMicroseconds(2);
            digitalWrite(trigPin, HIGH); delayMicroseconds(10);
            digitalWrite(trigPin, LOW);
            long dur = pulseIn(echoPin, HIGH, 30000);
            long dist = dur * 0.034 / 2;
            if (dist > 0 && dist < 20) {
                break;
            }
        }

        if (millis() - lastHeartbeat > 3000) {
            Serial.println("PASS");
            lastHeartbeat = millis();
        }
    }
}