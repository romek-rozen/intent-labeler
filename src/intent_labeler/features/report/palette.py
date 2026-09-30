"""Categorical colours for intents, in fixed order (validated light/dark pairs).

Colour follows the intent's position in the model output, never its share, so a
re-run that re-orders shares does not repaint intents. Beyond eight intents the
colour repeats and the label + legend carry identity.
"""
LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]
UNASSIGNED = "var(--muted)"


def slot(index: int) -> str:
    return f"var(--s{index % len(LIGHT) + 1})"


def css_vars(mode: str) -> str:
    colors = LIGHT if mode == "light" else DARK
    return " ".join(f"--s{i + 1}:{color};" for i, color in enumerate(colors))
