import math

import pytest
import cmath

from unittest import mock

from pytest import approx

import src.eastron as eastron


def test_Ii12():
    with mock.patch('src.eastron.Eastron3P3W._data', return_value=convert_addr({
        'P1': 1000,
        'Q1': 0,
        'P3': 0,
        'Q3': 0,
        'I1': 10,
        'I2': 10,
        'I3': 0,
        'U12': 100,
        'U23': 100,
        'U31': 100,
    })):
        e = eastron.Eastron3P3W(None, None)

        I1 = e.I1_u12()
        assert approx(10) == abs(I1)

        angle = cmath.phase(I1) / cmath.pi * 180
        assert approx(0) == angle

        angle = cmath.phase(e.I1_u1()) / cmath.pi * 180
        assert approx(-30) == angle

        I3 = e.I3_u1()
        assert approx(0) == I3

        I2 = e.I2_u1()
        assert approx(10) == abs(I2)

        angle = cmath.phase(e.I2_u2()) / cmath.pi * 180
        assert approx(30) == angle


def test_L12():
    with mock.patch('src.eastron.Eastron3P3W._data', return_value=convert_addr({
        'P1': 0,
        'Q1': 1000,
        'P3': 1,
        'Q3': 0,
        'I1': 10,
        'I2': 10,
        'I3': 0.01,
        'U12': 100,
        'U23': 100,
        'U31': 100,
    })):
        e = eastron.Eastron3P3W(None, None)

        assert 1000j == e.S1_u12()

        assert approx(10) == abs(e.I1_u12())

        angle = cmath.phase(e.I1_u1()) / cmath.pi * 180
        assert approx(-120) == angle

        angle = cmath.phase(e.I2_u1()) / cmath.pi * 180
        assert approx(60, rel=0.001) == angle

        angle = cmath.phase(e.I2_u2()) / cmath.pi * 180
        assert approx(-60, rel=0.001) == angle


def test_Ii23():
    with mock.patch('src.eastron.Eastron3P3W._data', return_value=convert_addr({
        'P1': 0,
        'Q1': 0,
        'P3': 1000,
        'Q3': 0,
        'I1': 0,
        'I2': 10,
        'I3': 10,
        'U12': 100,
        'U23': 100,
        'U31': 100,

    })):
        e = eastron.Eastron3P3W(None, None)

        I3 = e.I3_u32()
        assert approx(10) == abs(I3)

        angle = cmath.phase(I3) / cmath.pi * 180
        assert approx(0) == angle

        angle = cmath.phase(e.I3_u1()) / cmath.pi * 180
        assert approx(-90) == angle

        angle = cmath.phase(e.I3_u3()) / cmath.pi * 180
        assert approx(30) == angle

        I1 = e.I1_u1()
        assert approx(0) == I1

        I2 = e.I2_u1()
        assert approx(10) == abs(I2)

        angle = cmath.phase(e.I2_u2()) / cmath.pi * 180
        assert approx(-30) == angle


def test_Ii31():
    with mock.patch('src.eastron.Eastron3P3W._data', return_value=convert_addr({
        'P1': 1000 * math.cos(-60 / 180 * math.pi),
        'Q1': 1000 * math.sin(-60 / 180 * math.pi),
        'P3': 1000 * math.cos(60 / 180 * math.pi),
        'Q3': 1000 * math.sin(60 / 180 * math.pi),
        'I1': 10,
        'I2': 0,
        'I3': 10,
        'U12': 100,
        'U23': 100,
        'U31': 100,
    })):
        e = eastron.Eastron3P3W(None, None)

        I1 = e.I1_u12()
        assert approx(10) == abs(I1)

        angle = cmath.phase(e.I1_u1()) / cmath.pi * 180
        assert approx(30) == angle

        I3 = e.I3_u1()
        assert approx(10) == abs(I3)
        angle = cmath.phase(e.I3_u1()) / cmath.pi * 180
        assert approx(-150) == angle

        angle = cmath.phase(e.I3_u3()) / cmath.pi * 180
        assert approx(-30) == angle

        I2 = e.I2_u1()
        assert abs(I2) < 1




I12 = pytest.param(
    {
        'P1': 2116,
        'P3': 295,
        'Q1': -446,
        'Q3': 85,
        'I1': 9.198,
        'I2': 8.120,
        'I3': 1.294,
        'U12': 235.34,
        'U23': 237.46,
        'U31': 236.40,
    },
    id='I12',
)
I23 = pytest.param(
    {
        'P1': 85,
        'P3': 2749,
        'Q1': -116,
        'Q3': 87,
        'I1': 0.609,
        'I2': 11.063,
        'I3': 11.670,
        'U12': 235.90,
        'U23': 235.71,
        'U31': 235.81,
    },
    id='I23',
)
I31 = pytest.param(
    {
        'P1': 335,
        'Q1': -1207,
        'P3': 990,
        'Q3': 842,
        'I1': 5.296,
        'I2': 4.964,  # wrong
        'I3': 5.481,
        'U12': 236.52,
        'U23': 237.12,
        'U31': 236.82,
    },
    id='I31',
)
params = [I12, I23, I31]


def convert_addr(params: dict) -> dict:
    return {
        eastron.Eastron3P3W.defined_registers['Line 1 to Line 2 volts [V]']['addr']: params['U12'],
        eastron.Eastron3P3W.defined_registers['Line 2 to Line 3 volts [V]']['addr']: params['U23'],
        eastron.Eastron3P3W.defined_registers['Line 3 to Line 1 volts [V]']['addr']: params['U31'],
        eastron.Eastron3P3W.defined_registers['Phase 1 power [W]']['addr']: params['P1'],
        eastron.Eastron3P3W.defined_registers['Phase 1 volt amps reactive [VAr]']['addr']: params['Q1'],
        eastron.Eastron3P3W.defined_registers['Phase 3 power [W]']['addr']: params['P3'],
        eastron.Eastron3P3W.defined_registers['Phase 3 volt amps reactive [VAr]']['addr']: params['Q3'],
        eastron.Eastron3P3W.defined_registers['Frequency of supply voltage [Hz]']['addr']: 50,
        eastron.Eastron3P3W.defined_registers['Import Wh since reset [kWh]']['addr']: 0,
        eastron.Eastron3P3W.defined_registers['Export Wh since reset [kWh]']['addr']: 0,
        eastron.Eastron3P3W.defined_registers['Import VArh since reset [kVArh]']['addr']: 0,
        eastron.Eastron3P3W.defined_registers['Export VArh since reset [kVArh]']['addr']: 0,
    }


@pytest.mark.parametrize("params", params)
def test_sanity(params):
    with mock.patch('src.eastron.Eastron3P3W._data', return_value=convert_addr(params)):
        e = eastron.Eastron3P3W(None, None)
        assert e.U12() == params['U12']
        assert e.U23() == params['U23']
        assert e.U31() == params['U31']
        assert e.S1_u12().real == params['P1']
        assert e.S1_u12().imag == params['Q1']
        assert e.S3_u32().real == params['P3']
        assert e.S3_u32().imag == params['Q3']


@pytest.mark.parametrize("params", params)
def test_I1(params):
    with mock.patch('src.eastron.Eastron3P3W._data', return_value=convert_addr(params)):
        e = eastron.Eastron3P3W(None, None)

        assert abs(e.I1_u12()) == approx(params['I1'], rel=0.01)
        assert cmath.phase(e.I1_u12()) + (-30)/180*cmath.pi == approx(cmath.phase(e.I1_u1()))


@pytest.mark.parametrize("params", params)
def test_I3(params):
    with mock.patch('src.eastron.Eastron3P3W._data', return_value=convert_addr(params)):
        e = eastron.Eastron3P3W(None, None)

        assert abs(e.I3_u32()) == approx(params['I3'], rel=0.01)
        assert cmath.phase(e.I3_u32()) + (-90)/180*cmath.pi == approx(cmath.phase(e.I3_u1()))


@pytest.mark.parametrize("params", params)
@pytest.mark.xfail  # I2 is reported incorrectly
def test_I2(params):
    with mock.patch('src.eastron.Eastron3P3W._data', return_value=convert_addr(params)):
        e = eastron.Eastron3P3W(None, None)

        assert abs(e.I2_u1()) == approx(params['I2'], rel=0.01)


@pytest.mark.parametrize("params", params)
def test_Itot(params):
    with mock.patch('src.eastron.Eastron3P3W._data', return_value=convert_addr(params)):
        e = eastron.Eastron3P3W(None, None)

        assert e.I1_u1() + e.I2_u1() + e.I3_u1() == approx(0, abs=0.001)


def test_I31():
    with mock.patch('src.eastron.Eastron3P3W._data', return_value=convert_addr(I31[0][0])):
        e = eastron.Eastron3P3W(None, None)

        I1 = e.I1_u12()
        assert abs(I1) > 4

        angle = cmath.phase(e.I1_u1()) / cmath.pi * 180
        assert approx(30, abs=20) == angle

        I3 = e.I3_u1()
        assert abs(I3) > 4

        I2 = e.I2_u1()
        assert abs(I2) < 1
