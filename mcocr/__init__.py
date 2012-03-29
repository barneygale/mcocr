import font
import screenshot
import sys

if __name__ == '__main__':
	f = font.Font()
	s = screenshot.Screenshot(sys.argv[1], f)
	print s.text
	#print s.colours
	#print s.get_coords_positions()
