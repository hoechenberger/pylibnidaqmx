#!/usr/bin/env python
#
# Please follow
#   http://projects.scipy.org/numpy/wiki/CodingStyleGuidelines
#
# Author: Pearu Peterson
# Created: July 2009
#
# pylint: disable=C,R
#
# See http://pylibnidaqmx.googlecode.com/

"""
.. currentmodule:: nidaqmx

The :mod:`nidaqmx` package provides the following classes:

.. autosummary::

  AnalogInputTask
  AnalogOutputTask
  DigitalInputTask
  DigitalOutputTask
  CounterInputTask
  CounterOutputTask

that expose NI-DAQmx tasks to Python environment. The instances of
these task classes provide methods to create channels, to set timing
and triggering properties, as well as to read or write data.

Example usage
=============

The following example demonstrates how to create an analog output
task that generates voltage to given channel of the NI card::

>>> from nidaqmx import AnalogOutputTask
>>> import numpy as np
>>> data = 9.95*np.sin(np.arange(1000, dtype=np.float64)*2*np.pi/1000)
>>> task = AnalogOutputTask()
>>> task.create_voltage_channel('Dev1/ao2', min_val=-10.0, max_val=10.0)
>>> task.configure_timing_sample_clock(rate=1000.0)
>>> task.write(data, auto_start=False)
>>> task.start()
>>> raw_input('Generating voltage continuously. Press Enter to interrupt..')
>>> task.stop()
>>> del task

The generated voltage can be measured as well when connecting the corresponding
channels in the NI card::

>>> from nidaqmx import AnalogInputTask
>>> import numpy as np
>>> task = AnalogInputTask()
>>> task.create_voltage_channel('Dev1/ai16', terminal = 'rse', min_val=-10.0, max_val=10.0)
>>> task.configure_timing_sample_clock(rate=1000.0)
>>> task.start()
>>> data = task.read(2000, fill_mode='group_by_channel')
>>> del task
>>> from pylab import plot, show
>>> plot (data)
>>> show ()

that should plot two sine waves.

Learning about your NI card and software
========================================

The nidaqmx package allows you to make various queries about the NI
card devices as well as software properties. For that, use
`nidaqmx.System` instance as follows::

  >>> from nidaqmx import System
  >>> system = System()
  >>> print 'libnidaqmx version:',system.version
  libnidaqmx version: 8.0
  >>> print 'NI-DAQ devives:',system.devices
  NI-DAQ devives: ['Dev1', 'Dev2']
  >>> dev1 = system.devices[0]
  >>> print dev1.get_product_type()
  PCIe-6259
  >>> print dev1.get_bus()
  PCIe (bus=7, device=0)
  >>> print dev1.get_analog_input_channels()
  ['Dev1/ai0', 'Dev1/ai1', ..., 'Dev1/ai31']

Note that ``system.devices`` contains instances of
`nidaqmx.Device`.

Module content
==============
"""

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)


from .device import Device
from .system import System
from .loader import get_nidaqmx_version

from .system import System
from .device import Device
from .analog import AnalogInputTask, AnalogOutputTask
from .digital import DigitalInputTask, DigitalOutputTask
from .counter import CounterInputTask, CounterOutputTask


__all__ = [
    'AnalogInputTask', 'AnalogOutputTask',
    'DigitalInputTask', 'DigitalOutputTask',
    'CounterInputTask', 'CounterOutputTask',
    'System', 'Device', 'get_nidaqmx_version',
]


def main():
    t = AnalogInputTask('measure voltage')
    t.create_voltage_channel('Dev1/ai8', 'measure')
    t.configure_timing_sample_clock()

    g = AnalogOutputTask('generate voltage')
    g.create_voltage_channel('Dev1/ao2', 'generate')

    print(t.get_info_str(global_info=True))
    print(g.get_info_str())


if __name__ == '__main__':
    main()
