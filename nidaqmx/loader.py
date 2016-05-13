#!/usr/bin/env python

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os
import sys
import warnings
import ctypes
import ctypes.util

from .types import uInt32


def _find_library_linux():
    # TODO: Find the location of the NIDAQmx.h automatically (e.g. by
    # using the location of the library).
    header_name = '/usr/local/include/NIDAQmx.h'
    libname = 'nidaqmx'
    libfile = ctypes.util.find_library(libname)
    return header_name, libname, libfile


def _find_library_nt():
    import _winreg as winreg # pylint: disable=import-error
    regpath = r'SOFTWARE\National Instruments\NI-DAQmx\CurrentVersion'
    reg6432path = r'SOFTWARE\Wow6432Node\National Instruments\NI-DAQmx\CurrentVersion'
    libname = 'nicaiu'

    try:
        regkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg6432path)
    except WindowsError: # pylint: disable=undefined-variable
        try:
            regkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, regpath)
        except WindowsError: # pylint: disable=undefined-variable
            print('You need to install NI-DAQmx first.', file=sys.stderr)
            return None, libname, None
    nidaqmx_install = winreg.QueryValueEx(regkey, 'Path')[0]
    header_name = os.path.join(nidaqmx_install, r'include\NIDAQmx.h')
    if not os.path.isfile(header_name): # from Issue 23
        header_name = os.path.join(nidaqmx_install,
                                   r'DAQmx ANSI C Dev\include\NIDAQmx.h')
    if not os.path.isfile(header_name): # from Issue 32
        header_name = os.path.join(nidaqmx_install,
                                   r'National Instruments\Shared\CVI\Include\NIDAQmx.h')

    ansi_c_dev = os.path.join(nidaqmx_install,
                              r'National Instruments\NI-DAQ\DAQmx ANSI C Dev')
    if not os.path.isdir(ansi_c_dev): # from Issue 23
        ansi_c_dev = os.path.join(nidaqmx_install, r'DAQmx ANSI C Dev')
    regkey.Close()

    libfile = ctypes.util.find_library(libname)
    if libfile is None:
        # try default installation path:
        libfile = os.path.join(ansi_c_dev, r'lib\nicaiu.dll')
        if os.path.isfile(libfile):
            print('You should add %r to PATH environment variable and reboot.'
                  % (os.path.dirname(libfile)), file=sys.stderr)
        else:
            libfile = None

    return header_name, libname, libfile


def _find_library():
    if os.name == "nt":
        header_name, libname, libfile = _find_library_nt()
    else:
        header_name, libname, libfile = _find_library_linux()

    lib = None
    if libfile is None:
        warnings.warn(
            'Failed to find NI-DAQmx library.\n'
            'Make sure that lib%s is installed and its location is listed in PATH|LD_LIBRARY_PATH|.\n'
            'The functionality of PyLibNIDAQmx will be disabled.'
            % (libname), ImportWarning)
    else:
        if os.name == 'nt':
            lib = ctypes.windll.LoadLibrary(libfile)
        else:
            lib = ctypes.cdll.LoadLibrary(libfile)

    # FIXME If lib is None.
    return header_name, lib


def get_nidaqmx_version ():
    if libnidaqmx is None:
        return None
    d = uInt32 (0)
    libnidaqmx.DAQmxGetSysNIDAQMajorVersion(ctypes.byref(d))
    major = d.value
    libnidaqmx.DAQmxGetSysNIDAQMinorVersion(ctypes.byref(d))
    minor = d.value
    return '%s.%s' % (major, minor)


def _convert_header(header_name, header_module_name):
    import pprint
    assert os.path.isfile(header_name), repr(header_name)
    d = {}
    err_map = {}
    with open (header_name, 'r') as f:
        for line in f.readlines():
            if not line.startswith('#define'): continue
            i = line.find('//')
            words = line[7:i].strip().split(None, 2)
            if len (words) != 2: continue
            name, value = words
            if not name.startswith('DAQmx') or name.endswith(')'):
                continue
            if value.startswith('0x'):
                # Example: ^#define DAQmx_Buf_Input_BufSize                                          0x186C // Specifies the number of samples the input buffer can hold for each channel in the task. Zero indicates to allocate no buffer. Use a buffer size of 0 to perform a hardware-timed operation without using a buffer. Setting this property overrides the automatic input buffer allocation that NI-DAQmx performs.$
                d[name] = int(value, 16)
            elif name.startswith('DAQmxError') or name.startswith('DAQmxWarning'):
                # Example: ^#define DAQmxErrorCOCannotKeepUpInHWTimedSinglePoint                                    (-209805)$
                assert value[0]=='(' and value[-1]==')', repr((name, value))
                value = int(value[1:-1])
                name = name.replace("DAQmxError", "").replace("DAQmxWarning", "")
                err_map[value] = name
            elif name.startswith('DAQmx_Val') or name[5:] in ['Success','_ReadWaitMode']:
                # Examples:
                # ^#define DAQmx_Val_SynchronousEventCallbacks				     (1<<0)	// Synchronous callbacks$
                # ^#define DAQmxSuccess					 (0)$
                # ^#define DAQmx_ReadWaitMode	DAQmx_Read_WaitMode$
                d[name] = eval(value, {}, d) # pylint: disable=eval-used
            else:
                print(name, value, file=sys.stderr)

        # DAQmxSuccess is not renamed, because it's unused and I'm lazy.
        _d = {k.replace("DAQmx_", ""): v for k,v in d.viewitems()}

    try:
        path = os.path.dirname(os.path.abspath (__file__))
    except NameError:
        path = os.getcwd()
    fn = os.path.join(path, header_module_name)
    print('Generating %r' % (fn), file=sys.stderr)
    with open(fn, 'w') as f:
        f.write("# This file is auto-generated. Do not edit!\n\n")
        f.write("from collections import namedtuple\n\n")
        f.write("_d = %s\n" % pprint.pformat(_d))
        f.write("DAQmxConstants = namedtuple('DAQmxConstants', _d.keys())\n")
        f.write("DAQmx = DAQmxConstants(**_d)\n\n")
        f.write("error_map = %s\n" % pprint.pformat(err_map))

    print('Please upload generated file %r to http://code.google.com/p/pylibnidaqmx/issues'
          % (fn), file=sys.stderr)

def _load_header(header_name):
    if libnidaqmx is None:
        return (None, None)

    version = get_nidaqmx_version()
    mod_name = 'nidaqmx_h_%s' % (version.replace ('.', '_'))
    pkg_name = 'nidaqmx.headers.'

    try:
        mod = __import__(pkg_name + mod_name, fromlist=[mod_name])
    except ImportError:
        _convert_header(header_name, mod_name + ".py")
        mod = __import__(pkg_name + mod_name, fromlist=[mod_name])

    return mod.DAQmx, mod.error_map


_header_name, libnidaqmx = _find_library()
DAQmx, error_map = _load_header(_header_name)
