import cv2
from math import fabs
import video_loader
import os
import numpy as np


class Script:

    def __init__(self, script_array, spacing_rel_width: float = None, thresh_rel_width: float = None, height_rel__height: float = None, center_vertically=False):
        self.__script_array = script_array

        self.width = int(script_array[0][0])
        self.height = int(script_array[0][1])
        self.__fps = float(script_array[0][2])
        self.spacing = int(script_array[0][3])
        self.threshold = int(script_array[0][4])
        self.ramp_speed = float(script_array[0][5])
        self.__length = int(float(script_array[-1][2]) * self.__fps)
        self.target_height = -1
        self.y_offset = 0

        if spacing_rel_width is not None:
            self.relative_spacing(self.width, spacing_rel_width)

        if thresh_rel_width is not None:
            self.relative_threshold(self.width, thresh_rel_width)
            
        if height_rel__height is not None:
            self.relative_height(self.height, height_rel__height)

        if center_vertically and height_rel__height is not None:
            self.y_offset = int(((1 - height_rel__height) / 2) * self.height)

    def relative_spacing(self, relative_to, fraction):
        self.spacing = relative_to * fraction

    def relative_threshold(self, relative_to, fraction):
        self.threshold = relative_to * fraction
        
    def relative_height(self, relative_to, fraction):
        self.target_height = relative_to * fraction

    def set_fps(self, fps):
        self.__fps = fps
        self.__length = int(float(self.__script_array[-1][2]) * self.__fps)

    def video(self):
        return Video(self.__length, self.__fps, self.width, self.height, self.spacing, self.threshold, self.ramp_speed)

    def script_objects(self):
        objects = []
        for i in range(1, len(self.__script_array)):
            script_object = ScriptObject(self.__script_array[i], i - 1, self.target_height, self.y_offset)
            objects.append(script_object)
        return objects

    def video_objects(self):
        objects = []
        for script_object in self.script_objects():
            video_object = script_object.video_object(self.video())
            objects.append(video_object)
        return objects

    def extract(self):
        return self.video(), self.video_objects()

    def length(self):
        return self.__length


class ScriptObject:

    def __init__(self, line_data, index, target_height=-1, y_offset: int = 0):
        self.__name = line_data[0]
        self.__index = index
        self.in_time = float(line_data[1])
        self.out_time = float(line_data[2])
        self.trim_start = float(line_data[3])
        self.trim_end = float(line_data[4])
        self.fps_override = float(line_data[5])
        self.crop_top = int(line_data[6])
        self.crop_bottom = int(line_data[7])
        self.crop_left = int(line_data[8])
        self.crop_right = int(line_data[9])
        self.target_height = int(target_height)
        self.y_offset = int(y_offset)

    def name(self):
        return self.__name

    def raw(self):
        return [self.__name, self.in_time, self.out_time, self.trim_start, self.trim_end, self.fps_override, self.crop_top, self.crop_bottom, self.crop_left, self.crop_right]

    def video_object(self, video):
        return VideoObject(video, self.__index, script_object=self)


class Video:

    def __init__(self, length, fps, width, height, spacing=20, threshold=500, ramp_speed: float = 6):
        self.__length = length
        self.fps = fps
        self.__width = width
        self.__height = height
        self.__spacing = spacing
        self.__focus_threshold = threshold
        self.__ramp_speed = ramp_speed
        self.__default_ramp_speed = ramp_speed

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

    def set_ramp_speed(self, ramp_speed):
        self.__ramp_speed = ramp_speed

    def default_ramp_speed(self):
        return self.__default_ramp_speed


class VideoObject:

    def __init__(self, video: Video, index, video_name=None, focus_in=None, focus_out=None, timecode_in=None, timecode_out=None, crop_top=50, crop_bottom=80, crop_left=0, crop_right=0, set_height=-1, fps=0, script_object: ScriptObject = None):
        self.__current_frame = 0
        self.__posY = 0
        self.__index = index
        self.__video = video

        if script_object is None and video_name is None:
            raise RuntimeError("Either video name or ScriptObject must be provided when creating a VideoObject")
        elif script_object is not None:
            self.__name = script_object.name()

            self.__crop_top = script_object.crop_top
            self.__crop_bottom = script_object.crop_bottom
            self.__crop_left = script_object.crop_left
            self.__crop_right = script_object.crop_right

            self.__focus_in = script_object.in_time
            self.__focus_out = script_object.out_time

            self.__timecode_in = script_object.trim_start
            self.__timecode_out = script_object.trim_end

            self.__fps = script_object.fps_override
            
            self.__setHeight = script_object.target_height
            self.__posY = script_object.y_offset
        else:
            self.__name = video_name

            self.__crop_top = crop_top
            self.__crop_bottom = crop_bottom
            self.__crop_left = crop_left
            self.__crop_right = crop_right

            self.__focus_in = focus_in
            self.__focus_out = focus_out

            self.__timecode_in = timecode_in
            self.__timecode_out = timecode_out

            self.__fps = fps

            self.__setHeight = int(set_height)

        self.__total_crop_vert = self.__crop_top + self.__crop_bottom
        self.__total_crop_horizontal = self.__crop_left + self.__crop_right

        self.__focus_time = self.__focus_out - self.__focus_in
        self.__length = self.__timecode_out - self.__timecode_in

        if video_name == "":
            return

        self.__loader = cv2.VideoCapture(os.path.join("./source", self.__name))
        self.__frame_length = int(self.__loader.get(cv2.CAP_PROP_FRAME_COUNT))

        self.__clip_speed = self.__length / self.__focus_time
        self.__posX = video.width()
        self.__height, self.__width, actual_fps = video_loader.get_info(self.__name)
        self.__fps = actual_fps if self.__fps == 0 else self.__fps
        self.__scale = self.__height/self.__setHeight if self.__setHeight != -1 else 1
        self.__height -= self.__total_crop_vert * self.__scale
        self.__width -= self.__total_crop_horizontal * self.__scale

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
        image = image[int(self.__crop_top): int(self.__height / self.__scale + self.__crop_top), int(self.__crop_left): int(self.__width / self.__scale + self.__crop_left)]
        image = cv2.resize(image, (int(self.height() / image.shape[0] * image.shape[1]), self.height()))
        if self.__posX < 0 and self.__posX + image.shape[1] > self.__video.width():
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


class EmptyVideoObject(VideoObject):

    def __init__(self):
        return

    def focus_end(self):
        return 0

    def index(self):
        return -1
