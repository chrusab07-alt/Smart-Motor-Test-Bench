import serial

def check_port_access(port):
    try:
        s = serial.Serial(port)
        s.close()
        print(f"Successfully opened {port}.")
    except serial.SerialException as e:
        print(f"Failed to open {port}: {e}")

if __name__ == "__main__":
    check_port_access("COM4")
