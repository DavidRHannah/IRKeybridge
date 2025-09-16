#include <Arduino.h>
#include <IRremote.hpp>

const int RECV_PIN = 10;
const unsigned long BAUD_RATE = 115200;

const unsigned long REPEAT_THRESHOLD = 150;
const unsigned long MIN_CODE_INTERVAL = 50;

uint32_t lastCode = 0;
unsigned long lastCodeTime = 0;
bool initialized = false;

void setup() {
  Serial.begin(BAUD_RATE);
  IrReceiver.begin(RECV_PIN, false);
  IrReceiver.setReceivePin(RECV_PIN);

  Serial.println(F("READY"));
  initialized = true;
}

void loop() {
  if (IrReceiver.decode()) {
    processIRSignal();
    IrReceiver.resume();
  }
}

inline void processIRSignal() {
  unsigned long currentTime = millis();
  auto &data = IrReceiver.decodedIRData;
  
  if (data.protocol == UNKNOWN || 
      data.decodedRawData == 0 || 
      data.numberOfBits < 8) {
    return;
  }
  
  if (data.decodedRawData == lastCode) {
    unsigned long timeDiff = currentTime - lastCodeTime;
    if (timeDiff < MIN_CODE_INTERVAL) {
      return; 
    }
    if (timeDiff < REPEAT_THRESHOLD) {
      return;
    }
  }
  
  Serial.print(F("0x"));
  Serial.println(data.decodedRawData, HEX);
  
  lastCode = data.decodedRawData;
  lastCodeTime = currentTime;
}

void serialEvent() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'S') { 
      Serial.print(F("OK:"));
      Serial.println(lastCode, HEX);
    } else if (c == 'R') { 
      lastCode = 0;
      lastCodeTime = 0;
      IrReceiver.resume();
      Serial.println(F("RST"));
    }
    while (Serial.available()) Serial.read();
  }
}
