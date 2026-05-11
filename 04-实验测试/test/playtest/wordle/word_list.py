"""
Word list management for Wordle.
Provides validation and random word selection.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import List, Optional


# Embedded minimal word list for testing (common 5-letter English words)
_BUILTIN_WORDS = [
    "CRANE", "SLATE", "AROSE", "LEAST", "RAISE", "STARE", "SNARE", "TRACE",
    "CRATE", "IRATE", "STALE", "LATER", "ALTER", "ALERT", "RATEL", "TARES",
    "TEARS", "RATES", "ASTER", "RESAT", "EARLS", "LASER", "LARES", "ARLES",
    "REALS", "LEARN", "RENAL", "LANES", "LEAN", "PANEL", "PENAL", "PLANE",
    "APPLE", "CRANE", "WORLD", "FLAME", "BRAVE", "CHESS", "DRINK", "EAGLE",
    "FAINT", "GHOST", "HAPPY", "INLET", "JUDGE", "KNEEL", "LEMON", "MANGO",
    "NERVE", "OCEAN", "PIANO", "QUEEN", "RIVER", "SALVE", "TASTE", "ULTRA",
    "VAPOR", "WATER", "XENON", "YACHT", "ZEBRA", "ABOVE", "BLOWN", "CIVIC",
    "DEPOT", "EMPTY", "FEVER", "GRACE", "HABIT", "IGLOO", "JEWEL", "KIOSK",
    "LILAC", "MANOR", "NAIVE", "OLIVE", "POPPY", "QUOTA", "ROYAL", "SUGAR",
    "THORN", "UPSET", "VISOR", "WATCH", "OXIDE", "YOUTH", "ZONES", "AISLE",
    "BLAZE", "CLAMP", "DWARF", "ELBOW", "FLUTE", "GLOOM", "HINGE", "IRONY",
    "JOUST", "KNACK", "LLAMA", "MAIZE", "NOTCH", "OPTIC", "PERCH", "QUIRK",
    "RANCH", "SPITE", "THYME", "UNTIL", "VICAR", "WHISK", "XYLEM", "YEARN",
    "JAZZY", "QUEUE", "TRYST", "GLYPH", "NYMPH", "CRYPT", "BYWAY", "PYGMY",
]


class WordList:
    """
    Manages the valid 5-letter word list for Wordle.
    Supports loading from file or using the built-in list.
    """

    WORD_LENGTH = 5

    def __init__(self, words: List[str]) -> None:
        self._words: List[str] = [w.upper().strip() for w in words if len(w.strip()) == self.WORD_LENGTH]
        self._word_set: set = set(self._words)

    @classmethod
    def from_file(cls, path: str) -> "WordList":
        """Load word list from a text file (one word per line)."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Word list file not found: {path}")
        with open(p) as f:
            words = [line.strip() for line in f if line.strip()]
        return cls(words)

    @classmethod
    def builtin(cls) -> "WordList":
        """Use the embedded built-in word list (for testing and demos)."""
        return cls(_BUILTIN_WORDS)

    def get_random_word(self, seed: Optional[int] = None) -> str:
        """Return a random word from the list."""
        if not self._words:
            raise RuntimeError("Word list is empty")
        rng = random.Random(seed) if seed is not None else random
        return rng.choice(self._words)

    def is_valid_word(self, word: str) -> bool:
        """Check if a word exists in the valid word set."""
        return word.upper().strip() in self._word_set

    def get_all_words(self) -> List[str]:
        """Return all words in the list."""
        return list(self._words)

    def __len__(self) -> int:
        return len(self._words)
