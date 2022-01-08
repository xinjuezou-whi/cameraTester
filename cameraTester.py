# --------------------------------------------------------
# Camera sample code for Raspberry Pi or Jetson series
#
# This program could capture and display video from
# IP CAM, USB webcam, or the Tegra onboard camera.
# Refer to the following blog post for how to set up
# and run the code:
#
# Refactored by xinjue.zou@outlook.com
#
# Origin by JK Jung <jkjung13@gmail.com>
# --------------------------------------------------------


import sys
import argparse
import subprocess

import cv2


WINDOW_NAME = 'CameraTester'


def parse_args():
    # Parse input arguments
    desc = "capture and display live camera video on Raspberry Pi or Jetson TX2/TX1"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--raspi", dest="isJetson",
                        help="specify as Raspberry Pi board",
                        action="store_false")
    parser.add_argument("--jetson", dest="isJetson",
                        help="specify as Jeston series board",
                        action="store_true")
    parser.add_argument("--rtsp", dest="useRtsp",
                        help="use IP CAM (remember to also set --uri)",
                        action="store_true")
    parser.add_argument("--uri", dest="rtspUri",
                        help="RTSP URI, e.g. rtsp://192.168.1.64:554",
                        default=None, type=str)
    parser.add_argument("--latency", dest="rtspLatency",
                        help="latency in ms for RTSP [200]",
                        default=200, type=int)
    parser.add_argument("--usb", dest="useUsb",
                        help="use USB webcam (remember to also set --vid)",
                        action="store_true")
    parser.add_argument("--vid", dest="videoDev",
                        help="device # of USB webcam (/dev/video?) [1]",
                        default=1, type=int)
    parser.add_argument("--width", dest="imageWidth",
                        help="image width [1920]",
                        default=1920, type=int)
    parser.add_argument("--height", dest="imageHeight",
                        help="image height [1080]",
                        default=1080, type=int)
    args = parser.parse_args()
    return args


def open_cam_usb(isJetson, dev, width, height):
    # We want to set width and height here, otherwise we could just do:
    #   return cv2.VideoCapture(dev)
    if isJetson:
        gstStr = ("v4l2src device=/dev/video{} ! "
            "video/x-raw, width=(int){}, height=(int){} ! "
            "videoconvert ! appsink").format(dev, width, height)
        return cv2.VideoCapture(gstStr, cv2.CAP_GSTREAMER)
    else:
        cap = cv2.VideoCapture(dev)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        return cap


def open_cam_onboard(isJetson, width, height):
    if isJetson:
        gstElements = str(subprocess.check_output("gst-inspect-1.0"))
        if "nvcamerasrc" in gstElements:
            # On versions of L4T prior to 28.1, add "flip-method=2" into gstStr
            gstStr = ("nvcamerasrc ! "
                   "video/x-raw(memory:NVMM), "
                   "width=(int)2592, height=(int)1458, "
                   "format=(string)I420, framerate=(fraction)30/1 ! "
                   "nvvidconv ! "
                   "video/x-raw, width=(int){}, height=(int){}, "
                   "format=(string)BGRx ! "
                   "videoconvert ! appsink").format(width, height)
        elif "nvarguscamerasrc" in gstElements:
            gstStr = ("nvarguscamerasrc ! "
                   "video/x-raw(memory:NVMM), "
                   "width=(int)1920, height=(int)1080, "
                   "format=(string)NV12, framerate=(fraction)30/1 ! "
                   "nvvidconv flip-method=2 ! "
                   "video/x-raw, width=(int){}, height=(int){}, "
                   "format=(string)BGRx ! "
                   "videoconvert ! appsink").format(width, height)
        else:
            raise RuntimeError("onboard camera source not found!")

        return cv2.VideoCapture(gstStr, cv2.CAP_GSTREAMER)
    else:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        return cap


def open_cam_rtsp(isJetson, uri, width, height, latency):
    if isJetson:
        gst_str = ('rtspsrc location={} latency={} ! '
               'rtph264depay ! h264parse ! omxh264dec ! '
               'nvvidconv ! '
               'video/x-raw, width=(int){}, height=(int){}, '
               'format=(string)BGRx ! '
               'videoconvert ! appsink').format(uri, latency, width, height)
        return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
    else:
        cap = cv2.VideoCapture(uri)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        return cap


def open_window(width, height):
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, width, height)
    cv2.moveWindow(WINDOW_NAME, 0, 0)
    cv2.setWindowTitle(WINDOW_NAME, 'Camera tester for Raspberry Pi or Jetson TX2/TX1')


def read_cam(cap):
    show_help = True
    full_scrn = False
    help_text = '"Esc" to Quit, "H" for Help, "F" to Toggle Fullscreen'
    font = cv2.FONT_HERSHEY_PLAIN
    while True:
        if cv2.getWindowProperty(WINDOW_NAME, 0) < 0:
            # Check to see if the user has closed the window
            # If yes, terminate the program
            break
        ret, img = cap.read() # grab the next image frame from camera
        if show_help:
            cv2.putText(img, help_text, (11, 20), font,
                        1.0, (32, 32, 32), 4, cv2.LINE_AA)
            cv2.putText(img, help_text, (10, 20), font,
                        1.0, (240, 240, 240), 1, cv2.LINE_AA)
        cv2.imshow(WINDOW_NAME, img)
        key = cv2.waitKey(10)
        if key == 27: # ESC key: quit program
            break
        elif key == ord('H') or key == ord('h'): # toggle help message
            show_help = not show_help
        elif key == ord('F') or key == ord('f'): # toggle fullscreen
            full_scrn = not full_scrn
            if full_scrn:
                cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_NORMAL)


def main():
    args = parse_args()
    print('Called with args:')
    print(args)
    print('OpenCV version: {}'.format(cv2.__version__))

    if args.use_rtsp:
        cap = open_cam_rtsp(args.isJetson,
                            args.rtspUri,
                            args.imageWidth,
                            args.imageHeight,
                            args.rtspLatency)
    elif args.use_usb:
        cap = open_cam_usb(args.isJetson,
                            args.videoDev,
                            args.imageWidth,
                            args.imageHeight)
    else: # by default, use the Jetson onboard camera
        cap = open_cam_onboard(args.isJetson,
                                args.imageWidth,
                                args.imageHeight)

    if not cap.isOpened():
        sys.exit('Failed to open camera!')

    open_window(args.imageWidth, args.imageHeight)
    read_cam(cap)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
