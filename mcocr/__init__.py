import png, array
import zipfile
import sys
import re

SCANOVER = 10

colourize = lambda m, c: [m*(2*(1&c>>i)+(c>>3)) for i in range(2,-1,-1)]
colourize_bg = lambda c: colourize(21, c)
colourize_fg = lambda c: colourize(85, c) if c != 6 else [255, 170, 0]
bg_colours = [array.array('B', colourize_bg(i)) for i in range(16)]
fg_colours = [array.array('B', colourize_fg(i)) for i in range(16)]

error_limit = 10



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
    
    def set_pixel(self, x, y, data):
        index = self.element_width * (x + y*self.width)
        for j in range(self.element_width):
            self.data[index+j] = data[j]
    
    def iter_pixels(self):
        for index in range(0, self.width*self.height*self.element_width, self.element_width):
            o = self.data[index:index+self.element_width]
            #print "yielding", o[0]
            yield o[0]
            #yield o if len(0) > 1 else o[0]
    
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
    
    def match_area(self, x, y, glyph):
        #for y0 in glyph.height
        pass
    def __eq__(self, other):
        return self.width == other.width and self.height == other.height and self.element_width == other.element_width and self.data == other.data 

def get_glyphs():
    glyphs = dict([(i, []) for i in range(0,10)])

    zf = zipfile.ZipFile('/home/barney/.minecraft/bin/minecraft.jar')
    charset = zf.read('font.txt').decode("UTF8").split('\r\n')[1:]
    charset = ' '*32 + ''.join(charset)
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
                        char.set_pixel(nx, ny, [1])     #Foreground
                        char.set_pixel(nx+1, ny+1, [2]) #Shadow
            
            glyphs[len(strips)+1].append((charset[o], char))
             
            o += 1
    
    return glyphs

def debug_img(img, name):                 
    #print "Writing debug img..."
    output = array.array('B', (0,)*(img.width*img.height*3))
    index_1 = 0
    index_2 = 0
    for el in img.iter_pixels():
        #print el
        if el & 1:
            output[index_1  ] = 255
            output[index_1+1] = 255
            output[index_1+2] = 255
        if el & 2:
            output[index_1  ] = 128
            output[index_1+1] = 128
            output[index_1+2] = 128
        
        index_1 += 3
    
    f = open(name, 'wb')
    writer = png.Writer(img.width, img.height, alpha=False)
    writer.write_array(f, output)
    f.close()
    #print "Done."

                    
    
    
def char_match(a,b,curbest):
    errors = 0
    for i in range(0, len(a)):
        c = a[i]
        d = b[i]
        if (c != 0 and d == 0) or \
           (c == 0 and d != 0):
            errors += 1
            if errors >= curbest or errors >= error_limit:
                return errors
            
    
    return errors

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

def fix_linebreaks(text):
    output = ""
    lines = text.split("\n")
    for j in range(len(lines)-1):
        line = lines[j] + lines[j+1][0]
    
        #PART ONE: examine the first part to see if it wraps
        more = False
        if len(line) > chat_length:
            more = True
        else:
            width = 0
            i = 0
            while i < len(line):
                index = characters.find(line[i])
                width += character_widths[index+32]
                if width >= chat_width:
                    more = True
                    break
                i+=1
        output += lines[j]
        if not more:
            output += "\n"
    output += lines[len(lines)-1]
    return output
        

def ocr(filename, glyphs):
    f = open(filename, 'rb')
    reader = png.Reader(file=f)
    width, height, pixels, metadata = reader.read_flat()
    
    img = Array2D(width, height, metadata['planes'])
    img.data = pixels
    
    lines = []
    
    totalerr = 0
    
    #Line loop, from high y to low
    for y0 in range(img.height - 96 + (img.height % 2), 0, -18):
        line = ""
        x0 = 4
        space_count = 0
        #X loop
        while x0 < 640:
            strips = []

            #Character read loop
            while True:
                fg_data = False
                bg_data = False
                strip = array.array('B', (0,)*9)
                
                #Loop over pixels in a strip, low y to high
                for y1 in range(0,18,2):
                    
                    #Check the 2x2 area is contiguous
             
                    colour = img.get_pixel(x0, y0+y1)
                    contiguous = True
                    for i in range(1,4):
                        t = img.get_pixel(x0+(i&1), y0+y1+((i&2)>>1))
                        if t != colour:
                            contiguous = False
                            break
                        colour = t
                    if contiguous:
                        #Text foreground
                        if colour in fg_colours:
                            #Does it have a shadow? (noise otherwise)
                            if img.get_pixel(x0+2, y0+y1+2) in (bg_colours+fg_colours):
                                strip[y1/2] = 1
                                fg_data = True
                        #Text shadow
                        if colour in bg_colours:
                            #Is there a shadow caster? (noise otherwise)
                            if img.get_pixel(x0-2, y0+y1-2) in fg_colours:
                                strip[y1/2] = 2
                                bg_data = True

                x0 += 2

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
                #Handle any accumulated spaces up to this point.
                line += " " * (space_count/4)
                space_count = 0
                
                #Write strips to an array
                d = array.array('B', (0,)*(len(strips)*9))
                for nx, strip in enumerate(strips):
                    for ny, pixel in enumerate(strip):
                        d[nx+ny*len(strips)] = pixel
                
                #Try to find a character match. 
                best = (error_limit, '')
                for string, char in glyphs[len(strips)]:
                    errors = char_match(char.data, d, best[0])
                    if errors < best[0]:
                        best = (errors, string)
                        if errors == 0:
                            break

                #Append the best character match to the line
                line+=best[1]
                totalerr+=best[0]
        
        #Blank line? Don't bother reading any further up.
        if line == "":
            break
        lines.append(line)
    
    print "Total errors: %d" % totalerr
    return "\n".join(lines[::-1])
    
                            
                        
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
        #print match.group(1)
        start = match.start() + 1
        end = match.end()
        
        while newline_positions[newline_pos_index+1] < start:
            newline_pos_index += 1
        
        #If it's split over two lines...
        if newline_positions[newline_pos_index+1] < end:
            #print "At row 
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
print g[6][72][0]
text = ocr(sys.argv[1], g)
#text = fix_linebreaks(text)
#print text
split = text.split('\n')
#print split
rows = censor_coords(text)
for y, row in rows.items():
    for box in row:
        #print box
        split[y] = split[y][:box[0]] + '#'*(box[1]-box[0]) + split[y][box[1]:]

print '\n'.join(split)
        
        
