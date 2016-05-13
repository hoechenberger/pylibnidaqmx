#!/usr/bin/env python

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import ctypes
import numpy as np

from .utils import CALL
from .loader import DAQmx
from .types import bool32, int32, float64
from .task import Task


class AnalogInputTask(Task):
    """
    Exposes NI-DAQmx analog input task to Python.

    See also
    --------
    nidaqmx.libnidaqmx.Task
    """

    channel_type = 'AI'

    def get_convert_max_rate(self):
        """
        Indicates the maximum convert rate supported by the task,
        given the current devices and channel count.

        This rate is generally faster than the default AI Convert
        Clock rate selected by NI-DAQmx, because NI-DAQmx adds in an
        additional 10 microseconds per channel settling time to
        compensate for most potential system settling constraints.

        For single channel tasks, the maximum AI Convert Clock rate is
        the maximum rate of the ADC. For multiple channel tasks, the
        maximum AI Convert Clock rate is the maximum convert rate of
        the analog front end. Sig
        """
        d = float64(0)
        CALL('GetAIConvMaxRate', self, ctypes.byref(d))
        return d.value

    def create_voltage_channel(self, phys_channel, channel_name="",
                               terminal='default',
                               min_val=-1, max_val=1,
                               units='volts', custom_scale_name=None):
        """
        Creates channel(s) to measure voltage and adds the channel(s)
        to the task you specify with taskHandle. If your measurement
        requires the use of internal excitation or you need the
        voltage to be scaled by excitation, call
        DAQmxCreateAIVoltageChanWithExcit.

        Parameters
        ----------

        phys_channel : str
          The names of the physical channels to use to create virtual
          channels. You can specify a list or range of physical
          channels.

        channel_name : str
          The name(s) to assign to the created virtual channel(s). If
          you do not specify a name, NI-DAQmx uses the physical
          channel name as the virtual channel name. If you specify
          your own names for nameToAssignToChannel, you must use the
          names when you refer to these channels in other NI-DAQmx
          functions.

          If you create multiple virtual channels with one call to
          this function, you can specify a list of names separated by
          commas. If you provide fewer names than the number of
          virtual channels you create, NI-DAQmx automatically assigns
          names to the virtual channels.

        terminal : {'default', 'rse', 'nrse', 'diff', 'pseudodiff'}
          The input terminal configuration for the channel:

            'default'
              At run time, NI-DAQmx chooses the default terminal
              configuration for the channel.

            'rse'
              Referenced single-ended mode

            'nrse'
              Nonreferenced single-ended mode

            'diff'
              Differential mode

            'pseudodiff'
              Pseudodifferential mode

        min_val :
          The minimum value, in units, that you expect to measure.

        max_val :
          The maximum value, in units, that you expect to measure.

        units : {'volts', 'custom'}
          The units to use to return the voltage measurements:

            'volts'
              volts

            'custom'
              Units a custom scale specifies. Use custom_scale_name to
              specify a custom scale.

        custom_scale_name :
          The name of a custom scale to apply to the channel. To use
          this parameter, you must set units to 'custom'.  If you do
          not set units to 'custom', you must set custom_scale_name to
          None.

        Returns
        -------

          success_status : bool

        """
        phys_channel = str(phys_channel)
        channel_name = str(channel_name)
        terminal_map = dict(default=DAQmx.Val_Cfg_Default,
                            rse=DAQmx.Val_RSE,
                            nrse=DAQmx.Val_NRSE,
                            diff=DAQmx.Val_Diff,
                            pseudodiff=DAQmx.Val_PseudoDiff)
        units_map = dict(volts=DAQmx.Val_Volts,
                         custom=DAQmx.Val_FromCustomScale)

        terminal_val = self._get_map_value('terminal', terminal_map,
                                           terminal.lower())
        units_val = self._get_map_value('units', units_map, units)

        if units_val == DAQmx.Val_FromCustomScale:
            if custom_scale_name is None:
                raise ValueError(
                    'Must specify custom_scale_name for custom scale.')

        r = CALL('CreateAIVoltageChan', self, phys_channel, channel_name,
                 terminal_val,
                 float64(min_val), float64(max_val), units_val,
                 custom_scale_name)
        self._set_channel_type(self.get_channel_type(channel_name))
        return r == 0

    def read(self, samples_per_channel=None, timeout=10.0,
             fill_mode='group_by_scan_number'):
        """
        Reads multiple floating-point samples from a task that
        contains one or more analog input channels.

        Parameters
        ----------

        samples_per_channel : int
          The number of samples, per channel, to read. The default
          value of -1 (DAQmx_Val_Auto) reads all available samples. If
          readArray does not contain enough space, this function
          returns as many samples as fit in readArray.

          NI-DAQmx determines how many samples to read based on
          whether the task acquires samples continuously or acquires a
          finite number of samples.

          If the task acquires samples continuously and you set this
          parameter to -1, this function reads all the samples
          currently available in the buffer.

          If the task acquires a finite number of samples and you set
          this parameter to -1, the function waits for the task to
          acquire all requested samples, then reads those samples. If
          you set the Read All Available Samples property to TRUE, the
          function reads the samples currently available in the buffer
          and does not wait for the task to acquire all requested
          samples.

        timeout : float
          The amount of time, in seconds, to wait for the function to
          read the sample(s). The default value is 10.0 seconds. To
          specify an infinite wait, pass -1
          (DAQmx_Val_WaitInfinitely). This function returns an error
          if the timeout elapses.

          A value of 0 indicates to try once to read the requested
          samples. If all the requested samples are read, the function
          is successful. Otherwise, the function returns a timeout
          error and returns the samples that were actually read.

        fill_mode : {'group_by_channel', 'group_by_scan_number'}
          Specifies whether or not the samples are interleaved:

            'group_by_channel'
              Group by channel (non-interleaved)::

                ch0:s1, ch0:s2, ..., ch1:s1, ch1:s2,..., ch2:s1,..

            'group_by_scan_number'
              Group by scan number (interleaved)::

                ch0:s1, ch1:s1, ch2:s1, ch0:s2, ch1:s2, ch2:s2,...

        Returns
        -------

        data :
          The array to read samples into, organized according to `fill_mode`.
        """
        fill_mode_map = dict(group_by_channel=DAQmx.Val_GroupByChannel,
                             group_by_scan_number=DAQmx.Val_GroupByScanNumber)
        fill_mode_val = self._get_map_value('fill_mode', fill_mode_map,
                                            fill_mode)

        if samples_per_channel is None:
            samples_per_channel = self.get_samples_per_channel_available()

        number_of_channels = self.get_number_of_channels()
        # pylint: disable=no-member
        if fill_mode == 'group_by_scan_number':
            data = np.zeros((samples_per_channel, number_of_channels),
                            dtype=np.float64)
        else:
            data = np.zeros((number_of_channels, samples_per_channel),
                            dtype=np.float64)
        # pylint: enable=no-member
        samples_read = int32(0)

        CALL('ReadAnalogF64', self, samples_per_channel, float64(timeout),
             fill_mode_val, data.ctypes.data, data.size,
             ctypes.byref(samples_read), None)

        if samples_per_channel < samples_read.value:
            if fill_mode == 'group_by_scan_number':
                return data[:samples_read.value]
            else:
                return data[:, :samples_read.value]
        return data

    def read_scalar(self, timeout=10.0):
        """
        Reads a single floating-point sample from a task that
        contains a single analog input channel.

        Parameters
        ----------

        timeout : float
          The amount of time, in seconds, to wait for the function to
          read the sample(s). The default value is 10.0 seconds. To
          specify an infinite wait, pass -1 (DAQmx_Val_WaitInfinitely).
          This function returns an error if the timeout elapses.

          A value of 0 indicates to try once to read the requested
          samples. If all the requested samples are read, the function
          is successful. Otherwise, the function returns a timeout error
          and returns the samples that were actually read.

        Returns
        -------

        data : float
          The sample read from the task.
        """

        data = float64(0)
        CALL('ReadAnalogScalarF64', self,
             float64(timeout), ctypes.byref(data), None)
        return data.value


class AnalogOutputTask(Task):
    """Exposes NI-DAQmx analog output task to Python.
    """

    channel_type = 'AO'

    def create_voltage_channel(self, phys_channel, channel_name="",
                               min_val=-1, max_val=1,
                               units='volts', custom_scale_name=None):
        """
        Creates channel(s) to generate voltage and adds the channel(s)
        to the task you specify with taskHandle.

        Returns
        -------

          success_status : bool

        See also
        --------

          AnalogInputTask.create_voltage_channel
        """
        phys_channel = str(phys_channel)
        channel_name = str(channel_name)
        if custom_scale_name is not None:
            custom_scale_name = str(custom_scale_name)
        self._set_channel_type('AO')
        units_map = dict(volts=DAQmx.Val_Volts,
                         custom=DAQmx.Val_FromCustomScale)

        units_val = self._get_map_value('units', units_map, units)

        if units_val == DAQmx.Val_FromCustomScale:
            if custom_scale_name is None:
                raise ValueError(
                    'Must specify custom_scale_name for custom scale.')

        r = CALL('CreateAOVoltageChan', self, phys_channel, channel_name,
                 float64(min_val), float64(max_val), units_val,
                 custom_scale_name)
        self._set_channel_type(self.get_channel_type(channel_name))
        return r == 0

    def write(self, data,
              auto_start=True, timeout=10.0, layout='group_by_scan_number'):
        """
        Writes multiple floating-point samples or a scalar to a task
        that contains one or more analog output channels.

        Note: If you configured timing for your task, your write is
        considered a buffered write. Buffered writes require a minimum
        buffer size of 2 samples. If you do not configure the buffer
        size using DAQmxCfgOutputBuffer, NI-DAQmx automatically
        configures the buffer when you configure sample timing. If you
        attempt to write one sample for a buffered write without
        configuring the buffer, you will receive an error.

        Parameters
        ----------

        data : array

          The array of 64-bit samples to write to the task
          or a scalar.

        auto_start : bool

          Specifies whether or not this function automatically starts
          the task if you do not start it.

        timeout : float

          The amount of time, in seconds, to wait for this
          function to write all the samples. The default value is 10.0
          seconds. To specify an infinite wait, pass -1
          (DAQmx_Val_WaitInfinitely). This function returns an error
          if the timeout elapses.

          A value of 0 indicates to try once to write the submitted
          samples. If this function successfully writes all submitted
          samples, it does not return an error. Otherwise, the
          function returns a timeout error and returns the number of
          samples actually written.

        layout : {'group_by_channel', 'group_by_scan_number'}

          Specifies how the samples are arranged, either interleaved
          or noninterleaved:

            'group_by_channel' - Group by channel (non-interleaved).

            'group_by_scan_number' - Group by scan number (interleaved).

          Applies iff data is array.

        Returns
        -------

        samples_written : int

          The actual number of samples per channel successfully
          written to the buffer. Applies iff data is array.

        """
        if np.isscalar(data):  # pylint: disable=no-member
            return CALL('WriteAnalogScalarF64', self, bool32(auto_start),
                        float64(timeout), float64(data), None) == 0

        layout_map = dict(group_by_channel=DAQmx.Val_GroupByChannel,
                          group_by_scan_number=DAQmx.Val_GroupByScanNumber)
        layout_val = self._get_map_value('layout', layout_map, layout)

        samples_written = int32(0)

        data = np.asarray(data, dtype=np.float64)  # pylint: disable=no-member
        data, samples_per_channel = self._reshape_data(data, layout)

        CALL('WriteAnalogF64', self, int32(samples_per_channel),
             bool32(auto_start),
             float64(timeout), layout_val, data.ctypes.data,
             ctypes.byref(samples_written), None)

        return samples_written.value
