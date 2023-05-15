import logging
import sys
from datetime import datetime
from astropy import units as u

from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse

logger = logging.getLogger('WS_utils')


# datetime object containing current date and time
def current_time():
    now = datetime.now().isoformat()
    return now


# synchronous client
def setup_sync_client():
    """Run client setup."""
    logger.info("### Create WS client object")
    try:
        client = ModbusTcpClient(
            host='10.1.101.77',       # IP address of the ExpertDAQ converter
            submask='255.255.255.0',  # Subnet mask of the network at LST1
            method='rtu',             # Modbus method configured for WS, also possible 'ascii'
            port=502,                 # Port address of the ExpertDAQ Serial port
            # Common optional paramers:
            framer=ModbusRtuFramer,   # important to correctly interpret RTU output
            #    timeout=10,
            #    retries=3,
            #    retry_on_empty=False,y
            #    close_comm_on_error=False,
            #    strict=True,
            # TCP setup parameters
            #    source_address=("localhost", 0),
        )
    except ValueError:
        logger.error('Error in client set up. Check client parameters.')
    return client


def connect_client(client):
    """Connection to modbus client"""
    try:
        # connect to device
        logger.info('### WS client starting')
        isClientConnected = client.connect()
        logger.info('### Connected to Modbus server')
    except ConnectionError as err:
        logger.error(f'Exception in pymodbus {err}')
        #print("Error ", err)
        sys.exit(1)
    return isClientConnected


def stop_client(client):
    """Stop modbus client"""
    logger.info('### WS client stopping')
    client.close()


def validator(instance, data_type=True):
    """Decode 32bit register"""
    if not instance.isError():
        decoder = BinaryPayloadDecoder.fromRegisters(
            instance.registers,
            byteorder=Endian.Big,
            #wordorder=Endian.Big
        )
        if not data_type:
            return decoder.decode_32bit_uint()
        else:
            return decoder.decode_32bit_int()
    else:
        # Error handling.
        logger.error('The register does not exist. Try again.')
        return None


def readInputRegisters(client, inputregister_dict, precipitationtype_dict):
    """
        Read multiple input registers.
        Returns:
            A list of tuples, the tuples contain a sensorID and its value.
    """
    logger.info('### Reading input registers')
    doc = {}  # create a new MongoDB document dict
    for key, value in inputregister_dict.items():
        try:
            rr = client.read_input_registers(address=key-30001, count=2, slave=1)
            logger.debug('### Input register read correctly')
        except ModbusException as exc:
            txt = f'Exception in pymodbus {exc}'
            logger.error(txt)
            raise exc
        if isinstance(rr, ExceptionResponse):
            txt = f'Received exception from device {rr}!'
            logger.error(txt)
            # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
            raise ModbusException(txt)
        if rr.isError():
            txt = f'Pymodbus returned an error: {rr}'
            logger.error(txt)
            raise ModbusException(txt)
        if rr == 0x7FFFFFFF or rr == 0xFFFFFFFF:
            logger.error(f'### Error detected, incorrect measured value: {rr}')

        data = validator(rr, data_type=value[3])
        if (key == 31407):  # precipitation type
            precipitation_type = int(data)
            for key_p, value_p in precipitationtype_dict.items():
                if (precipitation_type == int(key_p)):
                    print(f'Register {key}, {value[0]}: {value_p} \n')
                    doc.update({str(value[0]): value_p})
        elif (key == 31401):
            data = int(data)
            print(f'Register {key}, {value[0]}: {data} \n')
            doc.update({str(value[0]): data})
        elif (key == 34601):
            data = int(data)
            #data = datetime.strptime(str(data), '%Y%m%d').date()
            print(f'Register {key}, {value[0]}: {data} \n')
            doc.update({str(value[0]): data})
        elif (key == 34603):
            data = int(data)
            #data = datetime.strptime(str(data), '%H%M%S').time()
            print(f'Register {key}, {value[0]}: {data} \n')
            doc.update({str(value[0]): data})
        #elif (key == 30003 or key == 30019):  # convert wind measurement from m/s to km/h
        #    data_formatter = '.2f'
        #    data = data * 3.6
        #    print(f'Register {key}, {value[0]}: {data/value[1]:>{data_formatter}} km/h \n')
        else:
            print(f'Register {key}, {value[0]}: {data/value[1]} {value[2]} \n')
            doc.update({str(value[0]): data/value[1]})
    return doc


def readHoldingRegisters(client, holdingregister_dict):
    """Read multiple holding registers"""
    logger.info('### Reading holding registers')
    for key, value in holdingregister_dict.items():
        try:
            rr = client.read_holding_registers(address=key, count=2, slave=1)
            logger.debug('### Holding register read correctly')
        except ModbusException as exc:
            txt = f'Exception in pymodbus {exc}'
            logger.error(txt)
            raise exc
        if isinstance(rr, ExceptionResponse):
            txt = f'Received exception from device {rr}!'
            logger.error(txt)
            # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
            raise ModbusException(txt)
        if rr.isError():
            txt = f'Pymodbus returned an error: {rr}'
            logger.error(txt)
            raise ModbusException(txt)

        data = validator(rr)
        print(f'Register {key}, {value[0]}: {data} \n')


def writeHoldingRegister(client, address, value):
    """Write single holding register"""
    logger.info('### Writing holding register')
    try:
        builder = BinaryPayloadBuilder(byteorder=Endian.Big)
        builder.add_32bit_int(value)
        payload = builder.build()
        client.write_registers(address=address, values=payload, count=2, slave=1, skip_encode=True)
        logger.info('### Write of holding register successfull')
    except ModbusException as exc:
        txt = f'Exception in pymodbus {exc}'
        logger.error(txt)
        raise ModbusException(txt)


# to read true values, averaging must be switched off
#                      address   parameter name                   scaling                   unit                    signed
inputregister_dict = {  30003: ['Mean Wind Speed',                  10,                     u.km/u.h,               False],
                        30011: ['Gusts Velocity',                   10,                     u.km/u.h,               False],
                        30019: ['Average Wind Speed',              100,                     u.km/u.h,               False],
                        30203: ['Mean Wind Direction',              10,                         u.deg,              False],
                        30401: ['Air Temperature',                  10,                     u.Celsius,               True],
                        30409: ['Wind Chill Temperature',           10,                     u.Celsius,               True],
                        30411: ['Heat Index Temperature',           10,                     u.Celsius,               True],
                        30601: ['Relative Humidity',                10,                     u.percent,              False],
                        30605: ['Dew Point Temperature',            10,                     u.Celsius,               True],
                        30801: ['Absolute Air Pressure',           100,                         u.hPa,              False],
                        31001: ['Global Radiation',                 10,                 u.W/(u.m*u.m),               True],
                        31213: ['Brightness (kLux)',               10,                         u.klx,              False],
                        31223: ['Brightness (Lux)',                 1,                          u.lx,              False],
                        31401: ['Precipitation Status',              1,      u.dimensionless_unscaled,              False],
                        31403: ['Precipitation Intensity',        1000,                      u.mm/u.h,              False],
                        31405: ['Precipitation Amount',           1000,                      u.mm/u.d,              False],  # in a day
                        31407: ['Precipitation Type',                1,      u.dimensionless_unscaled,              False],
                        34601: ['Date',                              1,      u.dimensionless_unscaled,              False],
                        34603: ['Time',                              1,      u.dimensionless_unscaled,              False],
                        30403: ['Internal Temperature',             10,                     u.Celsius,              False],
                        34811: ['Wind Sensor Status',                1,      u.dimensionless_unscaled,              False],
                        34809: ['Height',                            1,                           u.m,               True],
                        #30021: ['True Wind',                                   10,     u.m/u.s,                    False,    4],
                        #30211: ['Wind Direction of the gust',                   10,     u.deg,                      False,    5],
                        #30213: ['True Wind Direction',                         10,     u.m/u.s,                    False,    7],
                        #30603: ['Absolute Humidity',                           100,     u.g/(u.m*u.m*u.m),          False,    12],
                        #30803: ['Relative Air Pressure',                       100,     u.hPa,                      False,    15],
                        #34801: ['Degree of longitude',                     1000000,     u.deg,                      True,     6],
                        #34803: ['Degree of latitude',                      1000000,     u.deg,                      True,     6],
                        #34805: ['Elevation Position Sun',                       10,     u.deg,                      True,     1],
                        #34807: ['Azimuth Position Sun',                         10,     u.deg,                      True,     1], 
                        }

precipitationtype_dict = {  0: 'No precipitation',
                            40: 'Precipitation present',
                            51: 'Light drizzle',
                            52: 'Moderate drizzle',
                            53: 'Heavy drizzle',
                            61: 'Light rain',
                            62: 'Moderate rain',
                            63: 'Heavy rain',
                            67: 'Light rain and/or drizzle with snow',
                            68: 'Moderate rain and/or drizzle with snow',
                            70: 'Snowfall',
                            71: 'Light snow',
                            72: 'Moderate snow',
                            73: 'Heavy snow',
                            74: 'Ice pallets',
                            89: 'Heavy hail',
                            }

#                       address                    description
holdingregister_dict = {40015: ['Averaging interval for wind speed and wind direction'],
                        40031: ['Parity',                                             ],
                        40005: ['Baud rate',                                          ],
                        40013: ['Command interpreter',                                ],
                        40011: ['Duplex mode',                                        ],
                        40023: ['Heating conditions',                                 ],
                        40025: ['Height setting',                                     ],
                        40027: ['Heating control',                                    ],
                        40003: ['Identification number',                              ],
                        40009: ['Set key / password',                                 ],
                        40029: ['Magnetic Compass correction, housing for sensor.',   ],
                        40017: ['North correction of the wind direction',             ],
                        #40033: ['Unit of wind speed',                                ],
                        #40035: ['Automatic synchronization with GPS',                ],
                        40253: ['Reset',                                              ],
                        40019: ['Station height in m above sea level',                ],
                        40007: ['Serial number',                                      ],
                        45005: ['Software version',                                   ],
                        40021: ['Time zone',                                          ],
                        45001: ['Thies aricle number',                                ],
                        }
