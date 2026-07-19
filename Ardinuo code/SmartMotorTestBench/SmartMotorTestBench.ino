/*
  Smart Motor Test Bench
  Demo Mode
  Output:
  RPM,Voltage,Current,Power,Temperature,Efficiency
*/

#include <Arduino.h>

float angle = 0;

void setup() {
  Serial.begin(9600);
  delay(2000);   // Allow serial connection to stabilize
}

void loop() {

  angle += 0.05;

  // Demo values
  int rpm = 1700 + 120 * sin(angle);

  float voltage = 12.10 + 0.25 * sin(angle * 0.7);

  float current = 0.80 + 0.15 * sin(angle * 1.2);

  float power = voltage * current;

  float temperature = 35.0 + 4.0 * sin(angle * 0.4);

  float efficiency = 82.0 + 6.0 * sin(angle * 0.5);

  // Keep efficiency within limits
  if (efficiency > 100) efficiency = 100;
  if (efficiency < 0) efficiency = 0;

  // Send data
  Serial.print(rpm);
  Serial.print(",");

  Serial.print(voltage, 2);
  Serial.print(",");

  Serial.print(current, 2);
  Serial.print(",");

  Serial.print(power, 2);
  Serial.print(",");

  Serial.print(temperature, 1);
  Serial.print(",");

  Serial.println(efficiency, 1);

  delay(500);
}