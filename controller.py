import time, uuid, threading, textwrap
from enum import Enum, auto
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import png

class StreamController():
    def __init__(self, x_size, y_size):
        self.event = threading.Event()
        self.events = []
        self.uuid = uuid.uuid4()
        self.x_size = x_size
        self.y_size = y_size
        self.bg_color = (0, 0, 0)
        self.framebuf = self.blank_color(self.bg_color)

    class EventType(Enum):
        CLICK = auto()
        MESSAGE = auto()
        CLOSE = auto()

    def trigger_event(self, state):
        self.events.append(state)
        self.event.set()

    def await_event(self):
        if self.event.wait(timeout=30.0):
            self.event.clear()
            event = self.events.pop(0)
            print('event:', event)
            return event
        else:
            return None

    def print_text(self, text):
        full_text = textwrap.fill(text, width=180)
        height = (full_text.count('\n') + 1) * 11 + 1
        img = Image.new("RGB", (self.x_size, height), (0, 0, 0))
        fnt = ImageFont.truetype("FreeSans", 11)
        d = ImageDraw.Draw(img)
        d.multiline_text((5, 0), full_text, font=fnt, spacing=0)
        new_frame = np.reshape(np.frombuffer(img.tobytes(), dtype=np.uint8), newshape=(height, self.x_size, 3))
        combined_frame = np.concatenate((self.framebuf, new_frame))
        self.framebuf = combined_frame[-self.y_size:]
        return [(combined_frame[y:y+self.y_size], 1, 100) for y in range(0, height+1, 2)] + [(self.framebuf, 1, 100)]

    def generate_stream(self):
        self.print_text('(end of backlog)')
        try:
            header = png.png_header
            header += png.ihdr_chunk(self.x_size, self.y_size)
            header += png.text_chunk('Software', "commandblockguy's terrible APNG streamer")
            header += png.actl_chunk(0xffff, 1)
            start_frame = self.blank_color([255,0,255])
            header += png.idat_chunk(start_frame)
            yield header
            seq = 0
            current = start_frame
            gen = self.get_frames()
            while True:
                new_frames = next(gen)
                if new_frames == None:
                    new_frames = [(current, 0, 100)]
                # duplicate last frame to satisfy firefox
                data, current, seq = png.multi_frame_chunks(seq, current, new_frames + [new_frames[-1]])
                yield data
            yield png.iend_chunk()
        except StopIteration:
            print('Stopped in generator')
            return

    def blank_color(self, color):
        arr = np.zeros([self.y_size, self.x_size, 3], dtype=np.uint8)
        arr[:,:] = color
        return arr

    def get_frames(self):
        yield [(self.framebuf, 1, 100)]
        while True:
            event = self.await_event()
            if event:
                if event[0] == StreamController.EventType.CLOSE:
                    yield [(self.blank_color([0,0,0]), 1, 100)]
                    return
                if event[0] == StreamController.EventType.MESSAGE:
                    _, user, message = event
                    yield self.print_text('<' + user + '> ' + message)
            else:
                yield None
