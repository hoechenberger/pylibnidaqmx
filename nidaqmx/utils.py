#!/usr/bin/env python

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import sys
import ctypes
import textwrap
from .constants import default_buf_size
from .loader import libnidaqmx, error_map
from .exceptions import NIDAQmxRuntimeError


def CHK(return_code, funcname, *args):
    """
    Return ``return_code`` while handle any warnings and errors from
    calling a libnidaqmx function ``funcname`` with arguments
    ``args``.
    """
    if return_code == 0:  # call was succesful
        pass
    else:
        buf_size = default_buf_size
        while buf_size < 1000000:
            buf = ctypes.create_string_buffer(b'\000' * buf_size)
            try:
                r = libnidaqmx.DAQmxGetExtendedErrorInfo(ctypes.byref(buf),
                                                         buf_size)
                if r != 0:
                    r = libnidaqmx.DAQmxGetErrorString(return_code,
                                                       ctypes.byref(buf),
                                                       buf_size)
            except RuntimeError as msg:
                if 'Buffer is too small to fit the string' in str(msg):
                    buf_size *= 2
                else:
                    raise NIDAQmxRuntimeError(msg)
            else:
                break
        if r:
            if return_code < 0:
                raise NIDAQmxRuntimeError(
                    '%s%s failed with error %s=%d: %s'
                    % (funcname, args, error_map[return_code],
                       return_code, repr(buf.value)))
            else:
                warning = error_map.get(return_code, return_code)
                sys.stderr.write(
                    '%s%s warning: %s\n' % (funcname, args, warning))
        else:
            text = '\n  '.join(
                [''] + textwrap.wrap(buf.value, 80) + ['-' * 10])
            if return_code < 0:
                raise NIDAQmxRuntimeError('%s%s:%s' % (funcname, args, text))
            else:
                sys.stderr.write('%s%s warning:%s\n' % (funcname, args, text))
    return return_code


def CALL(name, *args):
    """
    Calls libnidaqmx function ``name`` and arguments ``args``.
    """
    funcname = 'DAQmx' + name
    func = getattr(libnidaqmx, funcname)
    new_args = []
    for a in args:
        if isinstance(a, unicode):
            # print(name, 'argument', a, 'is unicode', file=sys.stderr)
            new_args.append(bytes(a))
        else:
            new_args.append(a)
    r = func(*new_args)
    r = CHK(r, funcname, *new_args)
    return r


def make_pattern(paths, _main=True):
    """
    Returns a pattern string from a list of path strings.

    For example::

      >>> make_pattern(['Dev1/ao1', 'Dev1/ao2','Dev1/ao3', 'Dev1/ao4'])
      'Dev1/ao1:4'

    """
    patterns = {}
    flag = False
    for path in paths:
        if path.startswith('/'):
            path = path[1:]
        splitted = path.split('/', 1)
        if len(splitted) == 1:
            if patterns:
                assert flag, repr((flag, paths, patterns, path, splitted))
            flag = True
            word = splitted[0]
            i = 0
            while i < len(word):
                if word[i].isdigit():
                    break
                i += 1

            splitted = [word[:i], word[i:]]
        l = patterns.get(splitted[0], None)
        if l is None:
            l = patterns[splitted[0]] = set()
        l.update(splitted[1:])
    r = []
    for prefix in sorted(patterns.keys()):
        lst = list(patterns[prefix])
        if len(lst) == 1:
            if flag:
                r.append(prefix + lst[0])
            else:
                r.append(prefix + '/' + lst[0])
        elif lst:
            if prefix:
                subpattern = make_pattern(lst, _main=False)
                if subpattern is None:
                    if _main:
                        return ','.join(paths)
                        # raise NotImplementedError(repr((lst, prefix, paths, patterns))
                    else:
                        return None
                if ',' in subpattern:
                    subpattern = '{%s}' % (subpattern)
                if flag:
                    r.append(prefix + subpattern)
                else:
                    r.append(prefix + '/' + subpattern)
            else:
                slst = sorted(int(i) for i in lst)
                # assert slst == range(slst[0], slst[-1]+1), repr((slst, lst))
                if len(slst) == 1:
                    r.append(str(slst[0]))
                elif slst == range(slst[0], slst[-1] + 1):
                    r.append('%s:%s' % (slst[0], slst[-1]))
                else:
                    return None
                    # raise NotImplementedError(repr(slst), repr(prefix), repr(paths))
        else:
            r.append(prefix)
    return ','.join(r)


def _test_make_pattern():
    paths = ['Dev1/ao1', 'Dev1/ao2','Dev1/ao3', 'Dev1/ao4',
             'Dev1/ao5','Dev1/ao6','Dev1/ao7']
    assert make_pattern(paths) == 'Dev1/ao1:7',\
        repr(make_pattern(paths))
    paths += ['Dev0/ao1']
    assert make_pattern(paths) == 'Dev0/ao1,Dev1/ao1:7',\
        repr(make_pattern(paths))
    paths += ['Dev0/ao0']
    assert make_pattern(paths) == 'Dev0/ao0:1,Dev1/ao1:7',\
        repr(make_pattern(paths))
    paths += ['Dev1/ai1', 'Dev1/ai2','Dev1/ai3']
    assert make_pattern(paths) == 'Dev0/ao0:1,Dev1/{ai1:3,ao1:7}',\
        repr(make_pattern(paths))
    paths += ['Dev2/port0/line0']
    assert make_pattern(paths) == 'Dev0/ao0:1,Dev1/{ai1:3,ao1:7},Dev2/port0/line0',\
        repr(make_pattern(paths))
    paths += ['Dev2/port0/line1']
    assert make_pattern(paths) == 'Dev0/ao0:1,Dev1/{ai1:3,ao1:7},Dev2/port0/line0:1',\
        repr(make_pattern(paths))
    paths += ['Dev2/port1/line0','Dev2/port1/line1']
    assert make_pattern(paths) == 'Dev0/ao0:1,Dev1/{ai1:3,ao1:7},Dev2/{port0/line0:1,port1/line0:1}',\
        repr(make_pattern(paths))
