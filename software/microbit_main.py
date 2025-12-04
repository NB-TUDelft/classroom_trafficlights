# This is MicroPython code intended to run on the Microbit
from microbit import *
import neopixel
import radio

def on_logo_long_pressed():
    global deviceID, inputTimer, repeaterOn, currentColorIndex, beta
    if beta:
        return

    basic.show_string("ID")
    while inputTimer < 2000:
        if input.button_is_pressed(Button.B):
            deviceID += 1
            inputTimer = 0
            basic.show_number(deviceID)
            basic.pause(100)
            
        elif input.button_is_pressed(Button.A):
            deviceID = max(deviceID - 1, 0)
            inputTimer = 0
            basic.show_number(deviceID)
            basic.pause(100)
        elif input.logo_is_pressed():
            if repeaterOn:
                repeaterOn = False
                flashstorage.put("ROLE", "0")
                basic.show_string("S")
            else:
                repeaterOn = True
                flashstorage.put("ROLE", "1")
                basic.show_string("R")
            basic.pause(100)

        inputTimer += 1
        basic.pause(1)
    basic.clear_screen()
    inputTimer = 0
    currentColorIndex = 0
    flashstorage.put("ID", convert_to_text(deviceID))
    showColor(currentColorIndex, True)

beta = False
transmitter = False
input.on_logo_event(TouchButtonEvent.LONG_PRESSED, on_logo_long_pressed)


def on_button_pressed_a():
    global currentColorIndex, beta
    if beta:
        on_button_pressed_a_beta()
        return

    currentColorIndex = max(currentColorIndex - 1, 0)
    showColor(currentColorIndex, True)

input.on_button_pressed(Button.A, on_button_pressed_a)


def on_button_pressed_b():
    global currentColorIndex, beta
    if beta:
        on_button_pressed_b_beta()
        return

    currentColorIndex = min(len(colorList) - 1, currentColorIndex + 1)
    showColor(currentColorIndex, True)

input.on_button_pressed(Button.B, on_button_pressed_b)


def on_button_pressed_ab():
    global currentColorIndex, beta
    if beta:
        on_button_pressed_ab_beta()
        return

    currentColorIndex = 0
    showColor(currentColorIndex, True)

input.on_button_pressed(Button.AB, on_button_pressed_ab)


def on_received_string(receivedString):
    global receivedArray, currentColorIndex, beta
    if transmitter:
        serial.write_line(receivedString)
        return

    if receivedString == "SWITCHMODE":
        beta = True
        enter_beta_mode()
        return
    if beta:
        handle_beta_received(receivedString)
        return
    
    receivedArray = receivedString.split(",")
    if receivedArray[0] == "T" or receivedArray[0] == "RT":
        if parse_float(receivedArray[1]) == deviceID or parse_float(receivedArray[1]) == -1:
            currentColorIndex = parse_float(receivedArray[2])
            showColor(currentColorIndex, False)

    if repeaterOn:
        if receivedArray[0] == "T" or receivedArray[0] == "S":
            basic.pause(100)
            radio.send_string("R" + receivedString)

radio.on_received_string(on_received_string)


def showColor(colorIndex: number, radioOn: bool):
    strip.clear()
    strip.show_color(colorList[colorIndex])
    strip.set_brightness(128)
    strip.show()
    if radioOn:
        radio.send_string("S" + "," + convert_to_text(deviceID) + "," + convert_to_text(colorIndex))

receivedArray: List[str] = []
inputTimer = 0
deviceID = 0
repeaterOn = False
currentColorIndex = 0

colorList: List[number] = []
strip: neopixel.Strip = None
strip = neopixel.create(DigitalPin.P0, 8, NeoPixelMode.RGB)

colorList = [
    neopixel.colors(NeoPixelColors.GREEN),
    neopixel.colors(NeoPixelColors.ORANGE),
    neopixel.colors(NeoPixelColors.RED)
]

currentColorIndex = 0
radio.set_group(146)
radio.set_transmit_power(7)

if parse_float(flashstorage.get_or_default("ROLE", "0")) == 1:
    repeaterOn = True
else:
    repeaterOn = False

deviceID = parse_float(flashstorage.get_or_default("ID", "0"))
inputTimer = 0

showColor(currentColorIndex, True)
basic.show_number(deviceID)
basic.pause(1000)
basic.clear_screen()


def on_forever():
    global beta
    if transmitter:
        return
    if beta:
        beta_forever_loop()
        return
    basic.pause(randint(4000, 6000))
    showColor(currentColorIndex, True)

basic.forever(on_forever)

#
# Transmitter mode
#

def on_data_received():
    global transmitter
    if beta:
        on_data_received_beta()
        return
    transmitter = True
    radio.send_string(serial.read_line())
serial.on_data_received(serial.delimiters(Delimiters.NEW_LINE), on_data_received)

# ----------------------------------------------------------
# BETA IMPLEMENTATION
# ----------------------------------------------------------

message_mode = 0
debugmode = 0

def debug(code, msg):
    if debugmode:
        basic.show_string(str('ERR' + str(code)))

        for _ in range(50):
            strip.show_color(neopixel.colors(NeoPixelColors.RED))
            strip.show()
            basic.pause(100)
            strip.clear()
            strip.show()
            basic.pause(100)

        basic.show_string(str('ERR' + str(code)))
        serial.write_line("DEBUG: " + msg)

def enter_beta_mode():
    pass


def handle_beta_received(receivedString):
    if message_mode == 0 and handle_message(receivedString):
        return        
    '''if receivedString == "PING":
        radio.send_string("PONG")
    elif receivedString.startswith("SET"):
        # Example: SET,123  → flash store
        parts = receivedString.split(",")
        if len(parts) == 2:
            flashstorage.put("BETA", parts[1])
    elif receivedString == "GET":
        value = flashstorage.get_or_default("BETA", "NONE")
        radio.send_string("BETA," + value)'''

last_msg_id = -1
multi_buffers = [""]

def handle_message(msg):
    # Format:
    # MSG,<msg_id>,<transmit_count>,<command>
    # Returns False if message not processed, passes on to other handlers
    global last_msg_id
    parts = msg.split(",", 3)
    if len(parts) < 5:
        return False
    if parts[0] != "MSG":
        return False
    
    msg_id = int(parts[1])
    transmit_count = int(parts[2])
    command = parts[3]

    if msg_id <= last_msg_id:
        return True  # Already processed
    last_msg_id = msg_id
    
    if transmit_count:
        radio.send_string('MSG,' + str(msg_id) + ',' + str(transmit_count - 1) + ',' + command)

    handle_msg_command(command)

    return True


def handle_msg_command(command):
    global multi_buffers, handle_message, handle_beta_received, on_button_pressed_a_beta, on_button_pressed_b_beta, on_button_pressed_ab_beta, beta_forever_loop

    # Commands:
    # MULTI: allows longer messages by splitting into multiple parts
    #   Usage: MULTI,<cmd>
    #     Commands: CLEAR, APPEND <content>, NEXTMSG <type>, STOP
    # IF,<#id>,<cmd>: conditional execution based on device ID
    # RESET: resets the device, turns off beta mode

    parts = command.split(",", 1)
    
    if parts[0] == "RESET":
        control.reset()
        debug(105, "RESET command failed to reset device")
        return

    if parts[0] == "IF":
        if len(parts) < 2:
            debug(100, "IF with no condition")
            return
        cond_parts = parts[1].split(",", 1)
        if len(cond_parts) < 2:
            debug(103, "IF with no command")
            return
        target_id = int(cond_parts[0])
        if target_id == int(flashstorage.get_or_default("ID", "0")):
            handle_msg_command(cond_parts[1])
        return

    if parts[0] == "MULTI":
        if len(parts) < 2:
            debug(101, "MULTI with no command")
        parts = parts[1].split(",", 1)
        cmd = parts[0]
        if cmd == "CLEAR":
            multi_buffers = [""]
        elif cmd == "APPEND":
            if len(parts) < 2:
                debug(102, "MULTI APPEND with no content")
            multi_buffers[-1] += parts[1]
        elif cmd == "NEXTMSG":
            multi_buffers.append("")
        elif cmd == "STOP":
            for submsg in multi_buffers:
                handle_msg_command(submsg)
            multi_buffers = [""]
        else:
            debug(106, "MULTI unknown command: " + cmd)
        return

def on_button_pressed_a_beta():
    # Custom button A behavior in beta mode
    radio.send_string("A")


def on_button_pressed_b_beta():
    # Custom button B behavior in beta mode
    radio.send_string("B")


def on_button_pressed_ab_beta():
    # Custom AB behavior in beta mode
    radio.send_string("AB")


def beta_forever_loop():
    # Any repeated background activity in beta mode
    # Example: heartbeat ping
    basic.pause(2000)
    radio.send_string("HB")

def on_data_received_beta():
    pass
