"""CLI orchestration; algorithms live in core modules, SDK/GUI imports are lazy."""
import argparse
import json
from pathlib import Path
import sys
import time

from .analysis import frame_health, summarize
from .config import Config
from .geometry import frame_cloud, frame_point
from .sources import ReplaySource, SyntheticSource
from .storage import save_frame, write_json, write_ply


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Expected a positive integer")
    return number


def source_arguments(parser, count=300):
    parser.add_argument("--source", choices=("demo", "camera", "replay", "native"), default="demo")
    parser.add_argument("--input", help="Replay directory/.npz or SDK recording")
    parser.add_argument("--config", help="Strict JSON config; see configs/")
    parser.add_argument("--frames", type=positive, default=count)


def parser():
    root = argparse.ArgumentParser(prog="rs-lab", description="RealSense D435i Lab — meters, RGB-D, IMU")
    sub = root.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect", help="List devices, profiles, intrinsics and option ranges")
    inspect.add_argument("--output")
    infrared = sub.add_parser("infrared", help="Native left/right stereo infrared viewer")
    infrared.add_argument("--config")
    infrared.add_argument("--frames", type=positive, default=100000)
    view = sub.add_parser("view", help="Interactive 3D Object Explorer")
    source_arguments(view, 100000)
    view.add_argument("--output", default="artifacts")
    view.add_argument("--weights", help="Optional existing local YOLO weights")
    capture = sub.add_parser("capture", help="Save aligned portable RGB-D snapshots")
    source_arguments(capture)
    capture.add_argument("--output", required=True)
    capture.add_argument("--native-record", help="Also record native SDK streams (camera source only)")
    analyze = sub.add_parser("analyze", help="Pointcloud statistics and dominant-plane fit")
    source_arguments(analyze, 1)
    analyze.add_argument("--output")
    analyze.add_argument("--pixel", type=int, nargs=2, metavar=("X", "Y"))
    export = sub.add_parser("export", help="Export first source frame as colored PLY")
    source_arguments(export, 1)
    export.add_argument("--output", required=True)
    bench = sub.add_parser("benchmark", help="Observe stream intervals, gaps and host throughput")
    source_arguments(bench)
    bench.add_argument("--output")
    motion = sub.add_parser("imu", help="Capture accelerometer and gyroscope to CSV")
    motion.add_argument("--output", required=True)
    motion.add_argument("--seconds", type=float, default=10.)
    motion.add_argument("--serial", default="")
    imu_report = sub.add_parser("imu-report", help="Analyze a stationary IMU CSV capture")
    imu_report.add_argument("--input", required=True)
    imu_report.add_argument("--output")
    scan = sub.add_parser("reconstruct", help="TSDF fusion with supplied camera-to-world poses")
    scan.add_argument("--manifest", required=True)
    scan.add_argument("--output", required=True)
    return root


def make_source(args, config):
    if args.source == "demo":
        if args.input:
            raise ValueError("--input is only valid for replay/native")
        return SyntheticSource(args.frames, config.color_width, config.color_height, config.fps)
    if args.source == "replay":
        if not args.input:
            raise ValueError("replay requires --input")
        return ReplaySource(args.input)
    if args.source == "native" and not args.input:
        raise ValueError("native requires --input")
    if args.source == "camera" and args.input:
        raise ValueError("camera does not accept --input")
    from .sdk import CameraSource
    return CameraSource(config, playback=args.input if args.source == "native" else None,
                        record=getattr(args, "native_record", None), count=args.frames)


def emit(result, path=None):
    if path:
        write_json(path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


def process_frames(args):
    config = Config.load(args.config)
    if getattr(args, "native_record", None) and args.source != "camera":
        raise ValueError("--native-record requires --source camera")
    numbers, timestamps, domains = [], [], []
    started = time.monotonic()
    with make_source(args, config) as source:
        if args.command == "view":
            from .viewer import show
            detector = None
            if args.weights:
                from .detection import Detector
                detector = Detector(args.weights)
            show(source, config, args.output, detector)
            return
        for index, frame in enumerate(source):
            numbers.append(frame.number)
            timestamps.append(frame.timestamp_ms)
            domains.append(frame.timestamp_domain)
            if args.command == "capture":
                save_frame(Path(args.output)/f"frame_{index:06d}.npz", frame)
            elif args.command == "analyze":
                result = summarize(frame, config.max_depth_m)
                if args.pixel:
                    xyz, mad, count = frame_point(frame, args.pixel)
                    result["measurement"] = {"pixel": args.pixel, "xyz_m": xyz.tolist(),
                                             "depth_mad_m": mad, "valid_neighbors": count}
                emit(result, args.output)
                return
            elif args.command == "export":
                xyz, pixels = frame_cloud(frame, 2, config.max_depth_m)
                write_ply(args.output, xyz, frame.color[pixels[:, 0], pixels[:, 1]])
                emit({"points": len(xyz), "output": args.output})
                return
            if index+1 >= args.frames:
                break
    if not numbers:
        raise ValueError("Source produced no frames")
    report = frame_health(numbers, timestamps, domains, time.monotonic()-started)
    report["source"] = args.source
    report["config"] = config.to_dict()
    emit(report, args.output if args.command == "benchmark" else None)


def run(args):
    if args.command == "inspect":
        from .sdk import inspect_devices
        result = inspect_devices()
        emit(result, args.output)
        return 0 if result["devices"] else 2
    if args.command == "infrared":
        from .sdk import infrared_view
        infrared_view(Config.load(args.config), args.frames)
    elif args.command == "imu":
        from .sdk import collect_motion
        emit(collect_motion(args.output, args.seconds, args.serial))
    elif args.command == "imu-report":
        from .imu import summarize_imu
        emit(summarize_imu(args.input), args.output)
    elif args.command == "reconstruct":
        from .reconstruction import integrate
        emit(integrate(args.manifest, args.output))
    else:
        process_frames(args)
    return 0


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        return run(args)
    except KeyboardInterrupt:
        print("Interrupted; camera resources released.", file=sys.stderr)
        return 130
    except (ValueError, RuntimeError, OSError, KeyError) as exc:
        print(f"rs-lab: {exc}", file=sys.stderr)
        return 2
