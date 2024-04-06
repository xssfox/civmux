import argparse

import os, pty, tty, termios, fcntl, sys

import threading

import time

import logging
import serial

parser = argparse.ArgumentParser(
                    prog='ICOM CIV Mux',
                    description='Creates virtual serial ports so multiple applications can control the radio at once')

parser.add_argument('-c', '--count', type=int, help="Number of virtual ports to create", default=2)
parser.add_argument('-d','--device', type=str, help="Serial port for the radio", default="/dev/icomA")
parser.add_argument('--symlink-path', type=str, help="The path prefix for creating symlinks to pts devices", default="/tmp/civ")
parser.add_argument('-b','--baud-rate', type=int, help="Baud rate of the radio", default=19200)

args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG)

class interface:
    def __init__(self, link_name="", callback=None, realport=False, baud=None):
        self.callback = callback
        
        self.buffer = b''

        if realport:
            self.serial_port = serial.Serial(realport, baud)
            self.ttyname = realport
        else:
            self.serial_port = None

            self.control, self.user_port = pty.openpty()
            self.ttyname = os.ttyname(self.user_port)
            

            tty.setraw(self.control, termios.TCSANOW) # this makes the tty act more like a serial port

            # change flags to be non blocking so that buffer full doesn't cause issues
            # flags = fcntl.fcntl(self.control, fcntl.F_GETFL)
            # flags |= os.O_NONBLOCK
            # fcntl.fcntl(self.control, fcntl.F_SETFL, flags)
            os.set_blocking(self.control, True)

            try:
                os.symlink(self.ttyname, f"{link_name}")
            except FileExistsError:
                os.remove(f"{link_name}")
                os.symlink(self.ttyname, f"{link_name}")


        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

        logging.debug(f"{self.ttyname} started")

    def write(self, data):
        if self.serial_port:
            self.serial_port.write(data)
        else:
            try:
                
                os.set_blocking(self.control, False)
                os.write(self.control, data)
                os.set_blocking(self.control, True)
            except BlockingIOError:
                logging.error("PTY interface buffer is full. The connected application may have crashed or isn't reading fast enough. Data loss is likely. Alternatively you aren't using the PTY interface.")
                blocking = os.get_blocking(self.user_port) # remember what the state was before
                os.set_blocking(self.user_port, False)
                try:
                    while 1:
                        os.read(self.user_port,1) # read off the buffer until we've cleared it
                except BlockingIOError:
                    pass
                os.set_blocking(self.user_port, blocking) # restore the state after    
    def read(self):
        if self.serial_port:
            data = self.serial_port.read(1)
        else:
            data = os.read(self.control, 1)

        if not self.buffer: # handle empty buffer
            if data == b"\xfe":
                logging.info(f"start of message on {self.ttyname}")
            else:
                logging.error(f"Got {data} without preamble on {self.ttyname}")
                return
        self.buffer += data

        if data == b"\xfd":
            logging.debug(f"Full message on {self.ttyname} - calling back")
            if self.callback:
                self.callback(self, self.buffer)
            self.buffer=b''
    
    def run(self):
        while 1: #exiting is not an option since reads will be blocking
            self.read()


def callback(instance, data):
    logging.debug(f"rx on {instance.ttyname}")
    logging.debug(data)
    for ptyi in ptys:
        if ptyi == instance:
            logging.debug(f"skipping {ptyi.ttyname} as that's where data was received from")
            continue
        logging.debug(f"sending to {ptyi.ttyname}")
        ptyi.write(data)

ptys = [
    interface(f"{args.symlink_path}{x}", callback)
    for x in range(args.count)
]

ptys.append(
    interface(callback=callback, realport="/dev/icomA", baud=19200)
)


ptys[0].thread.join()

