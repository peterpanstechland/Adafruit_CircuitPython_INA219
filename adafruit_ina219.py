from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice

from adafruit_register.i2c_struct import ROUnaryStruct, UnaryStruct
from adafruit_register.i2c_bits import ROBits, RWBits
from adafruit_register.i2c_bit import ROBit

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_INA219.git"

_REG_CONFIG                 = const(0x00)

class BusVoltageRange:
    RANGE_16V               = 0x00      # set bus voltage range to 16V
    RANGE_32V               = 0x01      # set bus voltage range to 32V (default)

class Gain:
    DIV_1_40MV              = 0x00      # shunt prog. gain set to  1, 40 mV range
    DIV_2_80MV              = 0x01      # shunt prog. gain set to /2, 80 mV range
    DIV_4_160MV             = 0x02      # shunt prog. gain set to /4, 160 mV range
    DIV_8_320MV             = 0x03      # shunt prog. gain set to /8, 320 mV range

class ADCResolution:
    ADCRES_9BIT_1S          = 0x00      #  9bit,   1 sample,     84us
    ADCRES_10BIT_1S         = 0x01      # 10bit,   1 sample,    148us
    ADCRES_11BIT_1S         = 0x02      # 11 bit,  1 sample,    276us
    ADCRES_12BIT_1S         = 0x03      # 12 bit,  1 sample,    532us
    ADCRES_12BIT_2S         = 0x09      # 12 bit,  2 samples,  1.06ms
    ADCRES_12BIT_4S         = 0x0A      # 12 bit,  4 samples,  2.13ms
    ADCRES_12BIT_8S         = 0x0B      # 12bit,   8 samples,  4.26ms
    ADCRES_12BIT_16S        = 0x0C      # 12bit,  16 samples,  8.51ms
    ADCRES_12BIT_32S        = 0x0D      # 12bit,  32 samples, 17.02ms
    ADCRES_12BIT_64S        = 0x0E      # 12bit,  64 samples, 34.05ms
    ADCRES_12BIT_128S       = 0x0F      # 12bit, 128 samples, 68.10ms

class Mode:
    POWERDOW                = 0x00      # power down
    SVOLT_TRIGGERED         = 0x01      # shunt voltage triggered
    BVOLT_TRIGGERED         = 0x02      # bus voltage triggered
    SANDBVOLT_TRIGGERED     = 0x03      # shunt and bus voltage triggered
    ADCOFF                  = 0x04      # ADC off
    SVOLT_CONTINUOUS        = 0x05      # shunt voltage continuous
    BVOLT_CONTINUOUS        = 0x06      # bus voltage continuous
    SANDBVOLT_CONTINUOUS    = 0x07      # shunt and bus voltage continuous

_REG_SHUNTVOLTAGE           = const(0x01)

_REG_BUSVOLTAGE             = const(0x02)

_REG_POWER                  = const(0x03)

_REG_CURRENT                = const(0x04)

_REG_CALIBRATION            = const(0x05)


def _to_signed(num):
    if num > 0x7FFF:
        num -= 0x10000
    return num

class INA219:

    def __init__(self, i2c_bus, addr=0x40):
        self.i2c_device = I2CDevice(i2c_bus, addr)
        self.i2c_addr = addr

        self._cal_value = 0
        self._current_lsb = 0
        self._power_lsb = 0
        self.set_calibration_32V_2A()

    reset                   = RWBits( 1, _REG_CONFIG, 15, 2, False)
    bus_voltage_range       = RWBits( 1, _REG_CONFIG, 13, 2, False)
    gain                    = RWBits( 2, _REG_CONFIG, 11, 2, False)
    bus_adc_resolution      = RWBits( 4, _REG_CONFIG,  7, 2, False)
    shunt_adc_resolution    = RWBits( 4, _REG_CONFIG,  3, 2, False)
    mode                    = RWBits( 3, _REG_CONFIG,  0, 2, False)

    raw_shunt_voltage       = ROUnaryStruct(_REG_SHUNTVOLTAGE, ">h")

    raw_bus_voltage         = ROBits( 12, _REG_BUSVOLTAGE, 3, 2, False)
    conversion_ready        = ROBit(      _REG_BUSVOLTAGE, 1, 2, False)
    overflow                = ROBit(      _REG_BUSVOLTAGE, 0, 2, False)
    raw_power               = ROUnaryStruct(_REG_POWER, ">H")
    raw_current             = ROUnaryStruct(_REG_CURRENT, ">h")
    _raw_calibration        = UnaryStruct(_REG_CALIBRATION, ">H")

    @property
    def calibration(self):
        return self._cal_value # return cached value

    @calibration.setter
    def calibration(self, cal_value):
        self._cal_value = cal_value # value is cached for ``current`` and ``power`` properties
        self._raw_calibration = self._cal_value

    @property
    def shunt_voltage(self):
        return self.raw_shunt_voltage * 0.00001

    @property
    def bus_voltage(self):
        return self.raw_bus_voltage * 0.004

    @property
    def current(self):
        self._raw_calibration = self._cal_value
        return self.raw_current * self._current_lsb

    @property
    def power(self):
        self._raw_calibration = self._cal_value
        return self.raw_power * self._power_lsb

    def set_calibration_32V_2A(self): # pylint: disable=invalid-name
        self._current_lsb = .1  # Current LSB = 100uA per bit
        self._cal_value = 12412
        self._power_lsb = .002  # Power LSB = 2mW per bit
        self._raw_calibration = self._cal_value
        self.bus_voltage_range = BusVoltageRange.RANGE_32V
        self.gain = Gain.DIV_8_320MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.mode = Mode.SANDBVOLT_CONTINUOUS

    def set_calibration_32V_1A(self): # pylint: disable=invalid-name
        self._current_lsb = 0.04 # In milliamps
        self._cal_value = 31030
        self._power_lsb = 0.0008
        self._raw_calibration = self._cal_value
        self.bus_voltage_range = BusVoltageRange.RANGE_32V
        self.gain = Gain.DIV_8_320MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.mode = Mode.SANDBVOLT_CONTINUOUS

    def set_calibration_16V_400mA(self): # pylint: disable=invalid-name
        self._current_lsb = 0.05  # in milliamps
        self._cal_value = 24824
        self._power_lsb = 0.001
        self._raw_calibration = self._cal_value
        self.bus_voltage_range = BusVoltageRange.RANGE_16V
        self.gain = Gain.DIV_1_40MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.mode = Mode.SANDBVOLT_CONTINUOUS
