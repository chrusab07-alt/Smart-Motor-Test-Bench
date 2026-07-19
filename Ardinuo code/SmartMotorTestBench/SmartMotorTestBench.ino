/*
===========================================
Smart Motor Test Bench
Demo Mode (Random Values)
Output:
RPM,Voltage,Current,Power,Temperature,Efficiency
===========================================
*/

void setup() {
  Serial.begin(9600);
  randomSeed(analogRead(A0));   // Better random values
  delay(2000);
}

void loop() {

  // RPM: 1550 - 1800
  int rpm = random(1550, 1801);

  // Voltage: 11.80 - 12.40
  float voltage = random(1180, 1241) / 100.0;

  // Current: 0.55 - 0.95
  float current = random(70, 150) / 100.0;

  // Power
  float power = voltage * current;

  // Temperature: 28.0 - 35.0 °C
  float temperature = random(400, 650) / 10.0;

  // Efficiency: 78 - 90 %
  float efficiency = random(780, 901) / 10.0;

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