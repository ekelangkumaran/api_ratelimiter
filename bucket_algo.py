import time


class TokenBucket:

    def __init__(self, tokens, time_unit, forward_callback, drop_callback):
        self.tokens = tokens
        self.time_unit = time_unit
        self.forward_callback = forward_callback
        self.drop_callback = drop_callback
        self.bucket = tokens
        self.last_check = time.time()

    def handle(self, packet):
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current
        
        self.bucket = self.bucket + \
            time_passed * (self.tokens / self.time_unit)
        #filling the bucket with the number of tokens that can fit in the elapsed time
        print("current time: {} time passed: {} bucket: {}".format(current,time_passed,self.bucket,self.tokens))
        
        if (self.bucket > self.tokens):
            #Normalise the bucket to make sure it doesnt exceed its usual limit 
            self.bucket = self.tokens

        if (self.bucket < 1):
            #bucket is empty
            self.drop_callback(packet)
        else:
            self.bucket = self.bucket - 1
            self.forward_callback(packet)


def forward(packet):
    print("Packet Forwarded: " + str(packet))


def drop(packet):
    print("Packet Dropped: " + str(packet))


throttle = TokenBucket(2, 10, forward, drop)

packet = 0

#while True:
#    time.sleep(0.2)
#    throttle.handle(packet)
#    packet += 1
time.sleep(2)
throttle.handle(packet)
time.sleep(9)
throttle.handle(packet)

