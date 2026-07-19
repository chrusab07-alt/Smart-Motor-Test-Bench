import serial.tools.list_ports
ports = serial.tools.list_ports.comports()
print("Available ports:")
for p in ports:
    print(f"Device: {p.device}, Name: {p.name}, Description: {p.description}")
