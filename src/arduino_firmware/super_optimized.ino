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
    if (IrReceiver.decodedIRData.protocol != UNKNOWN && 
        IrReceiver.decodedIRData.decodedRawData != 0) {
      Serial.print(F("0x"));
      Serial.println(IrReceiver.decodedIRData.decodedRawData, HEX);
    }
    IrReceiver.resume();
  }
}


