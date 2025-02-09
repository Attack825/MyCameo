# BSD 3-Clause License

# Copyright (c) 2019, Nummist Media Corporation Limited, Joseph Howse, and
# Joe Minichino.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# - Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# - Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import cv2
import numpy
import pygame
import time
import utils


class WindowManager(object):
    def __init__(self, windowName, keypressCallback=None):
        self.keypressCallback = keypressCallback

        self._windowName = windowName
        self._isWindowCreated = False

    @property
    def isWindowCreated(self):
        return self._isWindowCreated

    def createWindow(self):
        cv2.namedWindow(self._windowName)
        self._isWindowCreated = True

    def show(self, frame):
        cv2.imshow(self._windowName, frame)

    def destroyWindow(self):
        cv2.destroyWindow(self._windowName)
        self._isWindowCreated = False

    def processEvents(self):
        keycode = cv2.waitKey(1)
        if self.keypressCallback is not None and keycode != -1:
            self.keypressCallback(keycode)


class PygameWindowManager(WindowManager):
    def createWindow(self):
        pygame.display.init()
        pygame.display.set_caption(self._windowName)
        self._isWindowCreated = True

    def show(self, frame):
        # Find the frame's dimensions in (w, h) format.
        frameSize = frame.shape[1::-1]

        # Convert the frame to RGB, which Pygame requires.
        if utils.isGray(frame):
            conversionType = cv2.COLOR_GRAY2RGB
        else:
            conversionType = cv2.COLOR_BGR2RGB
        rgbFrame = cv2.cvtColor(frame, conversionType)

        # Convert the frame to Pygame's Surface type.
        pygameFrame = pygame.image.frombuffer(rgbFrame.tostring(), frameSize, "RGB")

        # Resize the window to match the frame.
        displaySurface = pygame.display.set_mode(frameSize)

        # Blit and display the frame.
        displaySurface.blit(pygameFrame, (0, 0))
        pygame.display.flip()

    def destroyWindow(self):
        pygame.display.quit()
        self._isWindowCreated = False

    def processEvents(self):
        """
        Handle Pygame events by checking for keypresses and window closure.

        通过检查按键和窗口关闭来处理 Pygame 事件。
        """
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and self.keypressCallback is not None:
                self.keypressCallback(event.key)
            elif event.type == pygame.QUIT:
                self.destroyWindow()
                return

    def saveScreenshot(self, filename):
        pygame.image.save(pygame.display.get_surface(), filename)

class CaptureManager(object):
    """
    管理视频捕获设备的类，提供帧捕获、显示和保存功能。
    
    Attributes:
        previewWindowManager: 窗口管理器实例。
        shouldMirrorPreview: 是否镜像预览。
        _capture: cv2.VideoCapture 实例。
        _channel: 当前通道。
        _enteredFrame: 是否进入帧。
        _frame: 当前帧。
        _imageFilename: 图像文件名。
        _videoFilename: 视频文件名。
        _videoEncoding: 视频编码。
        _videoWriter: cv2.VideoWriter 实例。
        _startTime: 开始时间。
        _framesElapsed: 帧数。
        _fpsEstimate: FPS 估计。
    """

    def __init__(
        self,
        capture: cv2.VideoCapture,
        previewWindowManager: WindowManager = None,
        shouldMirrorPreview: bool = False,
    ):
        self.previewWindowManager: WindowManager = previewWindowManager
        self.shouldMirrorPreview: bool = shouldMirrorPreview

        self._capture: cv2.VideoCapture = capture
        self._channel: int = 0
        self._enteredFrame: bool = False
        self._frame: cv2.typing.MatLike = None
        self._imageFilename: str = None
        self._videoFilename: str = None
        self._videoEncoding: int = (
            None  # 使用 cv2的VideoWriter_fourcc函数来创建视频编码器
        )
        self._videoWriter: cv2.VideoWriter = None

        self._startTime: float = None
        self._framesElapsed: int = 0
        self._fpsEstimate: float = None

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

    def enterFrame(self):
        """
        Capture the next frame, if any.

        捕获下一帧，如果有的话。
        """

        # But first, check that any previous frame was exited.
        assert not self._enteredFrame, (
            "previous enterFrame() had no matching exitFrame()"
        )

        if self._capture is not None:
            self._enteredFrame = self._capture.grab()

    def exitFrame(self):
        """
        Draw to the window. Write to _videoWriter. Release the frame.

        在窗口中绘制，写入_videoWriter，释放帧。
        同时，对于每一帧判断是否需要写入图像文件或视频文件。
        """

        # Check whether any grabbed frame is retrievable.
        # The getter may retrieve and cache the frame.
        if self.frame is None:
            self._enteredFrame = False
            return

        # Update the FPS estimate and related variables.
        if self._framesElapsed == 0:
            self._startTime = time.time()
        else:
            timeElapsed = time.time() - self._startTime
            self._fpsEstimate = self._framesElapsed / timeElapsed
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

        把下一帧写入图像文件。
        """
        self._imageFilename = filename

    def startWritingVideo(
        self, filename, encoding=cv2.VideoWriter_fourcc("M", "J", "P", "G")
    ):
        """
        Start writing exited frames to a video file.

        开始把已退出的帧写入视频文件。
        """
        self._videoFilename = filename
        self._videoEncoding = encoding

    def stopWritingVideo(self):
        """
        Stop writing exited frames to a video file.

        停止将已退出的帧写入视频文件。
        """
        self._videoFilename = None
        self._videoEncoding = None
        self._videoWriter = None

    def _writeVideoFrame(self):
        """
        Write the next exited frame to the _videoWriter.

        把下一帧写入 _videoWriter。
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
