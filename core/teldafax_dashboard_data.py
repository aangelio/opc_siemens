import time

import snap7
import struct

class PlcRemoteUse():
    """
    class for connect to PLC Siemens
    public functions:
    get_out - read out bit in PLC
    tear_down - remove connection
    get_status_all_bit_in_byte - get status bits in byte
    get_bit - get bit in byte
    change_bit - change bit in byte (if 0 ->1, if 1->0)
    set_bit - set bit to hight
    reset_bit - set bit to low
    get_data - read data from PLC
    get_value - read data from PLC with ghost to number

    """

    def __init__(self, address, rack, slot, port=102):
        """
        :param address: ip plc
        :param rack: rack plc in hardware
        :param slot: slot plc in hardware
        db_read parameter DB in PLC from were read byte
        """
        self.client = snap7.client.Client()  # формирование обращения к соединению
        self.client.set_connection_type(3)
        self.client.connect(address, rack,
                            slot,
                            tcpport=port)  # подключение к контроллеру. Adress - IP адресс. Rack, slot - выставляються/смотрятся в TIA portal
        self.ves = 0
        self.dataRead = 0
        self.db_read = 3
        self.db_write = 10

    def get_out(self, byte, bit):  # метод для получения выхода контроллера
        """
        :param byte: byte address
        :param bit: bit address
        :return:

        """
        out = self.client.ab_read(int(byte), 1)
        value = int.from_bytes(out[0:1], byteorder='little', signed=True)
        bits = bin(value)
        bits = bits.replace("0b", "")
        if (len(bits) < 8):
            for i in range(8 - len(bits)):
                bits = "0" + bits
        bits = bits[::-1]
        try:
            status = bits[bit]
        except:
            status = 0
        return status

    def is_connected(self):
        return self.client.get_connected()

    def tear_down(self):  # отключение
        self.client.disconnect()
        self.client.destroy()


    def get_data(self, db_read, startDB, endDB):  # получение данных в байт формате
        """
        :param db_read: DB in PLC from were read data
        :param startDB: start address in DB
        :param endDB: offset from startDB
        :return:

        """
        try:
            data_read = self.client.db_read(db_read, startDB, endDB)
            return data_read
        except:
            return False

    def disassemble_float(self, data):  # метод для преобразования данных в real
        val = struct.unpack('>f', data)
        return val[0]

    def disassemble_double(self, data):  # метод для преобразования данных в bigint
        val = struct.unpack('>d', data)
        return val[0]

    def disassemble_int(self, data):  # метод для преобразования данных в int
        return int.from_bytes(data, "big")

    def transform_data_to_value(self, start, offset, data, type):
        """преобразование полученных данных из байт в значение"""
        end = int(start) + int(offset)
        try:
            if (type == 'int'):
                result = self.disassemble_int(data[int(start):int(end)])
            elif (type == 'real'):
                result = self.disassemble_float(data[int(start):int(end)])
            elif (type == 'double'):
                result = self.disassemble_int(data[int(start):int(end)])
            else:
                result = 'error type'
        except Exception as e:
            raise Exception('error disassemble %s' % type)
        else:
            return result

    def transform_data_to_bit(self, offset, bit, data):
        """получение статуса бита в прочитанном массиве данных"""
        value = int.from_bytes(data[int(offset):int(offset) + 1], byteorder='little', signed=True)
        bits = bin(value)
        bits = bits.replace("0b", "")
        bits = bits[::-1]
        try:
            status = bits[bit]
        except:
            status = 0
        return status

    def get_value(self, db_read, startDB, endDB,
                  type) -> int or float:  # получение значения с преобразование к величине
        """
        метод получения згначения из DB PLC

        :param db_read: DB in PLC from were read data
        :param startDB:  start address in DB
        :param endDB: offset from startDB
        :param str type: type variable (int,real,dint)
        :return:

        """
        try:
            data_read = self.client.db_read(db_read, startDB, endDB)
            if (type == 'int'):
                result = self.disassemble_int(data_read)
            elif (type == 'real'):
                result = self.disassemble_float(data_read)
            elif (type == 'double'):
                result = self.disassemble_int(data_read)
            else:
                result = 'error type'
            return result
        except:
            return False

    def get_dashboard_teldafax_value_power(self, db=300, start=0, offset=84):
        try:
            data_read = self.client.db_read(db, start, offset)
            power1 = self.transform_data_to_value(60, 4, data_read, 'real')
            power2 = self.transform_data_to_value(64, 4, data_read, 'real')
            power3 = self.transform_data_to_value(68, 4, data_read, 'real')
            power4 = self.transform_data_to_value(72, 4, data_read, 'real')
            sum_power = self.transform_data_to_value(80, 4, data_read, 'real')
            powers = {"power1": power1, 'power2': power2, 'power3': power3, 'power4': power4, 'sum_power': sum_power}
            return powers
        except:
            return {"error":"Нет связи с плк"}

    def get_status_machine(self, db=3001, start=5714, offset=141):
        try:
            work_status = self.get_value(64, 4, 2, 'int')
            time.sleep(0.01)
            data_read = self.client.db_read(db, start, offset)
            pump_p301_status = 3 & int.from_bytes(data_read[114:1], byteorder='little', signed=True)
            valve_B1101_status = int.from_bytes(data_read[108:1], byteorder='little', signed=True)
            valve_B1601_status = int.from_bytes(data_read[110:1], byteorder='little', signed=True)

            compres_V501_status = int.from_bytes(data_read[0:1], byteorder='little', signed=True)
            compres_V502_status = int.from_bytes(data_read[16:1], byteorder='little', signed=True)
            compres_V503_status = int.from_bytes(data_read[32:1], byteorder='little', signed=True)

            generator_D601_status1 = 7 & int.from_bytes(data_read[116:1], byteorder='little', signed=True)
            generator_D601_status2 = 24 & int.from_bytes(data_read[116:1], byteorder='little', signed=True)
            generator_D602_status1 = 7 & int.from_bytes(data_read[122:1], byteorder='little', signed=True)
            generator_D602_status2 = 24 & int.from_bytes(data_read[122:1], byteorder='little', signed=True)
            generator_D603_status1 = 7 & int.from_bytes(data_read[128:1], byteorder='little', signed=True)
            generator_D603_status2 = 24 & int.from_bytes(data_read[128:1], byteorder='little', signed=True)
            generator_D604_status1 = 7 & int.from_bytes(data_read[134:1], byteorder='little', signed=True)
            generator_D604_status2 = 24 & int.from_bytes(data_read[134:1], byteorder='little', signed=True)

            fakel_A604 = int.from_bytes(data_read[140:1], byteorder='little', signed=True) #😀
            statuses = {
                'work_status': work_status,
                'pump_p301_status': pump_p301_status,
                'valve_B1101_status': valve_B1101_status,
                'valve_B1601_status': valve_B1601_status,
                'compres_V501_status': compres_V501_status,
                'compres_V502_status': compres_V502_status,
                'compres_V503_status': compres_V503_status,
                'generator_D601_status1': generator_D601_status1,
                'generator_D601_status2': generator_D601_status2,
                'generator_D602_status1': generator_D602_status1,
                'generator_D602_status2': generator_D602_status2,
                'generator_D603_status1': generator_D603_status1,
                'generator_D603_status2': generator_D603_status2,
                'generator_D604_status1': generator_D604_status1,
                'generator_D604_status2': generator_D604_status2,
                'fakel_A604': fakel_A604
            }
            return statuses
        except:
            return {"error":"Нет связи с плк"}
