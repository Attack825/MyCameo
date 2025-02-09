import cv2
from window_manager import WindowManager
import numpy
import time
import sys


class CaptureManager(object):
    """The CaptureManager class manages the capture process."""

    def __init__(
        self,
        capture: cv2.VideoCapture,
        previewWindowManager: WindowManager = None,
        shouldMirrorPreview: bool = False,
        insertInterval: int = sys.maxsize,  # 通过插帧控制速率
    ):
        # public properties
        self.previewWindowManager: WindowManager = previewWindowManager
        self.shouldMirrorPreview: bool = shouldMirrorPreview

        # private properties for video capture
        self._capture: cv2.VideoCapture = capture
        self._enteredFrame: bool = False  # True if the next call to read() retrieves
        self._frame: cv2.typing.MatLike = None
        self.insertInterval = insertInterval

        # private properties for video processing
        self._channel: int = 0
        self._imageFilename: str = None
        self._videoFilename: str = None
        self._videoEncoding: int = None
        self._videoWriter: cv2.VideoWriter = None

        # private properties for FPS estimation
        self._startTime: float = None
        self._framesElapsed: int = 0
        self._fpsEstimate: float = None

    # ==================================================================================================
    # The CaptureManager class has the following properties:

    @property
    def channel(self) -> int:
        return self._channel

    @channel.setter
    def channel(self, value: int):
        if self._channel != value:
            self._channel = value
            self._frame = None

    @property
    def frame(self):
        if self._enteredFrame and self._frame is None:
            _, self._frame = self._capture.retrieve(self._frame, self.channel)

        return self._frame

    @property
    def isWritingImage(self):
        return self._imageFilename is not None

    @property
    def isWritingVideo(self):
        return self._videoFilename is not None

    @property
    def framesElapsed(self):
        return self._framesElapsed

    # ==================================================================================================
    # The CaptureManager class has the following methods:

    def enterFrame(self):
        """
        Capture the next frame, if any.
        """

        # But first, check that any previous frame was exited.
        assert not self._enteredFrame, (
            "previous enterFrame() had no matching exitFrame()"
        )

        if self._capture is not None:
            if self._framesElapsed % self.insertInterval == 0:
                self._enteredFrame = True  # 置为True，但是并没有移动指针
            else:
                self._enteredFrame = self._capture.grab()

    def exitFrame(self):
        """
        Draw to the window. Write to _videoWriter. Release the frame.
        """
        # Check whether any grabbed frame is retrievable.
        # The getter may retrieve and cache the frame.
        if self.frame is None:
            self._enteredFrame = False
            return

        #

        # Update the FPS estimate and related variables.
        if self._framesElapsed == 0:
            self._startTime = time.time()
        else:
            timeElapsed = time.time() - self._startTime
            self._fpsEstimate = self._framesElapsed / timeElapsed
            # print(self._fpsEstimate)
        self._framesElapsed += 1

        # Draw to the window, if any.
        if self.previewWindowManager is not None:
            if self.shouldMirrorPreview:
                mirroredFrame = numpy.fliplr(self._frame)
                self.previewWindowManager.show(mirroredFrame)
            else:
                self.previewWindowManager.show(self._frame)

        # Write to the image file, if any.
        if self.isWritingImage:
            cv2.imwrite(self._imageFilename, self._frame)
            self._imageFilename = None

        # Write to the video file, if any.
        self._writeVideoFrame()

        # Release the frame.
        self._frame = None
        self._enteredFrame = False

    def writeImage(self, filename):
        """
        Write the next exited frame to an image file.
        """
        self._imageFilename = filename

    def startWritingVideo(
        self, filename, encoding=cv2.VideoWriter_fourcc("M", "J", "P", "G")
    ):
        """
        Start writing exited frames to a video file.
        """
        self._videoFilename = filename
        self._videoEncoding = encoding

    def stopWritingVideo(self):
        """
        Stop writing exited frames to a video file.
        """
        self._videoFilename = None
        self._videoEncoding = None
        self._videoWriter = None

    def _writeVideoFrame(self):
        """
        Write the next exited frame to the _videoWriter.
        """
        if not self.isWritingVideo:
            return

        if self._videoWriter is None:
            fps = self._capture.get(cv2.CAP_PROP_FPS)
            if fps <= 0.0:
                # The capture's FPS is unknown so use an estimate.
                if self._framesElapsed < 20:
                    # Wait until more frames elapse so that the
                    # estimate is more stable.
                    return
                else:
                    fps = self._fpsEstimate
            size = (
                int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            )
            self._videoWriter = cv2.VideoWriter(
                self._videoFilename, self._videoEncoding, fps, size
            )

        self._videoWriter.write(self._frame)

    # ==================================================================================================
    # I will expand CaptureManager to support custom features
    # for example:
    # - a method to set the videos resolution
    # - a method to set the video start frame
    # - a method to slow down the video speed by inserting frames

    def jumpToFrame(self, start_frame: int) -> bool:
        """
        跳转到指定帧。
        :param start_frame: 目标帧号
        :return: 如果成功跳转，返回 True；否则返回 False
        """
        start_frame = int(start_frame)

        if not self._capture.isOpened():
            print("Error: Video capture object is not opened.")
            return False

        # 获取视频的总帧数
        total_frames = int(self._capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if start_frame < 0 or start_frame >= total_frames:
            print(
                f"Error: Target frame {start_frame} is out of range (0 to {total_frames - 1})."
            )
            return False

        # 跳转到指定帧
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        # 验证是否成功跳转
        current_frame = int(self._capture.get(cv2.CAP_PROP_POS_FRAMES))
        if current_frame == start_frame:
            return True
        else:
            print(
                f"Error: Failed to jump to frame {start_frame}. Current frame is {current_frame}."
            )
            return False

    def cropFrame(self, x, y, h, w):
        """
        Crop the frame to the specified size.
        """
        self._frame = self._frame[y : y + h, x : x + w]

    def adjustVideoResolution(self, width: int, height: int):
        """
        Adjust the resolution of the video.
        """
        self._frame = cv2.resize(self._frame, (width, height))
