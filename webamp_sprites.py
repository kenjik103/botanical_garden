"""Winamp classic-skin sprite coordinate map.

Classic Winamp skins do NOT store sprite coordinates — Winamp has the layout
hardcoded, so every skin's BMP sheets place each sprite at the same fixed
(x, y, w, h). This module is that universal coordinate table, transcribed
verbatim from Webamp (the JS Winamp reimplementation, which renders classic
skins pixel-for-pixel):

    github.com/captbaritone/webamp  ->  packages/webamp/js/skinSprites.ts

Pairing these coordinates with a given skin's pixel sheets is all the import
tool needs to "cut" sprites — the web equivalent of Winamp's internal blit is
a CSS background-position. See SKIN_IMPORT.md, Module 2.

Coordinate origin is the top-left of each sheet; +y is downward (matches CSS
negative background-position).
"""

# --- Bitmap font ----------------------------------------------------------
# text.bmp is a glyph atlas of fixed CHAR_W x CHAR_H cells. FONT_LOOKUP maps a
# character to its (row, col) cell; pixel offset is (col*CHAR_W, row*CHAR_H).
# (Webamp stores these as [row, col]; we keep that ordering.)
CHAR_W = 5
CHAR_H = 6

UTF8_ELLIPSIS = "…"

FONT_LOOKUP = {
    "a": (0, 0), "b": (0, 1), "c": (0, 2), "d": (0, 3), "e": (0, 4),
    "f": (0, 5), "g": (0, 6), "h": (0, 7), "i": (0, 8), "j": (0, 9),
    "k": (0, 10), "l": (0, 11), "m": (0, 12), "n": (0, 13), "o": (0, 14),
    "p": (0, 15), "q": (0, 16), "r": (0, 17), "s": (0, 18), "t": (0, 19),
    "u": (0, 20), "v": (0, 21), "w": (0, 22), "x": (0, 23), "y": (0, 24),
    "z": (0, 25),
    '"': (0, 26), "@": (0, 27), " ": (0, 30),
    "0": (1, 0), "1": (1, 1), "2": (1, 2), "3": (1, 3), "4": (1, 4),
    "5": (1, 5), "6": (1, 6), "7": (1, 7), "8": (1, 8), "9": (1, 9),
    UTF8_ELLIPSIS: (1, 10),
    ".": (1, 11), ":": (1, 12), "(": (1, 13), ")": (1, 14), "-": (1, 15),
    "'": (1, 16), "!": (1, 17), "_": (1, 18), "+": (1, 19), "\\": (1, 20),
    "/": (1, 21), "[": (1, 22), "]": (1, 23), "^": (1, 24), "&": (1, 25),
    "%": (1, 26), ",": (1, 27), "=": (1, 28), "$": (1, 29), "#": (1, 30),
    "Å": (2, 0), "Ö": (2, 1), "Ä": (2, 2), "?": (2, 3),
    "*": (2, 4),
    "<": (1, 22), ">": (1, 23), "{": (1, 22), "}": (1, 23),
}

# --- Sheet -> source BMP filename -----------------------------------------
# Filenames are matched case-insensitively against the .wsz contents.
SHEET_FILES = {
    "BALANCE": "balance.bmp",
    "CBUTTONS": "cbuttons.bmp",
    "MAIN": "main.bmp",
    "MONOSTER": "monoster.bmp",
    "NUMBERS": "numbers.bmp",
    "NUMS_EX": "nums_ex.bmp",
    "PLAYPAUS": "playpaus.bmp",
    "PLEDIT": "pledit.bmp",
    "EQ_EX": "eq_ex.bmp",
    "EQMAIN": "eqmain.bmp",
    "POSBAR": "posbar.bmp",
    "SHUFREP": "shufrep.bmp",
    "TEXT": "text.bmp",
    "TITLEBAR": "titlebar.bmp",
    "VOLUME": "volume.bmp",
    "GEN": "gen.bmp",
}


def _font_sprites():
    """Build the TEXT sheet's sprite list from FONT_LOOKUP."""
    out = []
    for char, (row, col) in FONT_LOOKUP.items():
        out.append({
            "name": "CHARACTER_%d" % ord(char),
            "x": col * CHAR_W,
            "y": row * CHAR_H,
            "width": CHAR_W,
            "height": CHAR_H,
        })
    return out


# --- Sprite sheets ---------------------------------------------------------
# {sheet: [ {name, x, y, width, height}, ... ]}
SPRITES = {
    "BALANCE": [
        {"name": "MAIN_BALANCE_BACKGROUND", "x": 9, "y": 0, "width": 38, "height": 420},
        {"name": "MAIN_BALANCE_THUMB", "x": 15, "y": 422, "width": 14, "height": 11},
        {"name": "MAIN_BALANCE_THUMB_ACTIVE", "x": 0, "y": 422, "width": 14, "height": 11},
    ],
    "CBUTTONS": [
        {"name": "MAIN_PREVIOUS_BUTTON", "x": 0, "y": 0, "width": 23, "height": 18},
        {"name": "MAIN_PREVIOUS_BUTTON_ACTIVE", "x": 0, "y": 18, "width": 23, "height": 18},
        {"name": "MAIN_PLAY_BUTTON", "x": 23, "y": 0, "width": 23, "height": 18},
        {"name": "MAIN_PLAY_BUTTON_ACTIVE", "x": 23, "y": 18, "width": 23, "height": 18},
        {"name": "MAIN_PAUSE_BUTTON", "x": 46, "y": 0, "width": 23, "height": 18},
        {"name": "MAIN_PAUSE_BUTTON_ACTIVE", "x": 46, "y": 18, "width": 23, "height": 18},
        {"name": "MAIN_STOP_BUTTON", "x": 69, "y": 0, "width": 23, "height": 18},
        {"name": "MAIN_STOP_BUTTON_ACTIVE", "x": 69, "y": 18, "width": 23, "height": 18},
        {"name": "MAIN_NEXT_BUTTON", "x": 92, "y": 0, "width": 23, "height": 18},
        {"name": "MAIN_NEXT_BUTTON_ACTIVE", "x": 92, "y": 18, "width": 22, "height": 18},
        {"name": "MAIN_EJECT_BUTTON", "x": 114, "y": 0, "width": 22, "height": 16},
        {"name": "MAIN_EJECT_BUTTON_ACTIVE", "x": 114, "y": 16, "width": 22, "height": 16},
    ],
    "MAIN": [
        {"name": "MAIN_WINDOW_BACKGROUND", "x": 0, "y": 0, "width": 275, "height": 116},
    ],
    "MONOSTER": [
        {"name": "MAIN_STEREO", "x": 0, "y": 12, "width": 29, "height": 12},
        {"name": "MAIN_STEREO_SELECTED", "x": 0, "y": 0, "width": 29, "height": 12},
        {"name": "MAIN_MONO", "x": 29, "y": 12, "width": 27, "height": 12},
        {"name": "MAIN_MONO_SELECTED", "x": 29, "y": 0, "width": 27, "height": 12},
    ],
    "NUMBERS": [
        {"name": "NO_MINUS_SIGN", "x": 9, "y": 6, "width": 5, "height": 1},
        {"name": "MINUS_SIGN", "x": 20, "y": 6, "width": 5, "height": 1},
        {"name": "DIGIT_0", "x": 0, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_1", "x": 9, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_2", "x": 18, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_3", "x": 27, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_4", "x": 36, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_5", "x": 45, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_6", "x": 54, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_7", "x": 63, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_8", "x": 72, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_9", "x": 81, "y": 0, "width": 9, "height": 13},
    ],
    "NUMS_EX": [
        {"name": "NO_MINUS_SIGN_EX", "x": 90, "y": 0, "width": 9, "height": 13},
        {"name": "MINUS_SIGN_EX", "x": 99, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_0_EX", "x": 0, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_1_EX", "x": 9, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_2_EX", "x": 18, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_3_EX", "x": 27, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_4_EX", "x": 36, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_5_EX", "x": 45, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_6_EX", "x": 54, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_7_EX", "x": 63, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_8_EX", "x": 72, "y": 0, "width": 9, "height": 13},
        {"name": "DIGIT_9_EX", "x": 81, "y": 0, "width": 9, "height": 13},
    ],
    "PLAYPAUS": [
        {"name": "MAIN_PLAYING_INDICATOR", "x": 0, "y": 0, "width": 9, "height": 9},
        {"name": "MAIN_PAUSED_INDICATOR", "x": 9, "y": 0, "width": 9, "height": 9},
        {"name": "MAIN_STOPPED_INDICATOR", "x": 18, "y": 0, "width": 9, "height": 9},
        {"name": "MAIN_NOT_WORKING_INDICATOR", "x": 36, "y": 0, "width": 9, "height": 9},
        {"name": "MAIN_WORKING_INDICATOR", "x": 39, "y": 0, "width": 9, "height": 9},
    ],
    "POSBAR": [
        {"name": "MAIN_POSITION_SLIDER_BACKGROUND", "x": 0, "y": 0, "width": 248, "height": 10},
        {"name": "MAIN_POSITION_SLIDER_THUMB", "x": 248, "y": 0, "width": 29, "height": 10},
        {"name": "MAIN_POSITION_SLIDER_THUMB_SELECTED", "x": 278, "y": 0, "width": 29, "height": 10},
    ],
    "SHUFREP": [
        {"name": "MAIN_SHUFFLE_BUTTON", "x": 28, "y": 0, "width": 47, "height": 15},
        {"name": "MAIN_SHUFFLE_BUTTON_DEPRESSED", "x": 28, "y": 15, "width": 47, "height": 15},
        {"name": "MAIN_SHUFFLE_BUTTON_SELECTED", "x": 28, "y": 30, "width": 47, "height": 15},
        {"name": "MAIN_SHUFFLE_BUTTON_SELECTED_DEPRESSED", "x": 28, "y": 45, "width": 47, "height": 15},
        {"name": "MAIN_REPEAT_BUTTON", "x": 0, "y": 0, "width": 28, "height": 15},
        {"name": "MAIN_REPEAT_BUTTON_DEPRESSED", "x": 0, "y": 15, "width": 28, "height": 15},
        {"name": "MAIN_REPEAT_BUTTON_SELECTED", "x": 0, "y": 30, "width": 28, "height": 15},
        {"name": "MAIN_REPEAT_BUTTON_SELECTED_DEPRESSED", "x": 0, "y": 45, "width": 28, "height": 15},
        {"name": "MAIN_EQ_BUTTON", "x": 0, "y": 61, "width": 23, "height": 12},
        {"name": "MAIN_EQ_BUTTON_SELECTED", "x": 0, "y": 73, "width": 23, "height": 12},
        {"name": "MAIN_EQ_BUTTON_DEPRESSED", "x": 46, "y": 61, "width": 23, "height": 12},
        {"name": "MAIN_EQ_BUTTON_DEPRESSED_SELECTED", "x": 46, "y": 73, "width": 23, "height": 12},
        {"name": "MAIN_PLAYLIST_BUTTON", "x": 23, "y": 61, "width": 23, "height": 12},
        {"name": "MAIN_PLAYLIST_BUTTON_SELECTED", "x": 23, "y": 73, "width": 23, "height": 12},
        {"name": "MAIN_PLAYLIST_BUTTON_DEPRESSED", "x": 69, "y": 61, "width": 23, "height": 12},
        {"name": "MAIN_PLAYLIST_BUTTON_DEPRESSED_SELECTED", "x": 69, "y": 73, "width": 23, "height": 12},
    ],
    "TEXT": _font_sprites(),
    "TITLEBAR": [
        {"name": "MAIN_TITLE_BAR", "x": 27, "y": 15, "width": 275, "height": 14},
        {"name": "MAIN_TITLE_BAR_SELECTED", "x": 27, "y": 0, "width": 275, "height": 14},
        {"name": "MAIN_EASTER_EGG_TITLE_BAR", "x": 27, "y": 72, "width": 275, "height": 14},
        {"name": "MAIN_EASTER_EGG_TITLE_BAR_SELECTED", "x": 27, "y": 57, "width": 275, "height": 14},
        {"name": "MAIN_OPTIONS_BUTTON", "x": 0, "y": 0, "width": 9, "height": 9},
        {"name": "MAIN_OPTIONS_BUTTON_DEPRESSED", "x": 0, "y": 9, "width": 9, "height": 9},
        {"name": "MAIN_MINIMIZE_BUTTON", "x": 9, "y": 0, "width": 9, "height": 9},
        {"name": "MAIN_MINIMIZE_BUTTON_DEPRESSED", "x": 9, "y": 9, "width": 9, "height": 9},
        {"name": "MAIN_SHADE_BUTTON", "x": 0, "y": 18, "width": 9, "height": 9},
        {"name": "MAIN_SHADE_BUTTON_DEPRESSED", "x": 9, "y": 18, "width": 9, "height": 9},
        {"name": "MAIN_CLOSE_BUTTON", "x": 18, "y": 0, "width": 9, "height": 9},
        {"name": "MAIN_CLOSE_BUTTON_DEPRESSED", "x": 18, "y": 9, "width": 9, "height": 9},
    ],
    "VOLUME": [
        {"name": "MAIN_VOLUME_BACKGROUND", "x": 0, "y": 0, "width": 68, "height": 420},
        {"name": "MAIN_VOLUME_THUMB", "x": 15, "y": 422, "width": 14, "height": 11},
        {"name": "MAIN_VOLUME_THUMB_SELECTED", "x": 0, "y": 422, "width": 14, "height": 11},
    ],
}
