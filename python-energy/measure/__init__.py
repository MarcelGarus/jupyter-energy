#!/usr/bin/env python

import ctypes
import os.path as osp

try:
    from py3nvml import py3nvml as nvml
    nvml.nvmlInit()
except ImportError:
    print("Couldn't import NVML. If you think this should be supported, try installing the py3nvml Python package.")
    pass

HERE = osp.abspath(osp.dirname(__file__))


class MeasureError(Exception):
    def __init__(self, type, arg):
        super().__init__(f'{type}: {arg}')


def assert_valid(name, obj):
    def fail(msg): raise MeasureError(name, msg)
    if obj >= 0:
        return obj
    if obj == -1:
        raise fail('Event is not supported.')
    if obj == -2:
        raise fail('Unknown unit. We can only handle joules.')
    if obj == -3:
        raise fail('Cannot access power measurement.')
    if obj == -4:
        raise fail('Unexpected event config file.')
    if obj == -5:
        raise fail('Missing permissions. Try running this as sudo.')
    if obj == -6:
        raise fail('Syscall failed for unknown reason.')
    if obj == -7:
        raise fail('Couldn\'t read consumed energy.')
    if obj == -8:
        raise fail('Used an invalid handle.')
    if obj == -9:
        raise fail('Couldn\'t write to MCP.')
    if obj == -10:
        raise fail('Couldn\'t read from MCP.')
    if obj == -11:
        raise fail('MCP didn\'t send ACK.')
    if obj == -12:
        raise fail('MCP checksum failed.')
    raise fail('Shared library returned unknown error code.')


_rapl = ctypes.CDLL(f'{HERE}/rapl.so')
_mcp = ctypes.CDLL(f'{HERE}/mcp.so')

class RaplHandle:
    def __init__(self, event_type: str):
        self.event_type = event_type
        self.handle = -1
        create_handle = _rapl.create_handle
        create_handle.restype = ctypes.c_long
        self.handle = self.assert_valid(create_handle(event_type.encode('utf-8')))

    def assert_valid(self, obj):
        return assert_valid(self.event_type, obj)

    def used_joules(self):
        read_handle_in_joules = _rapl.read_handle_in_joules
        read_handle_in_joules.restype = ctypes.c_double
        return self.assert_valid(read_handle_in_joules(self.handle))

    def __del__(self):
        drop_handle = _rapl.drop_handle
        drop_handle.restype = ctypes.c_int
        try:
            self.assert_valid(drop_handle(self.handle))
        except MeasureError:
            pass


class McpDevice:
    def __init__(self, filename: str):
        self.filename = filename
        self.device = -1
        create_device = _mcp.create_device
        create_device.restype = ctypes.c_long
        self.device = self.assert_valid(create_device(filename.encode('utf-8')))

    def assert_valid(self, obj):
        return assert_valid(self.filename, obj)

    def __del__(self):
        drop_device = _mcp.drop_device
        try:
            self.assert_valid(drop_device(self.device))
        except MeasureError:
            pass


class McpHandle:
    def __init__(self, device: McpDevice, channel: int):
        self.device = device
        self.handle = -1
        create_handle = _mcp.create_handle
        create_handle.restype = ctypes.c_long
        self.handle = self.assert_valid(create_handle(device.device, channel))

    def assert_valid(self, obj):
        return assert_valid(self.device.filename, obj)

    def current_watts(self):
        read_handle_in_watts = _mcp.read_handle_in_watts
        read_handle_in_watts.restype = ctypes.c_double
        return self.assert_valid(read_handle_in_watts(self.handle))

    def __del__(self):
        drop_handle = _mcp.drop_handle
        try:
            self.assert_valid(drop_handle(self.handle))
        except MeasureError:
            pass

class NvmlHandle:
    def __init__(self, gpu_index: int):
        name = f'nvml{gpu_index}'
        if nvml is None:
            raise MeasureError(name, 'NVML is not supported. Try installing the py3nvml library.')
        try:
            self.device = nvml.nvmlDeviceGetHandleByIndex(gpu_index)
        except nvml.NVMLError_InvalidArgument as e:
            raise MeasureError(name, f"Couldn't get the device: {e}")

    def current_watts(self):
        return nvml.nvmlDeviceGetPowerUsage(self.device) / 1000
