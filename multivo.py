# Rewritten clip.output() with interleaved video outputs for multiple destinations
# Mostly taken from old VapourSynth source codes
from __future__ import annotations
from typing import BinaryIO, Optional, Sequence, Set, TextIO, Union
import io

import vapoursynth as vs
assert vs.__version__.release_major >= 61

__all__ = ['SIMO', 'MIMO']

def y4m_header(clip: vs.VideoNode) -> str:
    assert clip.format
    if clip.format.color_family == vs.GRAY:
        y4mformat = 'mono'
        if clip.format.bits_per_sample > 8:
            y4mformat = y4mformat + str(clip.format.bits_per_sample)
    elif clip.format.color_family == vs.YUV:
        if clip.format.subsampling_w == 1 and clip.format.subsampling_h == 1:
            y4mformat = '420'
        elif clip.format.subsampling_w == 1 and clip.format.subsampling_h == 0:
            y4mformat = '422'
        elif clip.format.subsampling_w == 0 and clip.format.subsampling_h == 0:
            y4mformat = '444'
        elif clip.format.subsampling_w == 2 and clip.format.subsampling_h == 2:
            y4mformat = '410'
        elif clip.format.subsampling_w == 2 and clip.format.subsampling_h == 0:
            y4mformat = '411'
        elif clip.format.subsampling_w == 0 and clip.format.subsampling_h == 1:
            y4mformat = '440'
        if clip.format.bits_per_sample > 8:
            y4mformat = y4mformat + 'p' + str(clip.format.bits_per_sample)
    else:
        raise ValueError('Input clip has RGB color format which is not supported')

    y4mformat = 'C' + y4mformat + ' '

    header = 'YUV4MPEG2 {y4mformat}W{width} H{height} F{fps_num}:{fps_den} Ip A0:0 XLENGTH={length}\n'.format(
        y4mformat=y4mformat,
        width=clip.width,
        height=clip.height,
        fps_num=clip.fps.numerator,
        fps_den=clip.fps.denominator,
        length=len(clip)
    )

    return header


def SIMO(clip: vs.VideoNode,
         files: Sequence[Optional[Union[BinaryIO, TextIO]]],
         y4m: bool = True,
         backlog: Optional[int] = None) -> None:
    '''
    Single-Input-Multiple-Output
    '''
    num_files = len(files)
    assert num_files > 0
    assert clip.format

    use_y4m = False
    if y4m and clip.format.color_family in (vs.YUV, vs.GRAY):
        use_y4m = True
        header = y4m_header(clip)
        files_set: Set[BinaryIO] = set()
        for fileobj in files:
            if fileobj is None:
                continue
            if isinstance(fileobj, io.TextIOWrapper):
                fileobj = fileobj.buffer
            if fileobj not in files_set:
                fileobj.write(header.encode('ascii'))
                files_set.add(fileobj)
        del files_set

    if backlog is None:
        backlog = 3 * num_files
    for frame in clip.frames(backlog=backlog, close=True):
        for fileobj in files:
            if fileobj is None:
                continue
            if isinstance(fileobj, io.TextIOWrapper):
                fileobj = fileobj.buffer
            if use_y4m:
                fileobj.write(b'FRAME\n')
            for chunk in frame.readchunks():
                fileobj.write(chunk)
            fileobj.flush()


def MIMO(clips: Sequence[vs.VideoNode],
         files: Sequence[Optional[Union[BinaryIO, TextIO]]],
         y4m: bool = True,
         backlog: Optional[int] = None) -> None:
    '''
    Multiple-Input-Multiple-Output
    '''
    num_clips = len(clips)
    num_files = len(files)
    assert num_clips > 0
    assert num_clips == num_files
    for clip in clips:
        assert clip.format

    max_len = max(len(clip) for clip in clips)
    clips_aligned: list[vs.VideoNode] = []
    for clip in clips:
        if len(clip) < max_len:
            clip_aligned = clip + vs.core.std.BlankClip(clip, length=max_len - len(clip))
        else:
            clip_aligned = clip
        clips_aligned.append(vs.core.std.Interleave([clip_aligned] * num_clips))
    clips_vf = vs.core.std.BlankClip(length=max_len * num_clips, varformat=True, varsize=True)
    def _interleave(n: int) -> vs.VideoNode:
        return clips_aligned[n % num_clips]
    interleaved = vs.core.std.FrameEval(clips_vf, _interleave)

    use_y4m = [False] * num_clips
    if y4m:
        files_set: Set[BinaryIO] = set()
        for n, clip in enumerate(clips):
            if clip.format.color_family in (vs.YUV, vs.GRAY):
                use_y4m[n] = True
                header = y4m_header(clip)
                fileobj = files[n]
                if fileobj is None:
                    continue
                if isinstance(fileobj, io.TextIOWrapper):
                    fileobj = fileobj.buffer
                if fileobj not in files_set:
                    fileobj.write(header.encode('ascii'))
                    files_set.add(fileobj)
        del files_set

    if backlog is None:
        backlog = 3 * num_files
    for idx, frame in enumerate(interleaved.frames(backlog=backlog, close=True)):
        n = idx % num_clips
        clip = clips[n]
        finished = idx // num_clips
        if finished < len(clip):
            fileobj = files[n]
            if fileobj is None:
                continue
            if isinstance(fileobj, io.TextIOWrapper):
                fileobj = fileobj.buffer
            if use_y4m[n]:
                fileobj.write(b'FRAME\n')
            for chunk in frame.readchunks():
                fileobj.write(chunk)
            fileobj.flush()
