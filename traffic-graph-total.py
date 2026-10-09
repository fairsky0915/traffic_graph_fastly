import json
import sys
import os
import re
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

MONTH_MAP = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May", "06": "June", "07": "July", "08": "August",
    "09": "September", "10": "October", "11": "November", "12": "December",
}

METRICS = {
    "bandwidth": {
        "json_key": "bandwidth",
        "convert": lambda v: v / (1000 ** 5),
        "unit": "PB",
        "ylabel": "Bandwidth (PB)",
        "title": "Bandwidth Comparison",
    },
    "requests": {
        "json_key": "requests",
        "convert": lambda v: v / 1_000_000_000,
        "unit": "B",
        "ylabel": "Requests (Billion)",
        "title": "Request Comparison",
    },
}


def extract_service_name(file_path):
    filename = os.path.basename(file_path)
    name, _ = os.path.splitext(filename)
    prefix = name.split("-")[0]
    prefix = re.sub(r"(\D)(\d)", r"\1 \2", prefix)
    return prefix.title()


def file_to_label(file_path):
    filename = os.path.basename(file_path)
    name, _ = os.path.splitext(filename)
    yymm = name.split("-")[-1]

    if not re.fullmatch(r"\d{4}", yymm):
        return name

    yy, mm = yymm[:2], yymm[2:]
    return f"20{yy}/{MONTH_MAP.get(mm, mm)}"


def load_data(file_path, metric):
    cfg = METRICS[metric]
    key = cfg["json_key"]

    with open(file_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    rows = []
    total_raw = 0

    for item in payload.get("data", []):
        ts = item.get("start_time")
        raw = item.get(key)
        if ts is None or raw is None:
            continue

        dt = datetime.utcfromtimestamp(ts)
        rows.append((dt, cfg["convert"](raw)))
        total_raw += raw

    if not rows:
        raise ValueError(f"No '{key}' data found in {file_path}")

    rows.sort(key=lambda x: x[0])
    times = [r[0] for r in rows]
    values = [r[1] for r in rows]
    total_converted = cfg["convert"](total_raw)
    return times, values, total_raw, total_converted


def build_monthly_ticks(all_times, interval=5):
    ticks = []
    months = sorted(set((dt.year, dt.month) for dt in all_times))

    for year, month in months:
        month_dates = sorted(dt for dt in all_times if dt.year == year and dt.month == month)
        available = {dt.day: dt for dt in month_dates}
        last_day = max(available)

        for day in range(1, last_day + 1, interval):
            if day in available:
                ticks.append(available[day])

        if available[last_day] not in ticks:
            ticks.append(available[last_day])

    return sorted(set(ticks))


def build_block_positions(times_old, times_new, gap=2):
    old_x = list(range(1, len(times_old) + 1))
    new_start = len(times_old) + gap + 1
    new_x = list(range(new_start, new_start + len(times_new)))
    return old_x, new_x


def build_block_ticks(times_old, times_new, old_x, new_x, interval=5):
    ticks, labels = [], []

    for x_values, times in ((old_x, times_old), (new_x, times_new)):
        for i, (x, dt) in enumerate(zip(x_values, times)):
            if dt.day == 1 or dt.day % interval == 1 or i == len(times) - 1:
                ticks.append(x)
                labels.append(f"{dt.month}/{dt.day}")

    return ticks, labels


def annotate_peak(ax, x_values, times, values, color, label, unit):
    peak_value = max(values)
    idx = values.index(peak_value)
    peak_time = times[idx]
    peak_x = x_values[idx]

    ax.scatter([peak_x], [peak_value], s=140, edgecolors="black", linewidths=1.2, zorder=6)
    ax.annotate(
        f"{label} Peak\n{peak_time.month}/{peak_time.day}: {peak_value:.2f} {unit}",
        xy=(peak_x, peak_value),
        xytext=(0, 18),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color=color,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, alpha=0.95),
        arrowprops=dict(arrowstyle="->", color=color, lw=1.2),
    )


def draw_summary(fig, items):
    positions = [(0.32, 0.325), (0.63, 0.635)]
    for item, (bullet_x, text_x) in zip(items, positions):
        fig.text(bullet_x, 0.855, "■", color=item["color"], fontsize=18,
                 fontweight="bold", ha="right", va="center")
        fig.text(text_x, 0.855,
                 f' {item["label"]} (Total: {item["total"]:.2f} {item["unit"]})',
                 color="black", fontsize=15, ha="left", va="center")


def plot_comparison(metric, mode, file_current, file_previous):
    cfg = METRICS[metric]
    service_name = extract_service_name(file_current)
    label_current = file_to_label(file_current)
    label_previous = file_to_label(file_previous)

    tc, vc, raw_c, total_c = load_data(file_current, metric)
    tp, vp, raw_p, total_p = load_data(file_previous, metric)

    diff_raw = raw_c - raw_p
    diff_display = abs(cfg["convert"](diff_raw))
    pct = (diff_raw / raw_p * 100) if raw_p else 0

    if diff_raw >= 0:
        trend_color = "green"
        trend_text = f"Increase: {diff_display:.2f} {cfg['unit']} | Change: +{pct:.2f}%"
    else:
        trend_color = "red"
        trend_text = f"Decrease: {diff_display:.2f} {cfg['unit']} | Change: {pct:.2f}%"

    fig, ax = plt.subplots(figsize=(16, 9))

    # Always display older period first in the chart/summary.
    items = sorted([
        {"label": label_current, "times": tc, "values": vc, "total": total_c,
         "first_time": min(tc), "unit": cfg["unit"]},
        {"label": label_previous, "times": tp, "values": vp, "total": total_p,
         "first_time": min(tp), "unit": cfg["unit"]},
    ], key=lambda x: x["first_time"])
    old, new = items

    if mode == "yoy":
        x_old, x_new = build_block_positions(old["times"], new["times"], gap=2)
        bars_old = ax.bar(x_old, old["values"], width=0.8, alpha=0.85)
        bars_new = ax.bar(x_new, new["values"], width=0.8, alpha=0.85)

        color_old = bars_old.patches[0].get_facecolor()
        color_new = bars_new.patches[0].get_facecolor()

        ticks, labels = build_block_ticks(old["times"], new["times"], x_old, x_new, interval=5)
        ax.set_xticks(ticks)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=11)
        ax.axvline(x_old[0] - 0.5, linestyle="--", alpha=0.35, linewidth=1.5)
        ax.axvline(x_new[0] - 0.5, linestyle="--", alpha=0.35, linewidth=1.5)

        annotate_peak(ax, x_old, old["times"], old["values"], color_old, old["label"], cfg["unit"])
        annotate_peak(ax, x_new, new["times"], new["values"], color_new, new["label"], cfg["unit"])
    else:
        bars_old = ax.bar(old["times"], old["values"], width=0.8, alpha=0.85)
        bars_new = ax.bar(new["times"], new["values"], width=0.8, alpha=0.85)

        color_old = bars_old.patches[0].get_facecolor()
        color_new = bars_new.patches[0].get_facecolor()

        all_times = sorted(set(old["times"] + new["times"]))
        tick_times = build_monthly_ticks(all_times, interval=5)
        ax.set_xticks(tick_times)
        ax.set_xticklabels([f"{dt.month}/{dt.day}" for dt in tick_times],
                           rotation=45, ha="right", fontsize=11)

        month_starts = sorted(
            min(dt for dt in all_times if dt.year == y and dt.month == m)
            for y, m in sorted(set((dt.year, dt.month) for dt in all_times))
        )
        for dt in month_starts:
            ax.axvline(dt, linestyle="--", alpha=0.35, linewidth=1.5)

        annotate_peak(ax, old["times"], old["times"], old["values"], color_old, old["label"], cfg["unit"])
        annotate_peak(ax, new["times"], new["times"], new["values"], color_new, new["label"], cfg["unit"])

    old["color"] = color_old
    new["color"] = color_new

    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.2f}"))
    ax.set_xlabel("Date (UTC)", fontsize=16, fontweight="bold", labelpad=10)
    ax.set_ylabel(cfg["ylabel"], fontsize=16, fontweight="bold", labelpad=10)
    ax.grid(True, linestyle="--", alpha=0.25)

    fig.suptitle(f"{cfg['title']} ({service_name})", fontsize=26, fontweight="bold", y=0.985)
    fig.text(0.5, 0.905, trend_text, ha="center", va="center",
             fontsize=19, fontweight="bold", color=trend_color)
    draw_summary(fig, [old, new])

    print(f"\n=== {cfg['title']} / {mode.upper()} ===")
    print(f"{label_current} Total: {total_c:.2f} {cfg['unit']}")
    print(f"{label_previous} Total: {total_p:.2f} {cfg['unit']}")
    print(trend_text)

    plt.tight_layout(rect=[0.03, 0.06, 0.97, 0.80])
    plt.show()


def usage():
    print("Usage:")
    print("  python3 traffic-graph.py <bandwidth|requests> <mom|yoy> <current.json> <previous.json>")
    print("\nExamples:")
    print("  python3 traffic-graph.py bandwidth mom switch1-2604.json switch1-2603.json")
    print("  python3 traffic-graph.py bandwidth yoy switch1-2606.json switch1-2506.json")
    print("  python3 traffic-graph.py requests mom switch1-2604.json switch1-2603.json")
    print("  python3 traffic-graph.py requests yoy switch1-2606.json switch1-2506.json")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        usage()
        sys.exit(1)

    metric = sys.argv[1].lower()
    mode = sys.argv[2].lower()

    if metric not in METRICS or mode not in ("mom", "yoy"):
        usage()
        sys.exit(1)

    try:
        plot_comparison(metric, mode, sys.argv[3], sys.argv[4])
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)
