import time
import random
import datetime
import RPi.GPIO as GPIO
import sys

class laundrytool:
    
    def __init__(self):
        
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        
        
        self.GPIO_CS = 5
        self.GPIO_SCK = 13
        self.GPIO_MOSI = 7
        self.GPIO_MISO = 11
        
        GPIO.setup(self.GPIO_CS,GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.GPIO_SCK,GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.GPIO_MOSI,GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.GPIO_MISO,GPIO.IN)
        
        
        self.opcodes = {
        "EWDS" : 0x4,
        "EWEN" : 0x4,
        "READ" : 0x6,
        "WRITE" : 0x5,
        }   

        self.enabled_for_write = False


    def check_gpios(self):

        GPIO.setup(self.GPIO_MISO,GPIO.OUT)
        for t in range(100000):
                
            GPIO.output(self.GPIO_MOSI, GPIO.LOW)
            GPIO.output(self.GPIO_CS, GPIO.LOW)
            GPIO.output(self.GPIO_SCK, GPIO.LOW)
            GPIO.output(self.GPIO_MISO, GPIO.LOW)

            time.sleep(0.05)

            GPIO.output(self.GPIO_MOSI, GPIO.HIGH)
            GPIO.output(self.GPIO_CS, GPIO.HIGH)
            GPIO.output(self.GPIO_SCK, GPIO.HIGH)
            GPIO.output(self.GPIO_MISO, GPIO.HIGH)


            time.sleep(0.05)

        GPIO.setup(self.GPIO_MISO,GPIO.IN)



    def execute_instruction(self, instruction, address=0, data=0):
        
        address &= 0x3F
        data &= 0xFFFF
        
        if instruction is "EWEN":
            address = 0x30
            
            
        opcode = self.opcodes[instruction]

        frame = (opcode << 6 | address) & 0x1FF
        framelen = 9
        res=0
        
        if instruction == "READ" or instruction == "WRITE":
            frame = (frame << 16 | data) & 0x1FFFFFF
            framelen = 25
        
        
        
        GPIO.output(self.GPIO_CS, GPIO.HIGH)
        time.sleep(0.01)
        

        for i in range(framelen, 0, -1):
            
            bit = (frame >> (i-1)) & 0x01
            
            if bit:
                GPIO.output(self.GPIO_MOSI, GPIO.HIGH)
            else:
                GPIO.output(self.GPIO_MOSI, GPIO.LOW)
             
            time.sleep(0.001/2)
            self._clkpulse(0.001/2)
            
            if instruction == "READ" and i < 17:
                rbit = GPIO.input(self.GPIO_MISO)
                res = (res | (rbit<<(i-1))) & 0xFFFF
           
        
        GPIO.output(self.GPIO_MOSI, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(self.GPIO_CS, GPIO.LOW)
        time.sleep(0.01)
        return res

        
    def _clkpulse(self, stime=0.1):
    
            GPIO.output(self.GPIO_SCK, GPIO.HIGH)
            time.sleep(stime)
            GPIO.output(self.GPIO_SCK, GPIO.LOW)
            
    def _enable_write_operation(self, enable=True):
        
        if enable:
            self.execute_instruction("EWEN")
            self.enabled_for_write = True
            print("Write enabled")
        else:
            self.execute_instruction("EWDS")
            self.enabled_for_write = False
            print("Write disabled")
                
    def readall(self):
        ret = []
        check = []
        
        for adr in range(64):
            r = self.execute_instruction("READ",adr,0)
            ret.append(r)
            print("checkmem:: read data= %s @ address= %s" % (hex(r), hex(adr)))
        
        print("\n")
        
        adrl = [7,9,11,18,20,21]
        for adr in adrl:
            check.append(ret[adr])
        if len(set(check)) == 1:
            print("Adress set is coherent (%s)" % str(check[0]))
        else:
            print("Adress set is NOT coherent")
        

            
        return ret

    def checkmem(self):
        
        
        print("memcheck test ongoing...")
        self._enable_write_operation(True)
        
        testvect = []#constrct test vector 
        for adr in range(64):
            testvect.append(random.randint(0,0xFFFF))
            self.execute_instruction("WRITE",adr,testvect[adr])
            print("checkmem:: write data= %s @ address= %s" % (hex(testvect[adr]), hex(adr)))
            
        self._enable_write_operation(False)
        
        mem = self.readall()
        
        if (mem == testvect):
            print("memcheck test sucessful!")
            return True
        else:
            print("memcheck test failed!")
            return False
         
         
    def magic_sequence(self,tune=30):
        
        tune*=100
        
        adrl = [7,9,11,18,20,21]
        
        self.execute_instruction("EWEN")
        
        for adr in adrl:
            self.execute_instruction("WRITE",adr,tune)
        
            r = self.execute_instruction("READ",adr,0)
            if r == tune:
                print("%s...ok" % str(adr))
            else:
                print("%s...error" % str(adr))
                
            
        self.execute_instruction("EWDS")  




args = sys.argv[1:]
obj = laundrytool()

if args[0] == '-r':
    print("presleep! -> setup card connection for dump")
    time.sleep(12)
    print("go!")
    dump = obj.readall()
    print(dump)
    
elif args[0] == '-w':
    newsolde = args[1]
    print("presleep! -> setup card connection for write (%s CHF)" % newsolde)
    time.sleep(12)
    print("go!")
    obj.magic_sequence(int(newsolde))

elif args[0] == '-t':
    obj.check_gpios()
    
else:
    raise Exception("Not valid input args")


print("done!")





