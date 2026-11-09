import cv2
import numpy as np


def draw_debug(rectified, recognition, conflicts):
    display = rectified.copy()
    size = display.shape[0]
    step = size // 9
    layer = display.copy()
    for row, col in conflicts:
        cv2.rectangle(layer, (col * step, row * step), ((col + 1) * step - 1, (row + 1) * step - 1),
                      (30, 30, 255), -1)
    display = cv2.addWeighted(layer, 0.35, display, 0.65, 0)
    for index in range(10):
        coordinate = min(index * step, size - 1)
        cv2.line(display, (coordinate, 0), (coordinate, size - 1), (255, 150, 0), 1)
        cv2.line(display, (0, coordinate), (size - 1, coordinate), (255, 150, 0), 1)
    for row in range(9):
        for col in range(9):
            digit = int(recognition.grid[row, col])
            unknown = recognition.filled_mask[row, col] and digit == 0
            if digit or unknown:
                text = str(digit) if digit else "?"
                position = (col * step + 3, row * step + 15)
                cv2.putText(display, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 3)
                cv2.putText(display, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.48,
                            (0, 0, 220) if unknown else (0, 120, 0), 1)
    return display
