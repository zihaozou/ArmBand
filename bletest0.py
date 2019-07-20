import bluetooth
import time
import random

class BLE:
	def __init__(self):
		self.setup_connection()

	def setup_connection(self):
		self.server_socket=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
		port = 1
		self.server_socket.bind(("",port))
		self.server_socket.listen(1)
		print "Waiting for connection..."
		self.client_socket,address = self.server_socket.accept()
		print "Accepted connection from ",address

	def receive_data(self):
		data = self.client_socket.recv(1024)
		print "Received data is: ", data
		return data
		
	def send_data(self, message):
		self.client_socket.send(message)
		
	def listen(self):
		while 1:
			rcvd = self.receive_data()
			if rcvd == "Start":
				for i in range(5):
					sdata = str(random.randint(1,101))
					print "Sending data: ", sdata
					self.send_data(sdata)
					time.sleep(1)
			else:
				print "Unknow Command!"
	
	def close(self):
		self.client_socket.close()
		self.server_socket.close()

b1 = BLE()
b1.listen()
b1.close()
	
 
 

