import argparse
import cmath

import serial
from influxdb import InfluxDBClient

from eastron import DebuggableSerial, Eastron3P3W

parser = argparse.ArgumentParser(description='Eastron reader')
parser.add_argument('serial_port', help="Serial port to query on")
parser.add_argument('--db', help="influx database to write to", default='eastron')

args = parser.parse_args()


ser = DebuggableSerial(args.serial_port, 9600, serial.EIGHTBITS, serial.PARITY_EVEN, serial.STOPBITS_ONE)
ser.debug = False
ser.reset_input_buffer()
m = Eastron3P3W(ser, 1)

points = [
    {
        'measurement': 'power',
        'tags': {
            'phase': 'total',
        },
        'fields': {
            'true_W': m.S().real,
            'reactive_VAr': m.S().imag,
            'apparent_VA': abs(m.S()),
        },
    },
    {
        'measurement': 'power',
        'tags': {
            'phase': '1',
        },
        'fields': {
            'true_W': m.S1_u12().real,
            'reactive_VAr': m.S1_u12().imag,
            'apparent_VA': abs(m.S1_u12()),
        },
    },
    {
        'measurement': 'power',
        'tags': {
            'phase': '3',
        },
        'fields': {
            'true_W': m.S3_u32().real,
            'reactive_VAr': m.S3_u32().imag,
            'apparent_VA': abs(m.S3_u32()),
        },
    },
    {
        'measurement': 'energy',
        'tags': {},
        'fields': {
            'true_kWh': m.E().real,
            'reactive_kVArh': m.E().imag,
            'apparent_kVAh': abs(m.E()),
        },
    },
    {
        'measurement': 'frequency',
        'tags': {},
        'fields': {
            'frequency': m.f(),
        },
    },
    {
        'measurement': 'line_voltage',
        'tags': {
            'lines': '12',
        },
        'fields': {
            'voltage_V': m.U12(),
        },
    },
    {
        'measurement': 'line_voltage',
        'tags': {
            'lines': '23',
        },
        'fields': {
            'voltage_V': m.U23(),
        },
    },
    {
        'measurement': 'line_voltage',
        'tags': {
            'lines': '31',
        },
        'fields': {
            'voltage_V': m.U31(),
        },
    },
    {
        'measurement': 'line_current',
        'tags': {
            'line': '1',
        },
        'fields': {
            'current_A': abs(m.I1_u1()),
            'angle_deg': cmath.phase(m.I1_u1()),
        },
    },
    {
        'measurement': 'line_current',
        'tags': {
            'line': '2',
        },
        'fields': {
            'current_A': abs(m.I2_u2()),
            'angle_deg': cmath.phase(m.I2_u2()),
        },
    },
    {
        'measurement': 'line_current',
        'tags': {
            'line': '3',
        },
        'fields': {
            'current_A': abs(m.I3_u3()),
            'angle_deg': cmath.phase(m.I3_u3()),
        },
    },
]


db_con = InfluxDBClient(database=args.db)
db_con.write_points(points)
