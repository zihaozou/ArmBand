import RPi.GPIO as GPIO
import time
import spidev
import threading
from datetime import datetime
from matplotlib import pyplot
from matplotlib.animation import FuncAnimation
import bluetooth
import time
import random

CONFIG_SPI_MASTER_DUMMY   = 0xFF

# Register Read Commands
RREG  =  0x20		#Read n nnnn registers starting at address r rrrr
                                #first byte 001r rrrr (2xh)(2) - second byte 000n nnnn(2)
WREG  =  0x40		#Write n nnnn registers starting at address r rrrr
                                #first byte 010r rrrr (2xh)(2) - second byte 000n nnnn(2)
START		= 0x08		#Start/restart (synchronize) conversions
STOP		= 0x0A		#Stop conversion
RDATAC      = 0x10		#Enable Read Data Continuous mode.

#This mode is the default mode at power-up.
SDATAC		= 0x11		#Stop Read Data Continuously mode
RDATA		= 0x12		#Read data by command; supports multiple read back.

#Pin declartion the other you need are controlled by the SPI library
DRDY_PIN = 32   #GPIO 12
CS_PIN = 11     #GPIO 17
START_PIN = 18  #GPIO 24
PWDN_PIN = 16   #GPIO 23

#register address
REG_ID			= 0x00
REG_CONFIG1		= 0x01
REG_CONFIG2		= 0x02
REG_LOFF		= 0x03
REG_CH1SET		= 0x04
REG_CH2SET		= 0x05
REG_RLDSENS		= 0x06
REG_LOFFSENS            = 0x07
REG_LOFFSTAT            = 0x08
REG_RESP1	        = 0x09
REG_RESP2	        = 0x0A

#SPI Setup
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 10000000
spi.mode = 0b01

def GPIOsetup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(PWDN_PIN, GPIO.OUT)
    GPIO.setup(CS_PIN, GPIO.OUT)
    GPIO.setup(START_PIN, GPIO.OUT)
    GPIO.setup(DRDY_PIN, GPIO.IN)

def GPIOcleanup():
    GPIO.output(PWDN_PIN, GPIO.LOW)
    GPIO.output(CS_PIN, GPIO.LOW)
    GPIO.output(START_PIN, GPIO.LOW)
    GPIO.cleanup()                     # Release resource

class ADS:
    VREF = 2.42
    #figue = pyplot.figure()
    #ax= figue.add_subplot(111)
    #i=0
    #x_data, y_data = [], []
    def __init__(self):
        GPIOsetup()

    def setup_connection(self):
        self.server_socket=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
        port = 1
        self.server_socket.bind(("",port))
        self.server_socket.listen(1)
        print "Waiting for connection..."
        self.client_socket,address = self.server_socket.accept()
        print "Accepted connection from ",address
    def send_data(self, message):
        self.client_socket.send(message)
    def close(self):
        self.client_socket.close()
        self.server_socket.close()
    def receive_data(self):
        data = self.client_socket.recv(1024)
        print "Received data is: ", data
        return data
        
    def Initiate(self):
        self.Reset()
        time.sleep(0.1)
        self.Disable_Start()
        self.Enable_Start()
        
        self.Hard_Stop()
        self.Start_Data_Conv_Command()
        self.Soft_Stop()
        time.sleep(0.05)
        self.Stop_Read_Data_Continuous() # SDATAC command
        time.sleep(0.3)
        
        self.Reg_Read(REG_ID)
        time.sleep(0.01)
        
        self.Reg_Write(REG_CONFIG1, 0x00000110) 		#Set sampling rate to 500 SPS
        time.sleep(0.01)
        self.Reg_Write(REG_CONFIG2, 0b11100000)	#Lead-off comp off, test signal disabled
        time.sleep(0.01)
        self.Reg_Write(REG_LOFF, 0b00010000)		#Lead-off defaults
        time.sleep(0.01)
        self.Reg_Write(REG_CH1SET, 0b10000000)	#Ch 1 enabled, gain 6, test signal
        time.sleep(0.01)
        self.Reg_Write(REG_CH2SET, 0b01100000)	#Ch 2 enabled, gain 12, test signal
        time.sleep(0.01)
        self.Reg_Write(REG_RLDSENS, 0b00000000)	#RLD settings: fmod/16, RLD enabled, RLD inputs from Ch2 only
        time.sleep(0.01)
        self.Reg_Write(REG_LOFFSENS, 0x00101100)		#LOFF settings: all disabled
        time.sleep(0.01)
                                                            #Skip register 8, LOFF Settings default
        self.Reg_Write(REG_RESP1, 0b00000010)		#Respiration: MOD/DEMOD turned only, phase 0
        time.sleep(0.01)
        self.Reg_Write(REG_RESP2, 0b00000011)		#Respiration: Calib OFF, respiration freq defaults
        time.sleep(0.01)
        self.Reg_Read(REG_CH1SET)
        time.sleep(0.01)
        self.Reg_Read(REG_CH2SET)
        time.sleep(0.01)
        self.Start_Read_Data_Continuous()
        time.sleep(0.01)
        self.Enable_Start()
        self.setup_connection()
        
    def Reset(self):
        GPIO.output(PWDN_PIN, True)
        time.sleep(0.1)
        GPIO.output(PWDN_PIN, False)
        time.sleep(0.1)
        GPIO.output(PWDN_PIN, True)
        time.sleep(0.1)
    def PowerDown(self):
        print('Powering Down')
        self.Disable_Start()
        self.Stop_Read_Data_Continuous()
        GPIO.output(PWDN_PIN, True)
        time.sleep(0.1)
        GPIO.output(PWDN_PIN, False)
        time.sleep(5)

    def Disable_Start(self):
        GPIO.output(START_PIN, False)
        time.sleep(0.02)

    def Enable_Start(self):
        GPIO.output(START_PIN, True)
        time.sleep(0.02)

    def Hard_Stop (self):
        GPIO.output(START_PIN, False)
        time.sleep(0.1)

    def SPI_Command_Data(self, data_in):
        GPIO.output(CS_PIN, False)
        time.sleep(0.002)
        GPIO.output(CS_PIN, True)
        time.sleep(0.002)
        GPIO.output(CS_PIN, False)
        time.sleep(0.002)
        spi.writebytes([data_in])
        time.sleep(0.002)
        GPIO.output(CS_PIN, True)

    def Start_Data_Conv_Command(self):
        self.SPI_Command_Data(START) # Send 0x08 to the ADS1x9x

    def Soft_Stop(self):
        self.SPI_Command_Data(STOP) # Send 0x0A to the ADS1x9x

    def Start_Read_Data_Continuous(self):
        self.SPI_Command_Data(RDATAC) # Send 0x10 to the ADS1x9x

    def Stop_Read_Data_Continuous(self):
        self.SPI_Command_Data(SDATAC) # Send 0x11 to the ADS1x9x

    def Reg_Write(self, ADDRESS, DATA):
        if ADDRESS == 1:
            DATA = DATA & 0x87
        if ADDRESS == 2:
            DATA = DATA & 0xFB
            DATA |= 0x80
        if ADDRESS == 3:
            DATA = DATA & 0xFD
            DATA |= 0x10
        if ADDRESS == 7:
            DATA = DATA & 0x3F
        if ADDRESS == 8:
            DATA = DATA & 0x5F
        if ADDRESS == 9:
            DATA |= 0x02
        if ADDRESS == 10:
            DATA = DATA & 0x87
            DATA |= 0x01
        if ADDRESS == 11:
            DATA = DATA & 0x0F

        #now combine the register address and the command into one byte
        dataToSend = ADDRESS | WREG
        GPIO.output(CS_PIN, False)
        time.sleep(0.002)
        GPIO.output(CS_PIN, True)
        time.sleep(0.002)
        GPIO.output(CS_PIN, False)
        time.sleep(0.002)
        spi.writebytes([dataToSend]) #Send register location
        spi.writebytes([0x00])	   #number of register to wr
        spi.writebytes([DATA])	   #Send value to record into register
        time.sleep(0.002)
        GPIO.output(CS_PIN, True)
        
    def Reg_Read(self,ADDRESS):
        COMMAND=ADDRESS|RREG
        GPIO.output(CS_PIN, False)
        time.sleep(0.002)
        GPIO.output(CS_PIN, True)
        time.sleep(0.002)
        GPIO.output(CS_PIN, False)
        time.sleep(0.002)
        spi.writebytes([COMMAND])
        spi.writebytes([0x00])
        result=spi.readbytes(1)
        time.sleep(0.002)
        GPIO.output(CS_PIN, True)
        print(result)
        
    def Read_Data(self):
        while True:
                if not GPIO.input(DRDY_PIN):
                        break
        GPIO.output(CS_PIN, False)
        lst=spi.readbytes(9)
        GPIO.output(CS_PIN, True)
        print(lst)
        Ch1,Ch2=self.Process_Data(lst)
        #temp=self.Volt_To_Temp(Ch1)
        self.Volt_To_Temp(Ch2)
        print('Channel 1 data is'+str(Ch1)+',Channel 2 data is'+str(Ch2))
        return Ch1,Ch2
    def Read_Data_times(self):
        while 1:
                rcvd = self.receive_data()
                if rcvd == "Start":
                        break
        f=open("testresult.txt",'w')
        while True:
            while True:
                if not GPIO.input(DRDY_PIN):
                        q,p=self.Read_Data()
                        q=str(q)
                        p=str(p)
                        f.write(p+'\n')
                        self.send_data(p)
                        while 1:
                                recv1=self.receive_data()
                                if recv1 == "Ch2OK":
                                        break
                        break
        f.close()
    def twosCom_binDec(self,bin, digit):
        while len(bin)<digit :
                bin = '0'+bin
        if bin[0] == '0':
                return int(bin, 2)
        else:
                return -1 * (int(''.join('1' if x == '0' else '0' for x in bin), 2) + 1)

    def twosCom_decBin(self,dec, digit):
        if dec>=0:
                bin1 = bin(dec).split("0b")[1]
                while len(bin1)<digit :
                        bin1 = '0'+bin1
                return bin1
        else:
                bin1 = -1*dec
                return bin(dec-pow(2,digit)).split("0b")[1]
    def Process_Data(self,lst):
        Ch1=int(str("{0:08b}".format(int(lst[3])))+str("{0:08b}".format(int(lst[4])))+str("{0:08b}".format(int(lst[5]))),base=2)
        print(Ch1)
        temp=Ch1&0x800000
        if temp>=8388608:
            Ch1=Ch1-2**24
        Ch1=Ch1*(48.08*(10**(-9)))
        Ch2=int(str("{0:08b}".format(int(lst[6])))+str("{0:08b}".format(int(lst[7])))+str("{0:08b}".format(int(lst[8]))),base=2)
        print(Ch2)
        temp=Ch2&0x800000
        if temp>=8388608:
            Ch2=Ch2-2**24
        Ch2=Ch2*(24.04*(10**(-9)))*100
        return Ch1,Ch2
    def Volt_To_Temp(self,data):
        temp=(data*(10**6)-145300)/490+25
        print('temperature is'+str(temp))
        return temp
    
        
        
        
t1 = ADS()
t1.Initiate()
t1.Read_Data_times()
#animation = FuncAnimation(t1.figue, t1.update, interval=0.001)
#pyplot.show()
t1.PowerDown()
spi.close()
GPIOcleanup()
