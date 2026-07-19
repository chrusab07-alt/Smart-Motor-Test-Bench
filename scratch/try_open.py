import serial
try:
    s = serial.Serial("COM4", baudrate=115200, timeout=1)
    print(f"Successfully opened COM4: {s}")
    print("Reading 5 lines:")
    for _ in range(5):
        line = s.readline()
        print(f"Read: {repr(line)}")
    s.close()
except Exception as e:
    print(f"Failed to open/read COM4: {e}")
