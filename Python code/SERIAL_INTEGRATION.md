# Serial Connection & Live Data Integration

## Overview
The Smart Motor Test Bench has been enhanced to automatically connect to an Arduino device on startup and switch from simulated data to live serial data when a connection is established.

## Changes Made

### 1. **SerialManager** (`backend/serial_manager.py`)
**Status**: ✅ Fully Implemented

**Key Features**:
- Full PySerial integration with real COM port communication
- Automatic connection handling with error recovery
- Configurable baud rate (default 115200)
- Serial data parsing support
- Available ports listing capability
- Robust exception handling

**Public API**:
```python
# Connect to Arduino
success = serial_mgr.connect("COM3", baud_rate=115200)

# Read data line by line
data_line = serial_mgr.read_line()  # e.g., "1234.5,12.0,2.5,30.0,85.5,45.3,72"

# Send commands
serial_mgr.send_command("PWM:75")

# Check connection status
if serial_mgr.is_connected:
    print(f"Connected to {serial_mgr.port}")
```

**Expected Arduino Data Format**:
```
RPM,Voltage,Current,Power,Efficiency,Temperature,PWM
1234.5,12.0,2.5,30.0,85.5,45.3,72
```

### 2. **DataGenerator** (`backend/data_generator.py`)
**Status**: ✅ Dual-Mode Implementation

**Key Changes**:
- Added `set_serial_manager()` method to attach a SerialManager instance
- Enhanced `update()` method with intelligent data source selection:
  - Reads from Arduino when serial connection is active
  - Falls back to simulated data automatically if serial fails
  - Gracefully handles parsing errors and reconnects

**Behavior**:
```python
# Initialize with serial support
data_gen = DataGenerator()
data_gen.set_serial_manager(serial_mgr)

# update() automatically selects data source:
# - If serial is connected AND data is available: uses live data
# - Otherwise: uses simulated data (fallback)
data_gen.update()
```

### 3. **MainWindow** (`main.py`)
**Status**: ✅ Auto-Connect & Status Management

**Key Features**:
- Automatic connection attempt on application startup
- Dynamic status bar indicators:
  - **Connected**: Green dot + "LIVE DATA ({port} Connected)"
  - **Disconnected**: Orange dot + "SIMULATED DATA (Arduino Not Connected)"
- Connection state monitoring with periodic updates
- Clean error logging and diagnostics

**Implementation Details**:
```python
# Called automatically on app startup
_attempt_connection()

# Monitors connection state every timer tick
_check_and_update_connection_status()

# Updates status bar UI
_update_connection_status(connected: bool)
```

### 4. **Dashboard** (`pages/dashboard.py`)
**Status**: ✅ Dynamic Status Updates

**UI Updates**:
- **Arduino Status** label: "CONNECTED" (green) or "NOT CONNECTED" (red)
- **Connection Type** label: "USB Serial (Live)" or "USB (Virtual - Simulated)"
- Updates on every data refresh cycle to reflect current connection state

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Startup                        │
├─────────────────────────────────────────────────────────────┤
│  1. MainWindow created with SerialManager and DataGenerator  │
│  2. DataGenerator.set_serial_manager(serial_mgr)             │
│  3. _attempt_connection() triggered                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
   ✓ Connection Success      ✗ Connection Failed
        │                             │
        ▼                             ▼
   [GREEN STATUS]              [ORANGE STATUS]
   _update_connection_status   _update_connection_status
   (True)                      (False)
        │                             │
        ▼                             ▼
   Each timer tick:            Each timer tick:
   ┌─────────────────────┐     ┌─────────────────────┐
   │ DataGenerator.      │     │ DataGenerator.      │
   │ update()            │     │ update()            │
   │  ├─ Try serial read │     │  ├─ Try serial read │
   │  │  (SUCCESS)       │     │  │  (FAIL/NULL)     │
   │  └─ Use live data   │     │  └─ Use simulation  │
   └─────────────────────┘     └─────────────────────┘
        │                             │
        ▼                             ▼
   Dashboard displays          Dashboard displays
   live Arduino data           simulated data
```

## Configuration

### Settings File (`settings.json`)
```json
{
  "default_com_port": "COM3",
  "baud_rate": 115200,
  "refresh_rate_ms": 100
}
```

### Environment
- **Operating System**: Windows (via PySerial)
- **Python Version**: 3.8+
- **Required Package**: `pyserial>=3.5` (already in requirements.txt)

## Testing Checklist

### Scenario 1: No Arduino Connected
- [ ] Launch application with no Arduino on default COM port
- [ ] Status bar shows "SIMULATED DATA (Arduino Not Connected)" in orange
- [ ] Dashboard "Arduino Status" shows "NOT CONNECTED" in red
- [ ] Dashboard "Connection Type" shows "USB (Virtual - Simulated)"
- [ ] All metrics display simulated data

### Scenario 2: Arduino Connected
- [ ] Connect Arduino to default COM port
- [ ] Launch application
- [ ] Status bar shows "LIVE DATA (COM3 Connected)" in green
- [ ] Dashboard "Arduino Status" shows "CONNECTED" in green
- [ ] Dashboard "Connection Type" shows "USB Serial (Live)"
- [ ] Metrics display real Arduino data

### Scenario 3: Arduino Connected After Startup
- [ ] Launch with no Arduino (simulated mode)
- [ ] Connect Arduino while app is running
- [ ] Connection status updates automatically within 1 second
- [ ] Data source switches from simulated to live

### Scenario 4: Arduino Disconnected While Running
- [ ] Launch with Arduino connected (live mode)
- [ ] Disconnect Arduino during operation
- [ ] App detects disconnection and falls back to simulated data
- [ ] Status bar updates automatically

### Scenario 5: Custom COM Port
- [ ] Edit `settings.json` to use different COM port (e.g., "COM4")
- [ ] Launch application
- [ ] Connection attempts to custom port

## Error Handling

**Connection Failures**:
- Invalid COM port → Caught by PySerial, logged, falls back to simulated data
- Baud rate mismatch → Connection times out, app retries, falls back to simulated data
- Serial port permission denied → Caught and logged, falls back to simulated data

**Data Parsing**:
- Invalid CSV format → Parsing exception caught, falls back to simulated data for that tick
- Missing fields → IndexError caught, falls back to simulated data

**Graceful Fallback**:
- All errors result in fallback to simulated data
- No exception crashes the application
- All errors are logged to console with [SerialManager] or [StatusBar] prefix

## Troubleshooting

### Connection Not Established
1. Check `settings.json` - ensure correct COM port and baud rate
2. Verify Arduino is connected and recognized by Windows
3. Check Device Manager for "COM" port listing
4. Ensure no other application has exclusive access to the COM port
5. Look for [SerialManager] error messages in console output

### Simulated Data Instead of Live Data
1. Verify Arduino is transmitting data in correct format
2. Use Arduino IDE Serial Monitor to test transmission
3. Check console for parsing errors ([SerialManager] messages)
4. Verify baud rate matches on both sides

### Status Bar Not Updating
1. Ensure application refresh rate is adequate (100ms default)
2. Check that SerialManager instance is properly passed to MainWindow
3. Verify dashboard is in view (update_data() only called for visible page)

## Code References

- **Serial Connection Logic**: `main.py` lines 268-305
- **Status Updates**: `main.py` lines 307-335
- **Data Source Selection**: `data_generator.py` lines 79-118
- **Serial Parsing**: `data_generator.py` lines 120-154
- **Dashboard Status Display**: `pages/dashboard.py` lines 595-605

## Future Enhancements

1. Implement automatic reconnection attempts if connection drops
2. Add serial port auto-detection
3. Support multiple serial data formats
4. Add data validation and checksums
5. Implement command queueing for Arduino control
6. Add serial port speed/protocol negotiation
7. Store raw serial data to file for post-analysis
