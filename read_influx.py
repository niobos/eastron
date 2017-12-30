import argparse
import serial
from influxdb import InfluxDBClient

from eastron import DebuggableSerial, Eastron
from Promise import PromiseFunc


parser = argparse.ArgumentParser(description='Eastron reader')
parser.add_argument('serial_port', help="Serial port to query on")
parser.add_argument('--db', help="influx database to write to", default='eastron')

args = parser.parse_args()


ser = DebuggableSerial(args.serial_port, 9600, serial.EIGHTBITS, serial.PARITY_EVEN, serial.STOPBITS_ONE)
ser.debug = False
ser.reset_input_buffer()
m = Eastron(ser, 1)

points = [
    {
        'measurement': 'power',
        'tags': {
            'phase': 'total',
        },
        'fields': {
            'true_W': m.delayed_read(Eastron.defined_registers['Total system power [W]']['addr']),
            'reactive_VAr': m.delayed_read(Eastron.defined_registers['Total system VAr [VAr]']['addr']),
            'apparent_VA': m.delayed_read(Eastron.defined_registers['Total system volt amps [VA]']['addr']),
        },
    },
    {
        'measurement': 'power',
        'tags': {
            'phase': '1',
        },
        'fields': {
            'true_W': m.delayed_read(Eastron.defined_registers['Phase 1 power [W]']['addr']),
            'reactive_VAr': m.delayed_read(Eastron.defined_registers['Phase 1 volt amps reactive [VAr]']['addr']),
            'apparent_VA': m.delayed_read(Eastron.defined_registers['Phase 1 volt amps [VA]']['addr']),
        },
    },
    {
        'measurement': 'power',
        'tags': {
            'phase': '3',
        },
        'fields': {
            'true_W': m.delayed_read(Eastron.defined_registers['Phase 3 power [W]']['addr']),
            'reactive_VAr': m.delayed_read(Eastron.defined_registers['Phase 3 volt amps reactive [VAr]']['addr']),
            'apparent_VA': m.delayed_read(Eastron.defined_registers['Phase 3 volt amps [VA]']['addr']),
        },
    },
    {
        'measurement': 'energy',
        'tags': {},
        'fields': {
            'true_kWh': PromiseFunc(lambda i, e: i-e,
                                    i=m.delayed_read(Eastron.defined_registers['Import Wh since reset [kWh]']['addr']),
                                    e=m.delayed_read(Eastron.defined_registers['Export Wh since reset [kWh]']['addr'])),
            'reactive_kVArh': PromiseFunc(lambda i, e: i-e,
                                          i=m.delayed_read(Eastron.defined_registers['Import VArh since reset [kVArh]']['addr']),
                                          e=m.delayed_read(Eastron.defined_registers['Export VArh since reset [kVArh]']['addr'])),
            'apparent_kVAh': m.delayed_read(Eastron.defined_registers['VAh since reset [kVAh]']['addr']),
        },
    },
    {
        'measurement': 'frequency',
        'tags': {},
        'fields': {
            'frequency': m.delayed_read(Eastron.defined_registers['Frequency of supply voltage [Hz]']['addr']),
        },
    },
    {
        'measurement': 'line_voltage',
        'tags': {
            'lines': '12',
        },
        'fields': {
            'voltage_V': m.delayed_read(Eastron.defined_registers['Line 1 to Line 2 volts [V]']['addr']),
        },
    },
    {
        'measurement': 'line_voltage',
        'tags': {
            'lines': '23',
        },
        'fields': {
            'voltage_V': m.delayed_read(Eastron.defined_registers['Line 2 to Line 3 volts [V]']['addr']),
        },
    },
    {
        'measurement': 'line_voltage',
        'tags': {
            'lines': '31',
        },
        'fields': {
            'voltage_V': m.delayed_read(Eastron.defined_registers['Line 3 to Line 1 volts [V]']['addr']),
        },
    },
    {
        'measurement': 'line_current',
        'tags': {
            'line': '1',
        },
        'fields': {
            'current_A': m.delayed_read(Eastron.defined_registers['Phase 1 current [A]']['addr']),
        },
    },
    {
        'measurement': 'line_current',
        'tags': {
            'line': '2',
        },
        'fields': {
            'current_A': m.delayed_read(Eastron.defined_registers['Phase 2 current [A]']['addr']),
        },
    },
    {
        'measurement': 'line_current',
        'tags': {
            'line': '3',
        },
        'fields': {
            'current_A': m.delayed_read(Eastron.defined_registers['Phase 3 current [A]']['addr']),
        },
    },
]

tries = 3
while tries > 0:
    try:
        m.do_delayed_reads()
        break
    except TimeoutError:
        tries = tries - 1
if tries == 0:
    print("Timeout")
    exit(1)

for measurement in points:
    for field_name, field_value in measurement['fields'].items():
        measurement['fields'][field_name] = field_value.get_value()

db_con = InfluxDBClient(database=args.db)
db_con.write_points(points)
