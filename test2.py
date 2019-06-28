import RPi.GPIO as GPIO
import time
import spidev
import threading
class ADSTest2:
    outputlst=[11,18,16]
    input1=32
    CS=11
    DRDY=32
    START=18
    PDR=16
    RDATA=None
    spi=None
    y=None
    WR=[0x40]
    RR=[0x20]
    ID=[0x00]
    CONFIG1=[0x01]
    CONFIG2=[0x02]
    CH1=[0x04]
    CH2=[0x05]
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.outputlst,GPIO.OUT)
        GPIO.setup(self.input1,GPIO.IN)
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)
        self.spi.max_speed_hz=4000000
        self.spi.mode = 0b01
    def readR(self):
        self.reset()
        time.sleep(0.1)
        self.StartOFF()
        time.sleep(0.1)
        self.StartON()
        time.sleep(0.1)
        GPIO.output(self.CS,False)
        time.sleep(0.02)
        self.spi.xfer2([0x11])
        time.sleep(0.02)
        GPIO.output(self.CS,True)
        time.sleep(0.02)
        GPIO.output(self.CS,False)
        time.sleep(0.1)
        print(self.spi.xfer2([0x20,0x00]))
        time.sleep(0.02)
        GPIO.output(self.CS,True)
    def reset(self):
        GPIO.output(self.PDR,True)
        time.sleep(0.1)
        GPIO.output(self.PDR,False)
        time.sleep(0.01)
        GPIO.output(self.PDR,True)
        time.sleep(0.1)
        
    def StartOFF(self):
        GPIO.output(self.START,False)
        time.sleep(0.02)

    def StartON(self):
        GPIO.output(self.START,True)
        time.sleep(0.02)

a=ADSTest2()
a.readR()















        
