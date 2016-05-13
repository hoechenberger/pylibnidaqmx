#!/usr/bin/env python

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import ctypes
import numpy as np

from .task import Task
from .utils import CALL
from .loader import DAQmx
from .types import bool32, int32, uInt32, float64


class DigitalTask(Task):
    def get_number_of_lines(self, channel):
        """
        Indicates the number of digital lines in the channel.
        """
        channel_type = self.channel_type
        assert channel_type in ['DI', 'DO'], repr((channel_type, channel))
        channel = str(channel)
        d = uInt32(0)
        CALL('Get%sNumLines' % (channel_type), self, channel, ctypes.byref(d))
        return d.value

    def read(self, samples_per_channel=None, timeout=10.0,
             fill_mode='group_by_scan_number'):
        """
        Reads multiple samples from each digital line in a task. Each
        line in a channel gets one byte per sample.

        Parameters
        ----------

        samples_per_channel : int or None

          The number of samples, per channel, to
          read. The default value of -1 (DAQmx_Val_Auto) reads all
          available samples. If readArray does not contain enough
          space, this function returns as many samples as fit in
          readArray.

          NI-DAQmx determines how many samples to read based on
          whether the task acquires samples continuously or acquires a
          finite number of samples.

          If the task acquires samples continuously and you set this
          parameter to -1, this function reads all the samples
          currently available in the buffer.

          If the task acquires a finite number of samples and you set
          this parameter to -1, the function waits for the task to
          acquire all requested samples, then reads those samples. If
          you set the Read All Available Data property to TRUE, the
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

            'group_by_channel' - Group by channel (non-interleaved).

            'group_by_scan_number' - Group by scan number (interleaved).

        Returns
        -------

          data : array

            The array to read samples into. Each `bytes_per_sample`
            corresponds to one sample per channel, with each element
            in that grouping corresponding to a line in that channel,
            up to the number of lines contained in the channel.

          bytes_per_sample : int

            The number of elements in returned `data` that constitutes
            a sample per channel. For each sample per channel,
            `bytes_per_sample` is the number of bytes that channel
            consists of.

        """
        fill_mode_map = dict(group_by_channel=DAQmx.Val_GroupByChannel,
                             group_by_scan_number=DAQmx.Val_GroupByScanNumber)
        fill_mode_val = self._get_map_value('fill_mode', fill_mode_map,
                                            fill_mode)

        if samples_per_channel in [None, -1]:
            samples_per_channel = self.get_samples_per_channel_available()

        if self.one_channel_for_all_lines:
            nof_lines = []
            for channel in self.get_names_of_channels():
                nof_lines.append(self.get_number_of_lines(channel))
            c = int(max(nof_lines))
            dtype = getattr(np, 'uint%s' % (8 * c))
        else:
            c = 1
            dtype = np.uint8  # pylint: disable=no-member
        number_of_channels = self.get_number_of_channels()
        # pylint: disable=no-member
        if fill_mode == 'group_by_scan_number':
            data = np.zeros((samples_per_channel, number_of_channels),
                            dtype=dtype)
        else:
            data = np.zeros((number_of_channels, samples_per_channel),
                            dtype=dtype)
        # pylint: enable=no-member

        samples_read = int32(0)
        bytes_per_sample = int32(0)

        CALL('ReadDigitalLines', self, samples_per_channel, float64(timeout),
             fill_mode_val, data.ctypes.data, uInt32(data.size * c),
             ctypes.byref(samples_read), ctypes.byref(bytes_per_sample),
             None
             )
        if samples_read.value < samples_per_channel:
            if fill_mode == 'group_by_scan_number':
                return data[:samples_read.value], bytes_per_sample.value
            else:
                return data[:, :samples_read.value], bytes_per_sample.value
        return data, bytes_per_sample.value


class DigitalInputTask(DigitalTask):
    """Exposes NI-DAQmx digital input task to Python.
    """

    def __init__(self, name=""):
        super(DigitalInputTask, self).__init__(name)
        self.one_channel_for_all_lines = None

    channel_type = 'DI'

    def create_channel(self, lines, name='', grouping='per_line'):
        """
        Creates channel(s) to measure digital signals and adds the
        channel(s) to the task you specify with taskHandle. You can
        group digital lines into one digital channel or separate them
        into multiple digital channels. If you specify one or more
        entire ports in lines by using port physical channel names,
        you cannot separate the ports into multiple channels. To
        separate ports into multiple channels, use this function
        multiple times with a different port each time.

        Parameters
        ----------

        lines : str

          The names of the digital lines used to create a virtual
          channel. You can specify a list or range of lines.

        name : str

          The name of the created virtual channel(s). If you create
          multiple virtual channels with one call to this function,
          you can specify a list of names separated by commas. If you
          do not specify a name, NI-DAQmx uses the physical channel
          name as the virtual channel name. If you specify your own
          names for name, you must use the names when you refer to
          these channels in other NI-DAQmx functions.

        grouping : {'per_line', 'for_all_lines'}

          Specifies whether to group digital lines into one or more
          virtual channels. If you specify one or more entire ports in
          lines, you must set grouping to 'for_all_lines':

            'per_line' - One channel for each line

            'for_all_lines' - One channel for all lines

        Returns
        -------

          success_status : bool
        """
        lines = str(lines)
        grouping_map = dict(per_line=DAQmx.Val_ChanPerLine,
                            for_all_lines=DAQmx.Val_ChanForAllLines)
        grouping_val = self._get_map_value('grouping', grouping_map, grouping)
        self.one_channel_for_all_lines = grouping_val == DAQmx.Val_ChanForAllLines
        return CALL('CreateDIChan', self, lines, name, grouping_val) == 0


class DigitalOutputTask(DigitalTask):
    """Exposes NI-DAQmx digital output task to Python.
    """

    channel_type = 'DO'

    def __init__(self, name=""):
        super(DigitalOutputTask, self).__init__(name)
        self.one_channel_for_all_lines = None

    def create_channel(self, lines, name='', grouping='per_line'):
        """
        Creates channel(s) to generate digital signals and adds the
        channel(s) to the task you specify with taskHandle. You can
        group digital lines into one digital channel or separate them
        into multiple digital channels. If you specify one or more
        entire ports in lines by using port physical channel names,
        you cannot separate the ports into multiple channels. To
        separate ports into multiple channels, use this function
        multiple times with a different port each time.

        Parameters
        ----------

        lines : str

          The names of the digital lines used to create a virtual
          channel. You can specify a list or range of lines.

        name : str

          The name of the created virtual channel(s). If you create
          multiple virtual channels with one call to this function,
          you can specify a list of names separated by commas. If you
          do not specify a name, NI-DAQmx uses the physical channel
          name as the virtual channel name. If you specify your own
          names for name, you must use the names when you refer to
          these channels in other NI-DAQmx functions.

        grouping : {'per_line', 'for_all_lines'}

          Specifies whether to group digital lines into one or more
          virtual channels. If you specify one or more entire ports in
          lines, you must set grouping to 'for_all_lines':

            'per_line' - One channel for each line

            'for_all_lines' - One channel for all lines

        Returns
        -------

          success_status : bool
        """
        lines = str(lines)
        grouping_map = dict(per_line=DAQmx.Val_ChanPerLine,
                            for_all_lines=DAQmx.Val_ChanForAllLines)
        grouping_val = self._get_map_value('grouping', grouping_map, grouping)
        self.one_channel_for_all_lines = grouping_val == DAQmx.Val_ChanForAllLines
        return CALL('CreateDOChan', self, lines, name, grouping_val) == 0

    def write(self, data,
              auto_start=True, timeout=10.0,
              layout='group_by_channel'):
        """
        Writes multiple samples to each digital line in a task. When
        you create your write array, each sample per channel must
        contain the number of bytes returned by the
        DAQmx_Read_DigitalLines_BytesPerChan property.

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

          The samples to write to the task.

        auto_start : bool

          Specifies whether or not this function automatically starts
          the task if you do not start it.

        timeout : float

          The amount of time, in seconds, to wait for this function to
          write all the samples. The default value is 10.0 seconds. To
          specify an infinite wait, pass -1
          (DAQmx.Val_WaitInfinitely). This function returns an error
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
        """
        layout_map = dict(group_by_channel=DAQmx.Val_GroupByChannel,
                          group_by_scan_number=DAQmx.Val_GroupByScanNumber)
        layout_val = self._get_map_value('layout', layout_map, layout)
        samples_written = int32(0)

        number_of_channels = self.get_number_of_channels()

        # pylint: disable=no-member
        if np.isscalar(data):
            data = np.array([data] * number_of_channels, dtype=np.uint8)
        else:
            data = np.asarray(data, dtype=np.uint8)
        # pylint: enable=no-member

        data, samples_per_channel = self._reshape_data(data, layout)

        CALL('WriteDigitalLines', self, samples_per_channel,
             bool32(auto_start),
             float64(timeout), layout_val,
             data.ctypes.data, ctypes.byref(samples_written), None)

        return samples_written.value

    def set_drive_type(self, drive_type, channel=None):
        """Sets the drive type of the channel.

        Parameters
        ----------

        drive_type : str or None

          The drive type, one of "active", "open_collector", or None.
          None will reset the drive type.

        channel : str or None

          The name of a channel or terminal to modify.  If None is
          given, use all channels in the task (via
          get_names_of_channels()).

        """
        if channel is None:
            channel = ",".join(self.get_names_of_channels())
        else:
            channel = str(channel)
        output_drive_mapping = dict(
            active=DAQmx.Val_ActiveDrive,
            open_collector=DAQmx.Val_OpenCollector)
        if drive_type is None:
            CALL("ResetDOOutputDriveType", self, channel)
        else:
            drive_type = self._get_map_value(
                "output_drive", output_drive_mapping, drive_type)
            CALL("SetDOOutputDriveType", self, channel, drive_type)

            # NotImplemented: WriteDigitalU8, WriteDigitalU16, WriteDigitalU32, WriteDigitalScalarU32
