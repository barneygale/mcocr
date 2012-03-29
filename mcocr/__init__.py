import png, array
import zipfile
import sys
import re
import os

SCANOVER = 10

colourize = lambda m, c: [m*(2*(1&c>>i)+(c>>3)) for i in range(2,-1,-1)]
colourize_bg = lambda c: colourize(21, c)
colourize_fg = lambda c: colourize(85, c) if c != 6 else [255, 170, 0]
bg_colours = [array.array('B', colourize_bg(i)) for i in range(16)]
fg_colours = [array.array('B', colourize_fg(i)) for i in range(16)]

error_limit = 10

if sys.platform == 'win32':
    minecraft_path = os.environ['APPDATA']
else:
    minecraft_path = os.path.expanduser("~")
minecraft_path = os.path.join(minecraft_path, ".minecraft")

class Array2D:
    def __init__(self, w, h, element_width):
        self.width = w
        self.height = h
        self.element_width = element_width
    
    def null_array(self):
        self.data = array.array('B', (0,)*(self.width*self.height*self.element_width))
    
    def get_pixel(self, x, y):
        index = self.element_width * (x + y*self.width)
        return self.data[index:index+self.element_width]
    
    def set_pixel(self, x, y, *data):
        index = self.element_width * (x + y*self.width)
        for j in range(self.element_width):
            self.data[index+j] = data[j]
    
    def iter_pixels(self):
        for index in range(0, self.width*self.height*self.element_width, self.element_width):
            o = self.data[index:index+self.element_width]
            yield o[0]
    
    def get_area(self, x, y, dx, dy):
        #Width in bytes of data
        data_width = dx*self.element_width
    
        #New array
        out = array.array('B', (0,)*(dy*data_width))

        #Image array index
        i0 = self.element_width * (x + y*self.width)

        #New array index
        j0 = 0
        
        for y0 in range(y, y+dy):
            out[j0:j0+data_width] = self.data[i0:i0+data_width]
            
            i0 += self.width * self.element_width
            j0 += data_width
        
        return out
    
    def contiguous(self, x, y, scale):
        #Check if a given square, starting at x,y and ending at x+scale,y+scale is all the same colour
        area = self.get_area(x,y,scale,scale)
        last = area[:self.element_width]
        for i in range(self.element_width, len(area), self.element_width):
            j = area[i:i+self.element_width]
            if j != last:
                return False
            last = j
        return last
    def __eq__(self, other):
        return self.width == other.width and self.height == other.height and self.element_width == other.element_width and self.data == other.data 

def get_glyphs():
    #Key is character width. Value is a list of pairs: (String, Array2D)
    #Array2D format: 1 byte per pixel, 0: no data, 1: fg data, 2: bgdata
    glyphs = dict([(i, []) for i in range(0,10)])

    #Open minecraft.jar
    zf = zipfile.ZipFile(os.path.join(minecraft_path, 'bin', 'minecraft.jar'))
    
    #Read the character set
    charset = zf.read('font.txt').decode("UTF8").split('\r\n')[1:]
    charset = ' '*32 + ''.join(charset)
    
    #Read the font file
    reader = png.Reader(bytes=zf.read('font/default.png'))
    
    width, height, pixels, metadata = reader.read_flat()
    
    img = Array2D(width, height, metadata['planes'])
    img.data = pixels
    
    o = 32
    
    white_pixel = array.array('B', (255,)*4)
    
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
                        char.set_pixel(nx, ny, 0x20)     #Foreground
                        char.set_pixel(nx+1, ny+1, 0x30) #Shadow
            
            glyphs[len(strips)+1].append((charset[o], char))
             
            o += 1
    
    return glyphs
    
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
                if errors >= curbest or errors >= error_limit:
                    return errors, colour
            elif d & 0x30 == 0x20: #Foreground colour!
                colour = d & 0x0F
        return errors, colour

    print "Slow check"
    for y0 in range(a.height):
        for x0 in range(a.width):
            c = a.get_pixel(x0, y0)[0] #Character
            d = b.get_pixel(x0+xoffset, y0)[0] #Buffer
            if (c & 0x20 != d & 0x20):
                errors += 1
                if errors >= curbest or errors >= error_limit:
                    return errors, colour
            elif d & 0x30 == 0x20: #Foreground colour!
                colour = d & 0x0F
                
    return errors, colour

def get_line_width(line):
    chat_length = 119
    chat_width = 320
    characters = u' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_\'abcdefghijklmnopqrstuvwxyz{|}~\xe2\x8c\x82\xc3\x87\xc3\xbc\xc3\xa9\xc3\xa2\xc3\xa4\xc3\xa0\xc3\xa5\xc3\xa7\xc3\xaa\xc3\xab\xc3\xa8\xc3\xaf\xc3\xae\xc3\xac\xc3\x84\xc3\x85\xc3\x89\xc3\xa6\xc3\x86\xc3\xb4\xc3\xb6\xc3\xb2\xc3\xbb\xc3\xb9\xc3\xbf\xc3\x96\xc3\x9c\xc3\xb8\xc2\xa3\xc3\x98\xc3\x97\xc6\x92\xc3\xa1\xc3\xad\xc3\xb3\xc3\xba\xc3\xb1\xc3\x91\xc2\xaa\xc2\xba\xc2\xbf\xc2\xae\xc2\xac\xc2\xbd\xc2\xbc\xc2\xa1\xc2\xab\xc2\xbb#'
    character_widths = [
        1, 9, 9, 8, 8, 8, 8, 7, 9, 8, 9, 9, 8, 9, 9, 9,
        8, 8, 8, 8, 9, 9, 8, 9, 8, 8, 8, 8, 8, 9, 9, 9,
        4, 2, 5, 6, 6, 6, 6, 3, 5, 5, 5, 6, 2, 6, 2, 6,
        6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 2, 2, 5, 6, 5, 6,
        7, 6, 6, 6, 6, 6, 6, 6, 6, 4, 6, 6, 6, 6, 6, 6,
        6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 4, 6, 4, 6, 6,
        3, 6, 6, 6, 6, 6, 5, 6, 6, 2, 6, 5, 3, 6, 6, 6,
        6, 6, 6, 6, 4, 6, 6, 6, 6, 6, 6, 5, 2, 5, 7, 6,
        6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 4, 6, 3, 6, 6,
        6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 4, 6,
        6, 3, 6, 6, 6, 6, 6, 6, 6, 7, 6, 6, 6, 2, 6, 6,
        8, 9, 9, 6, 6, 6, 8, 8, 6, 8, 8, 8, 8, 8, 6, 6,
        9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9,
        9, 9, 9, 9, 9, 9, 9, 9, 9, 6, 9, 9, 9, 5, 9, 9,
        8, 7, 7, 8, 7, 8, 8, 8, 7, 8, 8, 7, 9, 9, 6, 7,
        7, 7, 7, 7, 9, 6, 7, 8, 7, 6, 6, 9, 7, 6, 7, 1]

    if len(line) > chat_length:
        return False, -1
    else:
        width = 0
        i = 0
        while i < len(line):
            index = characters.find(line[i])
            width += character_widths[index+32]
            if width >= chat_width:
                return False, chat_width
            i+=1
        
        return True, width  

def ocr(filename, glyphs, scale):
    f = open(filename, 'rb')
    reader = png.Reader(file=f)
    width, height, pixels, metadata = reader.read_flat()
    
    img = Array2D(width, height, metadata['planes'])
    img.data = pixels
    
    lines = []
    colour_positions=dict((i, []) for i in range(0,50)) #TODO: Confirm actual max lines on screen
    
    totalerr = 0
    
    x_padding = 9000 #Minimum x padding
    
    #Line loop, from high y to low
    start = {
        1:  49,
        2:  96,
        3:  145,
        4:  190}
    for y0 in range(img.height - start[scale] + (img.height % 2), 0, -9*scale):
        line = ""
        x0 = 0
        space_count = 0
        lastcolour = None
        #X loop
        while x0 < 320*scale:
            strips = []

            #Character read loop
            while True:
                fg_data = False
                bg_data = False
                strip = array.array('B', (0,)*9)
                
                #Loop over pixels in a strip, low y to high
                for y1 in range(0,9*scale,scale):
                    
                    #Check the scale*scale area is contiguous
                    colour = img.contiguous(x0, y0+y1, scale)
                    if colour:
                        #Text foreground
                        if colour in fg_colours:
                            colour2 = fg_colours.index(colour)
                            #Does it have a shadow? (noise otherwise)
                            shadow = img.contiguous(x0+scale, y0+y1+scale, scale)
                            if shadow:
                                index = -1
                                try: index=bg_colours.index(shadow) 
                                except:pass
                                try: index=fg_colours.index(shadow) 
                                except:pass
                                if index == colour2:
                                    strip[y1/scale] = 0x20 | colour2
                                    fg_data = True
                        #Text shadow
                        if colour in bg_colours:
                            colour2 = bg_colours.index(colour)
                            #Is there a shadow caster? (noise otherwise)
                            caster = img.contiguous(x0-scale, y0+y1-scale, scale)
                            if caster:
                                index = -1
                                try: index=fg_colours.index(caster)
                                except:pass
                                if index == colour2:
                                    strip[y1/scale] = 0x30 | colour2
                                    bg_data = True

                x0 += scale

                if fg_data or bg_data:
                    #We've got some character data
                    strips.append(strip)
                else:
                    #A space between words
                    space_count += 1
                if not fg_data:
                    #If there's no foreground data, we're done
                    #reading a character (or nothing at all)
                    break
            
            #If we've read a character (not part of a space)...
            if len(strips) > 0:
                #print "Got something!"
                #print strips
                #Handle any accumulated spaces up to this point.
                if len(line) == 0:
                    x_padding = min(x_padding, space_count)
                line += " " * (space_count/3)
                space_count = 0
                
                #Write strips to an array
                d = array.array('B', (0,)*(len(strips)*9))
                for nx, strip in enumerate(strips):
                    for ny, pixel in enumerate(strip):
                        d[nx+ny*len(strips)] = pixel
                
                #Make an Array2D out of it
                
                d2d = Array2D(len(strips), 9, 1)
                d2d.data = d
                
                #Try to find a character match.
                #Note that noise, especially on small-scale images, can very occasionally cause
                #Two or more characters to appear here.
                
                #Character loop
                x2 = 0
                while x2 < len(strips):
                    #errors, width, character
                    best = (error_limit, 0, colour, '')
                    charmatch = False
                    #Loop over known character widths, high to low, looking for a match
                    for i in range(len(strips)-x2, 1, -1):
                        if not i in glyphs: continue
                        
                        #Loop over known characters of a given width
                        for string, char in glyphs[i]:
                            errors, colour = char_match(char, d2d, x2, best[0])
                            if errors < best[0]:
                                best = (errors, i, colour, string)
                                if errors == 0:
                                    #Perfect match!
                                    charmatch = True
                                    break
                        if charmatch:
                            break
                     
                    #OK, we've got a character now!
                    totalerr += best[0]
                    x2 += best[1]
                    if best[2] != lastcolour:
                        lastcolour = best[2]
                        colour_positions[len(lines)].append((len(line), best[2]))
                    line += best[3]
               
        
        #Blank line? Don't bother reading any further up.
        if line == "":
            break
        lines.append(line)
        
    #Remove latent space-padding from x chatbox margin
    
    x_padding = x_padding/3
    if x_padding != 0:
        for i, l in enumerate(lines):
            lines[i] = lines[i][x_padding:]
    
    colour_positions = [[(j[0]-x_padding, j[1]) for j in colour_positions[i]] for i in range(len(lines)-1, -1, -1)]
    return totalerr, colour_positions, "\n".join(lines[::-1])
    
                            
                        
def censor_coords(text):
    stripped = text
    newline_positions = [0]
    index = 0
    while True:
        index = stripped.find('\n', index)
        if index == -1:
            break
        
        newline_positions.append(index) #Note: index is applicable to stripped text.
        stripped = stripped[:index] + stripped[index+1:]
    
    rows = dict([(i, []) for i in range(len(newline_positions))])
    pattern = '(?<!\d{2}-\d{2}) (-?\d+\s*[:,]{1}\s*-?\d+\s*[:,]{1}\s*-?\d+)' #Match coords
    newline_pos_index = 0
    
    for match in re.finditer(pattern, stripped):
        start = match.start() + 1
        end = match.end()
        
        while newline_positions[newline_pos_index+1] < start:
            newline_pos_index += 1
        
        #If it's split over two lines...
        if newline_positions[newline_pos_index+1] < end:
            #First box...
            rows[newline_pos_index].append((
                - newline_positions[newline_pos_index] + start, #start
                - newline_positions[newline_pos_index] + newline_positions[newline_pos_index+1])) #End
            #Second box...
            rows[newline_pos_index+1].append((
                0,
                end - newline_positions[newline_pos_index+1]))
        else:
            rows[newline_pos_index].append((
                - newline_positions[newline_pos_index] + start, #start
                - newline_positions[newline_pos_index] + end)) #end
    
    return rows
        

   

g = get_glyphs()
errors, colour_positions, text = ocr(sys.argv[1], g, int(sys.argv[2]))
split = text.split('\n')
rows = censor_coords(text)
for y, row in rows.items():
    for box in row:
        split[y] = split[y][:box[0]] + '#'*(box[1]-box[0]) + split[y][box[1]:]

print "\n".join(split)
#print "Colours: ", colour_positions
#print "---"
#print "Errors: %d" % errors
        
        
