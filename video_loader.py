import cv2
import os


def get_frame(video, frame_no):
    loader = cv2.VideoCapture(os.path.join("./source", video))

    length = int(loader.get(cv2.CAP_PROP_FRAME_COUNT))

    if frame_no < 0:
        frame_no = 0
    elif frame_no >= length:
        frame_no = length - 1

    loader.set(cv2.CAP_PROP_POS_FRAMES, frame_no - 1 if frame_no != 0 else 0)

    ret, frame = loader.read()

    loader.release()

    return frame


def get_info(video):
    loader = cv2.VideoCapture(os.path.join("./source", video))

    ret, frame = loader.read()

    fps = loader.get(cv2.CAP_PROP_FPS)

    loader.release()

    return frame.shape[0], frame.shape[1], fps
