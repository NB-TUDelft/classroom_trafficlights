import serial
import time

# Find your micro:bit's COM port (check Device Manager on Windows)
# Common ports: COM3, COM4, COM5, etc.
PORT = 'COM3'  # Change this to your micro:bit's port
BAUD_RATE = 115200

try:
    # Open serial connection
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for connection to establish
    
    print(f"Connected to {PORT}")
    
    # Send a message to activate transmitter mode and forward via radio
    # Format: "T,<deviceID>,<colorIndex>" or "RT,<deviceID>,<colorIndex>"
    message = "T,0,0\n"  # -1 targets all devices, 1 sets orange color
    #message = "BEEP"
    
    ser.write(message.encode())
    print(f"Sent: {message.strip()}")
    
    # Read any responses
    time.sleep(0.5)
    while ser.in_waiting:
        response = ser.readline().decode().strip()
        print(f"Received: {response}")
    
    ser.close()
    print("Connection closed")
    
except serial.SerialException as e:
    print(f"Error: {e}")
    print("Make sure the micro:bit is connected and the correct COM port is selected")
    print("Available COM ports:")
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"  {port.device}")