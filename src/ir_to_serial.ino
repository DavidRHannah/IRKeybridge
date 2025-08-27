#include <Arduino.h>
#include <IRremote.h>

const int RECV_PIN = 11;

IRrecv irrecv(RECV_PIN);
decode_results results;

void setup() {
  Serial.begin(9600);
  irrecv.enableIRIn();
}

void loop() {
  if (irrecv.decode(&results)) {
    if (results.decode_type == NEC) {
      Serial.print("0x");
      if (results.command < 0x10) Serial.print("0");
      Serial.println(results.command, HEX);
    } else {
      Serial.println("Unknown IR protocol");
    }

    irrecv.resume();
  }
}