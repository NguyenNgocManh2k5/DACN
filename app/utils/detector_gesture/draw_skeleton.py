import cv2

# Danh sách các cặp đường nối giữa các khớp tay (21 landmarks)
HAND_CONNECTIONS = [
    # Ngón cái
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Ngón trỏ
    (0, 5), (5, 6), (6, 7), (7, 8),
    # Ngón giữa
    (9, 10), (10, 11), (11, 12),
    # Ngón nhẫn
    (13, 14), (14, 15), (15, 16),
    # Ngón út
    (0, 17), (17, 18), (18, 19), (19, 20),
    # Nối lòng bàn tay
    (5, 9), (9, 13), (13, 17)
]

def draw_hand_skeleton(frame, lmList):  # Frame, Landmark List
    """Vẽ đường nối và điểm khớp cho khung xương bàn tay."""
    # 1. Vẽ các đường nối khớp
    for connection in HAND_CONNECTIONS:
        point_1 = (lmList[connection[0]][0], lmList[connection[0]][1])
        point_2 = (lmList[connection[1]][0], lmList[connection[1]][1])
        cv2.line(frame, point_1, point_2, (255, 153, 153), 2)

    # 2. Vẽ 21 khớp xương
    for lm in lmList:
        cv2.circle(frame, (lm[0], lm[1]), 4, (204, 153, 255), cv2.FILLED)

    # Vẽ 5 chấm tròn ở 5 đầu ngón tay
    finger_ids = [4, 8, 12, 16, 20]
    for tip_id in finger_ids:
        x, y = lmList[tip_id][0], lmList[tip_id][1]
        cv2.circle(frame, (x, y), 8, (153, 204, 255), cv2.FILLED)