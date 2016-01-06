# glitchy

Written by: Ciro Durán <ciro.duran@gmail.com>

Inspired by: Yole Quintero

## Description

This README contains the description and usage of the glitchy scripts.

This repository contains several scripts written for Python 2.7 that deal with image file format glitching.

glitch_png.py is inspired by [UCNV's work](http://ucnv.github.io/pnglitch/). By using Python hopefully this work can be easily used by OS X owners who already have Python 2.7 pre-installed.

## Usage

	usage: glitch_png.py [-h] [--glitch [N]] [--seed [SEED]]
						[--use_source_filters] [--use_random_filters]
						[--use_filter F] [--glitch_chance [%]]
						filename
	
	Reads a PNG file and writes it back glitched.
	
	positional arguments:
	filename              image filename
	
	optional arguments:
	-h, --help            show this help message and exit
	--glitch [N]          glitches data while storing PNG, writes N files
	--seed [SEED]         uses this value as random seed
	--use_source_filters  if source file is PNG, it will used the filters for
							each line from the source. Otherwise will filter to
							its own accord. If source is not PNG this value is not
							used.
	--use_random_filters  it will use random filters when writing to PNG. Not
							used if --use_source_filters is specified.
	--use_filter F        use this specific filter (0-4) for all lines
	--glitch_chance [%]   chance between 0.0-1.0 of applying glitch
 
## Example

This is an example of using png_glitch.py. The original image is on the right, and the glitched image is on the left. The image comes from the [USC-SIPI Image Database](http://sipi.usc.edu/database/database.php?volume=misc&image=14).

![Example of png_glitch.py](http://i.imgur.com/ZZuGGof.png)

Command line used for this image: `glitch_png.py 4.2.06.png --glitch 1 --use_source_filters --glitch_chance 0.99`

