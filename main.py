import random
from decimal import Decimal, getcontext

getcontext().prec = 28

# ------------------- CONFIG -------------------
CONFIG = {
    "input_file": "marks.txt",
    "output_file": "split_marks.txt",

    # Original maximum mark
    "input_max": Decimal("30"),

    # Maximum marks for each part.
    # Example: 30 -> 30 marks in 4 parts
    "part_max": [Decimal("8"), Decimal("7"), Decimal("8"), Decimal("7")],

    # If None, output_max = sum(part_max)
    # Example: 30 -> 30 marks, so output_max becomes 30
    "output_max": None,

    # "sequential" = fill parts in order, like your example
    # "proportional" = split proportionally to each part's max
    # "random" = randomly distribute marks/deductions across parts
    "mode": "random",

    # Step size for random marks (e.g. 0.5 for half-marks)
    "step": Decimal("0.5"),

    # Deduction weighting for random mode:
    # "proportional" = questions with more marks lose marks more often
    # "uniform" = all eligible questions equally likely to lose marks
    "random_weighting": "proportional",

    # Optional random seed for reproducible results (int or None)
    "random_seed": None,

    # Round output values. Use None for no rounding.
    "round_to": Decimal("0.01"),
}
# ----------------------------------------------


def fmt(d):
    """Format Decimal without unnecessary trailing zeros."""
    if CONFIG["round_to"] is not None:
        d = d.quantize(CONFIG["round_to"])
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def split_mark_random(scaled, part_max, step=Decimal("0.5"), weighting="proportional"):
    """
    Distribute deductions randomly in units of `step` starting from full marks for each part.
    This creates natural exam grading variance while ensuring:
    - 0 <= part[i] <= part_max[i]
    - sum(parts) == scaled
    - each part is a multiple of `step` (when scaled and part_max are multiples of `step`)
    """
    total_max = sum(part_max, Decimal("0"))
    if total_max <= 0:
        return [Decimal("0") for _ in part_max]

    if scaled >= total_max:
        return [pm for pm in part_max]

    if scaled <= Decimal("0"):
        return [Decimal("0") for _ in part_max]

    parts = [pm for pm in part_max]
    deficit = total_max - scaled

    if step <= Decimal("0"):
        step = Decimal("0.5")

    # If there is a fractional remainder smaller than step, deduct it first
    num_steps = int(deficit // step)
    rem = deficit - (Decimal(num_steps) * step)

    if rem > Decimal("0"):
        eligible = [i for i, p in enumerate(parts) if p >= rem]
        if eligible:
            if weighting == "proportional":
                weights = [float(parts[i]) for i in eligible]
                chosen = (
                    random.choices(eligible, weights=weights, k=1)[0]
                    if sum(weights) > 0
                    else random.choice(eligible)
                )
            else:
                chosen = random.choice(eligible)
            parts[chosen] -= rem

    for _ in range(num_steps):
        eligible = [i for i, p in enumerate(parts) if p >= step]
        if not eligible:
            break
        if weighting == "proportional":
            weights = [float(parts[i]) for i in eligible]
            chosen = (
                random.choices(eligible, weights=weights, k=1)[0]
                if sum(weights) > 0
                else random.choice(eligible)
            )
        else:
            chosen = random.choice(eligible)
        parts[chosen] -= step

    # Safeguard: ensure sum(parts) matches scaled exactly
    diff = scaled - sum(parts, Decimal("0"))
    if diff != Decimal("0"):
        if diff > 0:
            for i in range(len(parts)):
                avail = part_max[i] - parts[i]
                if avail >= diff:
                    parts[i] += diff
                    break
        elif diff < 0:
            abs_diff = -diff
            for i in range(len(parts)):
                if parts[i] >= abs_diff:
                    parts[i] -= abs_diff
                    break

    return parts


def split_mark(mark):
    input_max = CONFIG["input_max"]
    part_max = CONFIG["part_max"]

    output_max = CONFIG["output_max"]
    if output_max is None:
        output_max = sum(part_max, Decimal("0"))
    else:
        output_max = Decimal(str(output_max))

    mark = Decimal(str(mark))

    # Clamp mark to valid range
    if mark < 0:
        mark = Decimal("0")
    if mark > input_max:
        mark = input_max

    # Convert mark to the output total
    scaled = mark / input_max * output_max

    if CONFIG["mode"] == "proportional":
        values = []
        for pm in part_max:
            values.append(scaled * pm / output_max)

        # Force last part to preserve total
        values[-1] = scaled - sum(values[:-1])
        return values

    if CONFIG["mode"] == "random":
        step = CONFIG.get("step", Decimal("0.5"))
        weighting = CONFIG.get("random_weighting", "proportional")
        return split_mark_random(scaled, part_max, step, weighting)

    # sequential mode
    values = []
    remaining = scaled

    for pm in part_max:
        value = min(pm, remaining)
        values.append(value)
        remaining -= value

    # If something remains because output_max is larger than sum(part_max),
    # add it to the last part.
    if remaining > 0:
        values[-1] += remaining

    return values


def main():
    if CONFIG.get("random_seed") is not None:
        random.seed(CONFIG["random_seed"])

    with open(CONFIG["input_file"], "r", encoding="utf-8") as f:
        raw = f.read()

    # Read numbers separated by spaces, tabs, newlines, or commas
    tokens = raw.replace(",", " ").split()

    output_lines = []

    for token in tokens:
        try:
            mark = Decimal(token)
        except Exception:
            continue

        parts = split_mark(mark)

        # Each part becomes one row
        for value in parts:
            output_lines.append(fmt(value))

    with open(CONFIG["output_file"], "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
        if output_lines:
            f.write("\n")

    print(f"Done. Wrote {len(output_lines)} rows to {CONFIG['output_file']}")


if __name__ == "__main__":
    main()