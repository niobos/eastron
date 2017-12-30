Introduction
============

This code was made to read out the data exposed by an Eastron SDM630 (but probably also others) energy meter. It
consists of 2 parts:

* ``dump_all.py`` simply dumps all known registers for human inspection
* ``read_influx.py`` reads some chosen registers, and ingests them to my InfluxDB


Sample output
=============

Example output on a 3-phase delta (i.e. 3 wires, no neutral) configuration::

    # venv/bin/python dump_all.py /dev/ttyRS485
    Phase 1 line to neutral volts [V] = 0.0
    Phase 2 line to neutral volts [V] = 0.0
    Phase 3 line to neutral volts [V] = 0.0
    Phase 1 current [A] = 0.9989702701568604
    Phase 2 current [A] = 4.772903919219971
    Phase 3 current [A] = 2.321788787841797
    Phase 1 power [W] = 92.05419921875
    Phase 2 power [W] = 0.0
    Phase 3 power [W] = 521.0418090820312
    Phase 1 volt amps [VA] = 234.46800231933594
    Phase 2 volt amps [VA] = 0.0
    Phase 3 volt amps [VA] = 545.4363403320312
    Phase 1 volt amps reactive [VAr] = -215.6415252685547
    Phase 2 volt amps reactive [VAr] = 0.0
    Phase 3 volt amps reactive [VAr] = 161.2955780029297
    Phase 1 power factor [] = 0.3926132321357727
    Phase 2 power factor [] = 1.0
    Phase 3 power factor [] = 0.9552701115608215
    Phase 1 phase angle [º] = 0.0
    Phase 2 phase angle [º] = 0.0
    Phase 3 phase angle [º] = 0.0
    Average line to neutral volts [V] = 234.81521606445312
    Average line current [A] = 4.762885570526123
    Sum of line currents [A] = 14.288656234741211
    Total system power [W] = 614.8851318359375
    Total system volt amps [VA] = 781.4191284179688
    Total system VAr [VAr] = -55.0536994934082
    Total system power factor [] = 0.9960189461708069
    Total system phase angle [º] = -5.117457866668701
    Frequency of supply voltage [Hz] = 50.027801513671875
    Import Wh since reset [kWh] = 244.02200317382812
    Export Wh since reset [kWh] = 0.0010000000474974513
    Import VArh since reset [kVArh] = 69.47200012207031
    Export VArh since reset [kVArh] = 95.9469985961914
    VAh since reset [kVAh] = 294.80615234375
    Ah since reset [Ah] = 1442.406982421875
    Total system power demand [W] = 590.9715576171875
    Maximum total system power demand [W] = 5762.7353515625
    Total system VA demand [kVA] = 743.248779296875
    Maxumum total system VA demand [kVA] = 7024.75927734375
    Neutral current demand [A] = 0.0
    Maximum neutral current demand [A] = 0.0019397907890379429
    Line 1 to Line 2 volts [V] = 234.70968627929688
    Line 2 to Line 3 volts [V] = 234.9207305908203
    Line 3 to Line 1 volts [V] = 234.81529235839844
    Average line to line volts [V] = 234.81521606445312
    Neutral current [A] = 0.0
    Phase L1-N volts THD [%] = 0.0
    Phase L2-N volts THD [%] = 0.0
    Phase L3-N volts THD [%] = 0.0
    Phase 1 current THD [%] = 441.9278564453125
    Phase 2 current THD [%] = 0.0
    Phase 3 current THD [%] = 188.58114624023438
    Average L-N volts THD [%] = 0.0
    Average line current THD [%] = 315.2545166015625
    Phase 1 current demand [A] = 0.8047537803649902
    Phase 2 current demand [A] = 2.150317668914795
    Phase 3 current demand [A] = 2.359823226928711
    Maximum phase 1 current demand [A] = 13.310205459594727
    Maximum phase 2 current demand [A] = 24.01046371459961
    Maximum phase 3 current demand [A] = 24.498693466186523
    Line 1 to Line 2 volts THD [%] = 0.0
    Line 2 to Line 3 volts THD [%] = 3.58048152923584
    Line 3 to Line 1 volts THD [%] = 0.0
    Average line to line volts THD [%] = 1.79024076461792


Installation
============

No installation is required, but some python modules need to be present. It is recommended to use virtualenv::

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
