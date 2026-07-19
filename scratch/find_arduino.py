import subprocess

def find_devices():
    try:
        # Run PowerShell command to get all Win32_PnPEntity devices and filter them in Python to be safe and precise
        cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_PnPEntity | Select-Object Name, DeviceID | ConvertTo-Json -Depth 2"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            import json
            data = json.loads(result.stdout)
            if not isinstance(data, list):
                data = [data]
            print("Filtered Devices (containing COM or Arduino):")
            for dev in data:
                name = dev.get("Name") or ""
                device_id = dev.get("DeviceID") or ""
                # Check for COM port suffix like (COM1), (COM2) etc, or Arduino
                if "(COM" in name or "arduino" in name.lower() or "serial" in name.lower():
                    print(f"Name: {name}, DeviceID: {device_id}")
        else:
            print("Error or no stdout:")
            print(result.stderr)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_devices()
