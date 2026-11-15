"""Only this adapter imports pyrealsense2. No hardware import at package load."""
import importlib
import time

import numpy as np

from .models import Frame, Intrinsics


def sdk():
    try:
        return importlib.import_module("pyrealsense2")
    except ImportError as exc:
        raise RuntimeError("pyrealsense2 missing: install the [camera] extra; see docs/setup.md") from exc


def _info(device, rs, name):
    key = getattr(rs.camera_info, name)
    return device.get_info(key) if device.supports(key) else None


def inspect_devices() -> dict:
    rs = sdk()
    result = {"sdk_version": getattr(rs, "__version__", "unknown"), "devices": []}
    for device in rs.context().query_devices():
        entry = {name: _info(device, rs, name) for name in
                 ("name", "serial_number", "firmware_version", "usb_type_descriptor")}
        entry["sensors"] = []
        for sensor in device.query_sensors():
            profiles = []
            for profile in sensor.get_stream_profiles():
                p = {"stream": str(profile.stream_type()), "index": profile.stream_index(),
                     "format": str(profile.format()), "fps": profile.fps()}
                if profile.is_video_stream_profile():
                    video = profile.as_video_stream_profile()
                    k = video.get_intrinsics()
                    p.update(width=video.width(), height=video.height(), intrinsics={
                        "fx": k.fx, "fy": k.fy, "ppx": k.ppx, "ppy": k.ppy,
                        "model": str(k.model), "coeffs": list(k.coeffs)})
                profiles.append(p)
            options = []
            for option in sensor.get_supported_options():
                r = sensor.get_option_range(option)
                options.append({"name": str(option), "value": sensor.get_option(option),
                                "min": r.min, "max": r.max, "step": r.step,
                                "default": r.default, "read_only": sensor.is_option_read_only(option)})
            entry["sensors"].append({"name": sensor.get_info(rs.camera_info.name),
                                     "profiles": profiles, "options": options})
        result["devices"].append(entry)
    return result


class CameraSource:
    def __init__(self, config, playback=None, record=None, count=300):
        if playback and record:
            raise ValueError("Native recording and playback are mutually exclusive")
        self.config, self.playback, self.record, self.count = config, playback, record, count
        self.pipeline = None
        self._ray_key, self._rays = None, None

    def __enter__(self):
        self.rs = rs = sdk()
        cfg = rs.config()
        if self.playback:
            cfg.enable_device_from_file(str(self.playback), repeat_playback=False)
        else:
            if self.config.serial:
                cfg.enable_device(self.config.serial)
            cfg.enable_stream(rs.stream.depth, self.config.depth_width,
                              self.config.depth_height, rs.format.z16, self.config.fps)
            cfg.enable_stream(rs.stream.color, self.config.color_width,
                              self.config.color_height, rs.format.rgb8, self.config.fps)
        if self.record:
            from pathlib import Path
            path = Path(self.record)
            if path.exists():
                raise FileExistsError(f"Refusing to overwrite {path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            cfg.enable_record_to_file(str(path))
        self.pipeline = rs.pipeline()
        started = False
        try:
            if not cfg.can_resolve(rs.pipeline_wrapper(self.pipeline)):
                raise RuntimeError("Stream combination unavailable. Run rs-lab inspect; check USB and configs.")
            self.profile = self.pipeline.start(cfg)
            started = True
            if self.playback:
                self.profile.get_device().as_playback().set_real_time(False)
            self.scale = self.profile.get_device().first_depth_sensor().get_depth_scale()
            self.align = rs.align(rs.stream.color)
            self.threshold = rs.threshold_filter(self.config.min_depth_m, self.config.max_depth_m)
            self.to_disparity, self.to_depth = rs.disparity_transform(True), rs.disparity_transform(False)
            self.spatial = rs.spatial_filter() if self.config.spatial else None
            self.temporal = rs.temporal_filter() if self.config.temporal else None
            self.holes = rs.hole_filling_filter() if self.config.hole_filling else None
        except Exception:
            if started:
                self.pipeline.stop()
            self.pipeline = None
            raise
        return self

    def __exit__(self, *_):
        if self.pipeline is not None:
            self.pipeline.stop()
            self.pipeline = None
        return False

    def _filter(self, depth):
        depth = self.threshold.process(depth)
        if self.spatial or self.temporal:
            depth = self.to_disparity.process(depth)
            for f in (self.spatial, self.temporal):
                if f:
                    depth = f.process(depth)
            depth = self.to_depth.process(depth)
        return self.holes.process(depth) if self.holes else depth

    def _intrinsics(self, depth):
        k = depth.profile.as_video_stream_profile().get_intrinsics()
        value = Intrinsics(k.width, k.height, k.fx, k.fy, k.ppx, k.ppy,
                           str(k.model), tuple(k.coeffs))
        if value != self._ray_key:
            self._rays = None
            if k.model != self.rs.distortion.none:
                # Cache SDK deprojection once per geometry; never ignore lens distortion.
                self._rays = np.array([
                    self.rs.rs2_deproject_pixel_to_point(k, [x, y], 1.)
                    for y in range(k.height) for x in range(k.width)
                ], dtype=np.float32).reshape(k.height, k.width, 3)
            self._ray_key = value
        return value, self._rays

    def __iter__(self):
        emitted = 0
        while emitted < self.count:
            try:
                frames = self.pipeline.wait_for_frames(5000)
            except RuntimeError:
                if self.playback:
                    player = self.profile.get_device().as_playback()
                    if player.current_status() == self.rs.playback_status.stopped:
                        return
                raise
            # Align before filtering; compare against native-depth filtering in quality work.
            frames = self.align.process(frames)
            raw_depth, color = frames.get_depth_frame(), frames.get_color_frame()
            if not raw_depth or not color:
                continue
            depth = self._filter(raw_depth).as_depth_frame()
            k, rays = self._intrinsics(depth)
            rgb = np.asanyarray(color.get_data()).copy()
            if color.profile.format() == self.rs.format.bgr8:
                rgb = rgb[..., ::-1].copy()
            elif color.profile.format() != self.rs.format.rgb8:
                raise RuntimeError("RGB-D source requires RGB8/BGR8 color; convert the native recording first")
            yield Frame(rgb,
                        np.asanyarray(depth.get_data()).astype(np.float32)*self.scale,
                        k, raw_depth.get_timestamp(), raw_depth.get_frame_number(),
                        str(raw_depth.get_frame_timestamp_domain()), rays)
            emitted += 1


def collect_motion(path, seconds: float, serial: str = "") -> dict:
    """Choose actual advertised rates. Accel and gyro retain separate timestamps."""
    import csv
    from queue import Empty, Full, Queue
    from pathlib import Path
    if not np.isfinite(seconds) or seconds <= 0:
        raise ValueError("Positive finite duration required")
    rs = sdk()
    context = rs.context()
    devices = [d for d in context.query_devices()
               if not serial or _info(d, rs, "serial_number") == serial]
    if not devices:
        raise RuntimeError("No matching camera")
    if len(devices) != 1:
        raise RuntimeError("Multiple cameras: select --serial explicitly")
    device = devices[0]
    motion = [p for s in device.query_sensors() for p in s.get_stream_profiles()
              if p.stream_type() in (rs.stream.accel, rs.stream.gyro)
              and p.format() == rs.format.motion_xyz32f]
    cfg = rs.config()
    cfg.enable_device(_info(device, rs, "serial_number"))
    rates = {}
    for stream in (rs.stream.accel, rs.stream.gyro):
        choices = [p for p in motion if p.stream_type() == stream]
        if not choices:
            raise RuntimeError(f"{stream} unavailable; verify D435i model")
        profile = max(choices, key=lambda p: p.fps())
        cfg.enable_stream(stream, rs.format.motion_xyz32f, profile.fps())
        rates[str(stream)] = profile.fps()
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    pipe = rs.pipeline(context)
    count = 0
    queue = Queue(maxsize=10000)
    dropped = [0]

    def on_frame(frame):
        incoming = frame.as_frameset() if frame.is_frameset() else [frame]
        for sample in incoming:
            if sample.is_motion_frame():
                xyz = sample.as_motion_frame().get_motion_data()
                row = [str(sample.profile.stream_type()), sample.get_timestamp(),
                       str(sample.get_frame_timestamp_domain()),
                       sample.get_frame_number(), xyz.x, xyz.y, xyz.z]
                try:
                    queue.put_nowait(row)
                except Full:
                    dropped[0] += 1
    # Open output before starting hardware; never overwrite previous captures.
    with target.open("x", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["stream", "timestamp_ms", "domain", "frame_number", "x", "y", "z"])
        pipe.start(cfg, on_frame)
        try:
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                try:
                    writer.writerow(queue.get(timeout=.2))
                    count += 1
                except Empty:
                    continue
        finally:
            pipe.stop()
        while not queue.empty():
            writer.writerow(queue.get_nowait())
            count += 1
    if not count:
        raise RuntimeError("No motion samples received; inspect sensor profiles and device access")
    return {"samples": count, "advertised_rates_hz": rates,
            "software_queue_drops": dropped[0],
            "units": {"accel": "m/s^2", "gyro": "rad/s"}}


def infrared_view(config, count=100000):
    """Separate native stereo viewer: never mix IR pixels with RGB intrinsics."""
    from .viewer import cv_module
    cv, rs = cv_module(), sdk()
    cfg, pipe = rs.config(), rs.pipeline()
    if config.serial:
        cfg.enable_device(config.serial)
    for index in (1, 2):
        cfg.enable_stream(rs.stream.infrared, index, config.depth_width,
                          config.depth_height, rs.format.y8, config.fps)
    pipe.start(cfg)
    try:
        for _ in range(count):
            frames = pipe.wait_for_frames(5000)
            left, right = frames.get_infrared_frame(1), frames.get_infrared_frame(2)
            if not left or not right:
                continue
            cv.imshow("D435i native IR | left - right | Q quit", np.hstack((
                np.asanyarray(left.get_data()), np.asanyarray(right.get_data()))))
            if cv.waitKey(10) & 0xff in (ord("q"), 27):
                break
    finally:
        pipe.stop()
        cv.destroyAllWindows()
