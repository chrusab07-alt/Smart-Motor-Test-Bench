import subprocess
cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_PnPEntity | Where-Object { $_.Name -like '*COM*' } | Select-Object Name, DeviceID"]
result = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
