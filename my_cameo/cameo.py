import cv2
from window_manager import WindowManager
from capture_manager import CaptureManager


class MyCameo(object):
    def __init__(self):
        self._windowManager = WindowManager("MyCameo", self.onKeypress)
        # cv2.VideoCapture(0) opens the default camera
        # or pass the path to a video file to open it. e.g. cv2.VideoCapture("video.mp4")
        self._captureManager = CaptureManager(
            cv2.VideoCapture(0), self._windowManager, True
        )

    def run(self):
        """
        Run the main loop.
        """
        self._windowManager.createWindow()
        while self._windowManager.isWindowCreated:
            self._captureManager.enterFrame()
            frame: cv2.typing.MatLike = self._captureManager.frame

            if frame is not None:
                # TODO: Filter the frame
                pass

            self._captureManager.exitFrame()
            self._windowManager.processEvents()

    def onKeypress(self, keycode: int):
        """
        Handle a keypress.

        Keycode values:\n
            space  -> Take a screenshot.\n
            tab    -> Start/stop recording a screencast.\n
            escape -> Quit.
        """
        if keycode == 32:  # space
            self._captureManager.writeImage("screenshot.png")
        elif keycode == 9:  # tab
            if not self._captureManager.isWritingVideo:
                self._captureManager.startWritingVideo("screencast.avi")
            else:
                self._captureManager.stopWritingVideo()
        elif keycode == 27:  # escape
            self._windowManager.destroyWindow()

    def preprocess(self, video_path: str):
        self._captureManager = CaptureManager(
            cv2.VideoCapture(video_path), self._windowManager, False
        )
        self._windowManager.createWindow()
        # 跳转到指定帧
        _ = self._captureManager.jumpToFrame(start_frame=138.8 * 25)

        while self._windowManager.isWindowCreated:
            self._captureManager.enterFrame()
            frame: cv2.typing.MatLike = self._captureManager.frame

            if frame is not None:
                self._captureManager.cropFrame(0, 0, 1920, 1080)
                self._captureManager.adjustVideoResolution(640, 512)
                pass

            self._captureManager.exitFrame()
            self._windowManager.processEvents()


if __name__ == "__main__":
    # MyCameo().run()
    MyCameo().preprocess(r"raw_video\output_rgb.mp4")
