import RPi.GPIO as GPIO
import threading
import time
import spidev
#import threading
from datetime import datetime
import smbus
import dbus
from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor
# Register Read Commands
RREG  =  0x20       #Read n nnnn registers starting at address r rrrr
                                #first byte 001r rrrr (2xh)(2) - second byte 000n nnnn(2)
WREG  =  0x40       #Write n nnnn registers starting at address r rrrr
                                #first byte 010r rrrr (2xh)(2) - second byte 000n nnnn(2)
START       = 0x08      #Start/restart (synchronize) conversions
STOP        = 0x0A      #Stop conversion
RDATAC      = 0x10      #Enable Read Data Continuous mode.

#This mode is the default mode at power-up.
SDATAC      = 0x11      #Stop Read Data Continuously mode
RDATA       = 0x12      #Read data by command; supports multiple read back.

#Pin declartion the other you need are controlled by the SPI library
DRDY_PIN = 32   #GPIO 12
CS_PIN = 11     #GPIO 17
START_PIN = 18  #GPIO 24
PWDN_PIN = 16   #GPIO 23

#register address
REG_ID          = 0x00
REG_CONFIG1     = 0x01
REG_CONFIG2     = 0x02
REG_LOFF        = 0x03
REG_CH1SET      = 0x04
REG_CH2SET      = 0x05
REG_RLDSENS     = 0x06
REG_LOFFSENS            = 0x07
REG_LOFFSTAT            = 0x08
REG_RESP1           = 0x09
REG_RESP2           = 0x0A

#SPI Setup
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 10000000
spi.mode = 0b01

# I2C channel 1 is connected to the GPIO pins
channel = 1

#  MCP4725 defaults to address 0x60
address = 0x48

# Register addresses (with "normal mode" power-down bits)
reg_write_dac = 0x40

# Initialize I2C (SMBus)
bus = smbus.SMBus(channel)
Vlsb=0.01953125
#setting the GATT service
GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 20

def main():
    ECGstartup()
    BLEconnection=Application()
    BLEconnection.add_service(ECGPPGService(0))
    BLEconnection.register()

    BLEadvertise=ECGPPGAdvertisement(0)
    BLEadvertise.register()

    try:
        BLEconnection.run()
    except KeyboardInterrupt:
        BLEconnection.quit()



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



def ECGstartup():
    GPIOsetup()      #start the gpio connection
    Reset()
    time.sleep(0.1)
    Disable_Start()
    Enable_Start()

    Hard_Stop()
    Start_Data_Conv_Command()
    Soft_Stop()
    time.sleep(0.05)
    Stop_Read_Data_Continuous() # SDATAC command
    time.sleep(0.3)

    Reg_Read(REG_ID)
    time.sleep(0.01)
    print("if the REGID is not 115, please check the ads connection")
    Reg_Write(REG_CONFIG1, 0x00000110)      #Set sampling rate to 500 SPS
    time.sleep(0.01)
    Reg_Write(REG_CONFIG2, 0b10100000)  #Lead-off comp off, test signal disabled
    time.sleep(0.01)
    Reg_Write(REG_LOFF, 0b00010000)     #Lead-off defaults
    time.sleep(0.01)
    Reg_Write(REG_CH1SET, 0b10000000)   #Ch 1 enabled, gain 6, test signal
    time.sleep(0.01)
    Reg_Write(REG_CH2SET, 0b01100000)   #Ch 2 enabled, gain 12, test signal
    time.sleep(0.01)
    Reg_Write(REG_RLDSENS, 0b00000000)  #RLD settings: fmod/16, RLD enabled, RLD inputs from Ch2 only
    time.sleep(0.01)
    Reg_Write(REG_LOFFSENS, 0x00000000)     #LOFF settings: all disabled
    time.sleep(0.01)
                                                        #Skip register 8, LOFF Settings default
    Reg_Write(REG_RESP1, 0b00000010)        #Respiration: MOD/DEMOD turned only, phase 0
    time.sleep(0.01)
    Reg_Write(REG_RESP2, 0b00000011)        #Respiration: Calib OFF, respiration freq defaults
    time.sleep(0.01)
    Reg_Read(REG_CH1SET)
    time.sleep(0.01)
    Reg_Read(REG_CH2SET)
    time.sleep(0.01)
    Start_Read_Data_Continuous()
    time.sleep(0.01)
    Enable_Start()

def SPI_Command_Data(data_in):
    GPIO.output(CS_PIN, False)
    time.sleep(0.002)
    GPIO.output(CS_PIN, True)
    time.sleep(0.002)
    GPIO.output(CS_PIN, False)
    time.sleep(0.002)
    spi.writebytes([data_in])
    time.sleep(0.002)
    GPIO.output(CS_PIN, True)

def Start_Data_Conv_Command():
    SPI_Command_Data(START) # Send 0x08 to the ADS1x9x

def Soft_Stop():
    SPI_Command_Data(STOP) # Send 0x0A to the ADS1x9x

def Start_Read_Data_Continuous():
    SPI_Command_Data(RDATAC) # Send 0x10 to the ADS1x9x

def Stop_Read_Data_Continuous():
    SPI_Command_Data(SDATAC) # Send 0x11 to the ADS1x9x
def Start_Read_One_Time():
    SPI_Command_Data(START)
def Reg_Write(ADDRESS, DATA):
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
    spi.writebytes([0x00])     #number of register to wr
    spi.writebytes([DATA])     #Send value to record into register
    time.sleep(0.002)
    GPIO.output(CS_PIN, True)

def Reg_Read(ADDRESS):
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

def Reset():
    GPIO.output(PWDN_PIN, True)
    time.sleep(0.1)
    GPIO.output(PWDN_PIN, False)
    time.sleep(0.1)
    GPIO.output(PWDN_PIN, True)
    time.sleep(0.1)
def PowerDown():
    print('Powering Down')
    Disable_Start()
    Stop_Read_Data_Continuous()
    GPIO.output(PWDN_PIN, True)
    time.sleep(0.1)
    GPIO.output(PWDN_PIN, False)
    time.sleep(5)

def Disable_Start():
    GPIO.output(START_PIN, False)
    time.sleep(0.02)

def Enable_Start():
    GPIO.output(START_PIN, True)
    time.sleep(0.02)

def Hard_Stop ():
    GPIO.output(START_PIN, False)
    time.sleep(0.1)
def Read_Data():
        while True:
                if not GPIO.input(DRDY_PIN):
                        break
        GPIO.output(CS_PIN, False)
        lst=spi.readbytes(9)
        GPIO.output(CS_PIN, True)
        print(lst)
        Ch2=Process_Data(lst)
        #temp=self.Volt_To_Temp(Ch1)
        Volt_To_Temp(Ch2)
        print('ECG data is'+str(Ch2))
        return Ch2

def Process_Data(lst):
        '''Ch1=int(str("{0:08b}".format(int(lst[3])))+str("{0:08b}".format(int(lst[4])))+str("{0:08b}".format(int(lst[5]))),base=2)
        print(Ch1)
        temp=Ch1&0x800000
        if temp>=8388608:
            Ch1=Ch1-2**24
        Ch1=Ch1*(48.08*(10**(-9)))'''
        Ch2=int(str("{0:08b}".format(int(lst[6])))+str("{0:08b}".format(int(lst[7])))+str("{0:08b}".format(int(lst[8]))),base=2)
        print(Ch2)
        temp=Ch2&0x800000
        if temp>=8388608:
            Ch2=Ch2-2**24
        Ch2=(Ch2*(24.04*(10**(-9)))*100)**2
        return Ch2
def Volt_To_Temp(data):
        temp=(data*(10**6)-145300)/490+25
        print('temperature is'+str(temp))
        return temp
def PPGdata():
    bus.write_byte(address,reg_write_dac)
    value = bus.read_byte(address)
    value=float(value)*Vlsb
    print('PPG data is'+str(value))
    return value

class ECGPPGAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("ECGPPG")
        self.include_tx_power = True

class ECGPPGService(Service):
    ECGPPG_SVC_UUID = "00000001-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index):
        Service.__init__(self, index, self.ECGPPG_SVC_UUID, True)
        self.add_characteristic(ECGPPGCharacteristic(self))

class ECGPPGCharacteristic(Characteristic):
    ECGPPG_CHARACTERISTIC_UUID = "00000002-710e-4a5b-8d75-3e5b444bc3cf"
    ConditionKey=threading.Lock()
    breakflag=False
    p = None
    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(
                self, self.ECGPPG_CHARACTERISTIC_UUID,
                ["notify", "read"], service)
        self.add_descriptor(ECGPPGDescriptor(self))

    def get_ECGPPG_signal(self):
        while True:
            if not self.notifying:
                return
            DataStr=''
            clkbase=time.clock()
            for i in range(1000):
                clk=time.clock()-clkbase
                ecg=Read_Data()
                ppg=PPGdata()
                DataStr=DataStr+str(round(clk,5))+','+str(round(ecg,5))+','+str(round(ppg,5))+';'
                if not self.notifying:
                    return
            value=[]
            a=DataStr[:99]
            DataStr=DataStr[100:]
            a='h;'+a
            for c in a:
                value.append(dbus.Byte(c.encode()))
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
            time.sleep(0.05)
            pkgcounter=0
            while len(DataStr)!=0:
                value=[]
                if len(DataStr)>100:
                    a=DataStr[:99]
                    DataStr=DataStr[100:]
                else:
                    a=DataStr
                    DataStr=''
                if len(DataStr)==0:
                    a='t;'+a
                else:
                    a=str(pkgcounter)+';'+a
                for c in a:
                    value.append(dbus.Byte(c.encode()))
                if not self.notifying:
                    return
                #print('sending')
                self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
                pkgcounter=pkgcounter+1
                time.sleep(0.05)
            time.sleep(10)
            if not self.notifying:
                    break
    def set_ECGPPG_callback(self):
        if self.notifying:
            value = self.get_ECGPPG_signal()
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return
        print('start notify')
        self.notifying = True
        self.get_ECGPPG_signal()
        #self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        #self.add_timeout(NOTIFY_TIMEOUT, self.set_ECGPPG_callback)

    def StopNotify(self):
        self.notifying = False
    def ReadValue(self, options):
        #value = self.get_ECGPPG_signal()
        return 1
class ECGPPGDescriptor(Descriptor):
    ECGPPG_DESCRIPTOR_UUID = "2901"
    ECGPPG_DESCRIPTOR_VALUE = "ECG first, PPG second"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.ECGPPG_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.ECGPPG_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

main()