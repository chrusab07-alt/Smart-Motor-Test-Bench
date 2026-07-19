/*
 * Smart Motor Test Bench
 * Two-Way Serial Communication Sketch
 *
 * Telemetry Format: RPM,Voltage,Current,Power,Efficiency,PWM
 * Default Baud Rate: 115200
 */

unsigned long lastUpdate = 0;
const unsigned long updateInterval = 100; // 10Hz telemetry transmission

// System State
bool motorRunning = false; // Initially stopped
int pwmDuty = 0;
String direction = "FWD";

// Non-blocking serial reading buffer
const byte MAX_CMD_LEN = 32;
char cmdBuffer[MAX_CMD_LEN];
byte cmdIndex = 0;

void setup() {
  Serial.begin(115200);
}

void loop() {
  // 1. Process Incoming Serial Commands Non-Blockingly
  while (Serial.available() > 0) {
    char c = Serial.read();
    
    // Check for end of line (either newline or carriage return)
    if (c == '\n' || c == '\r') {
      if (cmdIndex > 0) {
        cmdBuffer[cmdIndex] = '\0'; // Null-terminate the string
        processCommand(cmdBuffer);
        cmdIndex = 0; // Reset buffer for the next command
      }
    } else {
      // Append character to buffer if space allows
      if (cmdIndex < MAX_CMD_LEN - 1) {
        cmdBuffer[cmdIndex] = c;
        cmdIndex++;
      }
    }
  }

  // 2. Transmit Telemetry Data without blocking
  unsigned long currentMillis = millis();
  if (currentMillis - lastUpdate >= updateInterval) {
    lastUpdate = currentMillis;
    sendTelemetry();
  }
}

void processCommand(const char* cmd) {
  String command = String(cmd);
  command.trim(); // Remove leading/trailing whitespace
  
  if (command == "START") {
    motorRunning = true;
  } 
  else if (command == "STOP") {
    motorRunning = false;
  }
  else if (command.startsWith("PWM:")) {
    // Extract the numeric value after "PWM:"
    String valueStr = command.substring(4);
    pwmDuty = valueStr.toInt();
  }
  else if (command.startsWith("DIR:")) {
    // Extract the direction after "DIR:"
    direction = command.substring(4);
  }
}

void sendTelemetry() {
  float voltage = 12.20; // Simulated supply voltage remains constant
  
  if (!motorRunning) {
    // When STOP is pressed, immediately output zeroes
    // Format: RPM,Voltage,Current,Power,Efficiency,PWM,Direction
    Serial.print("0.00,");
    Serial.print(voltage, 2);
    Serial.print(",0.00,0.00,0.00,0,");
    Serial.println(direction);
    return;
  }
  
  float rpm = 0.0;
  float current = 0.0;
  float power = 0.0;
  float efficiency = 0.0;

  // Read real sensors (placeholders)
  // Map ADC (0-1023) to arbitrary ranges for demonstration
  rpm = analogRead(A0) * 2.0;
  current = analogRead(A1) * (5.0 / 1023.0);
  power = voltage * current;
  efficiency = (power > 0) ? (power / (power + 5.0)) * 100.0 : 0.0;
  
  // Transmit telemetry CSV string
  Serial.print(rpm, 2);
  Serial.print(",");
  Serial.print(voltage, 2);
  Serial.print(",");
  Serial.print(current, 2);
  Serial.print(",");
  Serial.print(power, 2);
  Serial.print(",");
  Serial.print(efficiency, 2);
  Serial.print(",");
  Serial.print(pwmDuty);
  Serial.print(",");
  Serial.println(direction);
}
