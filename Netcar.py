import select
import socket
import pickle

import pygame
from pygame.locals import *
pygame.init()
pygame.event.set_allowed(QUIT)

black = 0,0,0
white = 255,255,255

class CarClient:
    def __init__(self, car_ip=None, car_port=None, listen_port = 7001):
        self.car_ip = car_ip
        self.car_port = car_port
        self.listen_port = listen_port
        self._screen = pygame.display.set_mode((640, 480))
        
        # 1:Left Forward 2:Left Reverse 4:Right Forward 8:Right Reverse
        self.controls = {
            pygame.K_q : (1, (0, 0, 10, 10)),
            pygame.K_s : (2, (0, 470, 10, 480)),
            pygame.K_p : (4, (630, 0, 640, 10)),
            pygame.K_l : (8, (630, 470, 640, 480))
            }

    def _locateNetcar(self):
        print('Listening for Netcar on port', self.listen_port, '...')
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', self.listen_port))
        sock.setblocking(0)

        while not self.car_ip and not self.car_port:
            result = select.select([sock],[],[])
            msg, addr = result[0][0].recvfrom(1024)
            msg = bytes.decode(msg)
            if msg: print(msg)
            if msg and msg.startswith('Netcar:'):
                self.car_ip = addr[0]
                self.car_port = int(msg.split(':')[1])
        sock.close()
    
    def run(self):
        if not self.car_ip or not self.car_port:
            self._locateNetcar()
                
        print('Connecting: ', self.car_ip, str(self.car_port))
        carSock = socket.socket()
        carSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        carSock.connect((self.car_ip, self.car_port))
        print('Connected!')

        while True:
            if pygame.event.get(QUIT):
                carSock.close()
                pygame.quit()
                return 1            

            self._screen.fill(black) #todo (maybe): fetch the camera image
            
            keys = pygame.key.get_pressed()
            command = 0
            for c in self.controls:
                if keys[c]:
                    command |= self.controls[c][0]
                    self._screen.fill(white, self.controls[c][1])

            carSock.send(command.to_bytes(1,byteorder='big'))
            
            pygame.display.flip()
            pygame.time.delay(10)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser('Netcar control client')
    parser.add_argument('-s', '--server', type=str, help='Netcar service ip')
    parser.add_argument('-p', '--port', type=int, help='Netcar service port')

    args = parser.parse_args()

    client = CarClient(args.server, args.port)
    client.run()