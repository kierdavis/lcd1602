# `lcd1602`

A 1602 LCD module controller for the Raspberry Pi, written in Python.

## Hardware

The LCD module has 16 pins; from left to right they are:

Pin  Signal         Type     Description
---  -------------  -------  -----------
1    `VSS`          Power    Ground
2    `VDD`          Power    Logic power supply
3    `V0`           Power    LCD power supply
4    `RS`           Control  Register select (low = instruction, high = data)
5    `RW`           Control  Read/write select (low = write, high = read)
6    `E`            Control  Enable
7    `DB0`          Data     Data bus (bit 0)
8    `DB1`          Data     Data bus (bit 1)
9    `DB2`          Data     Data bus (bit 2)
10   `DB3`          Data     Data bus (bit 3)
11   `DB4`          Data     Data bus (bit 4)
12   `DB5`          Data     Data bus (bit 5)
13   `DB6`          Data     Data bus (bit 6)
14   `DB7`          Data     Data bus (bit 7)
15   `LED+` or `A`  Power    Backlight power supply
16   `LED-` or `K`  Power    Backlight ground

### Wiring up the power supply

First, connect `VSS` (pin 1) to ground (0V) and `VDD` (pin 2) to a +5V power supply.

The LCD power supply voltage can be varied to adjust the contrast. A potentiometer can be used to allow adjusting this, but here we will just make a simple voltage divider out of two resistors.

Grab two resistors of the same value (anything between about 10 kΩ and 100 kΩ will do). Connect one between the +5V supply and `V0` (pin 3), and the other between `V0` and ground. This gives `V0` a voltage of 2.5V, which is good enough for now. You can always swap the resistors for different values to change the voltage of `V0`.

Lastly, connect up the backlight power by wiring `LED-` (pin 16) to ground and adding a 220 Ω resistor between `LED+` (pin 15) and the +5V supply.

### Wiring up the control signals

It is unusual to need to read data from the LCD. Mostly you'll just want to write data (text to display, cursor position etc.) to it, so we'll just wire the read/write select pin `RW` to ground, indicating that it will always be in write mode.

The other two control signals, `RS` and `E`, will need to be connected to the GPIO pins on the Raspberry Pi. 

Control pin mapping:

LCD signal    Raspberry Pi signal
------------  -------------------
`RS` (pin 4)  GPIO pin 4
`E` (pin 6)   GPIO pin 27

### Wiring up the data signals

The LCD provides both 8-bit and 4-bit modes. We will use the 4-bit mode, so only pins `DB4`, `DB5`, `DB6`, `DB7` are actually used for communication. Pins `DB0`, `DB1`, `DB2` and `DB3` are left disconnected.

LCD signal      Raspberry Pi signal
--------------  -------------------
`DB4` (pin 11)  GPIO pin 22
`DB5` (pin 12)  GPIO pin 23
`DB6` (pin 13)  GPIO pin 24
`DB7` (pin 14)  GPIO pin 25


## Software

`lcd1602.py` contains a class that can be used for controlling the LCD display.

Example usage:

    # Create LCD controller, specifying the pin numbers.
    # This also initialises the controller and clears the screen.
    lcd = lcd1602.LCD(4, 27, 22, 23, 24, 25)
    
    # Write some text.
    lcd.write("Hello, world!")
    
    # Clear the screen.
    lcd.clear()
    
    # Move the cursor to the top left.
    lcd.home()
    
    # Set cursor coordinates to second line, fourth character.
    lcd.set_cursor(1, 3)
    
    # Move cursor one character to the right.
    lcd.move_cursor(lcd1602.RIGHT)
    
    # Shift display one character to the left.
    lcd.shift_display(lcd1602.LEFT)
    
    # Change settings. See the docstrings for the set_entry_mode and
    # set_display_mode methods for information on what the parameters mean.
    lcd.set_entry_mode(direction    = lcd1602.RIGHT,
                       shift_enable = False)
    
    lcd.set_display_mode(display_on     = True,
                         cursor_visible = False,
                         cursor_blink   = False)
