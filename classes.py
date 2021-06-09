import cv2
from math import fabs
import video_loader
import os
import numpy as np


class Video:

    def __init__(self, length, fps, width, height, spacing=20, threshold=500, ramp_speed=6):
        self.__frames = []
        self.__length = length
        self.fps = fps
        self.__width = width
        self.__height = height
        self.__spacing = spacing
        self.__focus_threshold = threshold
        self.__ramp_speed = ramp_speed
        self.__default_ramp_speed = ramp_speed

    def write_frame(self, frame):
        height, width, _ = frame.shape
        if width != self.__width or height != self.__height:
            raise RuntimeError("Trying to add a frame with mismatched dimensions")
        self.__frames.append(frame)

    def width(self):
        return self.__width

    def height(self):
        return self.__height

    def object_spacing(self):
        return self.__spacing

    def focus_threshold(self):
        return self.__focus_threshold

    def ramp_speed(self):
        return self.__ramp_speed

    def frames(self):
        return self.__frames

    def set_ramp_speed(self, ramp_speed):
        self.__ramp_speed = ramp_speed

    def default_ramp_speed(self):
        return self.__default_ramp_speed


class VideoObject:

    def __init__(self, video_name, focus_in, focus_out, timecode_in, timecode_out, video: Video, index, crop_top=50, crop_bottom=80, set_height=-1, fps=0):
        # video_name: name of video file
        # focus_in, focus_out : timecode in which the object is the main focus of the video
        # timecode_in, timecode_out : used to trim the video object to start at in and end at out
        self.__current_frame = 0
        self.__posY = 0
        self.__setHeight = int(set_height)
        self.__index = index
        self.__crop_top = crop_top
        self.__crop_bottom = crop_bottom
        self.__total_crop = crop_top + crop_bottom

        self.__video = video
        self.__name = video_name
        self.__focus_time = focus_out - focus_in
        self.__focus_in = focus_in
        self.__focus_out = focus_out
        self.__length = timecode_out - timecode_in
        self.__timecode_in = timecode_in
        self.__timecode_out = timecode_out

        if video_name == "":
            return

        self.__loader = cv2.VideoCapture(os.path.join("./source", video_name))
        self.__frame_length = int(self.__loader.get(cv2.CAP_PROP_FRAME_COUNT))

        self.__clip_speed = self.__length / self.__focus_time
        self.__posX = video.width()
        self.__height, self.__width, self.__fps = video_loader.get_info(self.__name)
        self.__fps = self.__fps if fps == 0 else fps
        self.__scale = self.__height/self.__setHeight if self.__setHeight != -1 else 1
        self.__height -= self.__total_crop * self.__scale

        self.__aspect = self.__width / self.__height

        self.__frames = []

    def jump_to_time(self, time):
        if time - self.__focus_in > self.__focus_time:
            self.jump_to((self.__timecode_in + self.__focus_time * self.__clip_speed) * self.__fps)
        else:
            dt = (time - self.__focus_in) * self.__clip_speed
            if dt > 0:
                frame_count = (self.__timecode_in + dt) * self.__fps
                self.jump_to(frame_count)
            else:
                self.jump_to(self.__timecode_in * self.__fps)

    def jump_to(self, frame_no):
        self.__current_frame = frame_no

    def next_frame(self):
        self.__current_frame += self.__clip_speed

    def load_to_memory(self):
        print("Loading " + self.__name + " to memory")

        starting_frame = self.__timecode_in * self.__fps
        ending_frame = self.__timecode_out * self.__fps + 1

        self.__frames = [[0] for _ in range(int(starting_frame - 1) if int(starting_frame) != 0 else 0)]
        self.__loader.set(cv2.CAP_PROP_POS_FRAMES, starting_frame)
        ret, frame = self.__loader.read()
        frame = cv2.resize(frame, (int(self.__width / self.__scale), self.__setHeight))

        if len(self.__frames) != 0:
            self.__frames[0] = frame

        frame_no = starting_frame
        while ret:
            frame_no += 1
            if frame_no < starting_frame:
                self.__frames.append([])
            elif frame_no <= ending_frame:
                self.__frames.append(frame)

            ret, frame = self.__loader.read()

            if frame is not None:
                frame = cv2.resize(frame, (int(self.__width / self.__scale), self.__setHeight))

    def __raw_frame(self, frame_no):
        if not self.__frames:
            self.load_to_memory()
        if frame_no < 0:
            return self.__frames[0]
        elif frame_no >= self.__frame_length:
            return self.__frames[-1]
        elif frame_no >= len(self.__frames):
            return self.__frames[-1]
        else:
            return self.__frames[int(frame_no)] if len(self.__frames[int(frame_no)]) > 1 else np.zeros((self.__setHeight, int(self.__width / self.__scale), 3), np.uint8)

    def get_frame(self):
        if self.__current_frame % 1 != 0:
            # If the frame number is not an integer, apply frame blending
            frame_no = int(self.__current_frame)
            alpha = self.__current_frame % 1

            frame_a = self.__raw_frame(frame_no)
            frame_b = self.__raw_frame(frame_no + 1)

            frame = cv2.addWeighted(frame_a, (1 - alpha), frame_b, alpha, 0.0)
        else:
            frame = self.__raw_frame(self.__current_frame)

        frame = cv2.resize(frame, (int(self.__width / self.__scale), self.__setHeight))

        return frame

    def focus_end(self):
        return self.__focus_out

    def focus_start(self):
        return self.__focus_in

    def index(self):
        return self.__index

    def width(self):
        if self.__setHeight == -1:
            return int(self.__width)
        else:
            return int(self.__setHeight * self.__aspect)

    def height(self):
        return int(self.__setHeight) if self.__setHeight != -1 else int(self.__height)

    def x(self):
        return self.__posX

    def set_x(self, x):
        self.__posX = int(x)

    def set_y(self, y):
        self.__posY = int(y)

    def set_height(self, height):
        self.__setHeight = int(height)

    def move(self, dx):
        self.__posX += int(dx)

    def crop_top(self):
        return self.__crop_top

    def focus_time(self):
        return self.__focus_time

    def release(self):
        if self.__frames:
            print("Releasing " + self.__name + " from memory")
            self.__frames = []

    def put_self(self, surface):
        image = self.get_frame()
        image = image[int(self.__crop_top): int(self.__height / self.__scale + self.__crop_top), 0: self.width()]
        image = cv2.resize(image, (int(self.height() / image.shape[0] * image.shape[1]), self.height()))
        if self.__posX < 0 and self.__posX + image.shape[1] > self.__video.width() :
            front_crop = fabs(self.__posX)
            rear_crop = image.shape[1] - self.__video.width() - front_crop
            object_cropped = image[0: int(self.height()), int(front_crop): int(self.width() - rear_crop)]
            surface[self.__posY: self.__posY + self.height(), 0: object_cropped.shape[1]] = object_cropped
        elif self.__posX < 0:
            crop_amount = fabs(self.__posX)
            object_image = image
            object_cropped = object_image[0: self.height(), int(crop_amount): self.width()]
            surface[self.__posY: self.__posY + self.height(), 0: object_cropped.shape[1]] = object_cropped
        elif self.__posX + image.shape[1] > self.__video.width():
            crop_amount = (self.__posX + self.width()) - self.__video.width()
            object_image = image
            object_cropped = object_image[0: self.height(), 0: int(self.width() - crop_amount)]
            surface[self.__posY: self.__posY + self.height(), self.__posX: self.__video.width()] = object_cropped
        else:
            surface[self.__posY: self.__posY + self.height(), self.__posX: self.__posX + image.shape[1]] = image
        return surface
