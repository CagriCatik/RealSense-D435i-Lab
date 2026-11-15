"""Pure NumPy segmentation colors, also usable by headless snapshot tools."""
import numpy as np

PALETTE = np.array([[246, 189, 55], [80, 162, 245], [220, 110, 210],
                    [100, 220, 180], [235, 110, 90]], np.uint8)


def segmentation_rgb(result, height, width, stride):
    grid = result.labels
    image = np.zeros((*grid.shape, 3), np.uint8)
    image[grid == -2] = (35, 40, 50)  # measured, outside support/object band
    image[grid == -3] = (100, 80, 65)  # unclustered candidate
    image[grid == 0] = (55, 140, 95)  # reference plane
    for obj in result.report["objects"]:
        image[grid == obj["segment_id"]] = PALETTE[(obj["segment_id"]-1) % len(PALETTE)]
    return image.repeat(stride, axis=0).repeat(stride, axis=1)[:height, :width]
