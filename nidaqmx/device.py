#!/usr/bin/env python

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import ctypes

from .types import int32, uInt32
from .utils import CALL
from .loader import DAQmx
from .constants import default_buf_size


class Device(str):
    """
    Exposes NI-DACmx device to Python.
    """

    def get_product_type (self):
        """
        Indicates the product name of the device.
        """
        buf_size = default_buf_size
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL ('GetDevProductType', self, ctypes.byref (buf), buf_size)
        return buf.value

    def get_product_number(self):
        """
        Indicates the unique hardware identification number for the
        device.
        """
        d = uInt32 (0)
        CALL ('GetDevProductNum', self, ctypes.byref(d))
        return d.value

    def get_serial_number (self):
        """
        Indicates the serial number of the device. This value is zero
        if the device does not have a serial number.
        """
        d = uInt32 (0)
        CALL ('GetDevSerialNum', self, ctypes.byref(d))
        return d.value

    def get_analog_input_channels(self, buf_size=None):
        """
        Indicates an array containing the names of the analog input
        physical channels available on the device.

        Parameters
        ----------
        buf_size : {int, None}
          Size of the buffer for retrieving information. If ``buf_size``
          is ``None`` then `nidaqmx.libnidaqmx.default_buf_size` will be
          used.

        Returns
        -------
        names : list
        """
        if buf_size is None:
            buf_size = default_buf_size
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL ('GetDevAIPhysicalChans', self, ctypes.byref (buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        return names

    def get_analog_output_channels(self, buf_size=None):
        """
        Indicates an array containing the names of the analog output
        physical channels available on the device.

        Parameters
        ----------
        buf_size : {int, None}
          Size of the buffer for retrieving information. If ``buf_size``
          is ``None`` then `nidaqmx.libnidaqmx.default_buf_size` will be
          used.

        Returns
        -------
        names : list
        """
        if buf_size is None:
            buf_size = default_buf_size
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL('GetDevAOPhysicalChans', self, ctypes.byref (buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        return names

    def get_digital_input_lines(self, buf_size=None):
        """
        Indicates an array containing the names of the digital input
        lines available on the device.

        Parameters
        ----------
        buf_size : {int, None}
          Size of the buffer for retrieving information. If ``buf_size``
          is ``None`` then `nidaqmx.libnidaqmx.default_buf_size` will be
          used.

        Returns
        -------
        names : list
        """
        if buf_size is None:
            buf_size = default_buf_size
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL ('GetDevDILines', self, ctypes.byref (buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        return names

    def get_digital_input_ports(self, buf_size=None):
        """
        Indicates an array containing the names of the digital input
        ports available on the device.

        Parameters
        ----------
        buf_size : {int, None}
          Size of the buffer for retrieving information. If ``buf_size``
          is ``None`` then `nidaqmx.libnidaqmx.default_buf_size` will be
          used.

        Returns
        -------
        names : list
        """
        if buf_size is None:
            buf_size = default_buf_size
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL ('GetDevDIPorts', self, ctypes.byref (buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        return names

    def get_digital_output_lines(self, buf_size=None):
        """
        Indicates an array containing the names of the digital output
        lines available on the device.

        Parameters
        ----------
        buf_size : {int, None}
          Size of the buffer for retrieving information. If ``buf_size``
          is ``None`` then `nidaqmx.libnidaqmx.default_buf_size` will be
          used.

        Returns
        -------
        names : list
        """
        if buf_size is None:
            buf_size = default_buf_size
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL ('GetDevDOLines', self, ctypes.byref (buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        return names

    def get_digital_output_ports(self, buf_size=None):
        """
        Indicates an array containing the names of the digital output
        ports available on the device.

        Parameters
        ----------
        buf_size : {int, None}
          Size of the buffer for retrieving information. If ``buf_size``
          is ``None`` then `nidaqmx.libnidaqmx.default_buf_size` will be
          used.

        Returns
        -------
        names : list
        """
        if buf_size is None:
            buf_size = default_buf_size
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL ('GetDevDOPorts', self, ctypes.byref (buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        return names

    def get_counter_input_channels (self, buf_size=None):
        """
        Indicates an array containing the names of the counter input
        physical channels available on the device.

        Parameters
        ----------
        buf_size : {int, None}
          Size of the buffer for retrieving information. If ``buf_size``
          is ``None`` then `nidaqmx.libnidaqmx.default_buf_size` will be
          used.

        Returns
        -------
        names : list
        """
        if buf_size is None:
            buf_size = default_buf_size
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL ('GetDevCIPhysicalChans', self, ctypes.byref (buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        return names

    def get_counter_output_channels (self, buf_size=None):
        """
        Indicates an array containing the names of the counter output
        physical channels available on the device.

        Parameters
        ----------
        buf_size : {int, None}
          Size of the buffer for retrieving information. If ``buf_size``
          is ``None`` then `nidaqmx.libnidaqmx.default_buf_size` will be
          used.

        Returns
        -------
        names : list
        """
        if buf_size is None:
            buf_size = default_buf_size
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL ('GetDevCOPhysicalChans', self, ctypes.byref (buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        return names

    def get_bus_type(self):
        """
        Indicates the bus type of the device.
        """
        bus_type_map = {DAQmx.Val_PCI: 'PCI',
                        DAQmx.Val_PCIe: 'PCIe',
                        DAQmx.Val_PXI: 'PXI',
                        DAQmx.Val_SCXI:'SCXI',
                        DAQmx.Val_PCCard:'PCCard',
                        DAQmx.Val_USB:'USB',
                        DAQmx.Val_Unknown:'UNKNOWN'}
        d = int32(0)
        CALL ('GetDevBusType', self, ctypes.byref (d))
        return bus_type_map[d.value]

    def get_pci_bus_number (self):
        """
        Indicates the PCI bus number of the device.
        """
        d = uInt32(0)
        CALL ('GetDevPCIBusNum', self, ctypes.byref (d))
        return d.value

    def get_pci_device_number (self):
        """
        Indicates the PCI slot number of the device.
        """
        d = uInt32(0)
        CALL ('GetDevPCIDevNum', self, ctypes.byref (d))
        return d.value

    def get_pxi_slot_number (self):
        """
        Indicates the PXI slot number of the device.
        """
        d = uInt32(0)
        CALL ('GetDevPXISlotNum', self, ctypes.byref (d))
        return d.value

    def get_pxi_chassis_number (self):
        """
        Indicates the PXI chassis number of the device, as identified
        in MAX.
        """
        d = uInt32(0)
        CALL ('GetDevPXIChassisNum', self, ctypes.byref (d))
        return d.value

    def get_bus(self):
        t = self.get_bus_type()
        if t in ['PCI', 'PCIe']:
            return '%s (bus=%s, device=%s)' % (t, self.get_pci_bus_number (), self.get_pci_device_number())
        if t=='PXI':
            return '%s (chassis=%s, slot=%s)' % (t, self.get_pxi_chassis_number (), self.get_pxi_slot_number())
        return t

    def reset(self):
        """
        Stops and deletes all tasks on a device and rests outputs to their defaults
        calls  int32 DAQmxResetDevice (const char deviceName[]);
        """
        return CALL('ResetDevice',self)
