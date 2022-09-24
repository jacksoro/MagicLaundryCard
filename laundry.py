import time
import random
import datetime
import RPi.GPIO as GPIO


class laundrytool:
    
    def __init__(self):
        
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        
        
        self.GPIO_CS = 5
        self.GPIO_SCK = 3
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
        time.sleep(0.02)
        

        for i in range(framelen, 0, -1):
            
            bit = (frame >> (i-1)) & 0x01
            
            if bit:
                GPIO.output(self.GPIO_MOSI, GPIO.HIGH)
            else:
                GPIO.output(self.GPIO_MOSI, GPIO.LOW)
             
            time.sleep(0.001)
            self._clkpulse(0.001)
            
            if instruction == "READ" and i < 17:
                rbit = GPIO.input(self.GPIO_MISO)
                res = (res | (rbit<<(i-1))) & 0xFFFF
           
        
        GPIO.output(self.GPIO_MOSI, GPIO.LOW)
        time.sleep(0.02)
        GPIO.output(self.GPIO_CS, GPIO.LOW)
        time.sleep(0.02)
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
        
        for adr in range(64):
            r = self.execute_instruction("READ",adr,0)
            ret.append(r)
            print("checkmem:: read data= %s @ address= %s" % (hex(r), hex(adr)))
            
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
            print(adr)
            
        self.execute_instruction("EWDS")  

print("slep!")
time.sleep(13)
print("go!")
obj = laundrytool()
obj.magic_sequence(100)
newdat = obj.readall()
print("done!")

#obj.spi.close()



