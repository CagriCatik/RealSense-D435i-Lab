# Repository rules

- Use the D435i, not D435/D455/T265 capabilities as the target. Check official sources in docs/sources.md.
- Core modules (models, geometry, analysis, storage, tracking, imu, scene, scene_render, odometry, mapping, semantic_geometry, semantic_map) must not import SDK, GUI, ROS, YOLO or Open3D.
- Keep hardware access in sdk.py, model inference in detection.py, UI in viewer.py and ROS integration in ros2/.
- All core lengths are meters, timestamps milliseconds, RGB arrays RGB uint8. Optical axes: x right, y down, z forward.
- Missing depth is unknown. Never convert it to zero obstacle distance or free space.
- Do not silently discard distortion, mix timestamp domains or claim IMU-only drift-free position.
- Live/replay must share processing; preserve intrinsics, distortion/rays and timestamps in snapshots.
- Keep optional dependencies lazy. The headless demo and core tests need only NumPy.
- Test failure paths and meaningful numerical behavior with unittest. Hardware acceptance is separate.
- Update docs/capabilities.md with implementation, software verification and hardware evidence separately.
- Do not claim manufacturer conformance without physical measurements under the datasheet conditions.
- Do not commit captures, model weights, environments, generated reports or credentials.
- Do not update firmware, write calibration or change persistent device settings automatically.
- Semantic landmarks require accepted camera poses and valid depth. Preserve observation provenance and frame fingerprints.
- Mark synthetic color-fixture recognition explicitly; never report it as learned-model validation.
- Confirmed semantic IDs are static session hypotheses, not proof of identity or cross-session re-identification.
- README badges must reflect real checks or declared scope; do not invent coverage, release or hardware certification.
