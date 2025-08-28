/*
 * Elegoo Uno R3
 * Pin Config:
 * - IR Receiver: Pin 10
 * - Status LED: Pin 13
 * - Debug LED: Pin 12
 */

#include <Arduino.h>
#include <IRremote.hpp>

const int RECV_PIN = 10;           
const int STATUS_LED = 13;         
const int DEBUG_LED = 12;          
const unsigned long BAUD_RATE = 9600;

unsigned long lastValidCodeTime = 0;
uint32_t lastValidCode = 0;
decode_type_t lastValidProtocol = UNKNOWN;

void setup() {
  Serial.begin(BAUD_RATE);

  pinMode(STATUS_LED, OUTPUT);
  pinMode(DEBUG_LED, OUTPUT);

  
  delay(500);

  IrReceiver.begin(RECV_PIN, ENABLE_LED_FEEDBACK);  

  
  blinkLED(STATUS_LED, 3, 200);

  Serial.println(F("=== IR Remote Receiver v4.x ==="));
  Serial.println(F("Serial communication OK"));
  Serial.println(F("Waiting for valid IR signals..."));
  Serial.println(F("====================================="));

  digitalWrite(STATUS_LED, HIGH);
}

void loop() {
  if (IrReceiver.decode()) {
    processIRSignal();
    IrReceiver.resume(); 
  }

  handleSerialCommands();
  handleStatusLED();

  delay(50); 
}

void processIRSignal() {
  unsigned long currentTime = millis();

  
  digitalWrite(DEBUG_LED, HIGH);

  auto &data = IrReceiver.decodedIRData;

  
  if (!isValidIRSignal(data)) {
    digitalWrite(DEBUG_LED, LOW);
    return;
  }

  
  if (isRepeatSignal(data, currentTime)) {
    digitalWrite(DEBUG_LED, LOW);
    return;
  }

  
  String protocolName = getProtocolName(data.protocol);

  Serial.println(F("--- Valid IR Signal Detected ---"));
  Serial.print(F("Protocol: "));
  Serial.println(protocolName);
  Serial.print(F("Raw Value: 0x"));
  Serial.println(data.decodedRawData, HEX);
  Serial.print(F("Bits: "));
  Serial.println(data.numberOfBits);

  if (data.protocol != UNKNOWN) {
    uint16_t command = data.command;
    uint16_t address = data.address;

    Serial.print(F("Command: 0x"));
    if (command < 0x10) Serial.print(F("0"));
    Serial.println(command, HEX);

    Serial.print(F("Address: 0x"));
    if (address < 0x10) Serial.print(F("0"));
    Serial.println(address, HEX);
  }

  Serial.println(F("--------------------------------"));

  
  lastValidCode = data.decodedRawData;
  lastValidProtocol = data.protocol;
  lastValidCodeTime = currentTime;

  digitalWrite(DEBUG_LED, LOW);
}

bool isValidIRSignal(const IRData &data) {
  if (data.protocol == UNKNOWN && data.decodedRawData == 0) {
    return false;
  }
  if (data.numberOfBits < 8) {
    return false; 
  }
  if (data.decodedRawData == 0x0 || data.decodedRawData == 0x1200 || data.decodedRawData == 0xFFFFFFFF) {
    return false;
  }
  return true;
}

bool isRepeatSignal(const IRData &data, unsigned long currentTime) {
  return (data.decodedRawData == lastValidCode &&
          data.protocol == lastValidProtocol &&
          (currentTime - lastValidCodeTime) < 300);
}

String getProtocolName(decode_type_t protocol) {
  switch (protocol) {
    case NEC: return F("NEC");
    case SONY: return F("SONY");
    case RC5: return F("RC5");
    case RC6: return F("RC6");
    case SAMSUNG: return F("SAMSUNG");
    case LG: return F("LG");
    case JVC: return F("JVC");
    case PANASONIC: return F("PANASONIC");
    case WHYNTER: return F("WHYNTER");
    default: return F("UNKNOWN");
  }
}

void handleStatusLED() {
  static unsigned long lastToggle = 0;
  static bool ledState = false;
  unsigned long currentTime = millis();

  
  if (currentTime - lastValidCodeTime > 5000) {
    if (currentTime - lastToggle > 2000) {
      ledState = !ledState;
      digitalWrite(STATUS_LED, ledState);
      lastToggle = currentTime;
    }
  } else {
    digitalWrite(STATUS_LED, HIGH);
  }
}

void handleSerialCommands() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    command.toUpperCase();

    if (command == "STATUS") {
      Serial.println(F("System Status: READY"));
      Serial.print(F("Last valid code: 0x"));
      Serial.println(lastValidCode, HEX);
      Serial.print(F("Time since last code: "));
      Serial.print((millis() - lastValidCodeTime) / 1000);
      Serial.println(F(" seconds"));
    } 
    else if (command == "TEST") {
      Serial.println(F("Serial communication test: OK"));
      blinkLED(STATUS_LED, 2, 100);
    }
    else if (command == "RESET") {
      Serial.println(F("Resetting IR receiver..."));
      IrReceiver.start();
      Serial.println(F("Reset complete"));
    }
    else if (command == "HELP") {
      Serial.println(F("Available commands:"));
      Serial.println(F("  STATUS - Show system status"));
      Serial.println(F("  TEST   - Test serial communication"));
      Serial.println(F("  RESET  - Reset IR receiver"));
      Serial.println(F("  HELP   - Show this help"));
    }
  }
}

void blinkLED(int pin, int times, int delayMs) {
  bool originalState = digitalRead(pin);
  for (int i = 0; i < times; i++) {
    digitalWrite(pin, HIGH);
    delay(delayMs);
    digitalWrite(pin, LOW);
    delay(delayMs);
  }
  digitalWrite(pin, originalState);
}
