import pygame
import sys
import math
import random

pygame.init()
info = pygame.display.Info()

BOARD_SIZE = 10

LEFT_PANEL = 220
RIGHT_PANEL = 120
MARGIN = 20
TOP_MARGIN = 20
BOTTOM_MARGIN = 30

available_w = info.current_w - LEFT_PANEL - RIGHT_PANEL - 2 * MARGIN - 40
available_h = info.current_h - TOP_MARGIN - MARGIN - BOTTOM_MARGIN - 40

CELL = min(available_w, available_h) // BOARD_SIZE

WINDOW_W = LEFT_PANEL + BOARD_SIZE * CELL + RIGHT_PANEL + 2 * MARGIN
WINDOW_H = TOP_MARGIN + BOARD_SIZE * CELL + MARGIN + BOTTOM_MARGIN

PIECE_SIZE = CELL - 8
INNER_SIZE = PIECE_SIZE - 6

print(f"Экран: {info.current_w}x{info.current_h}, CELL={CELL}, окно={WINDOW_W}x{WINDOW_H}")

LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
SELECTED = (0, 255, 0)
TURN_HIGHLIGHT = (0, 255, 0)
MOVE_DOT = (0, 200, 0)
CAPTURE_RING = (255, 0, 0)
EN_PASSANT_RING = (255, 165, 0)
DOUBLE_DOT = (255, 200, 0)
CASTLE_RING = (0, 255, 200)
CHECK_COLOR = (255, 0, 0)
WIN_COLOR = (255, 215, 0)
RESIGN_COLOR = (255, 120, 120)
DROP_DOT = (80, 140, 255)
QUEUE_COLOR = (255, 220, 100)

OUTLINE_COLORS = {'w': (0, 0, 0), 'b': (255, 255, 255)}
PLAYER_COLORS = {'w': (200, 220, 255), 'b': (255, 150, 150)}
PLAYER_LABELS = {'w': 'Белые', 'b': 'Чёрные'}
TURN_ORDER = ['w', 'b']
PROMOTION_CHOICES = ['Q', 'R', 'B', 'N', 'N2', 'R2', 'J']
PAWN_FORWARD = {'w': (0, +1), 'b': (0, -1)}
PAWN_PROMOTION_LINE = {'w': 9, 'b': 0}
PAWN_START_ROW = {'w': 1, 'b': BOARD_SIZE - 2}  # ряд 1 для белых, ряд 8 для чёрных
KING_BACK_ROW = {'w': 0, 'b': 9}

# Реинкарнация: сколько своих ходов ждёт пешка.
REINCARNATION_TURNS = 3

DRAW_ICON = None
RESIGN_ICON = None
BACK_ICON = None
FLIP_ICON = None
FREESTYLE_ICON = None

BOARD_FLIPPED = False
DRAW_TIMEOUT = 10.0

# Уменьшение пиктограмм запасных фигур (включая перетаскиваемую).
RESERVE_ICON_SCALE = 0.7


def is_enemy(c1, c2):
    return c1 != c2


def add_outline(image, outline_color=(0, 0, 0), thickness=2):
    mask = pygame.mask.from_surface(image)
    outline = mask.to_surface(setcolor=outline_color, unsetcolor=(0, 0, 0, 0))
    result = pygame.Surface((image.get_width() + thickness * 2,
                             image.get_height() + thickness * 2), pygame.SRCALPHA)
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx == 0 and dy == 0:
                continue
            result.blit(outline, (thickness + dx, thickness + dy))
    result.blit(image, (thickness, thickness))
    return result


def load_pieces():
    pieces = {}
    types = ['K', 'Q', 'R', 'B', 'N', 'P']
    base_pieces = {}

    for base, prefix in [('white', 'w'), ('black', 'b')]:
        for symbol in types:
            path = f"images/pieces/{prefix}{symbol}.png"
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.smoothscale(img, (INNER_SIZE, INNER_SIZE))
                base_pieces[(base, symbol)] = img
            except pygame.error as e:
                print(f"Не найден файл: {path} — {e}")
                surf = pygame.Surface((INNER_SIZE, INNER_SIZE), pygame.SRCALPHA)
                color = (255, 255, 255) if base == 'white' else (0, 0, 0)
                pygame.draw.circle(surf, color, (INNER_SIZE // 2, INNER_SIZE // 2),
                                   INNER_SIZE // 2 - 2)
                base_pieces[(base, symbol)] = surf

    for base, prefix in [('white', 'w'), ('black', 'b')]:
        path2 = f"images/pieces/{prefix}N2.png"
        try:
            img2 = pygame.image.load(path2).convert_alpha()
            w, h = img2.get_size()
            scale = min(INNER_SIZE / w, INNER_SIZE / h)
            img2 = pygame.transform.smoothscale(img2, (int(w * scale), int(h * scale)))
            base_pieces[(base, 'N2')] = img2
        except pygame.error as e:
            print(f"Не найден файл: {path2} — {e} (использую обычного коня)")
            base_pieces[(base, 'N2')] = base_pieces[(base, 'N')]

    for base, prefix in [('white', 'w'), ('black', 'b')]:
        path_r2 = f"images/pieces/{prefix}R2.png"
        try:
            img_r2 = pygame.image.load(path_r2).convert_alpha()
            w, h = img_r2.get_size()
            scale = min(INNER_SIZE / w, INNER_SIZE / h) * 1.0
            img_r2 = pygame.transform.smoothscale(img_r2, (int(w * scale), int(h * scale)))
            base_pieces[(base, 'R2')] = img_r2
        except pygame.error as e:
            print(f"Не найден файл: {path_r2} — {e} (использую обычную ладью)")
            base_pieces[(base, 'R2')] = base_pieces[(base, 'R')]

    for base, prefix in [('white', 'w'), ('black', 'b')]:
        path_j = f"images/pieces/{prefix}J.png"
        try:
            img_j = pygame.image.load(path_j).convert_alpha()
            w, h = img_j.get_size()
            scale = min(INNER_SIZE / w, INNER_SIZE / h) * 1.2
            img_j = pygame.transform.smoothscale(img_j, (int(w * scale), int(h * scale)))
            base_pieces[(base, 'J')] = img_j
        except pygame.error as e:
            print(f"Не найден файл: {path_j} — {e} (использую ферзя)")
            base_pieces[(base, 'J')] = base_pieces[(base, 'Q')]

    all_symbols = ['K', 'Q', 'R', 'B', 'N', 'P', 'N2', 'R2', 'J']
    for player in ['w', 'b']:
        outline_color = OUTLINE_COLORS[player]
        base = 'white' if player == 'w' else 'black'
        for symbol in all_symbols:
            img = base_pieces[(base, symbol)]
            if symbol == 'R2':
                outlined = add_outline(img, outline_color, thickness=6)
            else:
                outlined = add_outline(img, outline_color, thickness=3)

            if symbol == 'R2':
                w, h = outlined.get_size()
                scale = min(PIECE_SIZE / w, PIECE_SIZE / h) * 1.0
                outlined = pygame.transform.smoothscale(
                    outlined, (int(w * scale), int(h * scale)))
            elif symbol in ('N2', 'J'):
                w, h = outlined.get_size()
                scale_mult = 1.2 if symbol == 'J' else 1.0
                scale = min(PIECE_SIZE / w, PIECE_SIZE / h) * scale_mult
                outlined = pygame.transform.smoothscale(
                    outlined, (int(w * scale), int(h * scale)))
            else:
                outlined = pygame.transform.smoothscale(outlined, (PIECE_SIZE, PIECE_SIZE))
            pieces[(player, symbol)] = outlined
    return pieces


def load_icon(filename, size):
    path = f"images/pieces/{filename}"
    try:
        img = pygame.image.load(path).convert_alpha()
        w, h = img.get_size()
        scale = min(size / w, size / h)
        img = pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))
        return img
    except pygame.error as e:
        print(f"Не найден файл: {path} — {e} (рисую пиктограмму программно)")
        return None


# --- Программные фолбэки иконок ---

def draw_handshake_icon(surface, center, size, color, thickness=3):
    cx, cy = center
    s = size
    cuff_w = int(s * 0.22); cuff_h = int(s * 0.45)
    cuff_x = cx - s // 2 + int(s * 0.05)
    cuff_y = cy - s // 2 + int(s * 0.10)
    pygame.draw.rect(surface, color,
                     pygame.Rect(cuff_x, cuff_y, cuff_w, cuff_h), thickness)
    pygame.draw.line(surface, color,
                     (cuff_x + cuff_w, cuff_y + cuff_h // 2),
                     (cx - int(s * 0.05), cy + int(s * 0.05)), thickness)
    for i in range(3):
        fx = cx - int(s * 0.20) + i * int(s * 0.10)
        fy = cy + int(s * 0.10)
        pygame.draw.arc(surface, color,
                        pygame.Rect(fx, fy, int(s * 0.14), int(s * 0.14)),
                        3.14, 6.28, thickness)
    cuff_x2 = cx + s // 2 - int(s * 0.05) - cuff_w
    pygame.draw.rect(surface, color,
                     pygame.Rect(cuff_x2, cuff_y, cuff_w, cuff_h), thickness)
    pygame.draw.line(surface, color,
                     (cuff_x2, cuff_y + cuff_h // 2),
                     (cx + int(s * 0.05), cy + int(s * 0.05)), thickness)
    for i in range(3):
        fx = cx + int(s * 0.06) - i * int(s * 0.10)
        fy = cy + int(s * 0.10)
        pygame.draw.arc(surface, color,
                        pygame.Rect(fx, fy, int(s * 0.14), int(s * 0.14)),
                        3.14, 6.28, thickness)
    pygame.draw.line(surface, color,
                     (cx - int(s * 0.05), cy + int(s * 0.05)),
                     (cx + int(s * 0.05), cy + int(s * 0.05)), thickness)


def draw_flag_icon(surface, center, size, color, thickness=4):
    cx, cy = center
    s = size
    pole_x = cx - int(s * 0.28)
    pole_top = cy - int(s * 0.32)
    pole_bottom = cy + int(s * 0.32)
    pygame.draw.line(surface, color, (pole_x, pole_top), (pole_x, pole_bottom), thickness)
    flag_w = int(s * 0.50)
    flag_h = int(s * 0.40)
    flag_points = [
        (pole_x, pole_top),
        (pole_x + flag_w, pole_top + flag_h // 2),
        (pole_x, pole_top + flag_h),
    ]
    pygame.draw.polygon(surface, color, flag_points, thickness)
    pygame.draw.line(surface, color,
                     (pole_x - int(s * 0.10), pole_bottom),
                     (pole_x + int(s * 0.10), pole_bottom), thickness)


def draw_back_icon(surface, center, size, color, thickness=4):
    cx, cy = center
    s = size
    left = cx - int(s * 0.32)
    right = cx + int(s * 0.32)
    top = cy - int(s * 0.30)
    bottom = cy + int(s * 0.30)
    mid_y = cy
    pygame.draw.line(surface, color, (left, mid_y), (right, mid_y), thickness)
    pygame.draw.line(surface, color, (left, mid_y), (left + int(s * 0.20), top), thickness)
    pygame.draw.line(surface, color, (left, mid_y), (left + int(s * 0.20), bottom), thickness)


def draw_flip_icon(surface, center, size, color, thickness=3):
    cx, cy = center
    s = size
    r = int(s * 0.30)
    arc_rect1 = pygame.Rect(cx - r, cy - r, 2 * r, 2 * r)
    pygame.draw.arc(surface, color, arc_rect1, 0.3, 3.0, thickness)
    ax = cx + int(r * 0.7)
    ay = cy - int(r * 0.7)
    pygame.draw.line(surface, color,
                     (ax, ay),
                     (ax - int(s * 0.10), ay - int(s * 0.06)), thickness)
    pygame.draw.line(surface, color,
                     (ax, ay),
                     (ax + int(s * 0.06), ay - int(s * 0.10)), thickness)
    arc_rect2 = pygame.Rect(cx - r, cy - r, 2 * r, 2 * r)
    pygame.draw.arc(surface, color, arc_rect2, 3.44, 6.14, thickness)
    bx = cx - int(r * 0.7)
    by = cy + int(r * 0.7)
    pygame.draw.line(surface, color,
                     (bx, by),
                     (bx + int(s * 0.10), by + int(s * 0.06)), thickness)
    pygame.draw.line(surface, color,
                     (bx, by),
                     (bx - int(s * 0.06), by + int(s * 0.10)), thickness)


def draw_freestyle_icon(surface, center, size, color, thickness=3):
    cx, cy = center
    s = size // 2
    pygame.draw.rect(surface, color,
                     pygame.Rect(cx - s, cy - s, 2 * s, 2 * s), thickness)
    dot_r = max(2, s // 5)
    for dx, dy in [(0, 0), (-s // 2, -s // 2), (s // 2, -s // 2),
                   (-s // 2, s // 2), (s // 2, s // 2)]:
        pygame.draw.circle(surface, color, (cx + dx, cy + dy), dot_r)


def draw_circle_button(screen, center, radius, active, icon, fill_active, fill_inactive,
                       border_active, border_inactive, icon_color_active, icon_color_inactive,
                       fallback_draw):
    cx, cy = center
    if active:
        fill_color = fill_active
        border_color = border_active
        icon_color = icon_color_active
    else:
        fill_color = fill_inactive
        border_color = border_inactive
        icon_color = icon_color_inactive

    pygame.draw.circle(screen, fill_color, (cx, cy), radius)
    pygame.draw.circle(screen, border_color, (cx, cy), radius, 4)

    icon_size = int(radius * 1.4)
    if icon is not None:
        img = icon
        w, h = img.get_size()
        scale = min(icon_size / w, icon_size / h)
        img = pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))
        if not active:
            tinted = img.copy()
            tint = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            tint.fill((*icon_color, 180))
            tinted.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            img = tinted
        screen.blit(img, img.get_rect(center=(cx, cy)))
    else:
        fallback_draw(screen, (cx, cy), icon_size, icon_color)


def get_piece_image(pieces, color, typ):
    return pieces[(color, typ)]


def initial_position():
    pos = {}
    pos[(0, 0)] = ('w', 'N2')
    pos[(1, 0)] = ('w', 'R')
    pos[(2, 0)] = ('w', 'N')
    pos[(3, 0)] = ('w', 'B')
    pos[(4, 0)] = ('w', 'Q')
    pos[(5, 0)] = ('w', 'K')
    pos[(6, 0)] = ('w', 'B')
    pos[(7, 0)] = ('w', 'N')
    pos[(8, 0)] = ('w', 'R')
    pos[(9, 0)] = ('w', 'N2')
    for c in range(BOARD_SIZE):
        pos[(c, 1)] = ('w', 'P')
    for (c, r), (color, typ) in list(pos.items()):
        if color == 'w':
            mirror_r = BOARD_SIZE - 1 - r
            pos[(c, mirror_r)] = ('b', typ)
    return pos


def random_back_rank():
    pieces = ['R', 'R', 'N2', 'N2', 'N', 'N', 'B', 'B', 'Q', 'K']
    while True:
        random.shuffle(pieces)
        bishops = [i for i, p in enumerate(pieces) if p == 'B']
        if (bishops[0] % 2) != (bishops[1] % 2):
            return pieces


def apply_random_position(position):
    back = random_back_rank()
    new_pos = {}
    for (c, r), piece in position.items():
        if r == 0 or r == BOARD_SIZE - 1:
            continue
        new_pos[(c, r)] = piece
    for c, t in enumerate(back):
        new_pos[(c, 0)] = ('w', t)
        new_pos[(c, BOARD_SIZE - 1)] = ('b', t)
    return new_pos


def in_bounds(c, r):
    return 0 <= c < BOARD_SIZE and 0 <= r < BOARD_SIZE


def is_promotion_square_for(color, c, r):
    return r == PAWN_PROMOTION_LINE[color]


def on_own_half(color, r):
    if color == 'w':
        return 0 <= r < BOARD_SIZE // 2
    return BOARD_SIZE // 2 <= r < BOARD_SIZE


def compute_en_passant(position, en_passant_move):
    result = {}
    if en_passant_move is None:
        return result
    fc, fr, tc, tr, pawn_color = en_passant_move
    if (tc, tr) not in position:
        return result
    if position[(tc, tr)][1] != 'P' or position[(tc, tr)][0] != pawn_color:
        return result
    our_color = 'b' if pawn_color == 'w' else 'w'
    our_dc, our_dr = PAWN_FORWARD[our_color]
    d = PAWN_FORWARD[pawn_color]
    for (c, r), (pc, pt) in position.items():
        if pc != our_color or pt != 'P':
            continue
        for crossed_r in range(fr + d[1], tr, d[1]):
            for ddc in [-1, +1]:
                if c + ddc == fc and r == crossed_r - our_dr:
                    if (fc, crossed_r) not in position:
                        result[(fc, crossed_r)] = (tc, tr)
    return result


def sliding_moves(position, c, r, color, directions):
    moves = []
    for dc, dr in directions:
        nc, nr = c + dc, r + dr
        while in_bounds(nc, nr):
            if (nc, nr) in position:
                if is_enemy(color, position[(nc, nr)][0]):
                    moves.append((nc, nr))
                break
            moves.append((nc, nr))
            nc += dc
            nr += dr
    return moves


def king_moves(position, c, r, color):
    moves = []
    for dc in [-1, 0, 1]:
        for dr in [-1, 0, 1]:
            if dc == 0 and dr == 0:
                continue
            nc, nr = c + dc, r + dr
            if not in_bounds(nc, nr):
                continue
            if (nc, nr) in position:
                if is_enemy(color, position[(nc, nr)][0]):
                    moves.append((nc, nr))
            else:
                moves.append((nc, nr))
    return moves


def knight_moves(position, c, r, color):
    moves = []
    for dc, dr in [(1, 2), (2, 1), (-1, 2), (-2, 1),
                   (1, -2), (2, -1), (-1, -2), (-2, -1)]:
        nc, nr = c + dc, r + dr
        if not in_bounds(nc, nr):
            continue
        if (nc, nr) in position:
            if is_enemy(color, position[(nc, nr)][0]):
                moves.append((nc, nr))
        else:
            moves.append((nc, nr))
    return moves


def two_headed_knight_moves(position, c, r, color):
    moves = []
    for dc, dr in [(1, 3), (3, 1), (-1, 3), (-3, 1),
                   (1, -3), (3, -1), (-1, -3), (-3, -1)]:
        nc, nr = c + dc, r + dr
        if not in_bounds(nc, nr):
            continue
        if (nc, nr) in position:
            if is_enemy(color, position[(nc, nr)][0]):
                moves.append((nc, nr))
        else:
            moves.append((nc, nr))
    return moves


def cheetah_moves(position, c, r, color):
    moves = []
    for dc, dr in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        nc, nr = c + dc, r + dr
        first_blocker = False
        jumped = False
        while in_bounds(nc, nr):
            if (nc, nr) in position:
                target_color, target_type = position[(nc, nr)]
                if not first_blocker:
                    first_blocker = True
                    if is_enemy(color, target_color):
                        moves.append((nc, nr))
                    jc, jr = nc + dc, nr + dr
                    if in_bounds(jc, jr) and (jc, jr) not in position:
                        jumped = True
                    if not jumped:
                        break
                else:
                    break
            else:
                moves.append((nc, nr))
            nc += dc
            nr += dr
    return moves


def genie_moves(position, c, r, color):
    moves = []
    directions = [
        (0, -1), (0, 1), (-1, 0), (1, 0),
        (-1, -1), (-1, 1), (1, -1), (1, 1),
    ]
    for dc, dr in directions:
        nc, nr = c + dc, r + dr
        first_blocker = False
        jumped = False
        while in_bounds(nc, nr):
            if (nc, nr) in position:
                target_color, target_type = position[(nc, nr)]
                if not first_blocker:
                    first_blocker = True
                    if is_enemy(color, target_color):
                        moves.append((nc, nr))
                    jc, jr = nc + dc, nr + dr
                    if in_bounds(jc, jr) and (jc, jr) not in position:
                        jumped = True
                    if not jumped:
                        break
                else:
                    break
            else:
                moves.append((nc, nr))
            nc += dc
            nr += dr
    return moves


def pawn_moves(position, c, r, color, moved_pawns, en_passant_moves):
    moves = []
    dc, dr = PAWN_FORWARD[color]
    on_start = (c, r) not in moved_pawns
    max_steps = 3 if on_start else 2
    for step in range(1, max_steps + 1):
        nc, nr = c + dc * step, r + dr * step
        if not in_bounds(nc, nr):
            break
        if (nc, nr) in position:
            break
        moves.append((nc, nr))
    diagonals = [(-1, dr), (+1, dr)]
    for ddc, ddr in diagonals:
        nc, nr = c + ddc, r + ddr
        if not in_bounds(nc, nr):
            continue
        if (nc, nr) in position:
            if is_enemy(color, position[(nc, nr)][0]):
                moves.append((nc, nr))
    for (tc, tr) in en_passant_moves.keys():
        for ddc, ddr in diagonals:
            if c + ddc == tc and r + ddr == tr:
                moves.append((tc, tr))
                break
    return moves


def get_moves(position, c, r, color, moved_pawns, en_passant_moves):
    if (c, r) not in position:
        return []
    pc, pt = position[(c, r)]
    if pt == 'P':
        return pawn_moves(position, c, r, pc, moved_pawns, en_passant_moves)
    elif pt == 'N':
        return knight_moves(position, c, r, pc)
    elif pt == 'N2':
        return two_headed_knight_moves(position, c, r, pc)
    elif pt == 'R2':
        return cheetah_moves(position, c, r, pc)
    elif pt == 'J':
        return genie_moves(position, c, r, pc)
    elif pt == 'R':
        return sliding_moves(position, c, r, pc,
                             [(0, -1), (0, 1), (-1, 0), (1, 0)])
    elif pt == 'B':
        return sliding_moves(position, c, r, pc,
                             [(-1, -1), (-1, 1), (1, -1), (1, 1)])
    elif pt == 'Q':
        return sliding_moves(position, c, r, pc,
                             [(-1, -1), (-1, 1), (1, -1), (1, 1),
                              (0, -1), (0, 1), (-1, 0), (1, 0)])
    elif pt == 'K':
        return king_moves(position, c, r, pc)
    return []


def find_all_kings(position, color):
    return [(c, r) for (c, r), (pc, pt) in position.items()
            if pc == color and pt == 'K']


def is_square_attacked(position, c, r, by_color):
    for (pc, pr), (color, typ) in position.items():
        if color != by_color:
            continue
        if typ == 'P':
            dc, dr = PAWN_FORWARD[color]
            for ddc, ddr in [(-1, dr), (+1, dr)]:
                if pc + ddc == c and pr + ddr == r:
                    return True
            continue
        if typ == 'N':
            moves = knight_moves(position, pc, pr, color)
        elif typ == 'N2':
            moves = two_headed_knight_moves(position, pc, pr, color)
        elif typ == 'R2':
            moves = cheetah_moves(position, pc, pr, color)
        elif typ == 'J':
            moves = genie_moves(position, pc, pr, color)
        elif typ == 'R':
            moves = sliding_moves(position, pc, pr, color,
                                  [(0, -1), (0, 1), (-1, 0), (1, 0)])
        elif typ == 'B':
            moves = sliding_moves(position, pc, pr, color,
                                  [(-1, -1), (-1, 1), (1, -1), (1, 1)])
        elif typ == 'Q':
            moves = sliding_moves(position, pc, pr, color,
                                  [(-1, -1), (-1, 1), (1, -1), (1, 1),
                                   (0, -1), (0, 1), (-1, 0), (1, 0)])
        elif typ == 'K':
            moves = king_moves(position, pc, pr, color)
        else:
            moves = []
        if (c, r) in moves:
            return True
    return False


def is_square_attacked_by_piece(position, piece_c, piece_r, target_c, target_r):
    if (piece_c, piece_r) not in position:
        return False
    color, typ = position[(piece_c, piece_r)]
    if typ == 'P':
        dc, dr = PAWN_FORWARD[color]
        for ddc, ddr in [(-1, dr), (+1, dr)]:
            if piece_c + ddc == target_c and piece_r + ddr == target_r:
                return True
        return False
    test_pos = dict(position)
    if (target_c, target_r) in test_pos:
        del test_pos[(target_c, target_r)]
    moves = get_moves(test_pos, piece_c, piece_r, color, set(), {})
    return (target_c, target_r) in moves


def has_any_king_attacked(position, color):
    enemy = 'b' if color == 'w' else 'w'
    for kp in find_all_kings(position, color):
        if is_square_attacked(position, kp[0], kp[1], enemy):
            return True
    return False


def is_in_check(position, color):
    return has_any_king_attacked(position, color)


def filter_legal_moves(position, c, r, color, moved_pawns, en_passant_moves):
    moves = get_moves(position, c, r, color, moved_pawns, en_passant_moves)
    legal = []
    for (mc, mr) in moves:
        new_position = dict(position)
        captured = new_position.pop((c, r))
        new_position[(mc, mr)] = captured
        if (mc, mr) in en_passant_moves:
            enemy_pos = en_passant_moves[(mc, mr)]
            if enemy_pos in new_position:
                del new_position[enemy_pos]
        if captured[1] == 'P' and is_promotion_square_for(color, mc, mr):
            new_position[(mc, mr)] = (color, 'Q')
        if not has_any_king_attacked(new_position, color):
            legal.append((mc, mr))
    return legal


def is_path_clear(position, c1, r1, c2, r2):
    dc = (c2 > c1) - (c2 < c1)
    dr = (r2 > r1) - (r2 < r1)
    nc, nr = c1 + dc, r1 + dr
    while (nc, nr) != (c2, r2):
        if (nc, nr) in position:
            return False
        nc += dc
        nr += dr
    return True


def is_king_castle_safe(position, king_c, king_r, partner_c, partner_r, color):
    enemy = 'b' if color == 'w' else 'w'
    if is_square_attacked(position, king_c, king_r, enemy):
        return False
    if is_square_attacked(position, partner_c, partner_r, enemy):
        return False
    return True


def can_castle(position, c1, r1, c2, r2, color):
    if (c1, r1) not in position or (c2, r2) not in position:
        return False
    p1_color, p1_type = position[(c1, r1)]
    p2_color, p2_type = position[(c2, r2)]
    if p1_color != color or p2_color != color:
        return False
    if p1_type == 'P' or p2_type == 'P':
        return False

    if p1_type == 'K':
        king_c, king_r = c1, r1
        partner_c, partner_r = c2, r2
    elif p2_type == 'K':
        king_c, king_r = c2, r2
        partner_c, partner_r = c1, r1
    else:
        king_c = None

    if king_c is not None:
        if king_r != KING_BACK_ROW[color]:
            return False
        if partner_r != KING_BACK_ROW[color]:
            return False
        if king_r != partner_r:
            return False
        if abs(king_c - partner_c) != 1:
            return False
        if not is_king_castle_safe(position, king_c, king_r,
                                   partner_c, partner_r, color):
            return False
        return True

    a_atk_c = is_square_attacked_by_piece(position, c1, r1, c2, r2)
    c_atk_a = is_square_attacked_by_piece(position, c2, r2, c1, r1)
    if not a_atk_c and not c_atk_a:
        return False
    return True


def compute_castle_moves(position, c, r, color):
    if (c, r) not in position:
        return []
    result = []
    for (oc, or_), (ocolor, otype) in position.items():
        if (oc, or_) == (c, r):
            continue
        if ocolor != color:
            continue
        if can_castle(position, c, r, oc, or_, color):
            result.append((oc, or_))
    return result


def apply_castle(position, c1, r1, c2, r2):
    p1 = position[(c1, r1)]
    p2 = position[(c2, r2)]
    position[(c1, r1)] = p2
    position[(c2, r2)] = p1


def has_own_pawn_on_file(position, color, file_c):
    """Есть ли на вертикали file_c хотя бы одна пешка цвета color."""
    for r in range(BOARD_SIZE):
        if (file_c, r) in position:
            pc, pt = position[(file_c, r)]
            if pc == color and pt == 'P':
                return True
    return False


def legal_drops(position, reserve, color, piece_type):
    if piece_type not in reserve[color]:
        return []
    result = []

    if piece_type == 'P':
        # Пешка — только на начальный ряд, только если на вертикали
        # нет других своих пешек, и после постановки король не под шахом.
        start_row = PAWN_START_ROW[color]
        for c in range(BOARD_SIZE):
            sq = (c, start_row)
            if sq in position:
                continue
            if has_own_pawn_on_file(position, color, c):
                continue
            test = dict(position)
            test[sq] = (color, 'P')
            if not has_any_king_attacked(test, color):
                result.append(sq)
        return result

    # Обычная логика для R2/J.
    for c in range(BOARD_SIZE):
        for r in range(BOARD_SIZE):
            if (c, r) in position:
                continue
            if not on_own_half(color, r):
                continue
            test = dict(position)
            test[(c, r)] = (color, piece_type)
            if not has_any_king_attacked(test, color):
                result.append((c, r))
    return result


def has_any_legal_move(position, color, moved_pawns, en_passant_moves, reserve):
    for (c, r), (pc, pt) in position.items():
        if pc == color:
            if filter_legal_moves(position, c, r, color, moved_pawns, en_passant_moves):
                return True
            if pt != 'P':
                castles = compute_castle_moves(position, c, r, color)
                for (oc, or_) in castles:
                    test_pos = dict(position)
                    apply_castle(test_pos, c, r, oc, or_)
                    if not has_any_king_attacked(test_pos, color):
                        return True
    for pt in reserve.get(color, []):
        if legal_drops(position, reserve, color, pt):
            return True
    return False


def is_checkmate(position, color, moved_pawns, en_passant_moves, reserve):
    if not is_in_check(position, color):
        return False
    return not has_any_legal_move(position, color, moved_pawns, en_passant_moves, reserve)


# --- Реинкарнация пешек ---

def register_pawn_capture(reincarnating, color):
    """Регистрирует срубленную пешку в очереди реинкарнации."""
    reincarnating[color].append({'turns_left': REINCARNATION_TURNS, 'ready': False})


def tick_reincarnation(reincarnating, color, reserve):
    """Уменьшает счётчики реинкарнации для указанного цвета.
       Вызывать после хода ЭТОГО цвета, до смены current_player."""
    queue = reincarnating[color]
    for entry in queue:
        if entry['turns_left'] > 0:
            entry['turns_left'] -= 1
        if entry['turns_left'] == 0:
            entry['ready'] = True
    # Если в запасе нет пешки — берём первую готовую.
    if 'P' not in reserve[color]:
        for i, entry in enumerate(queue):
            if entry['ready']:
                reserve[color].append('P')
                queue.pop(i)
                break


def promote_from_queue(reincarnating, color, reserve):
    """Если в запасе нет пешки — берём первую готовую из очереди.
       Вызывать после того, как место в запасе освободилось."""
    if 'P' in reserve[color]:
        return
    queue = reincarnating[color]
    for i, entry in enumerate(queue):
        if entry['ready']:
            reserve[color].append('P')
            queue.pop(i)
            return


# --- Геометрия ---
BOARD_ORIGIN_X = LEFT_PANEL + MARGIN
BOARD_ORIGIN_Y = TOP_MARGIN

RESERVE_CX = LEFT_PANEL + BOARD_SIZE * CELL + MARGIN + RIGHT_PANEL // 2
RESERVE_SIZE = int(CELL * 0.72)
RESERVE_GAP = max(6, CELL // 20)


def cell_to_pixel(c, r):
    if BOARD_FLIPPED:
        c = BOARD_SIZE - 1 - c
        r = BOARD_SIZE - 1 - r
    x = BOARD_ORIGIN_X + c * CELL
    y = BOARD_ORIGIN_Y + (BOARD_SIZE - 1 - r) * CELL
    return x, y


def pixel_to_cell(mx, my):
    if BOARD_FLIPPED:
        c = BOARD_SIZE - 1 - (mx - BOARD_ORIGIN_X) // CELL
        r = BOARD_SIZE - 1 - (BOARD_SIZE - 1 - (my - BOARD_ORIGIN_Y) // CELL)
    else:
        c = (mx - BOARD_ORIGIN_X) // CELL
        r = BOARD_SIZE - 1 - (my - BOARD_ORIGIN_Y) // CELL
    return c, r


def reserve_slots():
    """Слоты запаса: 3 типа (R2, J, P), сверху — чёрные, снизу — белые."""
    slots = []
    types = ['R2', 'J', 'P']
    top_y = TOP_MARGIN + CELL // 2
    for i, t in enumerate(types):
        y = top_y + i * (RESERVE_SIZE + RESERVE_GAP)
        slots.append(('b', t, RESERVE_CX, y))
    bottom_start = (TOP_MARGIN + BOARD_SIZE * CELL - CELL // 2
                    - (len(types) - 1) * (RESERVE_SIZE + RESERVE_GAP))
    for i, t in enumerate(types):
        y = bottom_start + i * (RESERVE_SIZE + RESERVE_GAP)
        slots.append(('w', t, RESERVE_CX, y))
    return slots


def slot_at(mx, my, slots):
    for s in slots:
        color, typ, cx, cy = s
        dx = mx - cx
        dy = my - cy
        if dx * dx + dy * dy <= (RESERVE_SIZE // 2) ** 2:
            return s
    return None


# --- Отрисовка ---

def draw_turn_indicator(screen, current_player):
    if current_player is None:
        return
    if current_player == 'w':
        c, r = 0, 0
    else:
        c, r = 0, BOARD_SIZE - 1
    x, y = cell_to_pixel(c, r)
    pygame.draw.rect(screen, TURN_HIGHLIGHT, (x, y, CELL, CELL), 5)


def draw_board(screen, font):
    for c in range(BOARD_SIZE):
        for r in range(BOARD_SIZE):
            x, y = cell_to_pixel(c, r)
            rect = pygame.Rect(x, y, CELL, CELL)
            pygame.draw.rect(screen, LIGHT if (c + r) % 2 == 0 else DARK, rect)
    for c in range(BOARD_SIZE):
        letter = chr(ord('a') + c)
        x, y = cell_to_pixel(c, 0)
        text = font.render(letter, True, (200, 200, 200))
        screen.blit(text, (x + CELL // 2 - 5, y + CELL + 4))
    for r in range(BOARD_SIZE):
        x, y = cell_to_pixel(0, r)
        text = font.render(str(r + 1), True, (200, 200, 200))
        screen.blit(text, (x - 22, y + CELL // 2 - 8))


def draw_piece_at(screen, center, color, typ, pieces):
    img = get_piece_image(pieces, color, typ)
    rect = img.get_rect(center=center)
    screen.blit(img, rect)


def draw_pieces(screen, position, pieces, dragging):
    for (c, r), (color, typ) in position.items():
        if dragging is not None and (c, r) == dragging:
            continue
        x, y = cell_to_pixel(c, r)
        draw_piece_at(screen, (x + CELL // 2, y + CELL // 2), color, typ, pieces)


def draw_highlights(screen, selected, moves, position, en_passant_moves,
                    double_moves, castle_moves, drop_moves):
    if selected is not None:
        c, r = selected
        x, y = cell_to_pixel(c, r)
        pygame.draw.rect(screen, SELECTED, (x, y, CELL, CELL), 4)
        for (mc, mr) in moves:
            mx, my = cell_to_pixel(mc, mr)
            center = (mx + CELL // 2, my + CELL // 2)
            if (mc, mr) in castle_moves:
                pygame.draw.circle(screen, CASTLE_RING, center, CELL // 2 - 10, 5)
            elif (mc, mr) in double_moves:
                pygame.draw.circle(screen, DOUBLE_DOT, center, CELL // 2 - 10, 4)
            elif (mc, mr) in en_passant_moves:
                pygame.draw.circle(screen, EN_PASSANT_RING, center, CELL // 2 - 10, 4)
            elif (mc, mr) in position:
                pygame.draw.circle(screen, CAPTURE_RING, center, CELL // 2 - 10, 4)
            else:
                pygame.draw.circle(screen, MOVE_DOT, center, max(4, CELL // 8))
    for (mc, mr) in drop_moves:
        mx, my = cell_to_pixel(mc, mr)
        center = (mx + CELL // 2, my + CELL // 2)
        pygame.draw.circle(screen, DROP_DOT, center, 12)


def draw_checks(screen, position, current_player):
    enemy = 'b' if current_player == 'w' else 'w'
    for (c, r), (pc, pt) in position.items():
        if pt == 'K' and pc == current_player:
            if is_square_attacked(position, c, r, enemy):
                x, y = cell_to_pixel(c, r)
                pygame.draw.rect(screen, CHECK_COLOR, (x, y, CELL, CELL), 6)


def draw_dragged_piece(screen, position, dragging, drag_pos, pieces):
    if dragging is None or drag_pos is None:
        return
    if dragging not in position:
        return
    color, typ = position[dragging]
    draw_piece_at(screen, drag_pos, color, typ, pieces)


def draw_dragged_reserve(screen, pieces, dragging_reserve, drag_pos):
    if dragging_reserve is None or drag_pos is None:
        return
    color, typ = dragging_reserve
    img = get_piece_image(pieces, color, typ)
    target = int((RESERVE_SIZE - 6) * RESERVE_ICON_SCALE)
    w, h = img.get_size()
    scale = min(target / w, target / h)
    if scale < 1.0:
        img = pygame.transform.smoothscale(
            img, (max(1, int(w * scale)), max(1, int(h * scale))))
    rect = img.get_rect(center=drag_pos)
    screen.blit(img, rect)


def draw_reserve(screen, pieces, reserve, selected_reserve,
                 current_player, game_over, reincarnating, font):
    panel_x = LEFT_PANEL + BOARD_SIZE * CELL + MARGIN
    panel_y = TOP_MARGIN
    panel_w = RIGHT_PANEL
    panel_h = BOARD_SIZE * CELL
    pygame.draw.rect(screen, (25, 25, 35), (panel_x, panel_y, panel_w, panel_h))

    slots = reserve_slots()
    for (color, typ, cx, cy) in slots:
        half = RESERVE_SIZE // 2
        in_reserve = typ in reserve[color]
        bg = (40, 40, 55) if in_reserve else (20, 20, 30)
        pygame.draw.rect(screen, bg,
                         (cx - half, cy - half, RESERVE_SIZE, RESERVE_SIZE))
        border = (100, 100, 130)
        if selected_reserve is not None:
            sc, st = selected_reserve
            if sc == color and st == typ:
                border = (80, 140, 255)
        pygame.draw.rect(screen, border,
                         (cx - half, cy - half, RESERVE_SIZE, RESERVE_SIZE), 3)

        # Для пешки рисуем цифру очереди рядом со слотом,
        # независимо от того, лежит ли она в запасе.
        if typ == 'P':
            q = len(reincarnating[color])
            if q > 0:
                qtext = font.render(str(q), True, QUEUE_COLOR)
                qr = qtext.get_rect()
                qr.topright = (cx + half - 2, cy - half + 2)
                screen.blit(qtext, qr)

        if not in_reserve:
            continue
        dim = (current_player != color) or game_over
        img = get_piece_image(pieces, color, typ)

        target = int((RESERVE_SIZE - 6) * RESERVE_ICON_SCALE)
        w, h = img.get_size()
        scale = min(target / w, target / h)
        if scale < 1.0:
            scaled = pygame.transform.smoothscale(
                img, (max(1, int(w * scale)), max(1, int(h * scale))))
        else:
            scaled = img
        rect = scaled.get_rect(center=(cx, cy))
        if dim:
            tmp = scaled.copy()
            tmp.set_alpha(90)
            screen.blit(tmp, rect)
        else:
            screen.blit(scaled, rect)


def draw_message(screen, big_font, lines, color):
    board_cx = BOARD_ORIGIN_X + BOARD_SIZE * CELL // 2
    board_cy = BOARD_ORIGIN_Y + BOARD_SIZE * CELL // 2
    rendered = [big_font.render(line, True, color) for line in lines]
    total_w = max(r.get_width() for r in rendered)
    total_h = sum(r.get_height() for r in rendered) + (len(rendered) - 1) * 10
    bg = pygame.Surface((total_w + 60, total_h + 40), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 200))
    bg_rect = bg.get_rect(center=(board_cx, board_cy))
    screen.blit(bg, bg_rect)
    y = board_cy - total_h // 2
    for r in rendered:
        rect = r.get_rect(center=(board_cx, y + r.get_height() // 2))
        screen.blit(r, rect)
        y += r.get_height() + 10


def draw_win_message(screen, big_font, winner):
    draw_message(screen, big_font,
                 [f"Мат! Победа {PLAYER_LABELS[winner]}!"],
                 WIN_COLOR)


def draw_resign_message(screen, big_font, loser):
    winner = 'b' if loser == 'w' else 'w'
    text = f"{PLAYER_LABELS[loser]} сдались!"
    sub = f"Победа {PLAYER_LABELS[winner]}!"
    draw_message(screen, big_font, [text, sub], RESIGN_COLOR)


def draw_draw_message(screen, big_font):
    draw_message(screen, big_font, ["НИЧЬЯ"], (200, 200, 255))


def get_promotion_buttons(promotion_pending):
    if promotion_pending is None:
        return {}
    c, r, color = promotion_pending
    board_cx = BOARD_ORIGIN_X + BOARD_SIZE * CELL // 2
    board_cy = BOARD_ORIGIN_Y + BOARD_SIZE * CELL // 2
    n = len(PROMOTION_CHOICES)
    total_w = n * CELL + (n - 1) * 10
    start_x = board_cx - total_w // 2
    y = board_cy - CELL // 2
    buttons = {}
    for i, typ in enumerate(PROMOTION_CHOICES):
        x = start_x + i * (CELL + 10)
        buttons[typ] = pygame.Rect(x, y, CELL, CELL)
    return buttons


def draw_promotion_window(screen, pieces, promotion_pending, font):
    if promotion_pending is None:
        return
    c, r, color = promotion_pending
    buttons = get_promotion_buttons(promotion_pending)
    if not buttons:
        return
    min_x = min(btn.x for btn in buttons.values())
    max_x = max(btn.x + btn.width for btn in buttons.values())
    min_y = min(btn.y for btn in buttons.values())
    max_y = max(btn.y + btn.height for btn in buttons.values())
    overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    screen.blit(overlay, (0, 0))
    padding = 20
    bg_rect = pygame.Rect(min_x - padding, min_y - padding - 40,
                          (max_x - min_x) + 2 * padding,
                          (max_y - min_y) + 2 * padding + 40)
    pygame.draw.rect(screen, (40, 40, 60), bg_rect)
    pygame.draw.rect(screen, (200, 200, 255), bg_rect, 3)
    title = font.render(f"Превращение: {PLAYER_LABELS[color]}", True, (255, 255, 255))
    title_rect = title.get_rect(center=(bg_rect.centerx, bg_rect.y + 20))
    screen.blit(title, title_rect)
    for typ, rect in buttons.items():
        pygame.draw.rect(screen, (200, 200, 200), rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 3)
        img = get_piece_image(pieces, color, typ)
        screen.blit(img, img.get_rect(center=rect.center))
        label = {'Q': 'Ферзь', 'R': 'Ладья', 'B': 'Слон', 'N': 'Конь',
                 'N2': 'Орёл', 'R2': 'Гепард', 'J': 'Джинн'}[typ]
        label_surf = font.render(label, True, (0, 0, 0))
        screen.blit(label_surf, label_surf.get_rect(
            center=(rect.centerx, rect.bottom + 15)))


def make_buttons():
    btn_w = LEFT_PANEL - 40
    cx = 20 + btn_w // 2
    radius = 38
    gap = 6
    total_h = 5 * radius * 2 + 4 * gap
    start_y = WINDOW_H // 2 - total_h // 2 + radius
    buttons = {}
    buttons['freestyle'] = (cx, start_y, radius)
    buttons['back'] = (cx, start_y + 2 * radius + gap, radius)
    buttons['flip'] = (cx, start_y + 2 * (2 * radius + gap), radius)
    buttons['resign'] = (cx, start_y + 3 * (2 * radius + gap), radius)
    buttons['draw'] = (cx, start_y + 4 * (2 * radius + gap), radius)
    return buttons


def draw_buttons(screen, buttons, current_player, game_over, history,
                 first_move_made, draw_offer):
    cx, cy, radius = buttons['freestyle']
    freestyle_active = not first_move_made and not game_over
    draw_circle_button(
        screen, (cx, cy), radius, freestyle_active, FREESTYLE_ICON,
        fill_active=(150, 100, 200), fill_inactive=(70, 50, 90),
        border_active=(200, 160, 255), border_inactive=(100, 80, 120),
        icon_color_active=(255, 255, 255), icon_color_inactive=(140, 110, 160),
        fallback_draw=lambda s, c, sz, col: draw_freestyle_icon(s, c, sz, col, thickness=3),
    )

    cx, cy, radius = buttons['back']
    back_active = len(history) > 0 and not game_over
    draw_circle_button(
        screen, (cx, cy), radius, back_active, BACK_ICON,
        fill_active=(120, 120, 200), fill_inactive=(60, 60, 80),
        border_active=(200, 200, 255), border_inactive=(90, 90, 110),
        icon_color_active=(255, 255, 255), icon_color_inactive=(140, 140, 160),
        fallback_draw=lambda s, c, sz, col: draw_back_icon(s, c, sz, col, thickness=4),
    )

    cx, cy, radius = buttons['flip']
    draw_circle_button(
        screen, (cx, cy), radius, True, FLIP_ICON,
        fill_active=(60, 160, 200), fill_inactive=(40, 90, 120),
        border_active=(150, 220, 255), border_inactive=(70, 120, 150),
        icon_color_active=(255, 255, 255), icon_color_inactive=(140, 180, 200),
        fallback_draw=lambda s, c, sz, col: draw_flip_icon(s, c, sz, col, thickness=4),
    )

    cx, cy, radius = buttons['resign']
    resign_active = not game_over
    draw_circle_button(
        screen, (cx, cy), radius, resign_active, RESIGN_ICON,
        fill_active=(220, 60, 60), fill_inactive=(90, 40, 40),
        border_active=(255, 150, 150), border_inactive=(120, 70, 70),
        icon_color_active=(255, 255, 255), icon_color_inactive=(160, 110, 110),
        fallback_draw=lambda s, c, sz, col: draw_flag_icon(s, c, sz, col, thickness=4),
    )

    cx, cy, radius = buttons['draw']
    draw_active = not game_over
    if draw_offer == current_player:
        draw_active = False
    draw_circle_button(
        screen, (cx, cy), radius, draw_active, DRAW_ICON,
        fill_active=(255, 165, 0), fill_inactive=(90, 70, 40),
        border_active=(255, 200, 100), border_inactive=(120, 100, 70),
        icon_color_active=(255, 255, 255), icon_color_inactive=(160, 140, 110),
        fallback_draw=lambda s, c, sz, col: draw_handshake_icon(s, c, sz, col, thickness=4),
    )


def button_at(mx, my, buttons):
    for name, (cx, cy, radius) in buttons.items():
        if math.hypot(mx - cx, my - cy) <= radius:
            return name
    return None


def button_at_with_margin(mx, my, buttons, margin=15):
    for name, (cx, cy, radius) in buttons.items():
        if math.hypot(mx - cx, my - cy) <= radius + margin:
            return name
    return None


def update_cursor(position, reserve, buttons, hovered_button,
                  dragging, drag_moves, dragging_reserve, reserve_drag_pos,
                  current_player, game_over, mx, my):
    if hovered_button is not None:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        return
    if dragging is not None:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        return
    if dragging_reserve is not None:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        return
    if game_over:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        return
    slot = slot_at(mx, my, reserve_slots())
    if slot is not None:
        color, typ, cx, cy = slot
        if current_player == color and typ in reserve[color]:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            return
    c, r = pixel_to_cell(mx, my)
    if in_bounds(c, r):
        if (c, r) in drag_moves:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            return
        if (c, r) in position:
            pc_color, pc_type = position[(c, r)]
            if pc_color == current_player:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                return
    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)


def draw_tooltip(screen, font, buttons, hovered_button, hovered_time, now):
    if hovered_button is None:
        return
    if now - hovered_time < 700:
        return
    labels = {
        'freestyle': 'Случайная расстановка',
        'back': 'Назад',
        'flip': 'Развернуть доску',
        'resign': 'Сдаться',
        'draw': 'Предложить ничью',
    }
    label = labels.get(hovered_button)
    if label is None:
        return
    cx, cy, radius = buttons[hovered_button]
    text_surf = font.render(label, True, (255, 255, 255))
    tw, th = text_surf.get_size()
    pad = 8
    bg_w = tw + 2 * pad
    bg_h = th + 2 * pad
    bg_x = cx + radius + 8
    bg_y = cy - bg_h // 2
    if bg_x + bg_w > WINDOW_W - 4:
        bg_x = cx - radius - 8 - bg_w
    if bg_y < 4:
        bg_y = 4
    if bg_y + bg_h > WINDOW_H - 4:
        bg_y = WINDOW_H - 4 - bg_h
    pygame.draw.rect(screen, (20, 20, 30), (bg_x, bg_y, bg_w, bg_h))
    pygame.draw.rect(screen, (200, 200, 255), (bg_x, bg_y, bg_w, bg_h), 2)
    screen.blit(text_surf, (bg_x + pad, bg_y + pad))


def main():
    global DRAW_ICON, RESIGN_ICON, BACK_ICON, FLIP_ICON, FREESTYLE_ICON, BOARD_FLIPPED

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Шахматы 10x10")
    font = pygame.font.SysFont("Arial", max(14, CELL // 5))
    big_font = pygame.font.SysFont("Arial", max(24, CELL // 2), bold=True)
    promo_font = pygame.font.SysFont("Arial", max(16, CELL // 4), bold=True)
    tooltip_font = pygame.font.SysFont("Arial", 16)

    pieces = load_pieces()
    DRAW_ICON = load_icon("draw.png", 256)
    RESIGN_ICON = load_icon("resign.png", 256)
    BACK_ICON = load_icon("back.png", 256)
    FLIP_ICON = load_icon("180.png", 256)
    FREESTYLE_ICON = load_icon("freestyle.png", 256)

    position = initial_position()
    reserve = {'w': ['R2', 'J'], 'b': ['R2', 'J']}
    reincarnating = {'w': [], 'b': []}
    history = []
    moved_pawns = set()
    en_passant_move = None
    en_passant_moves = {}
    first_move_made = False

    dragging = None
    drag_pos = None
    drag_moves = []
    drag_double_moves = []
    drag_castle_moves = []

    dragging_reserve = None
    reserve_drag_pos = None

    selected_reserve = None
    drop_moves = []

    vote_draw = {'w': False, 'b': False}
    draw_offer = None
    draw_deadline = 0.0
    winner = None
    is_draw = False
    current_player = 'w'
    promotion_pending = None
    resigned_by = None

    hovered_button = None
    hovered_time = 0

    buttons = make_buttons()

    def snapshot():
        return {
            'position': dict(position),
            'reserve': {'w': list(reserve['w']), 'b': list(reserve['b'])},
            'reincarnating': {'w': [dict(e) for e in reincarnating['w']],
                              'b': [dict(e) for e in reincarnating['b']]},
            'moved_pawns': set(moved_pawns),
            'en_passant_move': en_passant_move,
            'en_passant_moves': dict(en_passant_moves),
            'vote_draw': dict(vote_draw),
            'draw_offer': draw_offer,
            'winner': winner,
            'is_draw': is_draw,
            'resigned_by': resigned_by,
            'current_player': current_player,
            'first_move_made': first_move_made,
        }

    def restore(snap):
        nonlocal position, reserve, reincarnating, moved_pawns, en_passant_move
        nonlocal en_passant_moves, vote_draw, draw_offer, winner, is_draw
        nonlocal resigned_by, current_player, first_move_made
        position = dict(snap['position'])
        reserve = {'w': list(snap['reserve']['w']), 'b': list(snap['reserve']['b'])}
        reincarnating = {'w': [dict(e) for e in snap['reincarnating']['w']],
                         'b': [dict(e) for e in snap['reincarnating']['b']]}
        moved_pawns = set(snap['moved_pawns'])
        en_passant_move = snap['en_passant_move']
        en_passant_moves = dict(snap['en_passant_moves'])
        vote_draw = dict(snap['vote_draw'])
        draw_offer = snap['draw_offer']
        winner = snap['winner']
        is_draw = snap['is_draw']
        resigned_by = snap['resigned_by']
        current_player = snap['current_player']
        first_move_made = snap['first_move_made']

    running = True
    while running:
        now = pygame.time.get_ticks() / 1000.0
        game_over = (winner is not None) or is_draw or (resigned_by is not None)

        if draw_offer is not None and now > draw_deadline:
            draw_offer = None

        mx, my = pygame.mouse.get_pos()
        hb = button_at(mx, my, buttons)
        if hb is None and hovered_button is not None:
            if button_at_with_margin(mx, my, buttons, margin=15) == hovered_button:
                hb = hovered_button
        if hb != hovered_button:
            hovered_button = hb
            hovered_time = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if promotion_pending is not None:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    promo_buttons = get_promotion_buttons(promotion_pending)
                    for typ, rect in promo_buttons.items():
                        if rect.collidepoint(event.pos):
                            c, r, color = promotion_pending
                            position[(c, r)] = (color, typ)
                            promotion_pending = None
                            en_passant_move = None
                            en_passant_moves = {}
                            first_move_made = True
                            # Ход сделан — сначала уменьшаем счётчики того,
                            # кто ходил, потом меняем игрока.
                            tick_reincarnation(reincarnating, color, reserve)
                            current_player = 'b' if color == 'w' else 'w'
                            if is_checkmate(position, current_player,
                                            moved_pawns, en_passant_moves, reserve):
                                winner = 'w' if current_player == 'b' else 'b'
                            break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_z and (event.mod & pygame.KMOD_CTRL):
                    if history:
                        snap = history.pop()
                        restore(snap)
                        dragging = None
                        drag_pos = None
                        drag_moves = []
                        drag_double_moves = []
                        drag_castle_moves = []
                        dragging_reserve = None
                        reserve_drag_pos = None
                        selected_reserve = None
                        drop_moves = []
                        promotion_pending = None

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1:
                    continue
                emx, emy = event.pos

                clicked = button_at(emx, emy, buttons)
                if clicked == 'freestyle':
                    if not first_move_made and not game_over:
                        position = apply_random_position(position)
                    continue
                if clicked == 'back':
                    if history and not game_over:
                        snap = history.pop()
                        restore(snap)
                        dragging = None
                        drag_pos = None
                        drag_moves = []
                        drag_double_moves = []
                        drag_castle_moves = []
                        dragging_reserve = None
                        selected_reserve = None
                        drop_moves = []
                        promotion_pending = None
                    continue
                if clicked == 'flip':
                    BOARD_FLIPPED = not BOARD_FLIPPED
                    dragging = None
                    drag_moves = []
                    continue
                if clicked == 'resign':
                    if not game_over:
                        history.append(snapshot())
                        resigned_by = current_player
                        winner = 'b' if current_player == 'w' else 'w'
                        draw_offer = None
                    continue
                if clicked == 'draw':
                    if not game_over:
                        if draw_offer is None:
                            draw_offer = current_player
                            draw_deadline = now + DRAW_TIMEOUT
                        elif draw_offer != current_player:
                            is_draw = True
                            draw_offer = None
                    continue

                if game_over:
                    continue

                slot = slot_at(emx, emy, reserve_slots())
                if slot is not None:
                    color, typ, cx, cy = slot
                    if current_player == color and typ in reserve[color]:
                        dragging_reserve = (color, typ)
                        reserve_drag_pos = (emx, emy)
                        selected_reserve = None
                        drop_moves = []
                    continue

                c, r = pixel_to_cell(emx, emy)
                if not in_bounds(c, r):
                    continue
                if (c, r) in position:
                    pc_color, pc_type = position[(c, r)]
                    if pc_color == current_player:
                        dragging = (c, r)
                        drag_pos = (emx, emy)
                        drag_moves = filter_legal_moves(position, c, r, pc_color,
                                                        moved_pawns, en_passant_moves)
                        drag_double_moves = []
                        drag_castle_moves = []
                        if pc_type != 'P':
                            drag_castle_moves = compute_castle_moves(
                                position, c, r, pc_color)
                            for cm in drag_castle_moves:
                                if cm not in drag_moves:
                                    drag_moves.append(cm)

            elif event.type == pygame.MOUSEMOTION:
                if dragging is not None:
                    drag_pos = event.pos
                if dragging_reserve is not None:
                    reserve_drag_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button != 1:
                    continue
                emx, emy = event.pos

                # --- Отпускание drag из запаса ---
                if dragging_reserve is not None:
                    color, typ = dragging_reserve
                    c, r = pixel_to_cell(emx, emy)
                    if in_bounds(c, r):
                        drops = legal_drops(position, reserve, color, typ)
                        if (c, r) in drops:
                            history.append(snapshot())
                            reserve[color].remove(typ)
                            position[(c, r)] = (color, typ)
                            en_passant_move = None
                            en_passant_moves = {}
                            first_move_made = True
                            # Ход сделан: если поставили пешку — место в запасе
                            # освободилось, сразу подтягиваем следующую готовую.
                            if typ == 'P':
                                promote_from_queue(reincarnating, color, reserve)
                            tick_reincarnation(reincarnating, color, reserve)
                            current_player = 'b' if color == 'w' else 'w'
                            if is_checkmate(position, current_player,
                                            moved_pawns, en_passant_moves, reserve):
                                winner = 'w' if current_player == 'b' else 'b'
                    dragging_reserve = None
                    reserve_drag_pos = None
                    continue

                # --- Отпускание drag с доски ---
                if dragging is not None:
                    c, r = pixel_to_cell(emx, emy)
                    if in_bounds(c, r) and (c, r) in drag_moves:
                        history.append(snapshot())
                        is_castle = (c, r) in drag_castle_moves
                        captured_piece = None

                        if is_castle:
                            apply_castle(position, dragging[0], dragging[1], c, r)
                            en_passant_move = None
                            en_passant_moves = {}
                        else:
                            is_en_passant = (c, r) in en_passant_moves
                            enemy_pos = en_passant_moves.get((c, r))
                            if is_en_passant and enemy_pos is not None:
                                if enemy_pos in position:
                                    captured_piece = position[enemy_pos]
                                    del position[enemy_pos]
                            if (c, r) in position:
                                captured_piece = position[(c, r)]
                            moved_piece = position.pop(dragging)
                            position[(c, r)] = moved_piece
                            en_passant_move = None
                            if moved_piece[1] == 'P':
                                dc, dr = PAWN_FORWARD[current_player]
                                distance = (abs(r - dragging[1]) if dr != 0
                                            else abs(c - dragging[0]))
                                if distance >= 2:
                                    en_passant_move = (dragging[0], dragging[1],
                                                       c, r, current_player)
                                moved_pawns.add((c, r))
                            en_passant_moves = compute_en_passant(position, en_passant_move)
                            is_promo = (moved_piece[1] == 'P'
                                        and is_promotion_square_for(current_player, c, r))
                            if is_promo:
                                promotion_pending = (c, r, current_player)

                        # Срубленную пешку — в очередь реинкарнации.
                        if captured_piece is not None and captured_piece[1] == 'P':
                            register_pawn_capture(reincarnating, captured_piece[0])

                        first_move_made = True
                        if promotion_pending is None:
                            # Ход сделан — уменьшаем счётчики ходившего,
                            # потом меняем игрока.
                            tick_reincarnation(reincarnating, current_player, reserve)
                            current_player = 'b' if current_player == 'w' else 'w'
                            if is_checkmate(position, current_player,
                                            moved_pawns, en_passant_moves, reserve):
                                winner = 'w' if current_player == 'b' else 'b'
                    dragging = None
                    drag_pos = None
                    drag_moves = []
                    drag_double_moves = []
                    drag_castle_moves = []

        # --- Отрисовка ---
        screen.fill((30, 30, 30))
        draw_board(screen, font)
        draw_checks(screen, position, current_player)
        if not game_over:
            draw_turn_indicator(screen, current_player)
        draw_highlights(screen, dragging, drag_moves, position,
                        en_passant_moves, drag_double_moves,
                        drag_castle_moves, drop_moves)
        draw_pieces(screen, position, pieces, dragging)
        draw_dragged_piece(screen, position, dragging, drag_pos, pieces)
        draw_reserve(screen, pieces, reserve, selected_reserve,
                     current_player, game_over, reincarnating, font)
        draw_dragged_reserve(screen, pieces, dragging_reserve, reserve_drag_pos)
        draw_buttons(screen, buttons, current_player, game_over, history,
                     first_move_made, draw_offer)

        if resigned_by is not None:
            draw_resign_message(screen, big_font, resigned_by)
        elif winner is not None:
            draw_win_message(screen, big_font, winner)
        elif is_draw:
            draw_draw_message(screen, big_font)
        elif promotion_pending is not None:
            draw_promotion_window(screen, pieces, promotion_pending, promo_font)

        draw_tooltip(screen, tooltip_font, buttons,
                     hovered_button, hovered_time, now)

        update_cursor(position, reserve, buttons, hovered_button,
                      dragging, drag_moves, dragging_reserve, reserve_drag_pos,
                      current_player, game_over, mx, my)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
