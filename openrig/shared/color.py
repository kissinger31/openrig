"""Color functions and definitions."""
import colorsys

CSS_COLORS = {
    'AliceBlue': 'f0f8ff',
    'AntiqueWhite': 'faebd7',
    'Aqua': '00ffff',
    'Aquamarine': '7fffd4',
    'Azure': 'f0ffff',
    'Beige': 'f5f5dc',
    'Bisque': 'ffe4c4',
    'Black': '000000',
    'BlanchedAlmond': 'ffebcd',
    'Blue': '0000ff',
    'BlueViolet': '8a2be2',
    'Brown': 'a52a2a',
    'BurlyWood': 'deb887',
    'CadetBlue': '5f9ea0',
    'Chartreuse': '7fff00',
    'Chocolate': 'd2691e',
    'Coral': 'ff7f50',
    'CornflowerBlue': '6495ed',
    'CornSilk': 'fff8dc',
    'Crimson': 'dc143c',
    'Cyan': '00ffff',
    'DarkBlue': '00008b',
    'DarkCyan': '008b8b',
    'DarkGoldenrod': 'b8860b',
    'DarkGray': 'a9a9a9',
    'DarkGrey': 'a9a9a9',
    'DarkGreen': '006400',
    'DarkKhaki': 'bdb76b',
    'DarkMagenta': '8b008b',
    'DarkOliveGreen': '556b2f',
    'DarkOrange': 'ff8c00',
    'DarkOrchid': '9932cc',
    'DarkRed': '8b0000',
    'DarkSalmon': 'e9967a',
    'DarkSeaGreen': '8fbc8f',
    'DarkSlateBlue': '483d8b',
    'DarkSlateGray': '2f4f4f',
    'DarkSlateGrey': '2f4f4f',
    'DarkTurquoise': '00ced1',
    'DarkViolet': '9400d3',
    'DeepPink': 'ff1493',
    'DeepSkyBlue': '00bfff',
    'DimGray': '696969',
    'DimGrey': '696969',
    'DodgerBlue': '1e90ff',
    'Firebrick': 'b22222',
    'FloralWhite': 'fffaf0',
    'ForestGreen': '228b22',
    'Fuchsia': 'ff00ff',
    'Gainsboro': 'dcdcdc',
    'GhostWhite': 'f8f8ff',
    'Gold': 'ffd700',
    'Goldenrod': 'daa520',
    'Gray': '808080',
    'Grey': '808080',
    'Green': '008000',
    'GreenYellow': 'adff2f',
    'Honeydew': 'f0fff0',
    'HotPink': 'ff69b4',
    'IndianRed': 'cd5c5c',
    'Indigo': '4b0082',
    'Ivory': 'fffff0',
    'Khaki': 'f0e68c',
    'Lavender': 'e6e6fa',
    'LavenderBlush': 'fff0f5',
    'LawnGreen': '7cfc00',
    'LemonChiffon': 'fffacd',
    'LightBlue': 'add8e6',
    'LightCoral': 'f08080',
    'LightCyan': 'e0ffff',
    'LightGoldenrodYellow': 'fafad2',
    'LightGray': 'd3d3d3',
    'LightGrey': 'd3d3d3',
    'LightGreen': '90ee90',
    'LightPink': 'ffb6c1',
    'LightSalmon': 'ffa07a',
    'LightSeaGreen': '20b2aa',
    'LightSkyBlue': '87cefa',
    'LightSlateGray': '778899',
    'LightSlateGrey': '778899',
    'LightSteelBlue': 'b0c4de',
    'LightYellow': 'ffffe0',
    'Lime': '00ff00',
    'LimeGreen': '32cd32',
    'Linen': 'faf0e6',
    'Magenta': 'ff00ff',
    'Maroon': '800000',
    'MediumAquamarine': '66cdaa',
    'MediumBlue': '0000cd',
    'MediumOrchid': 'ba55d3',
    'MediumPurple': '9370db',
    'MediumSeaGreen': '3cb371',
    'MediumSlateBlue': '7b68ee',
    'MediumSpringGreen': '00fa9a',
    'MediumTurquoise': '48d1cc',
    'MediumVioletRed': 'c71585',
    'MidnightBlue': '191970',
    'MintCream': 'f5fffa',
    'MistyRose': 'ffe4e1',
    'Moccasin': 'ffe4b5',
    'NavajoWhite': 'ffdead',
    'Navy': '000080',
    'OldLace': 'fdf5e6',
    'Olive': '808000',
    'OliveDrab': '6b8e23',
    'Orange': 'ffa500',
    'OrangeRed': 'ff4500',
    'Orchid': 'da70d6',
    'PaleGoldenrod': 'eee8aa',
    'PaleGreen': '98fb98',
    'PaleTurquoise': 'afeeee',
    'PaleVioletRed': 'db7093',
    'PapayaWhip': 'ffefd5',
    'PeachPuff': 'ffdab9',
    'Per': 'cd853f',
    'Pink': 'ffc0cb',
    'Plum': 'dda0dd',
    'PowderBlue': 'b0e0e6',
    'Purple': '800080',
    'Red': 'ff0000',
    'RosyBrown': 'bc8f8f',
    'RoyalBlue': '4169e1',
    'SaddleBrown': '8b4513',
    'Salmon': 'fa8072',
    'SandyBrown': 'f4a460',
    'SeaGreen': '2e8b57',
    'Seashell': 'fff5ee',
    'Sienna': 'a0522d',
    'Silver': 'c0c0c0',
    'SkyBlue': '87ceeb',
    'SlateBlue': '6a5acd',
    'SlateGray': '708090',
    'SlateGrey': '708090',
    'Snow': 'fffafa',
    'SpringGreen': '00ff7f',
    'SteelBlue': '4682b4',
    'Tan': 'd2b48c',
    'Teal': '008080',
    'Thistle': 'd8bfd8',
    'Tomato': 'ff6347',
    'Turquoise': '40e0d0',
    'Violet': 'ee82ee',
    'Wheat': 'f5deb3',
    'White': 'ffffff',
    'WhiteSmoke': 'f5f5f5',
    'Yellow': 'ffff00',
    'YellowGreen': '9acd32',
}

_basic_color_names = ['Black', 'Silver', 'Gray', 'White', 'Maroon', 'Red', 'Purple', 'Fuchsia',
                      'Green', 'Lime', 'Olive', 'Yellow', 'Navy', 'Blue', 'Teal', 'Aqua']
BASIC_COLORS = {k: CSS_COLORS[k] for k in CSS_COLORS if k in _basic_color_names}


def name_to_hex(name):
    name = format_color_name(name)
    return CSS_COLORS.get(name)


def name_to_rgb(name, percent=False):
    name = format_color_name(name)
    hex_value = name_to_hex(name)
    if hex_value:
        return hex_to_rgb(hex_value, percent=percent)


def name_to_hsv(name):
    name = format_color_name(name)
    hex_value = name_to_hex(name)
    if hex_value:
        r, g, b = hex_to_rgb(hex_value)
        return colorsys.rgb_to_hsv(r, g, b)


def hex_to_name(hex_value):
    names = [k for k, v in CSS_COLORS.iteritems() if v == format_color_value(hex_value)]
    if names:
        return names[0]
    

def hex_to_rgb(hex_value, percent=False):
    r, g, b = bytearray.fromhex(format_color_value(hex_value).replace('#', ''))
    if percent:
        r, g, b = rgb_to_percent((r, g, b))
    return r, g, b
    
    
def hex_to_hsv(hex_value):
    r, g, b = hex_to_rgb(format_color_value(hex_value))
    return colorsys.rgb_to_hsv(r, g, b)


def rgb_to_name(rgb_value, percent=False):
    return hex_to_name(rgb_to_hex(format_color_value(rgb_value), percent=percent))
    

def rgb_to_hex(rgb_value, percent=False):
    r, g, b = format_color_value(rgb_value)
    if percent:
        r, g, b = rgb_to_percent((r, g, b))
    
    def clip(x):
        return max(0, min(x, 255))
    
    return "#%02x%02x%02x" % (clip(r), clip(g), clip(b))
    
    
def rgb_to_hsv(rgb_value, percent=False):
    r, g, b = format_color_value(rgb_value)
    r, g, b = colorsys.rgb_to_hsv(r, g, b)
    if percent:
        r, g, b = rgb_to_percent((r, g, b))
    return r, g, b


def hsv_to_name(hsv_value):
    return hex_to_name(hsv_to_hex(hsv_value))
    
    
def hsv_to_hex(hsv_value):
    h, s, v = format_color_value(hsv_value)
    return rgb_to_hex(colorsys.hsv_to_rgb(h, s, v))
    
    
def hsv_to_rgb(hsv_value, percent=False):
    h, s, v = format_color_value(hsv_value)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    if percent:
        r, g, b = rgb_to_percent((r, g, b))
    return r, g, b


def format_color_name(name):
    """Matches a known name in the CSS_COLORS dictionary.
    
    :param name: name of color to find
    """
    keys = [k for k in CSS_COLORS.keys() if k.lower() == name.lower()]
    if not keys:
        raise Exception('Color name cannot be found: %s' % name)
    return keys[0]


def format_color_value(*args):
    """Formats provided color as a tuple of float values or a single hex value.
    
    Color Args
    ##########
    Color args can be passed as 3 individual items, as a collection of 3 items (list, tuple), or as
    a string. Color args can represent a triplet of values or a single hex color value.
    
    Color Args Formats
    ##################
    +-------+-----------------------+
    | Type  | Format                |
    +=======+=======================+
    | int   | 5, 5, 5               |
    +-------+-----------------------+
    | float | 5.0, 5.0, 5.0         |
    +-------+-----------------------+
    | str   | '5', '5', '5'         |
    |       | '#000000' or '000000' |
    |       | 'red' or 'Red'        |
    +-------+-----------------------+
    | list  | [5, 5, 5]             |
    |       | [5.0, 5.0, 5.0]       |
    |       | ['5', '5', '5']       |
    +-------+-----------------------+
    | tuple | (5, 5, 5)             |
    |       | (5.0, 5.0, 5.0)       |
    |       | ('5', '5', '5')       |
    +-------+-----------------------+
    
    :param args: color value in a number of formats
    :type args: str | int | float | tuple | list
    
    :returns: triplet of floats or a hex string
    :rtype: tuple | string
    """
    try:
        if len(args) == 3:
            return tuple(map(float, args))
        elif len(args) == 1:
            value = args[0]
            if isinstance(value, (tuple, list)):
                return tuple(map(float, value))
            elif isinstance(value, basestring):
                if ',' in value:
                    value = value.split(',')
                    if len(value) == 3:
                        return tuple(map(float, value))
                elif ' ' in value:
                    value = value.split()
                    if len(value) == 3:
                        return tuple(map(float, value))
                elif is_hex(value) or value.startswith('#'):
                    if value.startswith('#'):
                        value = value.replace('#', '')
                    if not is_hex(value):
                        raise ValueError()
                    return value
                else:
                    value = name_to_rgb(format_color_name(value))
                    return value
        else:
            raise ValueError()
    except ValueError:
        value = args if len(args) > 1 else args[0]
        print 'Could not format color value:', value


def percent_to_rgb(value):
    value = format_color_value(value)
    return tuple(map(lambda x: x * 255.0, value))


def rgb_to_percent(value):
    value = format_color_value(value)
    return tuple(map(lambda x: x / 255.0, value))


def is_hex(value):
    try:
        int(value, 16)
        return True
    except ValueError:
        return False
