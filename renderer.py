from classes import *
import csv
import numpy as np
from math import fabs
import cv2
import time as t


def render():

    with open("script.csv") as csv_file:
        reader = csv.reader(csv_file)
        script_raw = list(reader)

    script = Script(script_raw, thresh_rel_width=0.47, height_rel_height=0.9, center_vertically=True)
    script.relative_spacing(script.height, 0.05)
    video, objects = script.extract()

    out = cv2.VideoWriter("export.avi", cv2.VideoWriter_fourcc("M", "J", "P", "G"), video.fps,
                          (video.width(), video.height()))

    speed = video.width() * len(script_raw) / script.length()
    target_speed = speed

    focus_object: VideoObject = EmptyVideoObject()

    rendering = True
    frame_no = -1

    start_time = t.time()
    frame_count = 0

    while rendering:
        frame_no += 1
        frame_count += 1

        time = frame_no / video.fps

        frame = np.zeros((script.height, script.width, 3), np.uint8)

        if focus_object.index() != len(objects) - 1 and time >= focus_object.focus_end() or focus_object.index() == -1:
            focus_object = objects[focus_object.index() + 1]

        if focus_object.focus_end() > time:
            new_target_speed = (focus_object.x() + focus_object.width() - video.focus_threshold()) / (
                        focus_object.focus_end() - time) / video.fps
            if fabs(target_speed - new_target_speed) > video.default_ramp_speed() and focus_object.focus_start() > time:
                video.set_ramp_speed(1.1*fabs(target_speed - new_target_speed))
            else:
                video.set_ramp_speed(video.default_ramp_speed())
            target_speed = new_target_speed
        else:
            target_speed = speed

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


if __name__ == '__main__':
    render()
