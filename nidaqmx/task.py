#!/usr/bin/env python

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import ctypes
import warnings
from inspect import getargspec

from .types import int32, bool32, uInt32, uInt64, float64, TaskHandle
from .constants import default_buf_size
from .utils import CALL, make_pattern
from .system import System
from .loader import libnidaqmx, DAQmx, error_map


class Task(TaskHandle):
    """
    Base class to NI-DAQmx task classes.

    Attributes
    ----------
    system
    channel_type : str
      Holds channel type.

    """

    #: Exposes NI-DACmx system properties, see `System`.
    _system = System()
    @property
    def system(self):
        """
        NI-DACmx system properties holder.

        See also
        --------
        nidaqmx.libnidaqmx.System
        """
        return self._system

    # pylint: disable=pointless-string-statement
    channel_type = None
    """
    Holds channel type.

    Returns
    -------
    channel_type : {'AI', 'AO', 'DI', 'DO', 'CI', 'CO'}

    See also
    --------
    channel_io_type
    """

    def __init__(self, name = ""):
        """
        Creates a task.

        If you create a task within a loop, NI-DAQmx creates a new
        task in each iteration of the loop. Use ``del task`` within the
        loop after you finish with the task to avoid allocating
        unnecessary memory.
        """
        name = str(name)
        super(Task, self).__init__(0)
        CALL('CreateTask', name, ctypes.byref(self))
        buf_size = max(len(name)+1, default_buf_size)
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL('GetTaskName', self, ctypes.byref(buf), buf_size)
        self.name = buf.value
        self.sample_mode = None
        self.samples_per_channel = None

    def _set_channel_type(self, t):
        """ Sets channel type for the task.
        """
        assert t in ['AI', 'AO', 'DI', 'DO', 'CI', 'CO'], repr(t)
        if self.channel_type is None:
            self.channel_type = t
        elif self.channel_type != t:
            raise ValueError('Expected channel type %r but got %r' % (self.channel_type, t))

    @property
    def channel_io_type (self):
        """ Return channel IO type: 'input' or 'output'.

        See also
        --------
        channel_type
        """
        t = self.channel_type
        if t is None:
            raise TypeError('%s: cannot determine channel I/O type when no channels have been created.' % (self.__class__.__name__))
        return 'input' if t[1]=='I' else 'output'

    # FIXME: why do we need this argument?
    def clear(self, libnidaqmx=libnidaqmx):
        """
        Clears the task.

        Before clearing, this function stops the task, if necessary,
        and releases any resources reserved by the task. You cannot
        use a task once you clear the task without recreating or
        reloading the task.

        If you use the DAQmxCreateTask function or any of the NI-DAQmx
        Create Channel functions within a loop, use this function
        within the loop after you finish with the task to avoid
        allocating unnecessary memory.
        """
        if self.value:
            r = libnidaqmx.DAQmxClearTask(self)
            if r:
                warnings.warn("DAQmxClearTask failed with error code %s (%r)" % (r, error_map.get(r)))

    __del__ = clear


    def __repr__(self):
        """ Returns string representation of a task instance.
        """
        return '%s(%r)' % (self.__class__.__name__, self.name)

    def is_done(self):
        """
        Queries the status of the task and indicates if it completed
        execution. Use this function to ensure that the specified
        operation is complete before you stop the task.
        """
        b = bool32(0)
        CALL('IsTaskDone', self, ctypes.byref(b))
        return b.value != 0

    # NotImplemented: DAQmxGetTaskComplete

    def start(self):
        """
        Transitions the task from the committed state to the running
        state, which begins measurement or generation. Using this
        function is required for some applications and optional for
        others.

        If you do not use this function, a measurement task starts
        automatically when a read operation begins. The autoStart
        parameter of the NI-DAQmx Write functions determines if a
        generation task starts automatically when you use an NI-DAQmx
        Write function.

        If you do not call StartTask and StopTask when you
        call NI-DAQmx Read functions or NI-DAQmx Write functions
        multiple times, such as in a loop, the task starts and stops
        repeatedly. Starting and stopping a task repeatedly reduces
        the performance of the application.

        Returns
        -------

          success_status : bool
        """
        return CALL('StartTask', self) == 0

    def stop(self):
        """
        Stops the task and returns it to the state it was in before
        you called StartTask or called an NI-DAQmx Write function with
        autoStart set to TRUE.

        If you do not call StartTask and StopTask when you call
        NI-DAQmx Read functions or NI-DAQmx Write functions multiple
        times, such as in a loop, the task starts and stops
        repeatedly. Starting and stopping a task repeatedly reduces
        the performance of the application.

        Returns
        -------

          success_status : bool
        """
        return CALL('StopTask', self) == 0

    @classmethod
    def _get_map_value(cls, label, map_, key):
        """
        Helper method.
        """
        val = map_.get(key)
        if val is None:
            raise ValueError('Expected %s %s but got %r'
                             % (label, '|'.join(map_.viewkeys()), key))
        return val

    def _reshape_data(self, data, layout):
        number_of_channels = self.get_number_of_channels()

        if number_of_channels == 0:
            raise ValueError('Can\'t write any data without any channels')

        if len(data.shape) == 1:
            if number_of_channels == 1:
                samples_per_channel = data.shape[0]
                if layout == 'group_by_scan_number':
                    data = data.reshape((samples_per_channel, 1))
                else:
                    data = data.reshape((1, samples_per_channel))
            else:
                samples_per_channel = data.size // number_of_channels
                if layout == 'group_by_scan_number':
                    data = data.reshape((samples_per_channel, number_of_channels))
                else:
                    data = data.reshape((number_of_channels, samples_per_channel))
        else:
            assert len(data.shape) == 2, repr(data.shape)
            if layout == 'group_by_scan_number':
                assert data.shape[-1] == number_of_channels, repr((data.shape, number_of_channels))
                samples_per_channel = data.shape[0]
            else:
                assert data.shape[0] == number_of_channels, repr((data.shape, number_of_channels))
                samples_per_channel = data.shape[-1]

        return data, samples_per_channel

    def get_number_of_channels(self):
        """
        Indicates the number of virtual channels in the task.
        """
        d = uInt32(0)
        CALL('GetTaskNumChans', self, ctypes.byref(d))
        return d.value

    def get_names_of_channels (self, buf_size=None):
        """
        Indicates the names of all virtual channels in the task.

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
        CALL('GetTaskChannels', self, ctypes.byref(buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        n = self.get_number_of_channels()
        assert len(names)==n,repr((names, n))
        return names

    def get_devices (self, buf_size=None):
        """
        Indicates an array containing the names of all devices in the
        task.

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
        CALL('GetTaskDevices', self, ctypes.byref(buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        return names

    def alter_state(self, state):
        """
        Alters the state of a task according to the action you
        specify. To minimize the time required to start a task, for
        example, DAQmxTaskControl can commit the task prior to
        starting.

        Parameters
        ----------

        state : {'start', 'stop', 'verify', 'commit', 'reserve', 'unreserve', 'abort'}

          'start' - Starts execution of the task.

          'stop' - Stops execution of the task.

          'verify' - Verifies that all task parameters are valid for the
          hardware.

          'commit' - Programs the hardware as much as possible according
          to the task configuration.

          'reserve' - Reserves the hardware resources needed for the
          task. No other tasks can reserve these same resources.

          'unreserve' - Releases all previously reserved resources.

          'abort' - Abort is used to stop an operation, such as Read or
          Write, that is currently active. Abort puts the task into an
          unstable but recoverable state. To recover the task, call
          Start to restart the task or call Stop to reset the task
          without starting it.

        Returns
        -------

          success_status : bool
        """
        state_map = dict(start = DAQmx.Val_Task_Start,
                         stop = DAQmx.Val_Task_Stop,
                         verify = DAQmx.Val_Task_Verify,
                         commit = DAQmx.Val_Task_Commit,
                         reserve = DAQmx.Val_Task_Reserve,
                         unreserve = DAQmx.Val_Task_Unreserve,
                         abort = DAQmx.Val_Task_Abort)
        state_val = self._get_map_value ('state', state_map, state)
        return CALL('TaskControl', self, state_val) == 0

    # Not implemented: DAQmxAddGlobalChansToTask, DAQmxLoadTask
    # DAQmxGetNthTaskChannel

    # Not implemented:
    # DAQmxCreateAIAccelChan, DAQmxCreateAICurrentChan, DAQmxCreateAIFreqVoltageChan,
    # DAQmxCreateAIMicrophoneChan, DAQmxCreateAIResistanceChan, DAQmxCreateAIRTDChan,
    # DAQmxCreateAIStrainGageChan, DAQmxCreateAITempBuiltInSensorChan,
    # DAQmxCreateAIThrmcplChan, DAQmxCreateAIThrmstrChanIex, DAQmxCreateAIThrmstrChanVex,
    # DAQmxCreateAIVoltageChanWithExcit
    # DAQmxCreateAIPosLVDTChan, DAQmxCreateAIPosRVDTChan

    # DAQmxCreateTEDSAI*

    # Not implemented: DAQmxCreateAOCurrentChan
    # DAQmxCreateDIChan, DAQmxCreateDOChan
    # DAQmxCreateCI*, DAQmxCreateCO*

    def configure_timing_change_detection(self,
                                          rising_edge_channel = '',
                                          falling_edge_channel = '',
                                          sample_mode = 'continuous',
                                          samples_per_channel = 1000):
        """
        Configures the task to acquire samples on the rising and/or
        falling edges of the lines or ports you specify.

        Returns
        -------

          success_status : bool
        """
        sample_mode_map = dict (finite = DAQmx.Val_FiniteSamps,
                                continuous = DAQmx.Val_ContSamps,
                                hwtimed = DAQmx.Val_HWTimedSinglePoint)
        sample_mode_val = self._get_map_value('sample_mode', sample_mode_map, sample_mode)
        self.samples_per_channel = samples_per_channel
        self.sample_mode = sample_mode
        r = CALL('CfgChangeDetectionTiming', self, rising_edge_channel, falling_edge_channel,
                 sample_mode_val, uInt64(samples_per_channel))
        return r==0


    def configure_timing_handshaking(self,
                                     sample_mode = 'continuous',
                                     samples_per_channel = 1000):
        """
        Determines the number of digital samples to acquire or
        generate using digital handshaking between the device and a
        peripheral device.

        Returns
        -------

          success_status : bool
        """
        sample_mode_map = dict (finite = DAQmx.Val_FiniteSamps,
                                continuous = DAQmx.Val_ContSamps,
                                hwtimed = DAQmx.Val_HWTimedSinglePoint)
        sample_mode_val = self._get_map_value('sample_mode', sample_mode_map, sample_mode)
        self.samples_per_channel = samples_per_channel
        self.sample_mode = sample_mode
        r = CALL('CfgHandshakingTiming', self, sample_mode_val, uInt64(samples_per_channel))
        return r==0

    def configure_timing_implicit(self,
                                  sample_mode = 'continuous',
                                  samples_per_channel = 1000):
        """
        Sets only the number of samples to acquire or generate without
        specifying timing. Typically, you should use this function
        when the task does not require sample timing, such as tasks
        that use counters for buffered frequency measurement, buffered
        period measurement, or pulse train generation.

        Returns
        -------

          success_status : bool
        """
        sample_mode_map = dict (finite = DAQmx.Val_FiniteSamps,
                                continuous = DAQmx.Val_ContSamps,
                                hwtimed = DAQmx.Val_HWTimedSinglePoint)
        sample_mode_val = self._get_map_value('sample_mode', sample_mode_map, sample_mode)
        self.samples_per_channel = samples_per_channel
        self.sample_mode = sample_mode
        r = CALL('CfgImplicitTiming', self, sample_mode_val, uInt64(samples_per_channel))
        return r==0

    def configure_timing_sample_clock(self,
                                      source = 'OnboardClock',
                                      rate = 1, # Hz
                                      active_edge = 'rising',
                                      sample_mode = 'continuous',
                                      samples_per_channel = 1000):
        """
        Sets the source of the Sample Clock, the rate of the Sample
        Clock, and the number of samples to acquire or generate.

        Parameters
        ----------

          source : str

            The source terminal of the Sample Clock. To use the
            internal clock of the device, use None or use
            'OnboardClock'.

          rate : float

            The sampling rate in samples per second. If you use an
            external source for the Sample Clock, set this value to
            the maximum expected rate of that clock.

          active_edge : {'rising', 'falling'}

            Specifies on which edge of the clock to
            acquire or generate samples:

              'rising' - Acquire or generate samples on the rising edges
              of the Sample Clock.

              'falling' - Acquire or generate samples on the falling
              edges of the Sample Clock.

          sample_mode : {'finite', 'continuous', 'hwtimed'}

            Specifies whether the task acquires or
            generates samples continuously or if it acquires or
            generates a finite number of samples:

              'finite' - Acquire or generate a finite number of samples.

              'continuous' - Acquire or generate samples until you stop the task.

              'hwtimed' - Acquire or generate samples continuously
              using hardware timing without a buffer. Hardware timed
              single point sample mode is supported only for the
              sample clock and change detection timing types.

          samples_per_channel : int

            The number of samples to acquire or generate for each
            channel in the task if `sample_mode` is 'finite'.  If
            sample_mode is 'continuous', NI-DAQmx uses this value to
            determine the buffer size.

        Returns
        -------

          success_status : bool
        """
        source = str(source)
        active_edge_map = dict (rising = DAQmx.Val_Rising,
                                falling = DAQmx.Val_Falling)
        sample_mode_map = dict (finite = DAQmx.Val_FiniteSamps,
                                continuous = DAQmx.Val_ContSamps,
                                hwtimed = DAQmx.Val_HWTimedSinglePoint)
        active_edge_val = self._get_map_value('active_edge', active_edge_map, active_edge)
        sample_mode_val = self._get_map_value('sample_mode', sample_mode_map, sample_mode)
        self.samples_per_channel = samples_per_channel
        self.sample_mode = sample_mode
        r = CALL('CfgSampClkTiming', self, source, float64(rate), active_edge_val, sample_mode_val,
                    uInt64(samples_per_channel))
        return r==0

    def configure_trigger_analog_edge_start(self, source, slope='rising',level=1.0):
        """
        Configures the task to start acquiring or generating samples
        when an analog signal crosses the level you specify.

        Parameters
        ----------

        source : str

          The name of a channel or terminal where there is an analog
          signal to use as the source of the trigger. For E Series
          devices, if you use a channel name, the channel must be the
          first channel in the task. The only terminal you can use for
          E Series devices is PFI0.

        slope : {'rising', 'falling'}

          Specifies on which slope of the signal to start acquiring or
          generating samples when the signal crosses trigger level:

            'rising' - Trigger on the rising slope of the signal.

            'falling' - Trigger on the falling slope of the signal.

        level : float

          The threshold at which to start acquiring or generating
          samples. Specify this value in the units of the measurement
          or generation. Use trigger slope to specify on which slope
          to trigger at this threshold.

        Returns
        -------

          success_status : bool
        """
        slope_map = dict (rising=DAQmx.Val_RisingSlope,
                          falling=DAQmx.Val_FallingSlope)
        slope_val = self._get_map_value('slope', slope_map, slope)
        return CALL ('CfgAnlgEdgeStartTrig', self, source, slope_val, float64(level))==0

    def configure_trigger_analog_window_start(self, source, when='entering',top=1.0,bottom=-1.0):
        """
        Configures the task to start acquiring or generating samples
        when an analog signal enters or leaves a range you specify.

        Parameters
        ----------

        source : str

          The name of a virtual channel or terminal where there
          is an analog signal to use as the source of the trigger.

          For E Series devices, if you use a virtual channel, it must
          be the first channel in the task. The only terminal you can
          use for E Series devices is PFI0.

        when : {'entering', 'leaving'}

          Specifies whether the task starts measuring or generating
          samples when the signal enters the window or when it leaves
          the window. Use `bottom` and `top` to specify the limits of
          the window.

        top : float

          The upper limit of the window. Specify this value in the
          units of the measurement or generation.

        bottom : float

          The lower limit of the window. Specify this value in the
          units of the measurement or generation.

        Returns
        -------

          success_status : bool
        """
        source = str(source)
        when_map = dict (entering=DAQmx.Val_EnteringWin,
                         leaving=DAQmx.Val_LeavingWin)
        when_val = self._get_map_value('when', when_map, when)
        return CALL ('CfgAnlgWindowStartTrig', self, source, when_val, float64(top), float64(bottom))==0

    def configure_trigger_digital_edge_start(self, source, edge='rising'):
        """
        Configures the task to start acquiring or generating samples
        on a rising or falling edge of a digital signal.

        Parameters
        ----------

        source : str

          The name of a terminal where there is a digital signal to
          use as the source of the trigger.

        edge : {'rising', 'falling'}

          Specifies on which edge of a digital signal to start
          acquiring or generating samples: rising or falling edge(s).

        Returns
        -------

          success_status : bool
        """
        source = str(source)
        edge_map = dict (rising=DAQmx.Val_Rising,
                         falling=DAQmx.Val_Falling)
        edge_val = self._get_map_value ('edge', edge_map, edge)
        return CALL('CfgDigEdgeStartTrig', self, source, edge_val) == 0

    def configure_trigger_digital_pattern_start(self, source, pattern, when='matches'):
        """
        Configures a task to start acquiring or generating samples
        when a digital pattern is matched.

        Parameters
        ----------

        source : str

          Specifies the physical channels to use for pattern
          matching. The order of the physical channels determines the
          order of the pattern. If a port is included, the order of
          the physical channels within the port is in ascending order.

        pattern : str

          Specifies the digital pattern that must be met for the
          trigger to occur.

        when : {'matches', 'does_not_match'}

          Specifies the conditions under which the trigger
          occurs: pattern matches or not.

        Returns
        -------

          success_status : bool
        """
        source = str(source)
        pattern = str(pattern)
        when_map = dict(matches = DAQmx.Val_PatternMatches,
                        does_not_match = DAQmx.Val_PatternDoesNotMatch)
        when_val = self._get_map_value('when', when_map, when)
        return CALL('CfgDigPatternStartTrig', self, source, pattern, when_val) == 0

    def configure_trigger_disable_start(self):
        """
        Configures the task to start acquiring or generating samples
        immediately upon starting the task.

        Returns
        -------

          success_status : bool
        """
        return CALL ('DisableStartTrig', self) == 0

    def configure_analog_edge_reference_trigger(self, source, slope='rising',level=1.0, pre_trigger_samps=0):
        """
        Configures the task to stop the acquisition when the device
        acquires all pretrigger samples, an analog signal reaches the
        level you specify, and the device acquires all post-trigger samples.


        source : str

          The name of a channel or terminal where there is an analog
          signal to use as the source of the trigger. For E Series
          devices, if you use a channel name, the channel must be the
          first channel in the task. The only terminal you can use for
          E Series devices is PFI0.

        slope : {'rising', 'falling'}

          Specifies on which slope of the signal to start acquiring or
          generating samples when the signal crosses trigger level:

            'rising' - Trigger on the rising slope of the signal.

            'falling' - Trigger on the falling slope of the signal.

        level : float

          The threshold at which to start acquiring or generating
          samples. Specify this value in the units of the measurement
          or generation. Use trigger slope to specify on which slope
          to trigger at this threshold.

        pre_trigger_samps : uint32

          The minimum number of samples per channel to acquire before
          recognizing the Reference Trigger. The number of posttrigger
          samples per channel is equal to number of samples per channel
          in the NI-DAQmx Timing functions minus pretriggerSamples.


        Returns
        -------

          success_status : bool
        """
        source = str(source)

        slope_map = dict (rising=DAQmx.Val_RisingSlope,
                          falling=DAQmx.Val_FallingSlope)
        slope_val = self._get_map_value('slope', slope_map, slope)
        return CALL ('CfgAnlgEdgeRefTrig', self, source, slope_val, float64(level), uInt32(pre_trigger_samps))==0


    def configure_analog_window_reference_trigger(self, source, when='entering',top=1.0, bottom=1.0, pre_trigger_samps=0):
        """
        Configures the task to stop the acquisition when the device
        acquires all pretrigger samples, an analog signal enters or
        leaves a range you specify, and the device acquires all
        post-trigger samples.


        source : str

          The name of a channel or terminal where there is an analog
          signal to use as the source of the trigger. For E Series
          devices, if you use a channel name, the channel must be the
          first channel in the task. The only terminal you can use for
          E Series devices is PFI0.

        when : {'entering', 'leaving'}

          Specifies whether the Reference Trigger occurs when the signal
          enters the window or when it leaves the window. Use
          bottom and top to specify the limits of the window.

            'entering' - Trigger when the signal enters the window.

            'leaving' - Trigger when the signal leaves the window.

        top : float

          The upper limit of the window. Specify this value in the
          units of the measurement or generation.

        bottom : float

          The lower limit of the window. Specify this value in the
          units of the measurement or generation.

        pre_trigger_samps : uint32

          The minimum number of samples per channel to acquire before
          recognizing the Reference Trigger. The number of posttrigger
          samples per channel is equal to number of samples per channel
          in the NI-DAQmx Timing functions minus pretriggerSamples.


        Returns
        -------

          success_status : bool
        """
        source = str(source)
        when_map = dict (entering=DAQmx.Val_EnteringWin,
                          leaving=DAQmx.Val_LeavingWin)
        when_val = self._get_map_value('when', when_map, when)
        return CALL ('CfgAnlgWindowRefTrig', self, source, when_val, float64(top), float64(bottom), uInt32(pre_trigger_samps))==0


    def configure_digital_edge_reference_trigger(self, source, slope='rising', pre_trigger_samps=0):
        """
        Configures the task to stop the acquisition when the device
        acquires all pretrigger samples, detects a rising or falling
        edge of a digital signal, and acquires all posttrigger samples.


        source : str

          The name of a channel or terminal where there is an analog
          signal to use as the source of the trigger. For E Series
          devices, if you use a channel name, the channel must be the
          first channel in the task. The only terminal you can use for
          E Series devices is PFI0.

        slope : {'rising', 'falling'}

          Specifies on which slope of the signal to start acquiring or
          generating samples when the signal crosses trigger level:

            'rising' - Trigger on the rising slope of the signal.

            'falling' - Trigger on the falling slope of the signal.

        pre_trigger_samps : uint32

          The minimum number of samples per channel to acquire before
          recognizing the Reference Trigger. The number of posttrigger
          samples per channel is equal to number of samples per channel
          in the NI-DAQmx Timing functions minus pretriggerSamples.


        Returns
        -------

          success_status : bool
        """
        source = str(source)
        if not source.startswith('/'): # source needs to start with a '/'
            source = '/'+source
        slope_map = dict (rising=DAQmx.Val_RisingSlope,
                          falling=DAQmx.Val_FallingSlope)
        slope_val = self._get_map_value('slope', slope_map, slope)
        return CALL ('CfgDigEdgeRefTrig', self, source, slope_val, uInt32(pre_trigger_samps))==0


    def configure_digital_pattern_reference_trigger(self, source, pattern, when='match', pre_trigger_samps=0):
        """
        Configures the task to stop the acquisition when the device
        acquires all pretrigger samples, matches or does not match
        a digital pattern, and acquires all posttrigger samples.


        source : str

          The name of a channel or terminal where there is an analog
          signal to use as the source of the trigger. For E Series
          devices, if you use a channel name, the channel must be the
          first channel in the task. The only terminal you can use for
          E Series devices is PFI0.

        pattern : str

          Specifies the digital pattern that must be met for the trigger to occur.

        when : {'entering', 'leaving'}

          Specifies the conditions under which the trigger occurs

            'match' - Trigger when the signal matches the pattern

            'nomatch' - Trigger when the signal does NOT match the pattern

        pre_trigger_samps : uint32

          The minimum number of samples per channel to acquire before
          recognizing the Reference Trigger. The number of posttrigger
          samples per channel is equal to number of samples per channel
          in the NI-DAQmx Timing functions minus pretriggerSamples.


        Returns
        -------

          success_status : bool
        """
        source = str(source)
        if not source.startswith('/'): # source needs to start with a '/'
            source = '/'+source
        when_map = dict (match=DAQmx.Val_PatternMatches,
                          nomatch=DAQmx.Val_PatternDoesNotMatch)
        when_val = self._get_map_value('when', when_map, when)
        return CALL ('CfgDigPatternRefTrig', self, source, pattern, when_val, uInt32(pre_trigger_samps))==0


    def disable_reference_trigger(self):
        """
        Disables reference triggering for the measurement or generation.

        Returns
        -------

          success_status : bool
        """
        return CALL ('DisableRefTrig', self) == 0


    def set_buffer (self, samples_per_channel):
        """
        Overrides the automatic I/O buffer allocation that NI-DAQmx performs.

        Parameters
        ----------

        samples_per_channel : int

          The number of samples the buffer can hold for each channel
          in the task. Zero indicates no buffer should be
          allocated. Use a buffer size of 0 to perform a
          hardware-timed operation without using a buffer.

        Returns
        -------

          success_status : bool
        """
        channel_io_type = self.channel_io_type
        return CALL('Cfg%sBuffer' % (channel_io_type.title()), self, uInt32(samples_per_channel)) == 0



    # Not implemented:
    # DAQmxReadBinary*, DAQmxReadCounter*, DAQmxReadDigital*
    # DAQmxGetNthTaskReadChannel, DAQmxReadRaw
    # DAQmxWrite*
    # DAQmxExportSignal
    # DAQmxCalculateReversePolyCoeff, DAQmxCreateLinScale
    # DAQmxWaitForNextSampleClock
    # DAQmxSwitch*
    # DAQmxConnectTerms, DAQmxDisconnectTerms, DAQmxTristateOutputTerm
    # DAQmxResetDevice
    # DAQmxControlWatchdog*

    # DAQmxAOSeriesCalAdjust, DAQmxESeriesCalAdjust, DAQmxGet*,
    # DAQmxMSeriesCalAdjust, DAQmxPerformBridgeOffsetNullingCal, DAQmxRestoreLastExtCalConst
    # DAQmxSelfCal, DAQmxSetAIChanCalCalDate, DAQmxSetAIChanCalExpDate, DAQmxSSeriesCalAdjust
    # External Calibration, DSA Calibration, PXI-42xx Calibration, SCXI Calibration
    # Storage, TEDS
    # DAQmxSetAnalogPowerUpStates, DAQmxSetDigitalPowerUpStates
    # DAQmxGetExtendedErrorInfo

    def get_physical_channel_name(self, channel_name):
        """
        Indicates the name of the physical channel upon which this
        virtual channel is based.
        """
        channel_name = str (channel_name)
        buf_size = default_buf_size
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        CALL('GetPhysicalChanName', self, channel_name, ctypes.byref(buf), uInt32(buf_size))
        return buf.value

    def get_channel_type(self, channel_name):
        """
        Indicates the type of the virtual channel.

        Returns
        -------

        channel_type : {'AI', 'AO', 'DI', 'DO', 'CI', 'CO'}
        """
        channel_name = str (channel_name)
        t = int32(0)
        CALL('GetChanType', self, channel_name, ctypes.byref(t))
        channel_type_map = {DAQmx.Val_AI:'AI', DAQmx.Val_AO:'AO',
                            DAQmx.Val_DI:'DI', DAQmx.Val_DO:'DO',
                            DAQmx.Val_CI:'CI', DAQmx.Val_CO:'CO',
                            }
        return channel_type_map[t.value]

    def is_channel_global (self, channel_name):
        """
        Indicates whether the channel is a global channel.
        """
        channel_name = str (channel_name)
        d = bool32(0)
        CALL('GetChanIsGlobal', self, channel_name, ctypes.byref (d))
        return bool(d.value)

    # NotImplemented: DAQmx*ChanDescr

    def get_buffer_size (self, on_board=False):
        """
        Returns the number of samples the I/O buffer can hold for each
        channel in the task.

        If on_board is True then specifies in samples per channel the
        size of the onboard I/O buffer of the device.

        See also
        --------
        set_buffer_size, reset_buffer_size
        """
        d = uInt32(0)
        channel_io_type = self.channel_io_type
        if on_board:
            CALL('GetBuf%sOnbrdBufSize' % (channel_io_type.title()), self, ctypes.byref(d))
        else:
            CALL('GetBuf%sBufSize' % (channel_io_type.title ()), self, ctypes.byref(d))
        return d.value

    def set_buffer_size(self, sz):
        """
        Specifies the number of samples the I/O buffer can hold for
        each channel in the task. Zero indicates to allocate no
        buffer. Use a buffer size of 0 to perform a hardware-timed
        operation without using a buffer. Setting this property
        overrides the automatic I/O buffer allocation that NI-DAQmx
        performs.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_buffer_size, reset_buffer_size
        """
        channel_io_type = self.channel_io_type
        return CALL('SetBuf%sBufSize' % (channel_io_type.title()), self, uInt32 (sz)) == 0

    def reset_buffer_size(self):
        """
        Resets buffer size.

        Returns
        -------

          success_status : bool

        See also
        --------
        set_buffer_size, get_buffer_size
        """
        channel_io_type = self.channel_io_type
        return CALL('ResetBuf%sBufSize' % (channel_io_type.title()), self) == 0

    def get_sample_clock_rate(self):
        """
        Returns sample clock rate.

        See also
        --------
        set_sample_clock_rate, reset_sample_clock_rate
        """
        d = float64(0)
        CALL ('GetSampClkRate', self, ctypes.byref(d))
        return d.value

    def set_sample_clock_rate(self, value):
        """
        Specifies the sampling rate in samples per channel per
        second. If you use an external source for the Sample Clock,
        set this input to the maximum expected rate of that clock.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_sample_clock_rate, reset_sample_clock_rate
        """
        return CALL ('SetSampClkRate', self, float64 (value))==0

    def reset_sample_clock_rate(self):
        """
        Resets sample clock rate.

        Returns
        -------

          success_status : bool

        See also
        --------
        set_sample_clock_rate, get_sample_clock_rate
        """
        return CALL ('ResetSampClkRate', self)==0

    def get_convert_clock_rate(self):
        """
        Returns convert clock rate.

        See also
        --------
        set_convert_clock_rate, reset_convert_clock_rate
        """
        d = float64(0)
        CALL ('GetAIConvRate', self, ctypes.byref(d))
        return d.value

    def set_convert_clock_rate(self, value):
        """
        Specifies the rate at which to clock the analog-to-digital
        converter. This clock is specific to the analog input section
        of multiplexed devices.

        By default, NI-DAQmx selects the maximum convert rate
        supported by the device, plus 10 microseconds per channel
        settling time. Other task settings, such as high channel
        counts or setting Delay, can result in a faster default
        convert rate.

        If you connect signal conditioning accessories with track and
        hold capabilities, such as an SCXI module, to the device,
        NI-DAQmx uses the fastest convert rate possible that meets the
        settling requirements for the slowest module sampled. Refer to
        the device documentation for the signal conditioning accessory
        for more information.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_convert_clock_rate, reset_convert_clock_rate
        """
        return CALL ('SetAIConvRate', self, float64 (value))==0

    def reset_convert_clock_rate(self):
        """
        Resets convert clock rate.

        Returns
        -------

          success_status : bool

        See also
        --------
        set_convert_clock_rate, get_convert_clock_rate
        """
        return CALL ('ResetAIConvRate', self)==0

    def get_sample_clock_max_rate (self):
        """
        Indicates the maximum Sample Clock rate supported by the task,
        based on other timing settings. For output tasks, the maximum
        Sample Clock rate is the maximum rate of the DAC. For input
        tasks, NI-DAQmx calculates the maximum sampling rate
        differently for multiplexed devices than simultaneous sampling
        devices.

        For multiplexed devices, NI-DAQmx calculates the maximum
        sample clock rate based on the maximum AI Convert Clock rate
        unless you set Rate. If you set that property, NI-DAQmx
        calculates the maximum sample clock rate based on that
        setting. Use Maximum Rate to query the maximum AI Convert
        Clock rate. NI-DAQmx also uses the minimum sample clock delay
        to calculate the maximum sample clock rate unless you set
        Delay.

        For simultaneous sampling devices, the maximum Sample Clock
        rate is the maximum rate of the ADC.
        """
        d = float64(0)
        CALL ('GetSampClkMaxRate', self, ctypes.byref(d))
        return d.value

    def get_max(self, channel_name):
        """
        Returns max value.

        See also
        --------
        set_max, reset_max
        """
        channel_name = str(channel_name)
        d = float64(0)
        channel_type = self.channel_type
        CALL ('Get%sMax' % (channel_type), self, channel_name, ctypes.byref(d))
        return d.value

    def set_max(self, channel_name, value):
        """
        Specifies the maximum value you expect to measure or generate.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_max, reset_max
        """
        channel_name = str(channel_name)
        channel_type = self.channel_type
        return CALL ('Set%sMax' % (channel_type), self, channel_name, float64 (value))==0

    def reset_max(self, channel_name):
        """
        Resets max value.

        See also
        --------
        set_max, reset_max
        """
        channel_name = str(channel_name)
        channel_type = self.channel_type
        return CALL ('Reset%sMax' % (channel_type), self, channel_name)==0

    def get_min(self, channel_name):
        """
        Returns min value.

        See also
        --------
        set_min, reset_min
        """
        channel_name = str(channel_name)
        d = float64(0)
        channel_type = self.channel_type
        CALL ('Get%sMin' % (channel_type), self, channel_name, ctypes.byref(d))
        return d.value

    def set_min(self, channel_name, value):
        """
        Specifies the minimum value you expect to measure or generate.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_min, reset_min
        """

        channel_name = str(channel_name)
        channel_type = self.channel_type
        return CALL ('Set%sMin' % (channel_type), self, channel_name, float64 (value))==0

    def reset_min(self, channel_name):
        """
        Resets min value.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_min, set_min
        """
        channel_name = str(channel_name)
        channel_type = self.channel_type
        return CALL ('Reset%sMin' % (channel_type), self, channel_name)==0

    def get_high(self, channel_name):
        """
        Specifies the upper limit of the input range of the
        device. This value is in the native units of the device. On E
        Series devices, for example, the native units is volts.

        See also
        --------
        set_high, reset_high
        """
        channel_name = str(channel_name)
        d = float64(0)
        channel_type = self.channel_type
        CALL ('Get%sRngHigh' % (channel_type), self, channel_name, ctypes.byref(d))
        return d.value

    def get_low(self, channel_name):
        """
        Specifies the lower limit of the input range of the
        device. This value is in the native units of the device. On E
        Series devices, for example, the native units is volts.

        See also
        --------
        set_low, reset_low
        """
        channel_name = str(channel_name)
        d = float64(0)
        channel_type = self.channel_type
        CALL ('Get%sRngLow' % (channel_type), self, channel_name, ctypes.byref(d))
        return d.value

    def get_gain (self, channel_name):
        """
        Specifies a gain factor to apply to the channel.

        See also
        --------
        set_gain, reset_gain
        """
        channel_name = str(channel_name)
        d = float64(0)
        channel_type = self.channel_type
        CALL ('Get%sGain' % (channel_type), self, channel_name, ctypes.byref(d))
        return d.value

    def get_measurment_type(self, channel_name):
        """
        Indicates the measurement to take with the analog input
        channel and in some cases, such as for temperature
        measurements, the sensor to use.

        Indicates whether the channel generates voltage or current.
        """
        channel_name = str(channel_name)
        d = int32(0)
        channel_type = self.channel_type
        if channel_type=='AI':
            CALL('GetAIMeasType', self, channel_name, ctypes.byref (d))
        elif channel_type=='AO':
            CALL('GetAOOutputType', self, channel_name, ctypes.byref (d))
        else:
            raise NotImplementedError(repr((channel_name, channel_type)))
        measurment_type_map = {DAQmx.Val_Voltage:'voltage',
                               DAQmx.Val_Current:'current',
                               DAQmx.Val_Voltage_CustomWithExcitation:'voltage_with_excitation',
                               DAQmx.Val_Freq_Voltage:'freq_voltage',
                               DAQmx.Val_Resistance:'resistance',
                               DAQmx.Val_Temp_TC:'temperature',
                               DAQmx.Val_Temp_Thrmstr:'temperature',
                               DAQmx.Val_Temp_RTD:'temperature',
                               DAQmx.Val_Temp_BuiltInSensor:'temperature',
                               DAQmx.Val_Strain_Gage:'strain',
                               DAQmx.Val_Position_LVDT:'position_lvdt',
                               DAQmx.Val_Position_RVDT:'position_rvdt',
                               DAQmx.Val_Accelerometer:'accelration',
                               DAQmx.Val_SoundPressure_Microphone:'pressure',
                               DAQmx.Val_TEDS_Sensor:'TEDS'
                               }
        return measurment_type_map[d.value]

    def get_units (self, channel_name):
        """
        Specifies in what units to generate voltage on the
        channel. Write data to the channel in the units you select.

        Specifies in what units to generate current on the
        channel. Write data to the channel is in the units you select.

        See also
        --------
        set_units, reset_units
        """
        channel_name = str(channel_name)
        mt = self.get_measurment_type(channel_name)
        channel_type = self.channel_type
        if mt=='voltage':
            d = int32(0)
            CALL('Get%sVoltageUnits' % (channel_type), self, channel_name, ctypes.byref(d))
            units_map = {DAQmx.Val_Volts:'volts',
                         #DAQmx.Val_FromCustomScale:'custom_scale',
                         #DAQmx.Val_FromTEDS:'teds',
                         }
            return units_map[d.value]
        raise NotImplementedError(repr((channel_name, mt)))

    def get_auto_zero_mode (self, channel_name):
        """
        Specifies when to measure ground. NI-DAQmx subtracts the
        measured ground voltage from every sample.

        See also
        --------
        set_auto_zero_mode, reset_auto_zero_mode
        """
        channel_name = str(channel_name)
        d = int32(0)
        channel_type = self.channel_type
        CALL('Get%sAutoZeroMode' % (channel_type), self, channel_name, ctypes.byref (d))
        auto_zero_mode_map = {DAQmx.Val_None:'none',
                              DAQmx.Val_Once:'once',
                              DAQmx.Val_EverySample:'every_sample'}
        return auto_zero_mode_map[d.value]

    def get_data_transfer_mechanism(self, channel_name):
        """
        Specifies the data transfer mode for the device.

        See also
        --------
        set_data_transfer_mechanism, reset_data_transfer_mechanism
        """
        channel_name = str(channel_name)
        d = int32(0)
        channel_type = self.channel_type
        CALL('Get%sDataXferMech' % (channel_type), self, channel_name, ctypes.byref (d))
        data_transfer_mechanism_map = {DAQmx.Val_DMA:'dma',
                                       DAQmx.Val_Interrupts:'interrupts',
                                       DAQmx.Val_ProgrammedIO:'programmed_io',
                                       DAQmx.Val_USBbulk:'usb'}
        return data_transfer_mechanism_map[d.value]

    def get_regeneration(self):
        """
        Return True if regeneration (generating the same data more
        than once) is allowed.

        See also
        --------
        set_regeneration, reset_regeneration
        """
        d = int32(0)
        CALL('GetWriteRegenMode', self, ctypes.byref (d))
        if d.value==DAQmx.Val_AllowRegen:
            return True
        if d.value==DAQmx.Val_DoNotAllowRegen:
            return False
        assert 0,repr(d.value)

    def set_regeneration(self, allow = True):
        """
        Specifies whether to allow NI-DAQmx to generate the same data
        multiple times.

        If you enable regeneration and write new data to the buffer,
        NI-DAQmx can generate a combination of old and new data, a
        phenomenon called glitching.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_regeneration, reset_regeneration
        """
        if allow:
            return CALL('SetWriteRegenMode', self, DAQmx.Val_AllowRegen)==0
        return CALL('SetWriteRegenMode', self, DAQmx.Val_DoNotAllowRegen)==0

    def reset_regeneration(self):
        """
        Resets regeneration.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_regeneration, set_regeneration
        """
        return CALL('ResetWriteRegenMode', self)==0

    def set_arm_start_trigger(self, trigger_type='digital_edge'):
        """
        Specifies the type of trigger to use to arm the task for a
        Start Trigger. If you configure an Arm Start Trigger, the task
        does not respond to a Start Trigger until the device receives
        the Arm Start Trigger.

        Parameters
        ----------

        trigger_type:

          'digital_edge' - Trigger on a rising or falling edge of a digital signal.
          None - Disable the trigger.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_arm_start_trigger, reset_arm_start_trigger
        """
        if trigger_type=='digital_edge':
            trigger_type_val = DAQmx.Val_DigEdge
        elif trigger_type in ['disable', None]:
            trigger_type_val = DAQmx.Val_None
        else:
            assert 0,repr(trigger_type)
        return CALL('SetArmStartTrigType', self, trigger_type_val)==0

    def get_arm_start_trigger(self):
        """
        Returns arm start trigger.

        See also
        --------
        set_arm_start_trigger, reset_arm_start_trigger
        """
        d = int32(0)
        CALL ('GetArmStartTrigType', self, ctypes.byref (d))
        if d.value==DAQmx.Val_DigEdge:
            return 'digital_edge'
        if d.value==DAQmx.Val_None:
            return None
        assert 0, repr(d.value)

    def reset_arm_start_trigger(self):
        '''
        Resets arm start trigger.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_arm_start_trigger, set_arm_start_trigger
        '''
        return CALL ('ResetArmStartTrigType', self)==0

    def set_arm_start_trigger_source (self, source):
        """
        Specifies the name of a terminal where there is a digital
        signal to use as the source of the Arm Start Trigger.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_arm_start_trigger_source, reset_arm_start_trigger_source
        """
        source = str (source)
        return CALL ('SetDigEdgeArmStartTrigSrc', self, source)==0

    def set_arm_start_trigger_edge (self, edge='rising'):
        """
        Specifies on which edge of a digital signal to arm the task
        for a Start Trigger.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_arm_start_trigger_edge, reset_arm_start_trigger_edge
        """
        edge_map = dict (rising=DAQmx.Val_Rising,
                         falling=DAQmx.Val_Falling)
        edge_val = self._get_map_value ('edge', edge_map, edge)
        return CALL ('SetDigEdgeArmStartTrigEdge', self, edge_val)==0

    _pause_trigger_type = None
    def set_pause_trigger(self, trigger_type = None):
        """
        Specifies the type of trigger to use to pause a task.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_pause_trigger, reset_pause_trigger
        """
        trigger_type_map = dict(digital_level = DAQmx.Val_DigLvl,
                                analog_level = DAQmx.Val_AnlgLvl,
                                analog_window = DAQmx.Val_AnlgWin,
                                )
        trigger_type_map[None] = DAQmx.Val_None
        trigger_type_val = self._get_map_value('trigger_type',trigger_type_map, trigger_type)
        self._pause_trigger_type = trigger_type
        return CALL ('SetPauseTrigType', self, trigger_type_val)==0

    def set_pause_trigger_source(self, source):
        """
        Specifies the name of a virtual channel or terminal where
        there is an analog signal to use as the source of the trigger.

        For E Series devices, if you use a channel name, the channel
        must be the only channel in the task. The only terminal you
        can use for E Series devices is PFI0.

        Returns
        -------

          success_status : bool

        See also
        --------
        get_pause_trigger_source, reset_pause_trigger_source
        """
        source = str(source)
        if self._pause_trigger_type is None:
            raise TypeError('pause trigger type is not specified')
        routine_map = dict(digital_level = 'SetDigLvlPauseTrigSrc',
                           analog_level = 'SetAnlgLvlPauseTrigSrc',
                           analog_window = 'SetAnlgWinPauseTrigSrc')
        routine = self._get_map_value('set_pause_trigger_src_routine', routine_map, self._pause_trigger_type)
        return CALL (routine, self, source)==0

    def set_pause_trigger_when (self, when = None):
        """
        Specifies whether the task pauses above or below the threshold
        you specify with Level.

        Specifies whether the task pauses while the trigger signal is
        inside or outside the window you specify with Bottom and Top.

        Specifies whether the task pauses while the signal is high or
        low.

        See also
        --------
        get_pause_trigger_when, reset_pause_trigger_when
        """
        if self._pause_trigger_type is None:
            raise TypeError('pause trigger type is not specified')
        routine_map = dict(digital_level = 'SetDigLvlPauseTrigWhen',
                           analog_level = 'SetAnlgLvlPauseTrigWhen',
                           analog_window = 'SetAnlgWinPauseTrigWhen')
        routine = self._get_map_value('set_pause_trigger_when_routine', routine_map, self._pause_trigger_type)
        type_when_map = dict(digital_level = dict (high = DAQmx.Val_High, low = DAQmx.Val_Low),
                             analog_level = dict (above = DAQmx.Val_AboveLvl, below = DAQmx.Val_BelowLvl),
                             analog_window = dict (inside = DAQmx.Val_InsideWin, outside=DAQmx.Val_OutsideWin))
        when_map = self._get_map_value('set_pause_trigger_when_map', type_when_map, self._pause_trigger_type)
        when_val = self._get_map_value('when', when_map, when)
        return CALL (routine, self, when_val)

    def get_info_str(self, global_info=False):
        """
        Return verbose information string about the task and its
        properties.

        Parameters
        ----------

        global_info: bool
          If True then include global information.
        """
        lines = []
        tab = ''
        if global_info:
            lines.append(tab+'NI-DAQwx version: %s' % (self.get_version()))
            lines.append(tab+'System devices: %s' % (', '.join(self.get_system_devices()) or None))
            lines.append(tab+'System global channels: %s' % (', '.join(self.get_system_global_channels()) or None))
            lines.append(tab+'System tasks: %s' % (', '.join(self.get_system_tasks()) or None))
            tab += '  '
            for device in self.get_system_devices():
                lines.append(tab[:-1]+'Device: %s' % (device))
                lines.append(tab + 'Product type: %s' % (device.get_product_type()))
                lines.append(tab + 'Product number: %s' % (device.get_product_number()))
                lines.append(tab + 'Serial number: %s' % (device.get_serial_number()))
                lines.append (tab+'Bus: %s' % (device.get_bus ()))
                lines.append (tab+'Analog input channels: %s' % (make_pattern(device.get_analog_input_channels()) or None))
                lines.append (tab+'Analog output channels: %s' % (make_pattern(device.get_analog_output_channels()) or None))
                lines.append (tab+'Digital input lines: %s' % (make_pattern(device.get_digital_input_lines()) or None))
                lines.append (tab+'Digital input ports: %s' % (make_pattern(device.get_digital_input_ports()) or None))
                lines.append (tab+'Digital output lines: %s' % (make_pattern(device.get_digital_output_lines()) or None))
                lines.append (tab+'Digital output ports: %s' % (make_pattern(device.get_digital_output_ports()) or None))
                lines.append (tab+'Counter input channels: %s' % (make_pattern(device.get_counter_input_channels()) or None))
                lines.append (tab+'Counter output channels: %s' % (make_pattern(device.get_counter_output_channels()) or None))
        lines.append(tab[:-1]+'Task name: %s' % (self.name))
        lines.append(tab+'Names of devices: %s' % (', '.join(self.get_devices()) or None))
        lines.append(tab+'Number of channels: %s' % (self.get_number_of_channels()))
        lines.append(tab+'Names of channels: %s' % (', '.join(self.get_names_of_channels()) or None))
        lines.append(tab+'Channel type: %s' % (self.channel_type))
        lines.append(tab+'Channel I/O type: %s' % (self.channel_io_type))
        lines.append(tab+'Buffer size: %s' % (self.get_buffer_size()))

        tab += '  '
        for channel_name in self.get_names_of_channels():
            lines.append(tab[:-1]+'Channel name: %s' % (channel_name))
            lines.append(tab+'Physical channel name: %s' % (self.get_physical_channel_name(channel_name)))
            lines.append(tab+'Channel type: %s' % (self.get_channel_type (channel_name)))
            lines.append(tab+'Is global: %s' % (self.is_channel_global(channel_name)))
            if self.channel_type in ['AI', 'AO']:
                lines.append(tab+'Measurment type: %s' % (self.get_measurment_type(channel_name)))
                lines.append(tab+'Minimum/Maximum values: %s/%s %s' % (self.get_min(channel_name),
                                                                   self.get_max(channel_name),
                                                                   self.get_units(channel_name)))
                #lines.append(tab+'Gain: %s' % (self.get_gain (channel_name)))
                lines.append(tab+'Data transfer mechanism: %s' % (self.get_data_transfer_mechanism(channel_name)))
            if self.channel_type=='AI':
                lines.append(tab+'High/Low values: %s/%s' % (self.get_high(channel_name),
                                                             self.get_low (channel_name)))
                lines.append(tab+'Auto zero mode: %s' % (self.get_auto_zero_mode(channel_name)))
            if self.channel_type=='CI':
                lines.append(tab+'Timebase rate: %sHz' % (self.get_timebase_rate(channel_name)))
                lines.append(tab+'Dublicate count prevention: %s' % (self.get_dublicate_count_prevention(channel_name)))
        return '\n'.join(lines)

    def get_read_current_position (self):
        """
        Indicates in samples per channel the current position in the
        buffer.
        """
        d = uInt64(0)
        CALL('GetReadCurrReadPos', self, ctypes.byref(d))
        return d.value

    def get_write_current_position(self):
        """
        Indicates the position in the buffer of the next sample to generate.
        This value is the same for all channels in the task.
        """
        d = uInt64(0)
        CALL('GetWriteCurrWritePos', self, ctypes.byref(d))
        return d.value

    def get_samples_per_channel_available(self):
        """
        Indicates the number of samples available to read per
        channel. This value is the same for all channels in the task.
        """
        d = uInt32(0)
        CALL('GetReadAvailSampPerChan', self, ctypes.byref(d))
        return d.value

    def get_samples_per_channel_acquired(self):
        """
        Indicates the total number of samples acquired by each
        channel. NI-DAQmx returns a single value because this value is
        the same for all channels.
        """
        d = uInt32(0)
        CALL('GetReadTotalSampPerChanAcquired', self, ctypes.byref(d))
        return d.value

    def get_samples_per_channel_generated(self):
        """
        Indicates the total number of samples generated by each
        channel. NI-DAQmx returns a single value because this value is
        the same for all channels.
        """
        d = uInt64(0)
        CALL('GetWriteTotalSampPerChanGenerated', self, ctypes.byref(d))
        return d.value

    def wait_until_done(self, timeout=-1):
        """
        Waits for the measurement or generation to complete. Use this
        function to ensure that the specified operation is complete
        before you stop the task.

        Parameters
        ----------

        timeout : float

          The maximum amount of time, in seconds, to wait for the
          measurement or generation to complete. The function returns
          an error if the time elapses before the measurement or
          generation is complete.

          A value of -1 (DAQmx_Val_WaitInfinitely) means to wait
          indefinitely.

          If you set timeout to 0, the function checks once and
          returns an error if the measurement or generation is not
          done.

        Returns
        -------

          success_status : bool

        """
        return CALL('WaitUntilTaskDone', self, float64 (timeout))==0

    def get_read_relative_to(self):
        """
        Returns the point in the buffer relative to which a read operation
        begins.

        Returns
        -------

          relative_mode : str
            The current read relative mode setting configured for the task

        See also
        --------

          set_read_relative_to
          reset_read_relative_to

        """

        d = uInt32(0)
        CALL('GetReadRelativeTo', self, ctypes.byref(d))
        relative_mode_map = { DAQmx.Val_FirstSample : 'first_sample',
                              DAQmx.Val_CurrReadPos : 'current_read_position',
                              DAQmx.Val_RefTrig : 'ref_trigger',
                              DAQmx.Val_FirstPretrigSamp : 'first_pretrigger_sample',
                              DAQmx.Val_MostRecentSamp : 'most_recent' }
        return relative_mode_map[d.value]

    def set_read_relative_to(self, relative_mode):
        """
        Sets the point in the buffer at which a read operation begins. If an offset is
        also specified, the read operation begins at that offset relative to the point
        selected with this property. The default value is 'current_read_position' unless a
        reference trigger has been specified for the task; if a reference trigger has been
        configured for the task, the default is 'first_pretrigger_sample'.

        Parameters
        ----------

          relative_mode : {'first_sample', 'current_read_position', 'ref_trigger', \
                           'first_pretrigger_sample', 'most_recent'}

            Specifies the point in the buffer at which to begin a read operation.

              'first_sample' - start reading samples relative to the first sample
              acquired in the buffer

              'current_read_position' - start reading samples relative to the last
              sample returned by the previous read. For the first read, this position
              is the first sample acquired, or if a reference trigger has been configured
              for the task, the first pretrigger sample

              'ref_trigger' - start reading samples relative to the first sample
              after the reference trigger occurred

              'first_pretrigger_sample' - start reading samples relative to the first
              pretrigger sample (the number of pretrigger samples is specified when
              configuring a reference trigger)

              'most_recent' - start reading samples relative to the next sample
              acquired; for example, use this value and set the offset to -1 to read
              the last sample acquired

        See also
        --------

          get_read_relative_to
          reset_read_relative_to

        """
        relative_mode_map = { 'first_sample' : DAQmx.Val_FirstSample,
                              'current_read_position' : DAQmx.Val_CurrReadPos,
                              'ref_trigger' : DAQmx.Val_RefTrig,
                              'first_pretrigger_sample' : DAQmx.Val_FirstPretrigSamp,
                              'most_recent' : DAQmx.Val_MostRecentSamp }
        relative_mode = self._get_map_value('relative_mode', relative_mode_map,
                                            relative_mode.lower())
        r = CALL('SetReadRelativeTo', self, relative_mode)
        return r == 0

    def reset_read_relative_to(self):
        """
        Resets the point at which data is read from the buffer to its default value of
        'current_read_position', or in cases where a reference trigger has been set up
        for the task, to 'first_pretrigger_sample'.

        Returns
        -------

          success_status : bool

        See also
        --------

          get_read_relative_to
          set_read_relative_to

        """
        r = CALL('ResetReadRelativeTo', self)
        return r == 0

    def get_read_overwrite(self):
        """
        Returns the current OverWrite mode setting configured for the task.

        Returns
        -------

          overwite_mode : str
            The current OverWrite mode setting configured for the task

        See also
        --------

          set_read_overwrite
          reset_read_overwrite

        """
        d = uInt32(0)
        CALL('GetReadOverWrite', self, ctypes.byref(d))
        overwrite_mode_map = {
            DAQmx.Val_OverwriteUnreadSamps : 'overwrite',
            DAQmx.Val_DoNotOverwriteUnreadSamps : 'no_overwrite' }
        return overwrite_mode_map[d.value]

    def set_read_overwrite(self, overwrite_mode):
        """
        Sets whether unread samples in the buffer should be overwritten.

        Parameters
        ----------

        overwrite_mode : {'overwrite', 'no_overwrite'}

          'overwrite' - unread samples are overwritten as the device's buffer
          fills during an acquisition. To read only the newest samples in the
          buffer, configure set_read_relative_to() to 'most_recent' and
          set_offset() to the appropriate number of samples

          'no_overwrite' - acquisition stops when the buffer encounters the first
          unread sample

        Returns
        -------

          success_status : bool

        See also
        --------

          get_read_overwrite
          reset_read_overwrite

        """
        overwrite_map = { 'overwrite' : DAQmx.Val_OverwriteUnreadSamps,
                          'no_overwrite' : DAQmx.Val_DoNotOverwriteUnreadSamps }
        overwrite_mode = self._get_map_value('overwrite_mode', overwrite_map,
                                             overwrite_mode.lower())
        r = CALL('SetReadOverWrite', self, overwrite_mode)
        return r == 0

    def reset_read_overwrite(self):
        """
        Resets the read overwrite mode to the default value of 'no_overwrite'.

        Returns
        -------

          success_status : bool

        See also
        --------
        set_read_overwrite
        get_read_overwrite

        """

        r = CALL('ResetReadOverWrite', self)
        return r == 0

    def get_read_offset(self):
        """
        Gets the current read offset set for the task.

        Returns
        -------

          offset : int
            The current read offset value, in number of samples, programmed
            into the task. The offset is relative to the position specified
            using set_read_relative_to().

        See also
        --------

          set_read_offset
          reset_read_offset
          set_read_relative_to

        """
        d = uInt32(0)
        CALL('GetReadOffset', self, ctypes.byref(d))
        return d.value

    def set_read_offset(self, offset):
        """
        Sets the read offset for the current task.

        Parameters
        ----------

          offset : int
            The offset, in number of samples, from which samples will be read
            from the buffer. The offset is relative to the position specified
            using set_read_relative_to().

        Returns
        -------

          success_status : bool

        See also
        --------

          get_read_offset
          reset_read_offset
          set_read_relative_to

        """
        r = CALL('SetReadOffset', self, uInt32(offset))
        return r == 0

    def reset_read_offset(self):
        """
        Resets the read offset for the current task to its default value.

        Returns
        -------

          success_status : bool

        See also
        --------

          set_read_offset
          get_read_offset

        """
        r = CALL('ResetReadOffset', self)
        return r == 0

    _register_every_n_samples_event_cache = None

    def register_every_n_samples_event(self, func,
                                       samples = 1,
                                       options = 0,
                                       cb_data = None
                                       ):
        """
        Registers a callback function to receive an event when the
        specified number of samples is written from the device to the
        buffer or from the buffer to the device. This function only
        works with devices that support buffered tasks.

        When you stop a task explicitly any pending events are
        discarded. For example, if you call DAQmxStopTask then you do
        not receive any pending events.

        Parameters
        ----------

        func : function

          The function that you want DAQmx to call when the event
          occurs. The function you pass in this parameter must have
          the following prototype::

            def func(task, event_type, samples, cb_data):
                ...
                return 0

          Upon entry to the callback, the task parameter contains the
          handle to the task on which the event occurred. The
          event_type parameter contains the value you passed in the
          event_type parameter of this function. The samples parameter
          contains the value you passed in the samples parameter of
          this function. The cb_data parameter contains the value you
          passed in the cb_data parameter of this function.

        samples : int

          The number of samples after which each event should occur.

        options, cb_data :

          See `register_done_event` documentation.

        Returns
        -------

          success_status : bool

        See also
        --------

        register_signal_event, register_done_event
        """
        event_type_map = dict(input=DAQmx.Val_Acquired_Into_Buffer,
                              output=DAQmx.Val_Transferred_From_Buffer)
        event_type = event_type_map[self.channel_io_type]

        if options=='sync':
            options = DAQmx.Val_SynchronousEventCallbacks

        if func is None:
            c_func = None # to unregister func
        else:
            if self._register_every_n_samples_event_cache is not None:
                # unregister:
                self.register_every_n_samples_event(None, samples=samples, options=options, cb_data=cb_data)
            argspec = getargspec(func)
            if len(argspec.args) != 4:
                raise ValueError("Function signature should be like f(task, event_type, samples, cb_data) -> 0.")
            # TODO: use wrapper function that converts cb_data argument to given Python object
            from .callback_maps import EveryNSamplesEventCallback_map
            c_func = EveryNSamplesEventCallback_map[self.channel_type](func)

        self._register_every_n_samples_event_cache = c_func

        return CALL('RegisterEveryNSamplesEvent', self, event_type, uInt32(samples), uInt32 (options), c_func, cb_data)==0

    _register_done_event_cache = None

    def register_done_event(self, func, options = 0, cb_data = None):
        """
        Registers a callback function to receive an event when a task
        stops due to an error or when a finite acquisition task or
        finite generation task completes execution. A Done event does
        not occur when a task is stopped explicitly, such as by
        calling DAQmxStopTask.

        Parameters
        ----------

        func : function

          The function that you want DAQmx to call when the event
          occurs.  The function you pass in this parameter must have
          the following prototype::

            def func(task, status, cb_data = None):
                ...
                return 0

          Upon entry to the callback, the taskHandle parameter
          contains the handle to the task on which the event
          occurred. The status parameter contains the status of the
          task when the event occurred. If the status value is
          negative, it indicates an error. If the status value is
          zero, it indicates no error. If the status value is
          positive, it indicates a warning. The callbackData parameter
          contains the value you passed in the callbackData parameter
          of this function.

        options : {int, 'sync'}

          Use this parameter to set certain options. You can
          combine flags with the bitwise-OR operator ('|') to set
          multiple options. Pass a value of zero if no options need to
          be set.

          'sync' - The callback function is called in the thread which
          registered the event. In order for the callback to occur,
          you must be processing messages. If you do not set this
          flag, the callback function is called in a DAQmx thread by
          default.

          Note: If you are receiving synchronous events faster than
          you are processing them, then the user interface of your
          application might become unresponsive.

        cb_data :

          A value that you want DAQmx to pass to the callback function
          as the function data parameter. Do not pass the address of a
          local variable or any other variable that might not be valid
          when the function is executed.

        Returns
        -------

          success_status : bool

        See also
        --------

        register_signal_event, register_every_n_samples_event
        """
        if options=='sync':
            options = DAQmx.Val_SynchronousEventCallbacks

        if func is None:
            c_func = None
        else:
            if self._register_done_event_cache is not None:
                self.register_done_event(None, options=options, cb_data=cb_data)
            argspec = getargspec(func)
            if len(argspec.args) != 3 or argspec.defaults != (None,):
                raise ValueError("Function signature should be like f(task, status, cb_data=None) -> 0.")
            from .callback_maps import DoneEventCallback_map
            c_func = DoneEventCallback_map[self.channel_type](func)
        self._register_done_event_cache = c_func

        return CALL('RegisterDoneEvent', self, uInt32 (options), c_func, cb_data)==0

    _register_signal_event_cache = None

    def register_signal_event(self, func, signal, options=0, cb_data = None):
        """
        Registers a callback function to receive an event when the
        specified hardware event occurs.

        When you stop a task explicitly any pending events are
        discarded. For example, if you call DAQmxStopTask then you do
        not receive any pending events.

        Parameters
        ----------

        func : function

          The function that you want DAQmx to call when the event
          occurs. The function you pass in this parameter must have the
          following prototype::

            def func(task, signalID, cb_data):
              ...
              return 0

          Upon entry to the callback, the task parameter contains the
          handle to the task on which the event occurred. The signalID
          parameter contains the value you passed in the signal
          parameter of this function. The cb_data parameter contains
          the value you passed in the cb_data parameter of this
          function.

        signal : {'sample_clock', 'sample_complete', 'change_detection', 'counter_output'}

          The signal for which you want to receive results:

          'sample_clock' - Sample clock
          'sample_complete' - Sample complete event
          'change_detection' - Change detection event
          'counter_output' - Counter output event

        options, cb_data :

          See `register_done_event` documentation.

        Returns
        -------

          success_status : bool

        See also
        --------

        register_done_event, register_every_n_samples_event
        """
        signalID_map = dict (
            sample_clock = DAQmx.Val_SampleClock,
            sample_complete = DAQmx.Val_SampleCompleteEvent,
            change_detection = DAQmx.Val_ChangeDetectionEvent,
            counter_output = DAQmx.Val_CounterOutputEvent
            )
        signalID_val = self._get_map_value('signalID', signalID_map, signal)
        if options=='sync':
            options = DAQmx.Val_SynchronousEventCallbacks

        if func is None:
            c_func = None
        else:
            if self._register_signal_event_cache is not None:
                self._register_signal_event(None, signal=signal, options=options, cb_data=cb_data)
            argspec = getargspec(func)
            if len(argspec.args) != 4:
                raise ValueError("Function signature should be like f(task, signalID, cb_data) -> 0.")
            from .callback_maps import SignalEventCallback_map
            c_func = SignalEventCallback_map[self.channel_type](func)
        self._register_signal_event_cache = c_func
        return CALL('RegisterSignalEvent', self, signalID_val, uInt32(options), c_func, cb_data)==0
