import sys
import binascii
import math
import zlib

def inflate(ba):
	return bytearray(zlib.decompress(bytes(ba), 32))

def deflate(ba):
	return zlib.compress(ba)[2:-4]
	
def byte_to_int(ba, starting_index, num_bytes = 4):
	si = starting_index;
	result = 0;
	
	for i in xrange(num_bytes):
		result |= ba[si+i] << ((num_bytes - 1 - i) * 8)
	return result

def get_bytes_per_pixel(color_type, bit_depth):
	ct = color_type
	bd = bit_depth
	
	if ct == 0:		# Grayscale
		if bd == 1:
			return 1
		elif bd == 2:
			return 1
		elif bd == 4:
			return 1
		elif bd == 8:
			return 1
		elif bd == 16:
			return 2
	elif ct == 2:	# Truecolor
		if bd == 8:
			return 3
		if bd == 16:
			return 6
	elif ct == 3:	# Indexed
		if bd == 1:
			return 1
		elif bd == 2:
			return 1
		elif bd == 4:
			return 1
		elif bd == 8:
			return 1
	elif ct == 4:	# Grayscale and alpha
		if bd == 8:
			return 2
		if bd == 16:
			return 4
	elif ct == 6:	# Truecolor and alpha
		if bd == 8:
			return 4
		if bd == 16:
			return 8
	
	# Fallback case
	error_message = "Invalid combination of color type (%d) and bit depth (%d)" % (ct, bd)
	return error_message
	
def get_bytes_per_line(color_type, bit_depth, width):
	ct = color_type
	bd = bit_depth
	
	if ct == 0:		# Grayscale
		if bd == 1:
			return int(math.ceil(width / 8)) + 1
		elif bd == 2:
			return int(math.ceil(width / 4)) + 1
		elif bd == 4:
			return int(math.ceil(width / 2)) + 1
		elif bd == 8:
			return width + 1
		elif bd == 16:
			return width * 2 + 1
	elif ct == 2:	# Truecolor
		if bd == 8:
			return width * 3 + 1
		if bd == 16:
			return width * 6 + 1
	elif ct == 3:	# Indexed
		if bd == 1:
			return int(math.ceil(width / 8)) + 1
		elif bd == 2:
			return int(math.ceil(width / 4)) + 1
		elif bd == 4:
			return int(math.ceil(width / 2)) + 1
		elif bd == 8:
			return width + 1
	elif ct == 4:	# Grayscale and alpha
		if bd == 8:
			return width * 2 + 1
		if bd == 16:
			return width * 4 + 1
	elif ct == 6:	# Truecolor and alpha
		if bd == 8:
			return width * 4 + 1
		if bd == 16:
			return width * 8 + 1
	
	# Fallback case
	error_message = "Invalid combination of color type (%d) and bit depth (%d)" % (ct, bd)
	return error_message

def break_in_scanlines(ba, bytes_per_line):
	r = []
	
	for i in range(0, len(ba), bytes_per_line):
		raw_scanline = ba[i : i + bytes_per_line]
		filter_type = raw_scanline[0]
		scanline = raw_scanline[1:]
		r.append((filter_type, scanline))
	return r

def paeth_predictor(left, up, corner):
	result = None
	p = left + up - corner
	pleft	= abs(p - left)
	pup		= abs(p - up)
	pcorner	= abs(p - corner)
	if pleft <= pup and pleft <= pcorner:
		result = left
	elif pup <= pcorner:
		result = up
	else:
		result = corner
	return result

def unfilter(ba, bytes_per_pixel, bytes_per_line, height):
	filter_type_scanline_tuple_list = break_in_scanlines(ba, bytes_per_line)
	
	if len(filter_type_scanline_tuple_list) != height:
		return "Invalid content (content size: %d, width: %d, height: %d, scanlines produced: %d)" % (len(ba), width, height, len(filter_type_scanline_tuple_list))
	
	scanlines_recon = []
	
	for scanline_number, (filter_type,scanline_filtered) in enumerate(filter_type_scanline_tuple_list):
		#print "Scanline number: %d, filter_type: %d" % (scanline_number, filter_type)
		if filter_type == 0:	# None
			scanline_recon = scanline_filtered
		elif filter_type == 1:	# Sub
			scanline_recon = bytearray()
			for i in range(len(scanline_filtered)):
				recon_left = 0 if i < bytes_per_pixel else scanline_recon[-bytes_per_pixel]
				scanline_recon.append((recon_left + scanline_filtered[i]) % 256)
		elif filter_type == 2:	# Up
			if scanline_number == 0:	# The above line is all zeroes
				scanline_recon = scanline_filtered
			else:
				scanline_recon = [((i + j) % 256) for i, j in zip(scanline_raw[-1], scanline_filtered)]
		elif filter_type == 3:	# Average
			scanline_recon = bytearray()
			for i in range(len(scanline_filtered)):
				recon_left = 0 if i < bytes_per_pixel else scanline_recon[-bytes_per_pixel]
				recon_up = 0 if scanline_number == 0 else scanlines_recon[-1][i]
				recon = (scanline_filtered[i] + int(math.floor((recon_left + recon_up) / 2))) % 256
				#print "byte: %d, filtered: %d, recon_left: %d, recon_up: %d, recon: %d" % (i, scanline_filtered[i], recon_left, recon_up, recon)
				scanline_recon.append(recon)
		elif filter_type == 4:	# Paeth
			scanline_recon = bytearray()
			for i in range(len(scanline_filtered)):
				recon_left = 0 if i < bytes_per_pixel else scanline_recon[-bytes_per_pixel]
				recon_up = 0 if scanline_number == 0 else scanlines_recon[-1][i]
				recon_corner = 0 if (i < bytes_per_pixel or scanline_number == 0) else scanlines_recon[-1][i - bytes_per_pixel]
				scanline_recon.append((scanline_filtered[i] + paeth_predictor(recon_left, recon_up, recon_corner)) % 256)
		else:
			return "Invalid scanline filter type (line: %d, type: %d)" % (scanline_number, filter_type)
		
		scanlines_recon.append(scanline_recon)
	
	return [item for sublist in scanlines_recon for item in sublist] # Flatten array of arrays

def get_chunks(ba):
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
		
		chunk_length = byte_to_int(chunk_len_arr, 0, 4)
		
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
		
		chunk_crc = byte_to_int(chunk_crc_arr, 0, 4)
		
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
	
	return chunks
	
def get_image_header(chunks, image_data):
	if len(chunks) == 0 or chunks[0].get("name") != "IHDR":
		return "No IHDR chunk found"
		
	ihdr_chunk = chunks[0]
	
	image_data["width"]					= byte_to_int(ihdr_chunk["contents"], 0, 4)
	image_data["height"]				= byte_to_int(ihdr_chunk["contents"], 4, 4)
	image_data["bit_depth"]				= byte_to_int(ihdr_chunk["contents"], 8, 1)
	image_data["color_type"]			= byte_to_int(ihdr_chunk["contents"], 9, 1)
	image_data["compression_method"]	= byte_to_int(ihdr_chunk["contents"], 10, 1)
	image_data["filter_method"]			= byte_to_int(ihdr_chunk["contents"], 11, 1)
	image_data["interlace_method"]		= byte_to_int(ihdr_chunk["contents"], 12, 1)
	
	if image_data["compression_method"] != 0:
		return "Compression method different than zero"
	
	if image_data["filter_method"] != 0:
		return "Filter method different than zero"
		
	if image_data["interlace_method"] != 0:
		return "Interlace method different than zero"
		
	ct = image_data["color_type"]
	bd = image_data["bit_depth"]
	bpp = get_bytes_per_pixel(ct, bd)
	
	if isinstance(bpp, basestring):
		return bpp
	
	bpl = get_bytes_per_line(ct, bd, image_data["width"]) # Includes extra byte for filter type
	
	if isinstance(bpl, basestring):
		return bpl
		
	image_data["bytes_per_pixel"] = bpp
	image_data["bytes_per_line"] = bpl

def get_image_data(chunks, image_data):
	image_contents_compressed = bytearray([])
	
	for c in chunks:
		if c["name"] != "IDAT":
			continue
		image_contents_compressed.extend(c["contents"])
	
	image_contents = inflate(image_contents_compressed)
	image_scanlines = unfilter(image_contents, image_data["bytes_per_pixel"], image_data["bytes_per_line"], image_data["height"])
	
	if isinstance(image_scanlines, basestring):
		return image_scanlines
		
	image_data["raw_data"] = image_scanlines

def read_png(filename):
	fr = open(filename, 'rb')
	ba = None
	try:
		ba = bytearray(fr.read())
	finally:
		fr.close()
	fr.close()
	
	chunks_or_error_string = get_chunks(ba)
	
	if isinstance(chunks_or_error_string, basestring):
		return chunks_or_error_string
	
	chunks = chunks_or_error_string
	image_data = dict({})
	
	error_string = get_image_header(chunks, image_data)
	
	if error_string is not None:
		return error_string
	
	error_string = get_image_data(chunks, image_data)
	
	if error_string is not None:
		return error_string
	
	print "Image is %dx%d" % (image_data["width"], image_data["height"])
	
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