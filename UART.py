from machine import UART
import array
import time

uart = UART(1, 9600)                         # init with given baudrate
uart.init(9600, bits=8, parity=None, stop=1) # init with given parameter
# this uses the UART_1 default pins for TXD and RXD (``P3`` and ``P4``)
uart = UART(1, baudrate=9600)
while 1:
    buf = uart.any()
    print(buf)
