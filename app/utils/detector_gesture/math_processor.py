import numpy as np

DEFAULT_SMOOTHING = 5

def get_distance(x1, x2, y1, y2):
    """Khoảng cách Euclid giữa 2 điểm (x1, y1) và (x2, y2)."""
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


def center_line(x1, x2, y1, y2):
    return (x1+x2)/2, (y1+y2)/2


def camera_to_screen(x_cam, y_cam, cap_w, cap_h, screen_w, screen_h, frame_r=120):
    """Quy đổi tọa độ từ camera sang màn hình máy tính."""
    x_target = np.interp(x_cam, (frame_r, cap_w - frame_r), (0, screen_w))
    x_target = np.clip(x_target, 0, screen_w - 1)

    y_target = np.interp(y_cam, (frame_r, cap_h - frame_r), (0, screen_h))
    y_target = np.clip(y_target, 0, screen_h - 1)

    return x_target, y_target


def smooth_coordinates(prev_x, prev_y, target_x, target_y, smoothing=DEFAULT_SMOOTHING):
    """Làm mượt chuyển động con trỏ chuột bằng nội suy tuyến tính."""
    curr_x = prev_x + (target_x - prev_x) / smoothing
    curr_y = prev_y + (target_y - prev_y) / smoothing
    return curr_x, curr_y