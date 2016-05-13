#!/usr/bin/env python

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import ctypes

from .types import uInt32
from .utils import CALL
from .constants import default_buf_size
from .device import Device


class System(object):
    """
    Exposes NI-DACmx system properties to Python.

    Attributes
    ----------
    major_version
    minor_version
    version
    devices
    tasks
    global_channels
    """

    @property
    def major_version(self):
        """
        Indicates the major portion of the installed version of NI-DAQ,
        such as 7 for version 7.0.
        """
        d = uInt32 (0)
        CALL ('GetSysNIDAQMajorVersion', ctypes.byref (d))
        return d.value

    @property
    def minor_version(self):
        """
        Indicates the minor portion of the installed version of NI-DAQ,
        such as 0 for version 7.0.
        """
        d = uInt32 (0)
        CALL ('GetSysNIDAQMinorVersion', ctypes.byref (d))
        return d.value

    @property
    def version (self):
        """
        Return NI-DAQ driver software version string.
        """
        return '%s.%s' % (self.major_version, self.minor_version)

    @property
    def devices(self):
        """
        Indicates the names of all devices installed in the system.
        """
        buf_size = default_buf_size
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL ('GetSysDevNames', ctypes.byref (buf), buf_size)
        names = [Device(n.strip()) for n in buf.value.split(',') if n.strip()]
        return names

    @property
    def tasks(self):
        """
        Indicates an array that contains the names of all tasks saved
        on the system.
        """
        buf_size = default_buf_size
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL ('GetSysTasks', ctypes.byref (buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        return names

    @property
    def global_channels(self):
        """
        Indicates an array that contains the names of all global
        channels saved on the system.
        """
        buf_size = default_buf_size
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL ('GetSysGlobalChans', ctypes.byref (buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        return names
