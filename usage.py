import subprocess
import vapoursynth as vs
from multivo import SIMO, MIMO

def SIMO_example():
    clip = vs.core.std.BlankClip(format=vs.YUV420P10).text.FrameNum()
    encode_1 = subprocess.Popen(['x265.exe', '--y4m', '-o', '1.hevc', '-'], stdin=subprocess.PIPE)
    encode_2 = subprocess.Popen(['x265.exe', '--y4m', '-o', '2.hevc', '-'], stdin=subprocess.PIPE)
    SIMO(clip, [encode_1.stdin, encode_2.stdin])
    encode_1.communicate()
    encode_2.communicate()
    encode_1.wait()
    encode_2.wait()


def MIMO_example_1():
    clip_1 = vs.core.std.BlankClip(format=vs.YUV420P10, width=1280, height=720, length=2000).text.FrameNum()
    clip_2 = vs.core.resize.Point(clip_2, 640, 480)[:1000]
    encode_1 = subprocess.Popen(['x265.exe', '--y4m', '-o', '1.hevc', '-'], stdin=subprocess.PIPE)
    encode_2 = subprocess.Popen(['x265.exe', '--y4m', '-o', '2.hevc', '-'], stdin=subprocess.PIPE)
    MIMO([clip_1, clip_2], [encode_1.stdin, encode_2.stdin])
    encode_1.communicate()
    encode_2.communicate()
    encode_1.wait()
    encode_2.wait()


def MIMO_example_2():
    clip = vs.core.std.BlankClip(format=vs.YUV420P10, length=2000).text.FrameNum()
    clip_0 = clip[0::2]
    clip_1 = clip[1::2]
    encode_1 = subprocess.Popen(['x265.exe', '--y4m', '-o', '1.hevc', '-'], stdin=subprocess.PIPE)
    encode_2 = subprocess.Popen(['x265.exe', '--y4m', '-o', '2.hevc', '-'], stdin=subprocess.PIPE)
    MIMO([clip_0, clip_0, clip_1], [encode_1.stdin, encode_2.stdin, encode_2.stdin])
    encode_1.communicate()
    encode_2.communicate()
    encode_1.wait()
    encode_2.wait()
