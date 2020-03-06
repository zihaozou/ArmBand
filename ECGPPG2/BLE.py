import dbus
from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor
GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000

class ECGPPGAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("ECGPPG")
        self.include_tx_power = True
        
class ECGPPGService(Service):
    ECGPPG_SVC_UUID = "00000001-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index):
        Service.__init__(self, index, self.ECGPPG_SVC_UUID, True)
        self.add_characteristic(ECGCharacteristic(self))
        #self.add_characteristic(PPGCharacteristic(self))

class ECGCharacteristic(Characteristic):
    ECG_CHARACTERISTIC_UUID = "00000002-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(
                self, self.ECG_CHARACTERISTIC_UUID,
                ["notify", "read"], service)
        self.add_descriptor(ECGDescriptor(self))

    def get_ECG_signal(self):
        value=[]
        ECGsignal=0.101
        strtemp = str(ECGsignal)
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))
        return value

    def set_ECG_callback(self):
        if self.notifying:
            value = self.get_ECG_signal()
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = self.get_ECG_signal()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_ECG_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_ECG_signal()

        return value

class ECGDescriptor(Descriptor):
    ECG_DESCRIPTOR_UUID = "2901"
    ECG_DESCRIPTOR_VALUE = "ECG signal"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.ECG_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.ECG_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

BLEconnection=Application()
BLEconnection.add_service(ECGPPGService(0))
BLEconnection.register()

BLEadvertise=ECGPPGAdvertisement(0)
BLEadvertise.register()

try:
    BLEconnection.run()
except KeyboardInterrupt:
    BLEconnection.quit()


