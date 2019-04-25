#!/usr/bin/python
import rospy
import struct
from rospy_tutorials.srv import AddTwoInts
from constants import ThrusterKillBoardConstants as tkb
from constants import ThrusterID


class CANDeviceHandle(object):
    '''
    Helper class to allow developers to write handles for communication with a particular CAN device.
    See ExampleCANDeviceHandle for an example of implementing one of these.
    '''
    def __init__(self, driver, device_id):
        '''
        Creates a CANDeviceHandle.
        @param driver: a USBtoCANBoard object that will be used for communication with the USB to CAN board
        @param device_id: the CAN id of the device this class will handle
        '''
        self._driver = driver
        self._device_id = device_id

    def request_data(self, length):
        '''
        Requests data from the device
        @param length: number of bytes to request
        @return: the response bytes from the device
        '''
        return self._driver.request_data(self._device_id, length)

    def send_data(self, data):
        '''
        Sends data to the device
        @param data: the data payload to send to the device (string/bytes object)
        '''
        return self._driver.send_data(data)


class ExampleEchoDeviceHandle(CANDeviceHandle):
    '''
    An example implementation of a CANDeviceHandle which will handle
    a device that echos back any data sent to it.
    '''
    def __init__(self, *args, **kwargs):
        super(ExampleEchoDeviceHandle, self).__init__(*args, **kwargs)
        # Setup a timer to check valid functionality every second
        self.timer = rospy.Timer(rospy.Duration(1.0), self.timer_cb)

    def timer_cb(self, *args):
        # Example string to test with
        test = 'HELLO'
        # Send example string to device
        self.send_data(test)
        # Request data from device
        res = self.request_data(len(test))
        # Ensure device correctly echoed exact same data back
        assert res == test
        rospy.loginfo('Succesfully echoed {}'.format(test))


class ExampleAdderDeviceHandle(CANDeviceHandle):
    '''
    An example implementation of a CANDeviceHandle which will handle
    a device that echos back any data sent to it.
    '''
    def __init__(self, *args, **kwargs):
        super(ExampleAdderDeviceHandle, self).__init__(*args, **kwargs)
        self._srv = rospy.Service('add_two_ints', AddTwoInts, self.on_service_req)

    def on_service_req(self, req):
        can_req = struct.pack('Bhh', 37, req.a, req.b)
        self.send_data(can_req)
        res_format = 'Bi'
        can_res = self.request_data(struct.calcsize(res_format))
        flag, my_sum = struct.unpack(res_format, can_res)
        if flag != 37:
            return -1
        return my_sum


class ThrusterKillBoardHandle(CANDeviceHandle):
    '''
    CANDevice handle which can send 'kill' and 'go' messages and
    receive status from the thruster kill board

    '''
    def __init__(self, *args, **kwargs):
        super(ThrusterKillBoardHandle, self).__init__(*args, **kwargs)
        self.timer = rospy.Timer(rospy.Duration(1.0), self.test_cb)

    def soft_kill(self, asserted):
        '''
        Sends message to kill/unkill the thrusters.
        @param asserted: boolean to specify whether to kill (true) or unkill (false)
        '''
        assertByte = tkb.ASSERTED if asserted else tkb.UNASSERTED
        killCommand = struct.pack('5B', tkb.KILL_MESSAGE, tkb.COMMAND, tkb.SOFT_KILL, assertByte, tkb.END)
        self.send_data(killCommand)

    def send_thruster_msg(self, thruster, value):
        '''
        @param thruster: the thruster (0-7) to control (use Thrusters class)
        @param value: value to send to the thruster (between -1 and 1, where 0 is full stop)
        '''
        thrusterCommand = struct.pack('2Bf', tkb.THRUSTER_MESSAGE, thruster, value)
        self.send_data(thrusterCommand)

    def get_kill_status(self):
        print self.request_data(5)

    def get_go_status(self):
        try:
            print self.request_data(3)
        except:
            pass

    def test_cb(self, *args):
        self.soft_kill(True)
        self.send_thruster_msg(ThrusterID.FHL, -1)
        self.send_thruster_msg(ThrusterID.FHR, 1)
        self.send_thruster_msg(ThrusterID.BVR, 0.234)
        self.get_go_status()
        # self.get_kill_status()
