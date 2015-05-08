import socket
import threading
import pickle
from time import sleep
import motorcontroller

class CarService:
    def __init__(self, port, broadcast_port, announce_interval, verbosity=0):
        self.port = port
        self.broadcast_port = broadcast_port
        self.announce_interval = announce_interval
        self.verbosity = verbosity
        
        self._motor_control = motorcontroller.MotorController()
        
    def run(self):

        if self.verbosity:
            print('Starting Service...')

        self._motor_control.RunThreaded()

        if self.verbosity:
            print('Listening on port', self.port)
        
        self._client = socket.socket()
        self._client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._client.bind(('', self.port))
        self._client.listen(1)

        if self.broadcast_port > 0 and self.announce_interval > 0:
            self._broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            t = threading.Thread()
            t.setDaemon(True)
            t.run=self.announce
            t.start()

        sleep(1)

        while True:
            if self.verbosity:
                print('waiting for connection...')
                
            conn, addr = self._client.accept()

            if self.verbosity:
                print(str(addr) + ' connected!')
            
            while True:
                data = conn.recv(256)

                if not data: break

                command = 0
                for b in data:
                    command |= b

                if self.verbosity >= 2:
                    print(command)
                    
                self._motor_control.SetCommands(command)
                
            conn.close()
                

    def announce(self):

        if self.verbosity:
            print('Announcing on port ' + str(self.broadcast_port))

        while True:
            msg = 'Netcar:'+str(self.port)
            
            if self.verbosity >= 2:
                print(msg)

            try:
                msg = str.encode(msg)
                self._broadcast.sendto(msg, ('255.255.255.255', self.broadcast_port))

                sleep(self.announce_interval)
                    
            except Exception as ex:
                print(ex)
                return
    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Netcar control service')
    parser.add_argument('-p', '--port', type=int, default=7000, help='Port for Netcar client connections')
    parser.add_argument('-a', '--announceport', type=int, default=7001, help='Port to announce this Netcar service on')
    parser.add_argument('-i', '--interval', type=int, default=15, help='Interval in seconds to announce the service on the network')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase output verbosity')

    args=parser.parse_args()
    
    service = CarService(args.port, args.announceport, args.interval, args.verbose)
    service.run()