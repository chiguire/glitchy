import sys
import binascii
import math
import zlib
import os
import random
import time
import argparse

def inflate(ba):
	return bytearray(zlib.decompress(str(ba), 32))

def deflate(ba):
	return bytearray(zlib.compress(str(ba), 9))
	
def byte_to_int(ba, starting_index, num_bytes = 4):
	si = starting_index;
	result = 0;
	
	for i in xrange(num_bytes):
		result |= ba[si+i] << ((num_bytes - 1 - i) * 8)
	return result
	
def int_to_byte(ba, value, num_bytes = 4):
	for i in range(num_bytes):
		n = int((value >> ((num_bytes - 1 - i) * 8)) & 0xff)
		ba.append(n)

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
	
def filter(image_data, use_previously_used_filters = False):
	if use_previously_used_filters and image_data.get("filter_types_used") is None:
		use_previously_used_filters = False
	
	if use_previously_used_filters:
		print "Using previously used filters"
	
	ba = []
	width = image_data["width"]
	bpp = image_data["bytes_per_pixel"]
	data = image_data["raw_data"]
	random_seed = int(time.time())
	random.seed(random_seed)
	#print "Random seed %d" % random_seed
	
	if use_previously_used_filters:
		filter_types = image_data["filter_types_used"]
	else:
		selected_filter_type = 1 #random.randint(1, 4)
	
	for i in range(0, len(data), width * bpp):
		scanline_number = int(i/(width*bpp))
		
		#print "In byte %d accessing scanline_number %d" % (i, scanline_number)
		
		if use_previously_used_filters:
			filter_type = filter_types[scanline_number]
		else:
			filter_type = selected_filter_type
		
		#print "Scanline number: %d, filter_type: %d" % (scanline_number, filter_type)
		
		ba_line = bytearray()
		ba_line.append(filter_type)
		line_original = data[i:i+width * bpp]
		line_filtered = bytearray()
		
		if filter_type == 0:	# None
			line_filtered.extend(line_original)
			#for j in range(len(line_filtered)):
			#	if random.random() > 0.5:
			#		line_filtered[j] = (line_filtered[j] + 127) % 256
		elif filter_type == 1:	# Sub
			for j in range(len(line_original)):
				recon_left = 0 if j < bpp else line_original[j - bpp]
				filtered = (256 + line_original[j] - recon_left) % 256
				line_filtered.append(filtered)
		elif filter_type == 2:	# Up
			if scanline_number == 0:	# The above line is all zeroes
				line_filtered.extend(line_original)
			else:
				line_filtered.extend([((256 + (j - i)) % 256) for i, j in zip(ba[-1][1:], line_original)])
		elif filter_type == 3:	# Average
			line_up = data[i-(width*bpp):i]
			for j in range(len(line_original)):
				recon_left = 0 if j < bpp else line_original[j - bpp]
				recon_up = 0 if scanline_number == 0 else line_up[j]
				recon = (256 + line_original[j] - int(math.floor((recon_left + recon_up) / 2))) % 256
				#print "filtered byte: %s, original byte: %s, original: %s, orig_left: %s, orig_up: %s, filtered: %s" % (hex((width*bpp+1)*scanline_number+j+1), hex(width*bpp*scanline_number+j), hex(line_original[j]), hex(recon_left), hex(recon_up), hex(recon))
				line_filtered.append(recon)
		elif filter_type == 4:	# Paeth
			line_up = data[i-(width*bpp):i]
			for j in range(len(line_original)):
				recon_left = 0 if j < bpp else line_original[j - bpp]
				recon_up = 0 if scanline_number == 0 else line_up[j]
				recon_corner = 0 if (j < bpp or scanline_number == 0) else line_up[j - bpp]
				line_filtered.append((256 + (line_original[j] - paeth_predictor(recon_left, recon_up, recon_corner))) % 256)
		
		ba_line.extend(line_filtered)
		
		#print "Scanline length: " + str(len(ba_line))
		ba.append(ba_line)
	
	#print "Final ext: " + str(len(ba))
	return bytearray([item for sublist in ba for item in sublist])
	

def unfilter(ba, bytes_per_pixel, bytes_per_line, height):
	filter_type_scanline_tuple_list = break_in_scanlines(ba, bytes_per_line)
	
	if len(filter_type_scanline_tuple_list) != height:
		return "Invalid content (content size: %d, height: %d, scanlines produced: %d)" % (len(ba), height, len(filter_type_scanline_tuple_list))
	
	scanlines_recon = []
	filter_type_list = []
	
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
				#print "filtered byte: %s, original byte: %s, filtered: %s, recon_left: %s, recon_up: %s, recon: %s" % (hex((1024*3+1)*scanline_number+i+1), hex(1024*3*scanline_number+i), hex(scanline_filtered[i]), hex(recon_left), hex(recon_up), hex(recon))
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
		
		filter_type_list.append(filter_type)
		scanlines_recon.append(scanline_recon)
	
	return (bytearray([item for sublist in scanlines_recon for item in sublist]), filter_type_list) # Flatten array of arrays

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
		
		chunk_length_cursor = cursor
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
		#print "CRC is " + str(chunk_crc)
		
		computed_crc = binascii.crc32(ba[chunk_name_cursor:chunk_name_cursor+4+chunk_length]) & 0xffffffff
		
		if computed_crc != chunk_crc:
			return "Failed CRC (0x%x != 0x%x)(byte 0x%x)" % (chunk_crc, computed_crc, cursor)
		
		print "Appending %d-byte %s chunk" % (chunk_length, chunk_name)
		chunks.append({
			"length":		chunk_length,
			"name":			chunk_name,
			"contents":		chunk_contents,
			"crc":			chunk_crc,
			"raw_chunk":	ba[chunk_length_cursor:chunk_length_cursor + chunk_length + 12]
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
	image_scanlines, filter_types_used = unfilter(image_contents, image_data["bytes_per_pixel"], image_data["bytes_per_line"],	image_data["height"])
	#print "Original data is %d bytes, filtered data is %d-bytes, compressed to %d bytes" % (len(image_scanlines), len(image_contents), len(image_contents_compressed))
	
	if isinstance(image_scanlines, basestring):
		return image_scanlines
	
	#compressed_contents = deflate(image_contents)
	#compressed_contents_len = len(compressed_contents)
	#bytes_differ = 0
	#for a, b in zip(image_contents_compressed, compressed_contents):
	#	if a != b:
	#		bytes_differ += 1
	#print "Recompressed data is %d bytes, differs from original in %d bytes" % (compressed_contents_len, bytes_differ)
	
	image_data["filtered_data"] = image_contents
	image_data["raw_data"] = image_scanlines
	image_data["filter_types_used"] = filter_types_used
	
	#filename, file_extension = os.path.splitext(image_data["filename"])
	#f = open(filename+"_filtered.bin", 'wb')
	#f.write(image_contents)
	#f.close()
	#f = open(filename+"_unfiltered.bin", 'wb')
	#f.write(image_scanlines)
	#f.close()
	
def get_IDAT_chunk(image_data, opts):
	if opts.has_key("--glitch_png") and opts["--glitch_png"]:
		pass #mess with filtered data
	else:
		chunk_contents = filter(image_data, True)
	
	compressed_contents = deflate(chunk_contents)
	compressed_contents_len = len(compressed_contents)
	
	#filename, file_extension = os.path.splitext(image_data["filename"])
	#f = open(filename+"_newly_filtered.bin", 'wb')
	#f.write(chunk_contents)
	#f.close()
	
	#print "Original data is %d bytes, filtered data is %d-bytes, compressed to %d bytes" % (len(image_data["raw_data"]), len(chunk_contents), compressed_contents_len)
	
	#bytes_differ = 0
	#bytes_differ_start = []
	#for n, (a, b) in enumerate(zip(image_data["filtered_data"], chunk_contents)):
	#	if a != b:
	#		bytes_differ += 1
	#		if len(bytes_differ_start) < 100:
	#			bytes_differ_start.append(n)
	#print "Newly filtered data differs from raw data in %d bytes, first 100 different bytes %s" % (bytes_differ, str([hex(j) for j in bytes_differ_start]))
	
	chunk_name_contents = bytearray("IDAT".encode("ascii"))
	chunk_name_contents.extend(compressed_contents)
	chunk_name_contents_crc = binascii.crc32(chunk_name_contents) & 0xffffffff
	#print "CRC is " + str(chunk_name_contents_crc)
	
	result = bytearray()
	int_to_byte(result, compressed_contents_len)
	result.extend(chunk_name_contents)
	int_to_byte(result, chunk_name_contents_crc)
	return result, compressed_contents_len
	

def read_png(filename):
	fr = open(filename, 'rb')
	
	ba = None
	try:
		ba = bytearray(fr.read())
	finally:
		fr.close()
	
	chunks_or_error_string = get_chunks(ba)
	
	if isinstance(chunks_or_error_string, basestring):
		return chunks_or_error_string
	
	chunks = chunks_or_error_string
	image_data = dict({})
	
	image_data["filename"] = filename
	
	error_string = get_image_header(chunks, image_data)
	
	if error_string is not None:
		return error_string
	
	error_string = get_image_data(chunks, image_data)
	
	if error_string is not None:
		return error_string
	
	image_data["chunks"] = chunks
	
	return image_data
	print "Image read succesfully. Dimensions are %dx%d." % (image_data["width"], image_data["height"])

# Returns a bytearray that represents a PNG image
def write_png(image_data, opts):
	ba = bytearray([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
	chunks = image_data["chunks"]
	wrote_IDAT_chunk = False
	
	for c in chunks:
		if c["name"] == "IDAT":
			if not wrote_IDAT_chunk:
				IDAT_chunk, length = get_IDAT_chunk(image_data, opts)
				ba.extend(IDAT_chunk)
				print "Writing %d-byte %s chunk" % (length, "IDAT")
				wrote_IDAT_chunk = True
			#else: ignore IDAT chunk
		else:
			if c["name"] == "IEND" and not wrote_IDAT_chunk:
				chunk_contents = filter(image_data, True)
				IDAT_chunk = get_IDAT_chunk(chunk_contents, opts)
				ba.extend(IDAT_chunk)
				wrote_IDAT_chunk = True
			else:
				print "Writing %d-byte %s chunk" % (c["length"], c["name"])
				ba.extend(c["raw_chunk"])
	return ba
	
def glitch_png(filename, image_data, opts):
	ba = write_png(image_data, opts)
	
	fr = open(filename, 'wb')
	try:
		fr.write(ba)
	finally:
		fr.close()
		print "Written image %s." % (filename)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Glitch PNGs.')
	parser.add_argument('filename', metavar='filename', help='image filename')
	parser.add_argument('--glitch_png', action='store_true', help='glitches filtered data')
	opts = parser.parse_args()
	
	filename = sys.argv[1]
	image_data = read_png(filename)
	
	if isinstance(image_data, basestring):
		print "Error reading %s: %s" % (filename, image)
		sys.exit(-1)
	
	filename, file_extension = os.path.splitext(filename)
	
	for i in xrange(1):
		glitch_png(filename+"_"+str(i)+file_extension, image_data, vars(opts))
	
	sys.exit(0)