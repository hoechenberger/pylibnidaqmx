#!/usr/bin/env python

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import ctypes
from .types import int32, uInt32, void_p
from .analog import AnalogInputTask, AnalogOutputTask
from .digital import DigitalInputTask, DigitalOutputTask
from .counter import CounterInputTask, CounterOutputTask


DoneEventCallback_map = dict(
    AI=ctypes.CFUNCTYPE(int32, AnalogInputTask, int32, void_p),
    AO=ctypes.CFUNCTYPE(int32, AnalogOutputTask, int32, void_p),
    DI=ctypes.CFUNCTYPE(int32, DigitalInputTask, int32, void_p),
    DO=ctypes.CFUNCTYPE(int32, DigitalOutputTask, int32, void_p),
    CI=ctypes.CFUNCTYPE(int32, CounterInputTask, int32, void_p),
    CO=ctypes.CFUNCTYPE(int32, CounterOutputTask, int32, void_p),
)

EveryNSamplesEventCallback_map = dict(
    AI=ctypes.CFUNCTYPE(int32, AnalogInputTask, int32, uInt32, void_p),
    AO=ctypes.CFUNCTYPE(int32, AnalogOutputTask, int32, uInt32, void_p),
    DI=ctypes.CFUNCTYPE(int32, DigitalInputTask, int32, uInt32, void_p),
    DO=ctypes.CFUNCTYPE(int32, DigitalOutputTask, int32, uInt32, void_p),
    CI=ctypes.CFUNCTYPE(int32, CounterInputTask, int32, uInt32, void_p),
    CO=ctypes.CFUNCTYPE(int32, CounterOutputTask, int32, uInt32, void_p),
)

SignalEventCallback_map = dict(
    AI=ctypes.CFUNCTYPE(int32, AnalogInputTask, int32, void_p),
    AO=ctypes.CFUNCTYPE(int32, AnalogOutputTask, int32, void_p),
    DI=ctypes.CFUNCTYPE(int32, DigitalInputTask, int32, void_p),
    DO=ctypes.CFUNCTYPE(int32, DigitalOutputTask, int32, void_p),
    CI=ctypes.CFUNCTYPE(int32, CounterInputTask, int32, void_p),
    CO=ctypes.CFUNCTYPE(int32, CounterOutputTask, int32, void_p),
)
