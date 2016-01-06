import sys
import random
import math

def make_glitch(filename, output):
	fr = open(filename, 'rb')
	ba = None
	try:
		ba = bytearray(fr.read())
	finally:
		fr.close()
	fr.close()
	
	glitches = random.randint(1, 100)
	
	glitch_count = dict()
	
	for i in range(glitches):
		glitch_type = random.randint(1, 3)
		size = random.randint(1, 3)
		byte = random.randint(math.ceil(len(ba)*1/4), len(ba) - size)
		if glitch_type == 1: # remove
			glitch_count["remove"] = glitch_count.get("remove",0) + 1
			for j in range(size):
				del ba[byte]
		elif glitch_type == 2: # zero
			glitch_count["zero"] = glitch_count.get("zero",0) + 1
			for j in range(size):
				ba[byte+j] = 0
		elif glitch_type == 3: # shift
			glitch_count["shift"] = glitch_count.get("shift",0) + 1
			for j in range(size):
				if ba[byte+j] == 255:
					ba[byte+j] = 0
				else:
					ba[byte+j] += 1
	
	print output + " count: " + ", ".join([k + ": "+ str(v) for k, v in glitch_count.iteritems()])
	
	fw = open(output, 'wb')
	fw.write(ba)
	fw.close()

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "Usage: " + sys.argv[0] + " [filename]"
		sys.exit(-1)
	filename = sys.argv[1]
	for i in range(10):
		make_glitch(filename, filename[:filename.rfind('.')] + ("_%s.jpg" % (str(i+1))))
	sys.exit(0)