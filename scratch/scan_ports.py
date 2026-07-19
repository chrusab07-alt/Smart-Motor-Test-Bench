import serial
print("Scanning ports COM1 to COM10...")
for i in range(1, 11):
    port = f"COM{i}"
    try:
        s = serial.Serial(port)
        s.close()
        print(f"Port {port} is AVAILABLE")
    except serial.SerialException as e:
        err = str(e)
        if "PermissionError" in err or "Access is denied" in err:
            print(f"Port {port} is BUSY / ALREADY IN USE")
        elif "FileNotFoundError" in err or "cannot find the file specified" in err:
            # Port does not exist
            pass
        else:
            print(f"Port {port} failed with: {err}")
    except Exception as e:
        print(f"Port {port} unexpected error: {e}")
print("Scan complete.")
