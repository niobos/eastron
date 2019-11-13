import argparse
import serial
import cmath

from src.eastron import DebuggableSerial, Eastron3P3W


parser = argparse.ArgumentParser(description='Eastron reader')
parser.add_argument('--addr', help="Address to query", type=int, default=1)
parser.add_argument('serial_port', help="Serial port to open")

args = parser.parse_args()


ser = DebuggableSerial(args.serial_port, 9600, serial.EIGHTBITS, serial.PARITY_EVEN, serial.STOPBITS_ONE)
ser.debug = False
ser.reset_input_buffer()
m = Eastron3P3W(ser, args.addr)

all_addresses = [
    info['addr']
    for name, info in Eastron3P3W.defined_registers.items()
]
all_data = m.read_input_registers_float(all_addresses)

for name in sorted(Eastron3P3W.defined_registers.keys(),
                   key=lambda n: Eastron3P3W.defined_registers[n]['addr']):
    addr = Eastron3P3W.defined_registers[name]['addr']
    print("{n} = {v}".format(n=name, v=all_data[addr]))


def abs_angle(num: complex) -> str:
    return "{} @ {}º".format(
        abs(num),
        cmath.phase(num) / cmath.pi * 180,
    )


print("")
print("Calculated I1 [A] = {}".format(abs_angle(m.I1)))
print("Calculated I2 [A] = {}".format(abs_angle(m.I2)))
print("Calculated I3 [A] = {}".format(abs_angle(m.I3)))
print("Calculated S1 [W] = {}".format(m.S1))
print("Calculated S3 [W] = {}".format(m.S3))
print("Calculated S [W] = {}".format(m.S))
