import serial
import serial.tools.list_ports

print("serial file:", serial.__file__)
print("list_ports file:", serial.tools.list_ports.__file__)

try:
    from serial.win32 import ITERATE_PORTS
    print("ITERATE_PORTS is present")
except ImportError as e:
    print("ImportError for win32 ITERATE_PORTS:", e)

ports = list(serial.tools.list_ports.comports())
print("Number of comports detected:", len(ports))
for p in ports:
    print(p)
