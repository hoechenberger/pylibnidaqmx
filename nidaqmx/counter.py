#!/usr/bin/env python

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import ctypes
import numpy as np

from .task import Task
from .utils import CALL
from .loader import DAQmx
from .types import bool32, int32, uInt32, float64


class CounterInputTask(Task):
    """Exposes NI-DAQmx counter input task to Python.
    """

    channel_type = 'CI'

    def __init__(self, name=""):
        super(CounterInputTask, self).__init__(name)
        self.data_type = float

    def create_channel_count_edges (self, counter, name="", edge='rising',
                                    init=0, direction='up'):
        """
        Creates a channel to count the number of rising or falling
        edges of a digital signal and adds the channel to the task you
        specify with taskHandle. You can create only one counter input
        channel at a time with this function because a task can
        include only one counter input channel. To read from multiple
        counters simultaneously, use a separate task for each
        counter. Connect the input signal to the default input
        terminal of the counter unless you select a different input
        terminal.

        Parameters
        ----------

        counter : str

          The name of the counter to use to create virtual channels.

        name : str

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

        edge : {'rising', 'falling'}

          Specifies on which edges of the input signal to increment or
          decrement the count, rising or falling edge(s).

        init : int

          The value from which to start counting.

        direction : {'up', 'down', 'ext'}

          Specifies whether to increment or decrement the
          counter on each edge:

            'up' - Increment the count register on each edge.

            'down' - Decrement the count register on each edge.

            'ext' - The state of a digital line controls the count
            direction. Each counter has a default count direction
            terminal.

        Returns
        -------

          success_status : bool
        """
        counter = str(counter)
        name = str(name)
        edge_map = dict (rising=DAQmx.Val_Rising, falling=DAQmx.Val_Falling)
        direction_map = dict (up=DAQmx.Val_CountUp, down=DAQmx.Val_CountDown,
                              ext=DAQmx.Val_ExtControlled)
        edge_val = self._get_map_value ('edge', edge_map, edge)
        direction_val = self._get_map_value ('direction', direction_map, direction)
        init = uInt32(init)
        return CALL ('CreateCICountEdgesChan', self, counter, name, edge_val, init, direction_val)==0

    def create_channel_linear_encoder(
                self,
                counter,
                name="",
                decodingType='X1',
                ZidxEnable=False,
                ZidxVal=0.0,
                ZidxPhase='AHighBHigh',
                units='Ticks',
                distPerPulse=1.0,
                init=0.0,
                customScaleName=None
                ):
        """
        Creates a channel that uses a linear encoder to measure linear position.
        You can create only one counter input channel at a time with this function
        because a task can include only one counter input channel. To read from
        multiple counters simultaneously, use a separate task for each counter.
        Connect the input signals to the default input terminals of the counter
        unless you select different input terminals.

        Parameters
        ----------

        counter : str

          The name of the counter to use to create virtual channels.

        name : str

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

        decodingType : {'X1', 'X2', 'X4', 'TwoPulseCounting'}

          Specifies how to count and interpret the pulses that the encoder
          generates on signal A and signal B. X1, X2, and X4 are valid for
          quadrature encoders only. TwoPulseCounting is valid only for
          two-pulse encoders.

          X2 and X4 decoding are more sensitive to smaller changes in position
          than X1 encoding, with X4 being the most sensitive. However, more
          sensitive decoding is more likely to produce erroneous measurements
          if there is vibration in the encoder or other noise in the signals.

        ZidxEnable : bool

          Specifies whether to enable z indexing for the measurement.

        ZidxVal : float

          The value, in units, to which to reset the measurement when signal Z
          is high and signal A and signal B are at the states you specify with
          ZidxPhase.

        ZidxPhase : {'AHighBHigh', 'AHighBLow', 'ALowBHigh', 'ALowBLow'}

          The states at which signal A and signal B must be while signal Z is high
          for NI-DAQmx to reset the measurement. If signal Z is never high while
          the signal A and signal B are high, for example, you must choose a phase
          other than DAQmx.Val_AHighBHigh.

          When signal Z goes high and how long it stays high varies from encoder to
          encoder. Refer to the documentation for the encoder to determine the
          timing of signal Z with respect to signal A and signal B.

        units  : {'Meters', 'Inches', 'Ticks', 'FromCustomScale'}

          The units to use to return linear position measurements from the channel.

        distPerPulse : float

          The distance measured for each pulse the encoder generates. Specify this
          value in units.

        init : float

          The position of the encoder when the measurement begins. This value is
          in units.

        customScaleName : str

          The name of a custom scale to apply to the channel. To use this parameter,
          you must set units to DAQmx.Val_FromCustomScale. If you do not set units
          to FromCustomScale, you must set customScaleName to NULL.

        Returns
        -------

          success_status : bool
        """
        counter = str(counter)
        name = str(name)

        decodingType_map = dict(X1=DAQmx.Val_X1, X2=DAQmx.Val_X2, X4=DAQmx.Val_X4,
                                TwoPulseCounting=DAQmx.Val_TwoPulseCounting)
        ZidxPhase_map = dict(AHighBHigh=DAQmx.Val_AHighBHigh, AHighBLow=DAQmx.Val_AHighBLow,
                            ALowBHigh=DAQmx.Val_ALowBHigh, ALowBLow=DAQmx.Val_ALowBLow)
        units_map = dict(Meters=DAQmx.Val_Meters, Inches=DAQmx.Val_Inches,
                        Ticks=DAQmx.Val_Ticks, FromCustomScale=DAQmx.Val_FromCustomScale)

        decodingType_val = self._get_map_value ('decodingType', decodingType_map, decodingType)
        ZidxPhase_val = self._get_map_value ('ZidxPhase', ZidxPhase_map, ZidxPhase)
        units_val = self._get_map_value ('units', units_map, units)

        if units_val != DAQmx.Val_FromCustomScale:
            customScaleName = None

        return CALL(
                'CreateCILinEncoderChan',
                self,
                counter,
                name,
                decodingType_val,
                bool32(ZidxEnable),
                float64(ZidxVal),
                ZidxPhase_val,
                units_val,
                float64(distPerPulse),
                float64(init),
                customScaleName
                )==0

    def create_channel_freq(self, counter, name="", min_val=1e2, max_val=1e3,
                            units="hertz", edge="rising", meas_method="low_freq1",
                            meas_time=1.0, divisor=1, custom_scale_name=None):
        """
        Creates a channel to measure the frequency of a digital signal
        and adds the channel to the task. You can create only one
        counter input channel at a time with this function because a
        task can include only one counter input channel. To read from
        multiple counters simultaneously, use a separate task for each
        counter. Connect the input signal to the default input
        terminal of the counter unless you select a different input
        terminal.

        Parameters
        ----------

        counter : str
          The name of the counter to use to create virtual channels.

        name : str
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

        min_val : float
          The minimum value, in units, that you expect to measure.

        max_val : float
          The maximum value, in units, that you expect to measure.

        units : {'hertz', 'ticks', 'custom'}
          Units to use to return the measurement and to specify the
          min/max expected value.

          'hertz' - Hertz, cycles per second
          'ticks' - timebase ticks
          'custom' - use custom_scale_name to specify units

        edge : {'rising', 'falling'}
          Specifies which edges to measure the frequency or period of the signal.

        meas_method : {'low_freq', 'high_freq', 'large_range'}
          The method used to calculate the period or frequency of the
          signal.  See the M series DAQ User Manual (371022K-01), page
          7-9 for more information.

            'low_freq'
              Use one counter that uses a constant timebase to measure
              the input signal.

            'high_freq'
              Use two counters, one of which counts pulses of the
              signal to measure during the specified measurement time.

            'large_range'
              Use one counter to divide the frequency of the input
              signal to create a lower frequency signal that the
              second counter can more easily measure.

        meas_time : float
          The length of time to measure the frequency or period of the
          signal, when meas_method is 'high_freq'.  Measurement accuracy
          increases with increased meas_time and with increased signal
          frequency.  Ensure that the meas_time is low enough to prevent
          the counter register from overflowing.

        divisor : int
          The value by which to divide the input signal, when
          meas_method is 'large_range'. The larger this value, the more
          accurate the measurement, but too large a value can cause the
          count register to roll over, resulting in an incorrect
          measurement.

        custom_scale_name : str
          The name of a custom scale to apply to the channel. To use
          this parameter, you must set units to 'custom'.  If you do
          not set units to 'custom', you must set custom_scale_name to
          None.

        Returns
        -------

          success_status : bool
        """

        self.data_type = float

        counter = str(counter)
        name = str(name)
        assert min_val <= max_val
        min_val = float64(min_val)
        max_val = float64(max_val)
        units_map = dict(hertz=DAQmx.Val_Hz,
                         ticks=DAQmx.Val_Ticks,
                         custom=DAQmx.Val_FromCustomScale)
        units_val = self._get_map_value('units', units_map, units)
        edge_map = dict(rising=DAQmx.Val_Rising, falling=DAQmx.Val_Falling)
        edge_val = self._get_map_value('edge', edge_map, edge)
        meas_meth_map = dict(low_freq=DAQmx.Val_LowFreq1Ctr,
                             high_freq=DAQmx.Val_HighFreq2Ctr,
                             large_range=DAQmx.Val_LargeRng2Ctr)
        meas_meth_val = self._get_map_value('meas_method', meas_meth_map,
                                            meas_method)
        meas_time = float64(meas_time)
        divisor = uInt32(divisor)
        assert divisor > 0
        if (units_val == DAQmx.Val_FromCustomScale
            and custom_scale_name is None):
            raise ValueError('Must specify custom_scale_name for custom scale.')
        if custom_scale_name is not None:
            custom_scale_name = str(custom_scale_name)

        return CALL('CreateCIFreqChan', self, counter, name,
                    min_val, max_val,
                    units_val, edge_val, meas_meth_val,
                    meas_time, divisor, custom_scale_name) == 0

    def set_terminal_count_edges(self, channel, terminal):
        """
        Specifies the input terminal of the signal to measure.

        Returns
        -------

          success_status : bool
        """
        return CALL('SetCICountEdgesTerm', self, channel, terminal)==0

    def get_duplicate_count_prevention(self, channel):
        """ Returns duplicate count prevention state.

        See also
        --------

        set_duplicate_count_prevention, reset_duplicate_count_prevention
        """
        b = bool32(0)
        r = CALL('GetCIDupCountPrevent', self, channel, ctypes.byref(b))
        assert r==0,repr((r, channel, b))
        return b != 0

    def set_duplicate_count_prevention(self, channel, enable=True):
        """
        Specifies whether to enable duplicate count prevention for the
        channel.

        Returns
        -------

          success_status : bool

        See also
        --------

        get_duplicate_count_prevention, reset_duplicate_count_prevention
        """
        b = bool32(enable)
        return CALL('SetCIDupCountPrevent', self, channel, b)==0

    def reset_duplicate_count_prevention(self, channel):
        """ Reset duplicate count prevention.

        Returns
        -------

          success_status : bool

        See also
        --------

        set_duplicate_count_prevention, get_duplicate_count_prevention
        """
        return CALL('ResetCIDupCountPrevent', self, channel)==0

    def get_timebase_rate(self, channel):
        """ Returns the frequency of the counter timebase.

        See also
        --------
        set_timebase_rate, reset_timebase_rate
        """
        data = float64(0)
        r = CALL('GetCICtrTimebaseRate', self, channel, ctypes.byref(data))
        assert r==0,repr((r, channel, data))
        return data.value

    def set_timebase_rate(self, channel, rate):
        """
        Specifies in Hertz the frequency of the counter
        timebase. Specifying the rate of a counter timebase allows you
        to take measurements in terms of time or frequency rather than
        in ticks of the timebase. If you use an external timebase and
        do not specify the rate, you can take measurements only in
        terms of ticks of the timebase.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_timebase_rate, reset_timebase_rate
        """
        data = float64(rate)
        return CALL('SetCICtrTimebaseRate', self, channel, data)==0

    def reset_timebase_rate(self, channel):
        """
        Resets the frequency of the counter timebase.

        Returns
        -------

          success_status : bool

        See also
        --------
        set_timebase_rate, get_timebase_rate
        """
        return CALL('ResetCICtrTimebaseRate', self, channel)==0


    def read(self, samples_per_channel=None, timeout=10.0):
        """
        Reads multiple 32-bit integer samples from a counter task.
        Use this function when counter samples are returned unscaled,
        such as for edge counting.

        Parameters
        ----------

        samples_per_channel : int
          The number of samples, per channel, to read. The default
          value of -1 (DAQmx.Val_Auto) reads all available samples. If
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
          (DAQmx.Val_WaitInfinitely). This function returns an error
          if the timeout elapses.

          A value of 0 indicates to try once to read the requested
          samples. If all the requested samples are read, the function
          is successful. Otherwise, the function returns a timeout
          error and returns the samples that were actually read.

        Returns
        -------

        data :
          The array to read samples into, organized according to `fill_mode`.
        """

        if samples_per_channel is None:
            samples_per_channel = self.get_samples_per_channel_available()

        data = np.zeros((samples_per_channel,),dtype=np.int32) # pylint: disable=no-member
        samples_read = int32(0)


        CALL('ReadCounterU32', self, samples_per_channel, float64(timeout),
             data.ctypes.data, data.size, ctypes.byref(samples_read), None)

        return data[:samples_read.value]

    def read_scalar(self, timeout=10.0):
        """
        Reads a single floating-point sample from a counter task. Use
        this function when the counter sample is scaled to a
        floating-point value, such as for frequency and period
        measurement.

        timeout : float
          The amount of time, in seconds, to wait for the function to
          read the sample(s). The default value is 10.0 seconds. To
          specify an infinite wait, pass -1
          (DAQmx.Val_WaitInfinitely). This function returns an error if
          the timeout elapses.

          A value of 0 indicates to try once to read the requested
          samples. If all the requested samples are read, the function
          is successful. Otherwise, the function returns a timeout error
          and returns the samples that were actually read.

        Returns
        -------

        data :
          The sample read from the task.
        """

        timeout = float64(timeout)
        data = float64(0)
        CALL("ReadCounterScalarF64", self,
             timeout, ctypes.byref(data), None)
        #assert ret == 0
        return data.value

class CounterOutputTask(Task):

    """Exposes NI-DAQmx counter output task to Python.
    """

    channel_type = 'CO'

    def create_channel_frequency(self, counter, name="", units='hertz', idle_state='low',
                                 delay=0.0, freq=1.0, duty_cycle=0.5):
        """
        Creates channel(s) to generate digital pulses that freq and
        duty_cycle define and adds the channel to the task.  The
        pulses appear on the default output terminal of the counter
        unless you select a different output terminal.

        Parameters
        ----------

        counter : str

          The name of the counter to use to create virtual
          channels. You can specify a list or range of physical
          channels.

        name : str

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

        units : {'hertz'}

          The units in which to specify freq:

            'hertz' - hertz

        idle_state : {'low', 'high'}

          The resting state of the output terminal.

        delay : float

          The amount of time in seconds to wait before generating the
          first pulse.

        freq : float

          The frequency at which to generate pulses.

        duty_cycle : float

          The width of the pulse divided by the pulse period. NI-DAQmx
          uses this ratio, combined with frequency, to determine pulse
          width and the interval between pulses.

        Returns
        -------

          success_status : bool
        """
        counter = str(counter)
        name = str(name)
        units_map = dict (hertz = DAQmx.Val_Hz)
        idle_state_map = dict (low=DAQmx.Val_Low, high=DAQmx.Val_High)
        units_val = self._get_map_value('units', units_map, units)
        idle_state_val = self._get_map_value('idle_state', idle_state_map, idle_state)
        return CALL('CreateCOPulseChanFreq', self, counter, name, units_val, idle_state_val,
                    float64(delay), float64(freq), float64(duty_cycle))==0

    def create_channel_ticks(self, counter, name="", source="", idle_state='low',
                             delay = 0, low_ticks=1, high_ticks=1):
        """
        Creates channel(s) to generate digital pulses defined by the
        number of timebase ticks that the pulse is at a high state and
        the number of timebase ticks that the pulse is at a low state
        and also adds the channel to the task. The pulses appear on
        the default output terminal of the counter unless you select a
        different output terminal.

        Parameters
        ----------

        counter : str

          The name of the counter to use to create virtual
          channels. You can specify a list or range of physical
          channels.

        name : str

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

        source : str

          The terminal to which you connect an external timebase. You
          also can specify a source terminal by using a terminal name.

        idle_state : {'low', 'high'}

          The resting state of the output terminal.

        delay : int

          The number of timebase ticks to wait before generating the
          first pulse.

        low_ticks : int

          The number of timebase ticks that the pulse is low.

        high_ticks : int

          The number of timebase ticks that the pulse is high.

        Returns
        -------

          success_status : bool
        """
        counter = str(counter)
        name = str(name)
        idle_state_map = dict (low=DAQmx.Val_Low, high=DAQmx.Val_High)
        idle_state_val = self._get_map_value('idle_state', idle_state_map, idle_state)
        return CALL('CreateCOPulseChanTicks', self, counter, name, source, idle_state_val,
                    int32 (delay), int32 (low_ticks), int32 (high_ticks))==0

    def create_channel_time(self, counter, name="", units="seconds", idle_state='low',
                             delay = 0, low_time=1, high_time=1):
        """
        Creates channel(s) to generate digital pulses defined by the
        number of timebase ticks that the pulse is at a high state and
        the number of timebase ticks that the pulse is at a low state
        and also adds the channel to the task. The pulses appear on
        the default output terminal of the counter unless you select a
        different output terminal.

        Parameters
        ----------

        counter : str

          The name of the counter to use to create virtual
          channels. You can specify a list or range of physical
          channels.

        name : str

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

        units : {'seconds'}

          The units in which to specify high and low time.

        idle_state : {'low', 'high'}

          The resting state of the output terminal.

        delay : float

          The amount of time in seconds to wait before generating the
          first pulse.

        low_time : float

          The amount of time the pulse is low, in seconds.

        high_time : float

          The amount of time the pulse is high, in seconds.

        Returns
        -------

          success_status : bool
        """
        counter = str(counter)
        name = str(name)
        units_map = dict (seconds = DAQmx.Val_Seconds)
        idle_state_map = dict (low=DAQmx.Val_Low, high=DAQmx.Val_High)
        units_val = self._get_map_value('units', units_map, units)
        idle_state_val = self._get_map_value('idle_state', idle_state_map, idle_state)
        return CALL('CreateCOPulseChanTime', self, counter, name, units_val, idle_state_val,
                    float64 (delay), float64(low_time), float64(high_time))==0

    def set_terminal_pulse (self, channel, terminal):
        """
        Specifies on which terminal to generate pulses.

        Returns
        -------

          success_status : bool
        """
        channel = str(channel)
        terminal = str(terminal)
        return CALL ('SetCOPulseTerm', self, channel, terminal)==0

    def write_ticks(self, high_ticks, low_ticks,
                    auto_start = False, timeout = 10.0,
                    layout = 'group_by_scan_number'):
        """
        Writes new pulse high tick counts and low tick counts to each
        channel in a continuous counter output task that contains one or
        more channels.

        Parameters
        ----------

        high_ticks : array

          The number of timebase ticks the pulse is high

        low_ticks : array

          The number of timebase ticks the pulse is low

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
        layout_map = dict(group_by_channel = DAQmx.Val_GroupByChannel,
                          group_by_scan_number = DAQmx.Val_GroupByScanNumber)
        layout_val = self._get_map_value('layout', layout_map, layout)
        samples_written = int32(0)

        assert len(high_ticks) == len(low_ticks)

        low_ticks = np.asarray(low_ticks, dtype = uInt32)
        low_ticks, samples_per_channel = self._reshape_data(low_ticks, layout)
        high_ticks = np.asarray(high_ticks, dtype = uInt32)
        high_ticks, samples_per_channel = self._reshape_data(high_ticks, layout)

        CALL('WriteCtrTicks', self, samples_per_channel,
                bool32(auto_start), float64(timeout), layout_val,
                high_ticks.ctypes.data, low_ticks.ctypes.data,
                ctypes.byref(samples_written), None)

        return samples_written.value