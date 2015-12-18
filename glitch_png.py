import sys
import binascii

def read_png(filename):
	fr = open(filename, 'rb')
	ba = None
	try:
		ba = bytearray(fr.read())
	finally:
		fr.close()
	fr.close()
	
	if len(ba) < 8:
		return "Invalid file size (0x%x bytes)" % (len(ba))
	
	# Check 8-byte signature
	if ba[:8] != bytearray([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]):
		return "Invalid PNG signature"
	
	# Start reading chunks
	cursor = 8
	chunks = []
	
	while cursor < len(ba):
		if cursor + 3 >= len(ba):
			return "Incomplete chunk, reading length (byte 0x%x)" % (cursor)
		chunk_len_arr = ba[cursor:cursor+4]
		
		chunk_length = chunk_len_arr[0] << 24 | chunk_len_arr[1] << 16 | chunk_len_arr[2] << 8 | chunk_len_arr[3]
		
		cursor = cursor + 4
		chunk_name_cursor = cursor
		
		if cursor + 3 >= len(ba):
			return "Incomplete chunk, reading name (byte 0x%x)" % (cursor)
		chunk_name_arr = ba[cursor:cursor+4]
		
		chunk_name = chunk_name_arr.decode("ascii")
		
		cursor = cursor + 4
		
		if cursor + chunk_length >= len(ba):
			return "Incomplete chunk, reading contents (byte 0x%x, reading %d bytes)" % (cursor, chunk_length)
		
		chunk_contents = ba[cursor:cursor+chunk_length]
		
		cursor = cursor + chunk_length
		
		if cursor + 3 >= len(ba):
			return "Incomplete chunk, reading crc (byte 0x%x)" % (cursor)
		
		chunk_crc_arr = ba[cursor:cursor+4]
		
		cursor = cursor + 4
		
		chunk_crc = chunk_crc_arr[0] << 24 | chunk_crc_arr[1] << 16 | chunk_crc_arr[2] << 8 | chunk_crc_arr[3]
		
		computed_crc = binascii.crc32(ba[chunk_name_cursor:chunk_name_cursor+4+chunk_length]) & 0xffffffff
		
		if computed_crc != chunk_crc:
			return "Failed CRC (0x%x != 0x%x)(byte 0x%x)" % (chunk_crc, computed_crc, cursor)
		
		print "Appending %d-byte %s chunk" % (chunk_length, chunk_name)
		chunks.append({
			"length":	chunk_length,
			"name":		chunk_name,
			"contents":	chunk_contents,
			"crc":		chunk_crc,
		})
	
if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "Usage: " + sys.argv[0] + " [filename]"
		sys.exit(-1)
	filename = sys.argv[1]
	image = read_png(filename)
	
	if isinstance(image, basestring):
		print "Error reading %s: %s" % (filename, image)
		sys.exit(-1)
	
	sys.exit(0)