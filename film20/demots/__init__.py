# -*- coding: utf-8 -*-

import os
import re
import math
import textwrap

try:
    from PIL import Image, ImageOps, ImageFont, ImageDraw
except ImportError:
    import Image, ImageOps, ImageFont, ImageDraw

# from easy_thumbnails utils
def image_entropy(im):
    """
    Calculate the entropy of an image. Used for "smart cropping".
    """
    if not isinstance(im, Image.Image):
        # Can only deal with PIL images. Fall back to a constant entropy.
        return 0
    hist = im.histogram()
    hist_size = float(sum(hist))
    hist = [h / hist_size for h in hist]
    return -sum([p * math.log(p, 2) for p in hist if p != 0])

# from easy_thumbnails utils
def _compare_entropy(start_slice, end_slice, slice, difference):
    """
    Calculate the entropy of two slices (from the start and end of an axis),
    returning a tuple containing the amount that should be added to the start
    and removed from the end of the axis.

    """
    start_entropy = image_entropy(start_slice)
    end_entropy = image_entropy(end_slice)
    if end_entropy and abs(start_entropy / end_entropy - 1) < 0.01:
        # Less than 1% difference, remove from both sides.
        if difference >= slice * 2:
            return slice, slice
        half_slice = slice // 2
        return half_slice, slice - half_slice
    if start_entropy > end_entropy:
        return 0, slice
    else:
        return slice, 0

# based on easy_thumbnails
def scale_and_crop(im, size, crop=False, upscale=False, **kwargs):

    source_x, source_y = [float(v) for v in im.size]
    target_x, target_y = [float(v) for v in size]

    if crop or not target_x or not target_y:
        scale = max(target_x / source_x, target_y / source_y)
    else:
        scale = min(target_x / source_x, target_y / source_y)

    # Handle one-dimensional targets.
    if not target_x:
        target_x = source_x * scale
    elif not target_y:
        target_y = source_y * scale

    if scale < 1.0 or (scale > 1.0 and upscale):
        # Resize the image to the target size boundary. Round the scaled
        # boundary sizes to avoid floating point errors.
        im = im.resize((int(round(source_x * scale)),
                        int(round(source_y * scale))),
                       resample=Image.ANTIALIAS)

    if crop:
        # Use integer values now.
        source_x, source_y = im.size
        # Difference between new image size and requested size.
        diff_x = int(source_x - min(source_x, target_x))
        diff_y = int(source_y - min(source_y, target_y))
        if diff_x or diff_y:
            # Center cropping (default).
            halfdiff_x, halfdiff_y = diff_x // 2, diff_y // 2
            box = [halfdiff_x, halfdiff_y,
                   min(source_x, int(target_x) + halfdiff_x),
                   min(source_y, int(target_y) + halfdiff_y)]
            # See if an edge cropping argument was provided.
            edge_crop = (isinstance(crop, basestring) and
                         re.match(r'(?:(-?)(\d+))?,(?:(-?)(\d+))?$', crop))
            if edge_crop and filter(None, edge_crop.groups()):
                x_right, x_crop, y_bottom, y_crop = edge_crop.groups()
                if x_crop:
                    offset = min(int(target_x) * int(x_crop) // 100, diff_x)
                    if x_right:
                        box[0] = diff_x - offset
                        box[2] = source_x - offset
                    else:
                        box[0] = offset
                        box[2] = source_x - (diff_x - offset)
                if y_crop:
                    offset = min(int(target_y) * int(y_crop) // 100, diff_y)
                    if y_bottom:
                        box[1] = diff_y - offset
                        box[3] = source_y - offset
                    else:
                        box[1] = offset
                        box[3] = source_y - (diff_y - offset)
            # See if the image should be "smart cropped".
            elif crop == 'smart':
                left = top = 0
                right, bottom = source_x, source_y
                while diff_x:
                    slice = min(diff_x, max(diff_x // 5, 10))
                    start = im.crop((left, 0, left + slice, source_y))
                    end = im.crop((right - slice, 0, right, source_y))
                    add, remove = _compare_entropy(start, end, slice, diff_x)
                    left += add
                    right -= remove
                    diff_x = diff_x - add - remove

                box = (left, top, right, bottom)
            # Finally, crop the image!
            if crop != 'scale':
                im = im.crop(box)
    return im


current_dir=os.path.abspath( os.path.dirname( __file__ ) )

class Demotivator( object ):

    size = ( 500, 100 )
    margin = 50

    text_options = {
        'title': {
            'font': os.path.join( current_dir, 'resources/fonts/DroidSans.ttf' ),
            'size': 35,
            'cols': 26,
        },
        'description': {
            'font': os.path.join( current_dir, 'resources/fonts/DroidSans.ttf' ),
            'size': 18,
            'cols': 50,
        },
        'footer': {
            'font': os.path.join( current_dir, 'resources/fonts/DroidSans.ttf' ),
            'size': 15,
            'cols': 25,
            'fill': '#999999',
        },
    }

    def __init__( self, image, line1, line2, footer_text=None ):
        self.image = Image.open( image )
        self.image = self.image.convert( 'RGBA' )

        self.line1 = line1.decode( 'utf-8' )#.upper()
        self.line2 = line2.decode( 'utf-8' )

        self.footer_text = footer_text
        self.final_image = None

    def _scale_source_image( self ):
        self.image = scale_and_crop( self.image, self.size, crop='smart', upscale=True )

    def _get_line( self, text, type='title' ):
        options = self.text_options[type]

        h, w = 0, 0
        lines = textwrap.wrap( text, width=options['cols'] )
        font = ImageFont.truetype( options['font'], options['size'], encoding='unic' )

        for line in lines:
            width, height = font.getsize( line )
            h += height
            if width > w:
                w = width

        return lines, font, w, h

    def _draw_line( self, lines, font, top, left=None, **kwargs ):
        draw = ImageDraw.Draw( self.final_image )
        on_center = left is None
        for line in lines:
            w, h = font.getsize( line )
            if on_center:
                left = ( self.final_image.size[0] - w )/ 2
            draw.text( ( left, top ), line, font=font, **kwargs )
            top += h
        del draw

    def _draw_footer( self ):
        logo = Image.open( os.path.join( current_dir, 'resources/images/logo.png' ) )
        logo = logo.convert( 'RGBA' )
        
        width, height = self.final_image.size
        w, h = logo.size

        self.final_image.paste( logo, ( width - w, height - h ), logo )

        # draw footer if is specified
        if self.footer_text:
            l, l_font, w, h = self._get_line( self.footer_text, type='footer' )
            self._draw_line( l, l_font, height - h - 10, 10, fill=self.text_options['footer'].get( 'fill' ) )

    def create( self, output ):
       
        # scale image
        self._scale_source_image()

        # get texts
        l1, l1_font, w1, h1 = self._get_line( self.line1 )
        l2, l2_font, w2, h2 = self._get_line( self.line2, type='description' )

        # calculate final image size
        width, height  = self.image.size

        width  += self.margin * 2 + 5
        height += self.margin * 2 + h1 + h2 + 30 + 5

        # add image border
        self.image = ImageOps.expand( self.image, border=1, fill='white' )

        # create black background
        self.final_image = Image.new( 'RGBA', ( width, height ), "black" )
        self.final_image.paste( self.image, ( self.margin, self.margin ), self.image )

        # draw texts
        self._draw_line( l1, l1_font, self.image.size[1] + self.margin + 10 )
        self._draw_line( l2, l2_font, self.image.size[1] + self.margin + 10 + h1 + 10 )
        
        # draw footer
        self._draw_footer()

        # self generated image
        self.final_image.save( output )
        
        return self.final_image

    def get_thumbnail( self, output, size=(200,100) ):
        image = self.final_image
        if image is None:
            image = self.create( "/tmp/demot.png" )
        image.thumbnail( size, Image.ANTIALIAS )
        image.save( output )
        
        return image
