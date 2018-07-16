import functools
import cmath
import struct
import typing

import crcmod
import serial

from Promise import Promise

eastron_crc = crcmod.mkCrcFun(0x18005, 0xffff, True, 0x0000)


class DebuggableSerial(serial.Serial):
    def __init__(self, *args, **kwargs):
        self.debug = False
        super().__init__(*args, **kwargs)

    def read(self, size=1):
        data = super().read(size)
        if self.debug:
            hexdata = " ".join("{:02x}".format(c) for c in data)
            print("> {}".format(hexdata))
        return data

    def read_with_idle_timeout(self, size=1, timeout=0.1):
        old_timeout = self.timeout
        try:
            self.timeout = timeout
            data = bytearray()
            while size > 0:
                new_data = self.read(size)
                if len(new_data) > 0:
                    size -= len(new_data)
                    data += new_data
                else:
                    raise TimeoutError("No new bytes received within timeout")
            return data
        finally:
            self.timeout = old_timeout

    def write(self, data):
        if self.debug:
            hexdata = " ".join("{:02x}".format(c) for c in data)
            print("< {}".format(hexdata))
        return super().write(data)


class Modbus:
    def __init__(self, serial_port, slave_address):
        self.serial = serial_port
        self.slave_address = slave_address

    @staticmethod
    def _construct_request(slave_address: int,
                           function_number: int,
                           start_address: int,
                           number_of_points: int) -> bytes:
        msg = struct.pack("> B B H H", slave_address, function_number, start_address, number_of_points)
        crc = eastron_crc(msg)
        msg += struct.pack("< H", crc)  # Yes, little endian...
        return msg

    @staticmethod
    def _read_modbus_response(get_n_bytes: typing.Callable) -> dict:
        data = get_n_bytes(3)
        crc_data = bytearray(data)
        slave_address, func, data_len = struct.unpack("BBB", data)

        payload = get_n_bytes(data_len)
        crc_data += payload

        data = get_n_bytes(2)
        crc_actual, = struct.unpack("<H", data)  # Yes, little endian...

        crc_should = eastron_crc(crc_data)
        if crc_actual != crc_should:
            raise ValueError("CRC mismatch. Calculated 0x{:x}, Received 0x{:x}".format(
                crc_should, crc_actual))

        return {
            'slave_address': slave_address,
            'function': func,
            'payload': payload,
        }

    @staticmethod
    def _normalize_ranges(*ranges) -> typing.List[typing.Tuple[int, int]]:
        """
        Normalize the given ranges to be a list of 2-tuples
        """
        if len(ranges) == 1 and (isinstance(ranges, list) or isinstance(ranges, tuple)):
            ranges = ranges[0]

        normalized_ranges = []
        while len(ranges) > 0:
            current_range = ranges[0]
            ranges = ranges[1:]

            if isinstance(current_range, tuple) or isinstance(current_range, list):
                if len(current_range) == 2:
                    normalized_ranges.append(current_range)
                    continue
                elif len(current_range) == 1:
                    current_range = current_range[0]
                    # and go on below
                else:
                    raise ValueError("Can not interpret a {}-tuple as a range".format(len(current_range)))

            # not elif, we fall through from above
            start_address = current_range
            range_length = ranges[0]
            ranges = ranges[1:]
            normalized_ranges.append((start_address, range_length))
        return normalized_ranges

    @staticmethod
    def _aggregate_ranges(*ranges) -> typing.List[typing.Tuple[int, int]]:
        ranges = Modbus._normalize_ranges(*ranges)
        ranges = sorted(ranges)

        # Always add the first item
        agg_ranges = [ranges[0]]
        ranges = ranges[1:]
        while len(ranges):
            next_address = agg_ranges[-1][0] + agg_ranges[-1][1]
            if ranges[0][0] == next_address:
                # Match, extend the length
                agg_ranges[-1] = (agg_ranges[-1][0], agg_ranges[-1][1] + ranges[0][1])
            else:
                agg_ranges.append(ranges[0])
            ranges = ranges[1:]

        return agg_ranges

    def read_input_registers(self, *ranges):
        ranges = self._aggregate_ranges(*ranges)
        registers = {}
        for start_addr, num in ranges:
            while num > 0:
                limited_num = min(num, 64)  # limit number of regs per query

                self.serial.write(self._construct_request(self.slave_address, 4, start_addr, limited_num))
                resp = self._read_modbus_response(lambda n: self.serial.read_with_idle_timeout(n))
                for i in range(limited_num):
                    register, = struct.unpack_from(">H", resp['payload'])
                    registers[start_addr + i] = register
                    resp['payload'] = resp['payload'][2:]
                num -= limited_num
        return registers


class Eastron(Modbus):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delayed_reads = {}

    defined_registers = {
        'Phase 1 line to neutral volts [V]':     {'addr': 0x0000, '4w': True,  '3w': False, '2w': True},
        'Phase 2 line to neutral volts [V]':     {'addr': 0x0002, '4w': True,  '3w': False, '2w': False},
        'Phase 3 line to neutral volts [V]':     {'addr': 0x0004, '4w': True,  '3w': False, '2w': False},
        'Phase 1 current [A]':                   {'addr': 0x0006, '4w': True,  '3w': True,  '2w': True},
        'Phase 2 current [A]':                   {'addr': 0x0008, '4w': True,  '3w': True,  '2w': False},  # THIS VALUE IS WRONG for 3w
        'Phase 3 current [A]':                   {'addr': 0x000a, '4w': True,  '3w': True,  '2w': False},
        'Phase 1 power [W]':                     {'addr': 0x000c, '4w': True,  '3w': True,  '2w': True},
        'Phase 2 power [W]':                     {'addr': 0x000e, '4w': True,  '3w': False, '2w': False},
        'Phase 3 power [W]':                     {'addr': 0x0010, '4w': True,  '3w': True,  '2w': False},
        'Phase 1 volt amps [VA]':                {'addr': 0x0012, '4w': True,  '3w': True,  '2w': True},
        'Phase 2 volt amps [VA]':                {'addr': 0x0014, '4w': True,  '3w': False, '2w': False},
        'Phase 3 volt amps [VA]':                {'addr': 0x0016, '4w': True,  '3w': True,  '2w': False},
        'Phase 1 volt amps reactive [VAr]':      {'addr': 0x0018, '4w': True,  '3w': True,  '2w': True},
        'Phase 2 volt amps reactive [VAr]':      {'addr': 0x001a, '4w': True,  '3w': False, '2w': False},
        'Phase 3 volt amps reactive [VAr]':      {'addr': 0x001c, '4w': True,  '3w': True,  '2w': False},
        'Phase 1 power factor []':               {'addr': 0x001e, '4w': True,  '3w': True,  '2w': True},
        'Phase 2 power factor []':               {'addr': 0x0020, '4w': True,  '3w': False, '2w': False},
        'Phase 3 power factor []':               {'addr': 0x0022, '4w': True,  '3w': True,  '2w': False},
        'Phase 1 phase angle [º]':               {'addr': 0x0024, '4w': True,  '3w': False, '2w': True},  # ??? 2w==True ???  # NOT FILLED IN FOR 3W
        'Phase 2 phase angle [º]':               {'addr': 0x0026, '4w': True,  '3w': False, '2w': False},
        'Phase 3 phase angle [º]':               {'addr': 0x0028, '4w': True,  '3w': False, '2w': False},
        'Average line to neutral volts [V]':     {'addr': 0x002a, '4w': True,  '3w': True,  '2w': False},
        'Average line current [A]':              {'addr': 0x002e, '4w': True,  '3w': True,  '2w': True},
        'Sum of line currents [A]':              {'addr': 0x0030, '4w': True,  '3w': True,  '2w': True},
        # 0x0032
        'Total system power [W]':                {'addr': 0x0034, '4w': True,  '3w': True,  '2w': True},
        # 0x0036
        'Total system volt amps [VA]':           {'addr': 0x0038, '4w': True,  '3w': True,  '2w': True},
        # 0x003a
        'Total system VAr [VAr]':                {'addr': 0x003c, '4w': True,  '3w': True,  '2w': True},
        'Total system power factor []':          {'addr': 0x003e, '4w': True,  '3w': True,  '2w': True},
        # 0x0040
        'Total system phase angle [º]':          {'addr': 0x0042, '4w': True,  '3w': True,  '2w': True},
        # 0x0044
        'Frequency of supply voltage [Hz]':      {'addr': 0x0046, '4w': True,  '3w': True,  '2w': True},
        'Import Wh since reset [kWh]':           {'addr': 0x0048, '4w': True,  '3w': True,  '2w': True},
        'Export Wh since reset [kWh]':           {'addr': 0x004a, '4w': True,  '3w': True,  '2w': True},
        'Import VArh since reset [kVArh]':       {'addr': 0x004c, '4w': True,  '3w': True,  '2w': True},
        'Export VArh since reset [kVArh]':       {'addr': 0x004e, '4w': True,  '3w': True,  '2w': True},
        'VAh since reset [kVAh]':                {'addr': 0x0050, '4w': True,  '3w': True,  '2w': True},
        'Ah since reset [Ah]':                   {'addr': 0x0052, '4w': True,  '3w': True,  '2w': True},
        'Total system power demand [W]':         {'addr': 0x0054, '4w': True,  '3w': True,  '2w': True},
        'Maximum total system power demand [W]': {'addr': 0x0056, '4w': True,  '3w': True,  '2w': True},
        # 0x0058-0x0063
        'Total system VA demand [kVA]':          {'addr': 0x0064, '4w': True,  '3w': True,  '2w': True},
        'Maxumum total system VA demand [kVA]':  {'addr': 0x0066, '4w': True,  '3w': True,  '2w': True},
        'Neutral current demand [A]':            {'addr': 0x0068, '4w': True,  '3w': False, '2w': False},
        'Maximum neutral current demand [A]':    {'addr': 0x006a, '4w': True,  '3w': False, '2w': False},
        # 0x006c-0x00c7
        'Line 1 to Line 2 volts [V]':            {'addr': 0x00c8, '4w': True,  '3w': True,  '2w': False},
        'Line 2 to Line 3 volts [V]':            {'addr': 0x00ca, '4w': True,  '3w': True,  '2w': False},
        'Line 3 to Line 1 volts [V]':            {'addr': 0x00cc, '4w': True,  '3w': True,  '2w': False},
        'Average line to line volts [V]':        {'addr': 0x00ce, '4w': True,  '3w': True,  '2w': False},
        # 0x00d0-0x00df
        'Neutral current [A]':                   {'addr': 0x00e0, '4w': True,  '3w': False, '2w': False},
        # 0x00e2-0x00e9
        'Phase L1-N volts THD [%]':              {'addr': 0x00ea, '4w': True,  '3w': False, '2w': True},
        'Phase L2-N volts THD [%]':              {'addr': 0x00ec, '4w': True,  '3w': False, '2w': False},
        'Phase L3-N volts THD [%]':              {'addr': 0x00ee, '4w': True,  '3w': False, '2w': False},
        'Phase 1 current THD [%]':               {'addr': 0x00f0, '4w': True,  '3w': True,  '2w': True},
        'Phase 2 current THD [%]':               {'addr': 0x00f2, '4w': True,  '3w': False, '2w': False},
        'Phase 3 current THD [%]':               {'addr': 0x00f4, '4w': True,  '3w': True,  '2w': False},
        'Average L-N volts THD [%]':             {'addr': 0x00f8, '4w': True,  '3w': False, '2w': True},
        'Average line current THD [%]':          {'addr': 0x00fa, '4w': True,  '3w': True,  '2w': True},
        # 0x00fc
        #'-Total system power factor [º]':        {'addr': 0x00fe, '4w': True,  '3w': True,  '2w': True},
        # ^^^^ Wrong (should be Total system phase angle [º]) and duplicate of 0x0042
        # 0x0100
        'Phase 1 current demand [A]':            {'addr': 0x0102, '4w': True,  '3w': True,  '2w': True},
        'Phase 2 current demand [A]':            {'addr': 0x0104, '4w': True,  '3w': True,  '2w': False},
        'Phase 3 current demand [A]':            {'addr': 0x0106, '4w': True,  '3w': True,  '2w': False},
        'Maximum phase 1 current demand [A]':    {'addr': 0x0108, '4w': True,  '3w': True,  '2w': True},
        'Maximum phase 2 current demand [A]':    {'addr': 0x010a, '4w': True,  '3w': True,  '2w': False},
        'Maximum phase 3 current demand [A]':    {'addr': 0x010c, '4w': True,  '3w': True,  '2w': False},
        # 0x010e-0x014d
        'Line 1 to Line 2 volts THD [%]':        {'addr': 0x014e, '4w': True,  '3w': True,  '2w': False},
        'Line 2 to Line 3 volts THD [%]':        {'addr': 0x0150, '4w': True,  '3w': True,  '2w': False},
        'Line 3 to Line 1 volts THD [%]':        {'addr': 0x0152, '4w': True,  '3w': True,  '2w': False},
        'Average line to line volts THD [%]':    {'addr': 0x0154, '4w': True,  '3w': True,  '2w': False},
    }

    def read_input_registers_float(self, *addresses):
        if len(addresses) == 1 and (isinstance(addresses, list) or isinstance(addresses, tuple)):
            addresses = addresses[0]

        ranges = [(a, 2) for a in addresses]
        registers = self.read_input_registers(*ranges)
        assert len(registers) % 2 == 0

        float_regs = {}
        for a in addresses:
            float_value, = struct.unpack(">f", struct.pack(">HH", registers[a], registers[a+1]))
            float_regs[a] = float_value
        return float_regs

    def delayed_read(self, address, modifier_function=None):
        p = Promise(modifier_function)

        if address not in self.delayed_reads:
            self.delayed_reads[address] = []
        self.delayed_reads[address].append(p)

        return p

    def do_delayed_reads(self):
        addresses = []
        for addr, _ in self.delayed_reads.items():
            addresses.append(addr)
        vals = self.read_input_registers_float(addresses)

        for addr, proms in self.delayed_reads.items():
            for prom in proms:
                prom.set_value(vals[addr])

        self.delayed_reads = {}


class Eastron3P3W(Eastron):
    """Wrapper class to re-calculate wrong values"""
    @functools.lru_cache()
    def _data(self) -> dict:
        return self.read_input_registers_float(
            self.defined_registers['Line 1 to Line 2 volts [V]']['addr'],
            self.defined_registers['Line 2 to Line 3 volts [V]']['addr'],
            self.defined_registers['Line 3 to Line 1 volts [V]']['addr'],
            self.defined_registers['Phase 1 power [W]']['addr'],
            self.defined_registers['Phase 1 volt amps reactive [VAr]']['addr'],
            self.defined_registers['Phase 3 power [W]']['addr'],
            self.defined_registers['Phase 3 volt amps reactive [VAr]']['addr'],
            self.defined_registers['Frequency of supply voltage [Hz]']['addr'],
            self.defined_registers['Import Wh since reset [kWh]']['addr'],
            self.defined_registers['Export Wh since reset [kWh]']['addr'],
            self.defined_registers['Import VArh since reset [kVArh]']['addr'],
            self.defined_registers['Export VArh since reset [kVArh]']['addr'],
        )

    def _addr(self, addr: int) -> float:
        return self._data()[addr]

    def U12(self) -> float:
        return self._addr(self.defined_registers['Line 1 to Line 2 volts [V]']['addr'])

    def U23(self) -> float:
        return self._addr(self.defined_registers['Line 2 to Line 3 volts [V]']['addr'])

    def U31(self) -> float:
        return self._addr(self.defined_registers['Line 3 to Line 1 volts [V]']['addr'])

    def S1_u12(self) -> complex:
        """Phase 1 power. Angle lagging relative to U12."""
        return complex(
            self._addr(self.defined_registers['Phase 1 power [W]']['addr']),
            self._addr(self.defined_registers['Phase 1 volt amps reactive [VAr]']['addr']),
        )

    def S3_u32(self) -> complex:
        """Phase 3 power. Angle lagging relative to U32."""
        return complex(
            self._addr(self.defined_registers['Phase 3 power [W]']['addr']),
            self._addr(self.defined_registers['Phase 3 volt amps reactive [VAr]']['addr']),
        )
    
    def S(self) -> complex:
        # TODO: do we need to correct the phase angles?
        return self.S1_u12() + self.S3_u32()

    def E(self) -> complex:
        r = self._addr(self.defined_registers['Import Wh since reset [kWh]']['addr']) - \
            self._addr(self.defined_registers['Export Wh since reset [kWh]']['addr'])
        im = self._addr(self.defined_registers['Import VArh since reset [kVArh]']['addr']) - \
            self._addr(self.defined_registers['Export VArh since reset [kVArh]']['addr'])
        return complex(r, im)

    def I1_u12(self) -> complex:
        """Phase 1 current. Angle leading relative to U12."""
        return (self.S1_u12() / self.U12()).conjugate()

    def I1_u1(self) -> complex:
        """Phase 1 current. Angle leading relative to U1"""
        # Should match in amplitude with "Phase 1 current [A]"
        # Convert from relative to U12 -> relative to U1
        return - (self.I1_u12() * cmath.rect(1, 150 / 180 * cmath.pi))

    def I3_u32(self) -> complex:
        """Phase 1 current. Angle leading relative to U12"""
        return (self.S3_u32() / self.U23()).conjugate()

    def I3_u1(self) -> complex:
        """Phase 3 current. Angle leading relative to U1"""
        # Should match in amplitude with "Phase 3 current [A]"
        # Convert from relative to U32 -> relative to U1
        return - (self.I3_u32() * cmath.rect(1, 90 / 180 * cmath.pi))

    def I3_u3(self) -> complex:
        """Phase 3 current. Angle leading relative to U3"""
        return self.I3_u1() * cmath.rect(1, 120 / 180 * cmath.pi)

    def I2_u1(self) -> complex:
        """Phase 2 current. Angle leading relative to U1"""
        # "Phase 2 current [A]" is wrong. We need to calculate it ourselves
        return - self.I1_u1() - self.I3_u1()

    def I2_u2(self) -> complex:
        """Phase 2 current. Angle leading relative to U2"""
        return self.I2_u1() * cmath.rect(1, -120 / 180 * cmath.pi)

    def f(self) -> float:
        return self._addr(self.defined_registers['Frequency of supply voltage [Hz]']['addr'])
