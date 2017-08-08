"""Keyboard module for SHA2017 badge.

TODO:

    Display options in <left, up, right, down> instead of line after line,
    If len(range) < 4, just display the options instead of redundant subranges
"""

import time
import math

try:
    import ugfx
    import badge
    MICROPYTHON = True
except ImportError:
    import unittest
    import unittest.mock as mock
    ugfx = mock.Mock()
    badge = mock.Mock()
    MICROPYTHON = False


NUM_RANGES = 4
ASCII_RANGE = (32, 126)
FONT = 'Roboto_Regular12'


def gen_range(f, to, n, m):
    chunk_size = (to - f) / m
    return (int(math.ceil(f + (chunk_size * n))),
            int(math.floor(f + (chunk_size * (n+1)))))


class CharacterInput:

    def __init__(self, callback, ascii_range=ASCII_RANGE):
        self.ascii_range = ascii_range
        self.stack = [ascii_range]
        self.reset()
        self.callback = callback

    def reset(self):
        self.start, self.end = self.ascii_range

    def select_range(self, range_number):
        self.start, self.end = gen_range(self.start, self.end,
                                         range_number, NUM_RANGES)
        if self.start > self.end:
            raise RuntimeError('self.start > self.end')
        if self.start == self.end:
            c = chr(self.end)
            self.stack.pop()
            self.start, self.end = self.stack[-1]
            self.callback(c)
        else:
            self.stack.append((self.start, self.end))

    def maybe_back(self):
        if len(self.stack) > 1:
            self.stack.pop()
            self.start, self.end = self.stack[-1]
            print('Popped')
        else:
            print('Cannot go back on first node')

    def __repr__(self):
        return ('CharacterInput(stack=%(stack)r,'
                'start=%(start)r, end=%(end)r)') % self.__dict__


class Editor:
    """This class is responsible for receiving input and defining the editor
    logic."""

    def __init__(self, ugfx):
        self.buf = ""
        self.character_input = CharacterInput(lambda c: self.got_character(c))
        self.ugfx = ugfx
        self.RANGE_ORDER = [self.ugfx.JOY_LEFT, self.ugfx.JOY_UP,
                            self.ugfx.JOY_RIGHT, self.ugfx.JOY_DOWN]

    def got_character(self, the_character):
        print('Got character=%r' % the_character)
        self.buf += the_character

    def display_state(self):
        print(("Drawing. self.buf=%(buf)r, "
              "self.character_input=%(character_input)r") % self.__dict__)
        self.ugfx.clear(self.ugfx.WHITE)
        self.ugfx.string_box(0, 4 * 16, 90, 90, self.buf, FONT,
                             self.ugfx.BLACK, self.ugfx.justifyCenter)

        for i in range(NUM_RANGES):
            start, end = gen_range(self.character_input.start,
                                   self.character_input.end, i, NUM_RANGES)
            if start == end:
                s = chr(start)
            else:
                s = '%r - %r' % (chr(start), chr(end))
            self.ugfx.string_box(0, i * 16, 90, 90, s, FONT,
                                 self.ugfx.BLACK, self.ugfx.justifyCenter)
        self.ugfx.flush()

    def key_pressed(self, key):
        if key in self.RANGE_ORDER:
            self.character_input.select_range(self.RANGE_ORDER.index(key))
        elif key == self.ugfx.BTN_START:
            self.character_input.maybe_back()
        elif key == self.ugfx.BTN_SELECT:
            self.buf = self.buf[:-1]

        self.display_state()

    def init_input(self):
        self.ugfx.init()
        self.ugfx.input_init()
        for key in self.RANGE_ORDER + [self.ugfx.BTN_START,
                                       self.ugfx.BTN_SELECT]:
            def closure(is_pressed, k=key):
                if is_pressed:
                    self.key_pressed(k)
            self.ugfx.input_attach(key, closure)

    def run(self):
        self.init_input()
        self.display_state()


if MICROPYTHON:
    badge.init()
    Editor(ugfx).run()
    while True:
        time.sleep(0.1)

###########################################################################
# else
###########################################################################

class CharacterInputTest(unittest.TestCase):

    def setUp(self):
        self.c = CharacterInput(mock.Mock(), ascii_range=(0, 128))

    def test_select_range_2(self):
        s, e = self.c.start, self.c.end
        self.c.select_range(2)
        self.assertNotEqual(s, self.c.start)
        self.assertNotEqual(e, self.c.end)

    def test_simple_go_back(self):

        s, e = self.c.start, self.c.end
        self.c.select_range(2)
        self.c.maybe_back()
        self.assertEqual(s, self.c.start)
        self.assertEqual(e, self.c.end)

    def test_start_gt_end(self):
        self.c = CharacterInput(mock.Mock(), ascii_range=(32, 136))
        self.c.select_range(1)
        self.c.select_range(1)
        self.c.select_range(1)
        self.c.select_range(1)
        self.c.select_range(2)


unittest.main()
