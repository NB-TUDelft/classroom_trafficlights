#This is MicroPython code intended to run on the Microbit
def on_logo_long_pressed():
    global deviceID, inputTimer, repeaterOn, currentColorIndex
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
input.on_logo_event(TouchButtonEvent.LONG_PRESSED, on_logo_long_pressed)

def on_button_pressed_a():
    global currentColorIndex
    currentColorIndex = max(currentColorIndex - 1, 0)
    showColor(currentColorIndex, True)
input.on_button_pressed(Button.A, on_button_pressed_a)

def on_button_pressed_ab():
    global currentColorIndex
    currentColorIndex = 0
    showColor(currentColorIndex, True)
input.on_button_pressed(Button.AB, on_button_pressed_ab)

def on_received_string(receivedString):
    global receivedArray, currentColorIndex
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

def on_button_pressed_b():
    global currentColorIndex
    currentColorIndex = min(len(colorList) - 1, currentColorIndex + 1)
    showColor(currentColorIndex, True)
input.on_button_pressed(Button.B, on_button_pressed_b)

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
colorList = [neopixel.colors(NeoPixelColors.GREEN),
    neopixel.colors(NeoPixelColors.ORANGE),
    neopixel.colors(NeoPixelColors.RED)]
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
    basic.pause(randint(4000, 6000))
    showColor(currentColorIndex, True)
basic.forever(on_forever)
