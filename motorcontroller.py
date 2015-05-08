import RPi.GPIO as GPIO
import time
import threading
 
class MotorController:
        def __init__(self, pwm_freq=500, default_speed=50, timeout_delay=.1):
                self.timeout_delay = timeout_delay
                self._commands = LockingBuffer()
                self.SetCommands = self._commands.SetBuffer #Expose this for incoming commands
                #Guess we don't need to store the pwm_freq or default_speed since each motor saves its own
               
                GPIO.cleanup()
                GPIO.setmode(GPIO.BOARD)
               
                # 1:Left Forward 2:Left Reverse 4:Right Forward 8:Right Reverse
                names = {1:23, 2:21, 4:26, 8:24}
                self.motorDict = {}
                for n,p in names.items():
                        GPIO.setup(p,GPIO.OUT)
                        self.motorDict[n] = Motor(p,pwm_freq,default_speed)
               
                print('  --- Motors Initialized ---')

        def RunThreaded(self):
                t = threading.Thread()
                t.setDaemon(True) #daemon allows this thread to die when the main thread exits
                t.run=self.Run
                t.start()
 
        def Run(self):

                print('Motor control started...')
                
                while True:
                        currentTime = time.time()
         
                        #Get commands from buffer
                        commands = self._commands.ReadBuffer()
         
                        #Update timeout times
                        for c, m in self.motorDict.items():
                                if commands & c:
                                        m.timeout_time = currentTime + self.timeout_delay

                                if m.timeout_time > currentTime:
                                        m.TurnOn()
                                else:
                                        m.TurnOff()
                       
class Motor:
        def __init__(self, pin, freq, speed):
                self.pwm = GPIO.PWM(pin,freq)
                self.pin = pin
                self.speed = speed
                self.timeout_time = 0
               
        def TurnOn(self):
                self.pwm.start(self.speed)
               
        def TurnOff(self):
                self.pwm.stop()
                       
class LockingBuffer:
        def __init__(self):
                self._buflock = threading.Lock()
                self._buf = 0
               
        def ReadBuffer(self):
                self._buflock.acquire()
                commands = self._buf
                self._buf = 0
                self._buflock.release()
                return commands
       
        def SetBuffer(self, command):
                self._buflock.acquire()
                self._buf = command
                self._buflock.release()