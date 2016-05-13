#!/usr/bin/env python

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import ctypes


int8 = ctypes.c_int8
uInt8 = ctypes.c_uint8
int16 = ctypes.c_int16
uInt16 = ctypes.c_uint16
int32 = ctypes.c_int32
bool32 = uInt32 = ctypes.c_uint32
int64 = ctypes.c_int64
uInt64 = ctypes.c_uint64
float32 = ctypes.c_float
float64 = ctypes.c_double
TaskHandle = void_p = ctypes.c_void_p
