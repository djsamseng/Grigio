import smbus
import struct
import time

class RomiMotorController:
  def __init__(self):
    self.bus = smbus.SMBus(1)

  def __write(self, address, format, *data):
    data_array = list(struct.pack(format, *data))
    self.bus.write_i2c_block_data(20, address, data_array)
    time.sleep(0.0001)

  def set_motors(self, left, right):
    self.__write(6, 'hh', left, right)

