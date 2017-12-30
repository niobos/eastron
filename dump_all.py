import argparse
import serial

from eastron import DebuggableSerial, Eastron


parser = argparse.ArgumentParser(description='Eastron reader')
parser.add_argument('serial_port', help="Serial port to open")

args = parser.parse_args()


ser = DebuggableSerial(args.serial_port, 9600, serial.EIGHTBITS, serial.PARITY_EVEN, serial.STOPBITS_ONE)
ser.debug = False
ser.reset_input_buffer()
m = Eastron(ser, 1)

all_addresses = [
    info['addr']
    for name, info in Eastron.defined_registers.items()
]
all_data = m.read_input_registers_float(all_addresses)

for name in sorted(Eastron.defined_registers.keys(),
                   key=lambda n: Eastron.defined_registers[n]['addr']):
    addr = Eastron.defined_registers[name]['addr']
    print("{n} = {v}".format(n=name, v=all_data[addr]))
