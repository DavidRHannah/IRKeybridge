#include <Arduino.h>
#include <IRremote.h>

// Define the pin your IR receiver is connected to
const int RECV_PIN = 11;

IRrecv irrecv(RECV_PIN);
decode_results results;

void setup() {
  Serial.begin(9600);  // Match your Python script's baud rate
  irrecv.enableIRIn(); // Start the receiver
}

void loop() {
  if (irrecv.decode(&results)) {
    if (results.decode_type == NEC) {
      // Extract command portion and print as hex (e.g. 0x45)
      Serial.print("0x");
      if (results.command < 0x10) Serial.print("0"); // pad 0 for nicer output
      Serial.println(results.command, HEX);
    } else {
      Serial.println("Unknown IR protocol");
    }

    irrecv.resume(); // Receive the next value
  }
}