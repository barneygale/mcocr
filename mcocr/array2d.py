#A useful class for dealing with 2-D arrays

import array

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
