import json
import sys
import os
import re
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

def requests_to_billion(value):
    return value / 1_000_000_000

def extract_service_name(file_path):
    filename = os.path.basename(file_path)
    name, _ = os.path.splitext(filename)
    prefix = name.split("-")[0]
    prefix = re.sub(r'(\D)(\d)', r'\1 \2', prefix)
    return prefix.title()

def file_to_label(file_path):
    filename = os.path.basename(file_path)
    name, _ = os.path.splitext(filename)

    month_map = {
        "01": "January", "02": "February", "03": "March",
        "04": "April", "05": "May", "06": "June",
        "07": "July", "08": "August", "09": "September",
        "10": "October", "11": "November", "12": "December",
    }

    yymm = name.split("-")[-1]
    yy = yymm[:2]
    mm = yymm[2:]

    return f"20{yy}/{month_map.get(mm, mm)}"

def load_request_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    times = []
    values_billion = []
    total_requests = 0

    for item in data.get("data", []):
        ts = item.get("start_time")
        req = item.get("requests", 0)

        if ts is None:
            continue

        dt = datetime.utcfromtimestamp(ts)
        times.append(dt)
        values_billion.append(requests_to_billion(req))
        total_requests += req

    return times, values_billion, total_requests, requests_to_billion(total_requests)

def build_block_positions(times_old, times_new, gap=2):
    old_x = list(range(1, len(times_old) + 1))
    new_start = len(times_old) + gap + 1
    new_x = list(range(new_start, new_start + len(times_new)))
    return old_x, new_x

def build_block_ticks(times_old, times_new, old_x, new_x, interval=5):
    ticks = []
    labels = []

    for i, (x, dt) in enumerate(zip(old_x, times_old)):
        if dt.day == 1 or dt.day % interval == 1 or i == len(times_old) - 1:
            ticks.append(x)
            labels.append(f"{dt.month}/{dt.day}")

    for i, (x, dt) in enumerate(zip(new_x, times_new)):
        if dt.day == 1 or dt.day % interval == 1 or i == len(times_new) - 1:
            ticks.append(x)
            labels.append(f"{dt.month}/{dt.day}")

    return ticks, labels

def annotate_peak(ax, x_values, times, values, color, label):
    if not times or not values:
        return

    peak_value = max(values)
    peak_index = values.index(peak_value)
    peak_time = times[peak_index]
    peak_x = x_values[peak_index]

    ax.scatter(
        [peak_x],
        [peak_value],
        s=140,
        edgecolors="black",
        linewidths=1.2,
        zorder=6
    )

    ax.annotate(
        f"{label} Peak\n{peak_time.month}/{peak_time.day}: {peak_value:.2f}B",
        xy=(peak_x, peak_value),
        xytext=(0, 18),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color=color,
        bbox=dict(
            boxstyle="round,pad=0.25",
            fc="white",
            ec=color,
            alpha=0.95
        ),
        arrowprops=dict(
            arrowstyle="->",
            color=color,
            lw=1.2
        )
    )

def plot_comparison(file_current, file_previous):
    service_name = extract_service_name(file_current)

    label_current = file_to_label(file_current)
    label_previous = file_to_label(file_previous)

    times_current, req_current, total_current_raw, total_current_billion = load_request_data(file_current)
    times_previous, req_previous, total_previous_raw, total_previous_billion = load_request_data(file_previous)

    diff_raw = total_current_raw - total_previous_raw
    diff_billion = abs(requests_to_billion(diff_raw))
    pct_change = (diff_raw / total_previous_raw * 100) if total_previous_raw else 0

    if diff_raw >= 0:
        trend_color = "green"
        trend_text = f"Increase: {diff_billion:.2f}B | Change: +{pct_change:.2f}%"
    else:
        trend_color = "red"
        trend_text = f"Decrease: {diff_billion:.2f}B | Change: {pct_change:.2f}%"

    items = sorted([
        {
            "label": label_current,
            "times": times_current,
            "values": req_current,
            "total": total_current_billion,
            "first_time": min(times_current)
        },
        {
            "label": label_previous,
            "times": times_previous,
            "values": req_previous,
            "total": total_previous_billion,
            "first_time": min(times_previous)
        }
    ], key=lambda x: x["first_time"])

    old = items[0]
    new = items[1]

    x_old, x_new = build_block_positions(old["times"], new["times"], gap=2)

    fig, ax = plt.subplots(figsize=(16, 9))

    bars_old = ax.bar(x_old, old["values"], width=0.8, alpha=0.85)
    bars_new = ax.bar(x_new, new["values"], width=0.8, alpha=0.85)

    color_old = bars_old.patches[0].get_facecolor()
    color_new = bars_new.patches[0].get_facecolor()

    ticks, tick_labels = build_block_ticks(
        old["times"], new["times"],
        x_old, x_new,
        interval=5
    )

    ax.set_xticks(ticks)
    ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=11)

    ax.axvline(x_old[0] - 0.5, linestyle="--", alpha=0.35, linewidth=1.5)
    ax.axvline(x_new[0] - 0.5, linestyle="--", alpha=0.35, linewidth=1.5)

    annotate_peak(ax, x_old, old["times"], old["values"], color_old, old["label"])
    annotate_peak(ax, x_new, new["times"], new["values"], color_new, new["label"])

    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.2f}"))

    ax.set_xlabel("Date (UTC)", fontsize=16, fontweight="bold", labelpad=10)
    ax.set_ylabel("Requests (Billion)", fontsize=16, fontweight="bold", labelpad=10)
    ax.grid(True, linestyle="--", alpha=0.25)

    fig.suptitle(
        f"Request Comparison ({service_name})",
        fontsize=26,
        fontweight="bold",
        y=0.985
    )

    fig.text(
        0.5,
        0.905,
        trend_text,
        ha="center",
        va="center",
        fontsize=19,
        fontweight="bold",
        color=trend_color
    )

    fig.text(0.32, 0.855, "■", color=color_old, fontsize=18, fontweight="bold", ha="right", va="center")
    fig.text(0.325, 0.855, f' {old["label"]} (Total: {old["total"]:.2f}B)', color="black", fontsize=15, ha="left", va="center")

    fig.text(0.63, 0.855, "■", color=color_new, fontsize=18, fontweight="bold", ha="right", va="center")
    fig.text(0.635, 0.855, f' {new["label"]} (Total: {new["total"]:.2f}B)', color="black", fontsize=15, ha="left", va="center")

    print("\n=== Request Comparison ===")
    print(f"{label_current} Total: {total_current_billion:.2f}B")
    print(f"{label_previous} Total: {total_previous_billion:.2f}B")
    print(trend_text)

    plt.tight_layout(rect=[0.03, 0.06, 0.97, 0.80])
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 requests-sum.py <current_period.json> <previous_period.json>")
    else:
        plot_comparison(sys.argv[1], sys.argv[2])
