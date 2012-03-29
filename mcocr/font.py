import os
import sys
import zipfile
import png
import array

from array2d import Array2D

colourize = lambda m, c: [m*(2*(1&c>>i)+(c>>3)) for i in range(2,-1,-1)]
colourize_bg = lambda c: colourize(21, c)
colourize_fg = lambda c: colourize(85, c) if c != 6 else [255, 170, 0]
bg_colours = [array.array('B', colourize_bg(i)) for i in range(16)]
fg_colours = [array.array('B', colourize_fg(i)) for i in range(16)]

white_pixel = array.array('B', (255,)*4)

#Computes the amount of error between two characters
#Params:
#1. Known character as Array2D
#2. Array2D, containing a character to check against at a given offset
#3. x offset
#4. current best error count. Used to stop prematurely if it's already 
#   obvious this is a poor match
#Returns:
#1. error count
#2. colour (0-15)
def char_match(a,b,xoffset,curbest):
    errors = 0
    colour = None
    if xoffset == 0 and a.width == b.width and a.height == b.height:
        #print "Fast check"
        for i in range(a.width*a.height):
            c = a.data[i]
            d = b.data[i]
            if (c & 0x20 != d & 0x20):
                errors += 1
                if errors >= curbest:
                    return errors, colour
            elif d & 0x30 == 0x20: #Foreground colour!
                colour = d & 0x0F
        return errors, colour

    for y0 in range(a.height):
        for x0 in range(a.width):
            c = a.get_pixel(x0, y0)[0] #Character
            d = b.get_pixel(x0+xoffset, y0)[0] #Buffer
            if (c & 0x20 != d & 0x20):
                errors += 1
                if errors >= curbest:
                    return errors, colour
            elif d & 0x30 == 0x20: #Foreground colour!
                colour = d & 0x0F
                
    return errors, colour

class Font:
    def __init__(self, **kargs):
        if len(kargs) < 2:
            if sys.platform == 'win32':
                appdata = os.environ['APPDATA']
            else:
                appdata = os.path.expanduser("~")
            zf = zipfile.ZipFile(os.path.join(appdata, '.minecraft', 'bin', 'minecraft.jar'))
        
        ##
        ## Load the charset
        ##

        if 'charset' in kargs:
            with open(kargs['charset'], 'r') as f:
                charset = r.read()
        else:
                charset = zf.read('font.txt')
        
        #Strip the first line
        charset = charset.decode("UTF8").split('\r\n')[1:]
        #32 control characters at the beginning...
        charset = ' '*32 + ''.join(charset)

        ##
        ## Load the image...
        ##

        if 'img' in kargs:
            with open(kargs['img'], 'rb') as f:
                font_bytes=f.read()
        else:
            font_bytes=zf.read('font/default.png')

        reader = png.Reader(bytes=font_bytes)
        width, height, pixels, metadata = reader.read_flat()
        
        #Wrap the data in an Array2D
        img = Array2D(width, height, metadata['planes'])
        img.data = pixels
        
        o = 32 #Character ordinal
        
        glyphs = dict([(i, []) for i in range(0,10)])
        
        for y0 in range(16, 88, 8):
            for x0 in range(0, 128, 8):
                strips = []
                x1 = 0
                while True:
                    data = False
                    strip = array.array('B', (0,)*8)
                    for y1 in range(0,8):
                        if img.get_pixel(x0+x1, y0+y1) == white_pixel:
                            strip[y1] = 1
                            data = True
                    
                    if not data:
                        break
                    
                    strips.append(strip)
                    x1 += 1
                    
                
                char = Array2D(len(strips)+1,9,1)
                char.null_array()
                for nx, strip in enumerate(strips):
                    for ny, pixel in enumerate(strip):
                        if pixel == 1:
                            char.set_pixel(nx,   ny,   0x20) #Foreground
                            char.set_pixel(nx+1, ny+1, 0x30) #Shadow
                
                glyphs[len(strips)+1].append((charset[o], char))
                 
                o += 1
        
        self.glyphs = glyphs
    def get_by_width(self, width):
        return self.glyphs.get(width, [])
                
