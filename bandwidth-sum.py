import json
import sys
import os
import re
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

def bytes_to_pb(bytes_value):
    return bytes_value / (1000 ** 5)

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

def load_bandwidth_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    times = []
    values_pb = []
    total_bytes = 0

    for item in data.get("data", []):
        ts = item.get("start_time")
        bw = item.get("bandwidth", 0)

        if ts is None:
            continue

        dt = datetime.utcfromtimestamp(ts)
        times.append(dt)
        values_pb.append(bytes_to_pb(bw))
        total_bytes += bw

    return times, values_pb, total_bytes, bytes_to_pb(total_bytes)

def build_monthly_ticks(all_times, interval=5):
    """
    각 월별로 1일부터 다시 시작:
    2/1, 2/6, 2/11...
    3/1, 3/6, 3/11...
    """
    if not all_times:
        return []

    tick_times = []
    months = sorted(set((dt.year, dt.month) for dt in all_times))

    for year, month in months:
        month_dates = sorted(
            dt for dt in all_times
            if dt.year == year and dt.month == month
        )

        available_days = {dt.day: dt for dt in month_dates}
        last_day = max(available_days.keys())

        day = 1
        while day <= last_day:
            if day in available_days:
                tick_times.append(available_days[day])
            day += interval

        # 마지막 날짜도 표시
        if available_days[last_day] not in tick_times:
            tick_times.append(available_days[last_day])

    return sorted(set(tick_times))

def annotate_peak(ax, times, values, color, label):
    if not times or not values:
        return

    peak_value = max(values)
    peak_index = values.index(peak_value)
    peak_time = times[peak_index]

    ax.scatter(
        [peak_time],
        [peak_value],
        s=140,
        edgecolors="black",
        linewidths=1.2,
        zorder=6
    )

    ax.annotate(
        f"{label} Peak\n{peak_time.month}/{peak_time.day}: {peak_value:.2f} PB",
        xy=(peak_time, peak_value),
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

def plot_comparison(file1, file2):
    service_name = extract_service_name(file1)

    label1 = file_to_label(file1)  # current month
    label2 = file_to_label(file2)  # previous month

    times1, bw1, total1_bytes, total1_pb = load_bandwidth_data(file1)
    times2, bw2, total2_bytes, total2_pb = load_bandwidth_data(file2)

    diff_bytes = total1_bytes - total2_bytes
    diff_pb = bytes_to_pb(abs(diff_bytes))
    pct_change = (diff_bytes / total2_bytes * 100) if total2_bytes else 0

    if diff_bytes >= 0:
        trend_color = "green"
        trend_text = f"Increase: {diff_pb:.2f} PB | Change: +{pct_change:.2f}%"
    else:
        trend_color = "red"
        trend_text = f"Decrease: {diff_pb:.2f} PB | Change: {pct_change:.2f}%"

    fig, ax = plt.subplots(figsize=(16, 9))

    # Bar chart
    bars1 = ax.bar(
        times1,
        bw1,
        width=0.8,
        alpha=0.85,
        label=label1
    )
    bars2 = ax.bar(
        times2,
        bw2,
        width=0.8,
        alpha=0.85,
        label=label2
    )

    color1 = bars1.patches[0].get_facecolor()
    color2 = bars2.patches[0].get_facecolor()

    all_times = sorted(set(times1 + times2))

    # X-axis: each month starts from day 1
    tick_times = build_monthly_ticks(all_times, interval=5)
    ax.set_xticks(tick_times)
    ax.set_xticklabels(
        [f"{dt.month}/{dt.day}" for dt in tick_times],
        rotation=45,
        ha="right",
        fontsize=11
    )

    # Month boundary lines
    month_starts = sorted(
        min(dt for dt in all_times if dt.year == year and dt.month == month)
        for year, month in sorted(set((dt.year, dt.month) for dt in all_times))
    )

    for dt in month_starts:
        ax.axvline(dt, linestyle="--", alpha=0.35, linewidth=1.5)

    # Peak annotations
    annotate_peak(ax, times1, bw1, color1, label1)
    annotate_peak(ax, times2, bw2, color2, label2)

    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.2f}"))

    ax.set_xlabel("Date (UTC)", fontsize=16, fontweight="bold", labelpad=10)
    ax.set_ylabel("Bandwidth (PB)", fontsize=16, fontweight="bold", labelpad=10)

    ax.grid(True, linestyle="--", alpha=0.25)

    # Title
    fig.suptitle(
        f"Bandwidth Comparison ({service_name})",
        fontsize=26,
        fontweight="bold",
        y=0.985
    )

    # Increase / Decrease line
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

    # Text-style legend
    fig.text(
        0.32,
        0.855,
        "■",
        color=color2,
        fontsize=18,
        fontweight="bold",
        ha="right",
        va="center"
    )
    fig.text(
        0.325,
        0.855,
        #f" {label1} (Total: {total1_pb:.2f} PB)",
        f" {label2} (Total: {total2_pb:.2f} PB)",
        color="black",
        fontsize=15,
        ha="left",
        va="center"
    )

    fig.text(
        0.63,
        0.855,
        "■",
        color=color1,
        fontsize=18,
        fontweight="bold",
        ha="right",
        va="center"
    )
    fig.text(
        0.635,
        0.855,
        #f" {label2} (Total: {total2_pb:.2f} PB)",
        f" {label1} (Total: {total1_pb:.2f} PB)",
        color="black",
        fontsize=15,
        ha="left",
        va="center"
    )

    plt.tight_layout(rect=[0.03, 0.06, 0.97, 0.80])
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 bandwidth-sum.py <current_month.json> <previous_month.json>")
    else:
        plot_comparison(sys.argv[1], sys.argv[2])