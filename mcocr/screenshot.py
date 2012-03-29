import re
import png
import array

import font
from array2d import Array2D

class Screenshot:
    char_error_limit = 4
    img_error_limit = 100
    text_accept_score = -16
    y_end = {
        1:  49,
        2:  96,
        3:  145,
        4:  190}
    def __init__(self, path, font, *args):
        self.path = path
        self.font = font
        if args:
            preferred_scales = args[0]
        else:
            preferred_scales = [2,3,1,4]

        #Read the screenshot
        f = open(path, 'rb')
        reader = png.Reader(file=f)
        width, height, pixels, metadata = reader.read_flat()
        f.close()
    
        #Wrap it in an Array2D
        img = Array2D(width, height, metadata['planes'])
        img.data = pixels
        
        #Loop over different scales attempting to OCR...
        best = (self.img_error_limit, [], '')
        for scale in preferred_scales:
            errors, colours, text = self.ocr(img, scale)
            score = errors-len(text)
            if score < best[0]:
                best = (score, scale, colours, text)
            if score <= self.text_accept_score:
                break

        self.errors, self.scale, self.colours, self.text = best
        
    def ocr(self, img, scale):
        lines = []
        colour_positions=dict((i, []) for i in range(0,50)) #TODO: Confirm actual max lines on screen
        totalerr = 0
        x_padding = 9000 #Minimum x padding
        x_offsets = []
        
        #Line loop, from high y to low
        for y0 in range(img.height - self.y_end[scale] + (img.height % 2), 0, -9*scale):
            line = ""
            x0 = 0
            space_count = 0
            lastcolour = 15
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
                            if colour in font.fg_colours:
                                colour2 = font.fg_colours.index(colour)
                                #Does it have a shadow? (noise otherwise)
                                shadow = img.contiguous(x0+scale, y0+y1+scale, scale)
                                if shadow:
                                    index = -1
                                    try: index=font.bg_colours.index(shadow) 
                                    except:pass
                                    try: index=font.fg_colours.index(shadow) 
                                    except:pass
                                    if index == colour2:
                                        strip[y1/scale] = 0x20 | colour2
                                        fg_data = True
                            #Text shadow
                            if colour in font.bg_colours:
                                colour2 = font.bg_colours.index(colour)
                                #Is there a shadow caster? (noise otherwise)
                                caster = img.contiguous(x0-scale, y0+y1-scale, scale)
                                if caster:
                                    index = -1
                                    try: index=font.fg_colours.index(caster)
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
                    #Handle any accumulated spaces up to this point.
                    if len(line) == 0:
                        x_padding = min(x_padding, space_count)
                        x_offsets.append(space_count)
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
                        best = (self.char_error_limit, 0, colour, '')
                        charmatch = False
                        #Loop over known character widths, high to low, looking for a match
                        for i in range(len(strips)-x2, 1, -1):
                            
                            #Loop over known characters of a given width
                            for string, char in self.font.get_by_width(i):
                                errors, colour = font.char_match(char, d2d, x2, best[0])
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
                        #Quit at this scale if our total error is higher than the image limit.
                        if totalerr >= self.img_error_limit:
                            return self.img_error_limit, [], ''
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
        for i, l in enumerate(lines):
            lines[i] = lines[i][(x_offsets[i]-x_padding)/3:]
        
        colour_positions = [[(j[0]-x_padding, font.colourize_fg(j[1])) for j in colour_positions[i]] for i in range(len(lines)-1, -1, -1)]
        return totalerr, colour_positions, "\n".join(lines[::-1])
    
    def get_coords_positions(self):
        stripped = self.text
        newline_positions = [0]
        index = 0
        while True:
            index = stripped.find('\n', index)
            if index == -1:
                break
            
            newline_positions.append(index) #Note: index is applicable to stripped text.
            stripped = stripped[:index] + stripped[index+1:]
        
        rows = [[] for i in range(len(newline_positions))]
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
