from classes import *
import csv
import numpy as np
from math import fabs
import cv2
import time as t
from multiprocessing import Process


def padding(video: Video):
    return video.width()*0.05


def render():

    render_size = (1920, 1080)
    fps = 24

    with open("script.csv") as csv_file:
        reader = csv.reader(csv_file)
        script = list(reader)

    total_length = int(float(script[-1][2]) * fps)

    video = Video(total_length, fps, render_size[0], render_size[1], spacing=render_size[1]*0.05, threshold=0.47*render_size[0], ramp_speed=0.4)
    objects = initialise_objects(script, for_video=video)

    out = cv2.VideoWriter("output3.avi", cv2.VideoWriter_fourcc("M", "J", "P", "G"), video.fps,
                          (video.width(), video.height()))

    speed = video.width() * len(script) / total_length
    target_speed = speed

    focus_object: VideoObject = VideoObject("", 0, -1, 0, -1, video, -1)

    rendering = True
    frame_no = -1

    start_time = t.time()
    frame_count = 0

    while rendering:
        frame_no += 1
        frame_count += 1

        time = frame_no / fps

        frame = np.zeros((render_size[1], render_size[0], 3), np.uint8)

        if focus_object.index() != len(objects) - 1 and time >= focus_object.focus_end() or focus_object.index() == -1:
            focus_object = objects[focus_object.index() + 1]

        if focus_object.focus_end() > time:
            target_speed = (focus_object.x() + focus_object.width() - video.focus_threshold()) / (focus_object.focus_end() - time) / video.fps
        else:
            target_speed = speed

        # print(str(speed) + "->" + str(target_speed))

        if fabs(target_speed - speed) < video.ramp_speed():
            speed = target_speed

        if target_speed > speed:
            speed += video.ramp_speed()
        elif target_speed < speed:
            speed -= video.ramp_speed()

        focus_object.move((-1) * speed)
        focus_object.jump_to_time(time)
        if focus_object.x() + focus_object.width() < 0:
            rendering = False
        else:
            frame = focus_object.put_self(frame)

        objects_on_screen = []

        f_offset = video.object_spacing() + focus_object.width()
        for fwd in range(1, len(objects) - focus_object.index()):
            obj: VideoObject = objects[focus_object.index() + fwd]
            if f_offset + focus_object.x() <= video.width():
                obj.set_x(f_offset + focus_object.x())
                objects_on_screen.append(obj)
            else:
                break
            f_offset += obj.width() + video.object_spacing()

        b_offset = video.object_spacing()
        for bck in range(1, focus_object.index() + 1):
            obj: VideoObject = objects[focus_object.index() - bck]
            if focus_object.x() - b_offset >= 0:
                obj.set_x(focus_object.x() - b_offset - obj.width())
                objects_on_screen.append(obj)
            else:
                obj.release()
                break
            b_offset += obj.width() + video.object_spacing()

        for each_on_screen in objects_on_screen:
            each_on_screen.jump_to_time(time)
            frame = each_on_screen.put_self(frame)

        if t.time() - start_time > 5:
            print("Rendering average: " + str(frame_count/(t.time() - start_time)) + " fps")
            start_time = t.time()
            frame_count = 0
            print("Timeline Time: " + str(time))

        cv2.imshow("Rendering Preview", cv2.resize(frame, (640, 360)))
        cv2.waitKey(5)

        out.write(frame)
    out.release()


def initialise_objects(script, for_video: Video):
    objects = []

    i = 0
    for each_object in script:
        obj = VideoObject(each_object[0], float(each_object[1]), float(each_object[2]), float(each_object[3]), float(each_object[4]), for_video, i, set_height=for_video.height() - padding(for_video), fps=float(each_object[5]), crop_top=int(each_object[6]), crop_bottom=int(each_object[7]))
        obj.set_y(padding(for_video)/2)
        objects.append(obj)
        i += 1

    return objects

if __name__ == '__main__':
    render()
