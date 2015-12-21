# 1602 LCD module controller for the Raspberry Pi

import time
import RPi.GPIO as GPIO

LEFT = object()
RIGHT = object()

_ENTRY_MODE_DIRECTION = 1
_ENTRY_MODE_SHIFT_ENABLE = 0

_DISPLAY_MODE_DISPLAY_ON = 2
_DISPLAY_MODE_CURSOR_VISIBLE = 1
_DISPLAY_MODE_CURSOR_BLINK = 0

class Deadline(object):
    def __init__(self):
        self.t = time.clock()
    
    def set(self, secs_from_now):
        self.t = time.clock() + secs_from_now
    
    def wait(self):
        if time.clock() - self.t > 500e-6:
            time.sleep(time.clock() - self.t)
        
        while time.clock() < self.t:
            pass

class LCD(object):
    def __init__(self, rs_pin, e_pin, db4_pin, db5_pin, db6_pin, db7_pin):
        self.rs_pin = rs_pin
        self.e_pin = e_pin
        self.db4_pin = db4_pin
        self.db5_pin = db5_pin
        self.db6_pin = db6_pin
        self.db7_pin = db7_pin
        
        # Used to ensure that we do not send another command before the previous
        # one has finished.
        self.deadline = Deadline()
        
        self._entry_mode = 0
        self._display_mode = 0
        
        self._init_pins()
        self._init_lcd()
    
    def _init_pins(self):
        """
        Set all pins as outputs and initialise them to their idle states.
        """
        
        GPIO.setup(self.rs_pin, GPIO.OUT)
        GPIO.setup(self.e_pin, GPIO.OUT)
        GPIO.setup(self.db4_pin, GPIO.OUT)
        GPIO.setup(self.db5_pin, GPIO.OUT)
        GPIO.setup(self.db6_pin, GPIO.OUT)
        GPIO.setup(self.db7_pin, GPIO.OUT)
        GPIO.output(self.rs_pin, False)
        GPIO.output(self.e_pin, False)
        GPIO.output(self.db4_pin, False)
        GPIO.output(self.db5_pin, False)
        GPIO.output(self.db6_pin, False)
        GPIO.output(self.db7_pin, False)
    
    def _init_lcd(self):
        """
        Initialise the LCD.
        """
        
        # LCD needs 40 ms to start up after power on
        self.deadline.set(40e-3)
        
        # Synchronise and set to 4 bit mode
        self._send_4bit(0x3)
        self.deadline.set(4.5e-3) # 4.5 ms
        self._send_4bit(0x3)
        self.deadline.set(150e-6) # 150 us
        self._send_4bit(0x3)
        self.deadline.set(150e-6) # 150 us
        self._send_4bit(0x2)
        self.deadline.set(150e-6) # 150 us
        
        # Set function (4-bit mode, 2 lines, 5x8 characters)
        self._send_command(0x28)
        self.deadline.set(37e-6)
        
        # Set parameters
        self.set_display_mode(display_on = False, cursor_visible = False, cursor_blink = False)
        self.clear()
        self.set_entry_mode(direction = RIGHT, shift_enable = False)
        self.set_display_mode(display_on = True)
    
    def clear(self):
        """
        Clear the display.
        """
        
        self._send_command(0x01)
        self.deadline.set(1.52e-3)
    
    def home(self):
        """
        Move the cursor to the home position (top left corner).
        """
        
        self._send_command(0x02)
        self.deadline.set(1.52e-3)
    
    def set_entry_mode(self, direction = None, shift_enable = None):
        """
        Set entry mode settings.
        
        direction:
            The direction in which the cursor will move after each character is
            written (either LEFT or RIGHT).
        shift_enable:
            Whether or not the entire display will shift when a character is
            written. The cursor moves with the display.
        
        A value of None can also be given as a settings, which indicates that
        the setting should retain its previous value. All parameters default to
        None.
        """
        
        if direction is not None:
            if direction is RIGHT:
                self._entry_mode |= (1 << _ENTRY_MODE_DIRECTION)
            elif direction is LEFT:
                self._entry_mode &= ~(1 << _ENTRY_MODE_DIRECTION)
            else:
                raise ValueError("Expected either LEFT or RIGHT for parameter 'direction'")
        
        if shift_enable is not None:
            if shift_enable:
                self._entry_mode |= (1 << _ENTRY_MODE_SHIFT_ENABLE)
            else:
                self._entry_mode &= ~(1 << _ENTRY_MODE_SHIFT_ENABLE)
        
        self._send_command(0x04 | (self._entry_mode & 0x03))
        self.deadline.set(37e-6)
    
    def set_display_mode(self, display_on = None, cursor_visible = None, cursor_blink = None):
        """
        Set display mode settings.
        
        display_on;
            Whether or not the display is enabled.
        cursor_visible:
            Whether or not the cursor is visible.
        cursor_blink:
            Whether or not cursor blinking is enabled.
        
        A value of None can also be given as a settings, which indicates that
        the setting should retain its previous value. All parameters default to
        None.
        """
        
        if display_on is not None:
            if display_on:
                self._display_mode |= (1 << _DISPLAY_MODE_DISPLAY_ON)
            else:
                self._display_mode &= ~(1 << _DISPLAY_MODE_DISPLAY_ON)
        
        if cursor_visible is not None:
            if cursor_visible:
                self._display_mode |= (1 << _DISPLAY_MODE_CURSOR_VISIBLE)
            else:
                self._display_mode &= ~(1 << _DISPLAY_MODE_CURSOR_VISIBLE)
        
        if cursor_blink is not None:
            if cursor_blink:
                self._display_mode |= (1 << _DISPLAY_MODE_CURSOR_BLINK)
            else:
                self._display_mode &= ~(1 << _DISPLAY_MODE_CURSOR_BLINK)
        
        self._send_command(0x08 | (self._display_mode & 0x07))
        self.deadline.set(37e-6)
    
    def move_cursor(self, direction):
        """
        Move the cursor by one character in the given direction.
        """
        
        if direction is LEFT:
            self._send_command(0x10)
        elif direction is RIGHT:
            self._send_command(0x14)
        else:
            raise ValueError("Expected either LEFT or RIGHT for parameter 'direction'")
        self.deadline.set(37e-6)
    
    def shift_display(self, direction):
        """
        Shift the displayed text by one character in the given direction.
        """
        
        if direction is LEFT:
            self._send_command(0x18)
        elif direction is RIGHT:
            self._send_command(0x1C)
        else:
            raise ValueError("Expected either LEFT or RIGHT for parameter 'direction'")
        self.deadline.set(37e-6)
    
    def _set_cgram_addr(self, addr):
        """
        Set the LCD address counter to the given location in CGRAM.
        """
        
        self._send_command(0x40 | (addr & 0x3F))
        self.deadline.set(37e-6)
    
    def set_cursor(self, line, column):
        """
        Set the cursor and text insertion position. line and column are both
        0-indexed.
        """
        
        if line < 0 or line > 1:
            raise ValueError("'line' out of range (0 to 1)")
        if column < 0x00 or column > 0x39:
            raise ValueError("'column' out of range (0 to 39)")
        
        self._set_ddram_addr(line*0x40 + column)
    
    def _set_ddram_addr(self, addr):
        """
        Set the LCD address counter to the given location in DDRAM.
        """
        
        self._send_command(0x80 | (addr & 0x7F))
        self.deadline.set(37e-6)
    
    def write(self, string):
        """
        Write text to the LCD at the current cursor position.
        """
        
        if isinstance(string, unicode):
            string = string.encode("ascii")
        
        for char in string:
            self._write_byte(ord(value))
    
    def _write_byte(self, value):
        """
        Write a data byte to the current LCD RAM address, then increment or
        decrement the RAM address according to the 'direction' entry mode
        setting.
        """
        
        self._send_data(value & 0xFF)
        self.deadline.set(37e-6)
    
    def _send_command(self, value):
        """
        Send a command byte, setting the RS pin to indicate command mode.
        """
        
        # Set RS low
        GPIO.output(self.rs_pin, False)
        
        # MSB first
        self._send_nibble(value >> 4, False)
        self._send_nibble(value, False)
    
    def _send_data(self, value):
        """
        Send a data byte, setting the RS pin to indicate data mode.
        """
        
        # Set RS high
        GPIO.output(self.rs_pin, True)
        
        # MSB first
        self._send_nibble(value >> 4, False)
        self._send_nibble(value, False)
    
    def _send_nibble(self, value):
        """
        Send a nibble (4 bit value).
        """
        
        # Do not start transmission until the LCD is done processing the last
        # command.
        self.deadline.wait()
        
        # Set data pins
        GPIO.output(self.db4_pin, bool(value & 0x1))
        GPIO.output(self.db5_pin, bool(value & 0x2))
        GPIO.output(self.db6_pin, bool(value & 0x4))
        GPIO.output(self.db7_pin, bool(value & 0x8))
        
        # Pulse enable pin
        GPIO.output(self.e_pin, True)
        _delay(1e-6) # 1 us
        GPIO.output(self.e_pin, False)
        _delay(1e-6) # 1 us
