from pathlib import Path
from typing import Union
from collections.abc import Sequence
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import dates as mdates
from matplotlib.ticker import FixedLocator
from scipy.stats import circmean
import pandas as pd
import re
import warnings

# Shared plot style constants
GRID_STYLE = dict(linestyle="-", color="#E0E0E0", alpha=0.7)
LEGEND_STYLE = dict(frameon=True, edgecolor="k")
FLOOD_COLOR = "b"
EBB_COLOR = "r"
SLACK_COLOR = "#808080"


def flowVisualized(
        mainOutputDir: Union[str, Path],
        DMY: Sequence[str],
        velSigned_depthAvg: np.ndarray,
        velDir_depthAvg: np.ndarray,
        floodSign_depthAvg: np.ndarray,
        ebbSign_depthAvg: np.ndarray,
        slackSign_depthAvg: np.ndarray,
        Eas_depthAvg: np.ndarray,
        Nor_depthAvg: np.ndarray,
        floodVelMag_depthtimeAvg: float | int,
        ebbVelMag_depthtimeAvg: float | int,
        floodMeanDir: float | int,
        ebbMeanDir: float | int,
        siteID: str,
) -> None:
    if not Path(mainOutputDir).is_dir():
        raise FileNotFoundError(
            "The flow visualization function does not receive a valid main output directory."
        )

    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["savefig.dpi"] = 1000

    generate_figure1(
        mainOutputDir,
        DMY,
        floodVelMag_depthtimeAvg,
        ebbVelMag_depthtimeAvg,
        floodMeanDir,
        ebbMeanDir,
        siteID,
    )
    generate_figure2(
        mainOutputDir,
        DMY,
        velSigned_depthAvg,
        floodSign_depthAvg,
        ebbSign_depthAvg,
        slackSign_depthAvg,
        siteID,
    )
    generate_figure3(mainOutputDir, DMY, Eas_depthAvg, Nor_depthAvg, siteID)
    generate_figure4(
        mainOutputDir,
        DMY,
        velSigned_depthAvg,
        floodSign_depthAvg,
        ebbSign_depthAvg,
        slackSign_depthAvg,
        siteID,
    )
    generate_figure5(mainOutputDir, DMY, velSigned_depthAvg, velDir_depthAvg, siteID)
    generate_figure6(
        mainOutputDir,
        DMY,
        velSigned_depthAvg,
        floodSign_depthAvg,
        ebbSign_depthAvg,
        slackSign_depthAvg,
        siteID,
    )


def _dmy_label(DMY: Sequence[str]) -> str:
    """Returns the common '(start to end)' date range label used in figure titles."""
    return f"({DMY[0]} to {DMY[-1]})"


def _apply_time_axis(
        ax: plt.Axes,
        DMY: Sequence[str],
        fmt: str = "%m/%d",
        freq: str = "7D",
) -> None:
    """
    Configures a matplotlib Axes with midnight-aligned x-ticks for time-series plots.
    Shared across generate_figure2, generate_figure3, and generate_figure6.
    Default format omits time-of-day since every tick is midnight-aligned;
    including '%H:%M' just adds redundant width that causes labels to overlap
    when there are many weekly ticks across a multi-month deployment.
    """
    tick_dates = calculate_midnight_ticks(DMY, freq=freq)
    ax.set_xlim(tick_dates[0], tick_dates[-1])
    ax.xaxis.set_major_locator(FixedLocator(mdates.date2num(tick_dates)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
    ax.minorticks_off()


def calculate_midnight_ticks(DMY: Sequence[str], freq: str = "7D") -> pd.DatetimeIndex:
    """
    Generates tick dates fixed at 00:00 (midnight) from a list/numpy array of date strings (DMY).
    Ensures the first tick starts before or at the date start, and the last tick extends past the data end.
    """
    dmy_datetime = pd.to_datetime(DMY)

    start_date = dmy_datetime.min().floor("D")
    end_date = dmy_datetime.max().ceil("D")

    tick_dates = pd.date_range(start=start_date, end=end_date, freq=freq)

    if tick_dates[-1] < end_date:
        next_tick = tick_dates[-1] + pd.Timedelta(freq)
        tick_dates = pd.DatetimeIndex(tick_dates.append(pd.DatetimeIndex([next_tick])))

    return tick_dates


# Figure 1: Summary of Info about Tidal Flow (_FlowSummary.png)
def generate_figure1(
        mainOutputDir: Union[str, Path],
        DMY: Sequence[str],
        floodVelMag_depthtimeAvg: float | int,
        ebbVelMag_depthtimeAvg: float | int,
        floodMeanDir: float | int,
        ebbMeanDir: float | int,
        siteID: str,
) -> None:
    date_label = _dmy_label(DMY)
    fig_title = f"{siteID} {date_label}"
    fig = plt.figure(num=fig_title, figsize=(8,4))  # type: ignore
    #fig = plt.figure(num=fig_title, figsize=(1000.0, 450.0, "px"))  # type: ignore

    # Axis range sized to the data (with headroom) rather than a fixed value --
    # a hardcoded ceiling clips/flattens the bars and polar vectors whenever
    # the site's real current speeds exceed what the old test dataset had.
    mag_max = max(floodVelMag_depthtimeAvg, ebbVelMag_depthtimeAvg)
    axis_max = float(np.ceil(mag_max * 1.2 * 10) / 10)

    # Axis 1: Bar Chart
    ax_bar = fig.add_axes((0.1, 0.15, 0.35, 0.7))
    ax_bar.bar(
        ["Flood", "Ebb"],
        [floodVelMag_depthtimeAvg, ebbVelMag_depthtimeAvg],
        edgecolor="k",
        width=0.6,
    )
    ax_bar.set_ylabel("Average Magnitude (m/s)")
    ax_bar.set_title(fig_title, fontweight="bold", fontsize=11)
    ax_bar.set_ylim(0, axis_max)
    ax_bar.set_axisbelow(True)
    ax_bar.grid(True, **GRID_STYLE)

    # Axis 2: Polar Plot
    ax_polar = fig.add_axes((0.55, 0.1, 0.4, 0.8), polar=True)
    ax_polar.set_theta_zero_location("N")  # type: ignore
    ax_polar.set_theta_direction(-1)  # type: ignore

    floodRad = np.radians(floodMeanDir)
    ebbRad = np.radians(ebbMeanDir)

    ax_polar.plot(
        [0, floodRad],
        [0, floodVelMag_depthtimeAvg],
        linewidth=2,
        color=[0.2, 0.4, 0.9],
        label="Flood",
    )
    ax_polar.plot(
        [0, ebbRad],
        [0, ebbVelMag_depthtimeAvg],
        linewidth=2,
        color=[0.9, 0.2, 0.2],
        label="Ebb",
    )

    ax_polar.scatter(
        floodRad, floodVelMag_depthtimeAvg, s=70, color=[0.2, 0.4, 0.9], zorder=3
    )
    ax_polar.scatter(ebbRad, ebbVelMag_depthtimeAvg, s=70, color=[0.9, 0.2, 0.2])

    ax_polar.set_xticks(np.radians(np.arange(0, 360, 45)))
    ax_polar.set_xticklabels(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])

    ax_polar.set_rlim(0, axis_max)  # type: ignore
    ax_polar.set_rticks(np.round(np.linspace(0, axis_max, 4)[1:], 2))  # type: ignore
    ax_polar.set_rlabel_position(
        157.5)  # type: ignore -- quiet zone: avoids the N/E/S/W compass labels and the flood/ebb direction lines
    ax_polar.grid(True, **GRID_STYLE)

    # Offset scaled to axis_max (not a fixed value) so the direction labels
    # stay clear of the scatter markers regardless of how large the radial
    # axis is -- a fixed offset sized for the old 0.6 m/s scale left the text
    # sitting behind the marker once real current speeds pushed axis_max higher.
    label_offset = axis_max * 0.16
    ax_polar.text(
        floodRad - 0.19,
        floodVelMag_depthtimeAvg - label_offset,
        f"{floodMeanDir:.1f}\u00b0 T",
        color=[0.2, 0.4, 0.9],
        weight="bold",
        ha="right",
    )
    ax_polar.text(
        ebbRad + 0.06,
        ebbVelMag_depthtimeAvg - label_offset,
        f"{ebbMeanDir:.1f}\u00b0 T",
        color=[0.9, 0.2, 0.2],
        weight="bold",
        ha="left",
    )
    ax_polar.set_title(
        f"{siteID} {date_label}:\nDominant Current Directions (True North)",
        pad=20,
        fontweight="bold",
    )
    ax_polar.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.07),
        ncol=1,
        **LEGEND_STYLE,
    )

    plt.savefig(Path(mainOutputDir) / "_FlowSummary.png", bbox_inches="tight")
    plt.close(fig)
    print("fig1 (_FlowSummary.png) generated.")


# Figure 2: Time Series (_TimeSeries.png)
def generate_figure2(
        mainOutputDir: Union[str, Path],
        DMY: Sequence[str],
        velSigned_depthAvg: np.ndarray,
        floodSign_depthAvg: np.ndarray,
        ebbSign_depthAvg: np.ndarray,
        slackSign_depthAvg: np.ndarray,
        siteID: str,
) -> None:
    dmy_arr = pd.to_datetime(np.array(DMY)).to_numpy()
    vel_arr = np.array(velSigned_depthAvg)

    fig_title = (
        f"{siteID} {_dmy_label(DMY)}:\nTidal Flow Analysis: Flood (+) and Ebb (-) Tides"
    )
    fig = plt.figure(num=fig_title, figsize=(9,4))  # type: ignore
    #fig = plt.figure(num=fig_title, figsize=(1200.0, 600.0, "px"))  # type: ignore

    ax = fig.add_subplot(111)

    ax.plot(dmy_arr, vel_arr, "k", linewidth=0.5, label="Velocity")
    ax.plot(
        dmy_arr[floodSign_depthAvg],
        vel_arr[floodSign_depthAvg],
        "b.",
        markersize=4,
        label="Flood Tide",
    )
    ax.plot(
        dmy_arr[ebbSign_depthAvg],
        vel_arr[ebbSign_depthAvg],
        "r.",
        markersize=4,
        label="Ebb Tide",
    )
    ax.plot(
        dmy_arr[slackSign_depthAvg],
        vel_arr[slackSign_depthAvg],
        ".",
        color=SLACK_COLOR,
        markersize=4,
        label="Slack",
    )

    ax.set_xlabel("Time")
    ax.set_ylabel("Velocity (m/s)")
    ax.set_title(fig_title, pad=15, fontweight="bold")

    _apply_time_axis(ax, DMY)
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")

    vel_max = float(np.nanmax(np.abs(vel_arr)) * 1.1)
    ax.set_ylim(-vel_max, vel_max)

    ax.legend(loc="upper right", **LEGEND_STYLE)
    ax.grid(True, **GRID_STYLE)

    plt.savefig(Path(mainOutputDir) / "_TimeSeries.png", bbox_inches="tight")
    plt.close(fig)
    print("fig2 (_TimeSeries.png) generated.")


# Figure 3: Velocity Components (_Components.png)
def generate_figure3(
        mainOutputDir: Union[str, Path],
        DMY: Sequence[str],
        Eas_depthAvg: np.ndarray,
        Nor_depthAvg: np.ndarray,
        siteID: str,
) -> None:
    dmy_arr = pd.to_datetime(np.array(DMY)).to_numpy()
    east_arr = np.array(Eas_depthAvg)
    north_arr = np.array(Nor_depthAvg)

    fig_title = f"{siteID} {_dmy_label(DMY)}: Velocity Components"
    fig = plt.figure(num=fig_title, figsize=(6,2))
    #fig = plt.figure(num=fig_title, figsize=(1200.0, 400.0, "px"))  # type: ignore

    ax = fig.add_subplot(111)

    ax.plot(dmy_arr, east_arr, "r-", linewidth=1.2, label="Eastward")
    ax.plot(dmy_arr, north_arr, "g-", linewidth=1.2, label="Northward")

    ax.set_xlabel("Time")
    ax.set_ylabel("Velocity (m/s)")
    ax.set_title(fig_title, pad=15, fontweight="bold")

    _apply_time_axis(ax, DMY)

    ax.legend(loc="upper right", **LEGEND_STYLE)
    ax.grid(True, **GRID_STYLE)

    plt.savefig(Path(mainOutputDir) / "_Components.png", bbox_inches="tight")
    plt.close(fig)
    print("fig3 (_Components.png) generated.")


# Figure 4: Statistical Analysis (_Statistics.png)
def generate_figure4(
        mainOutputDir: Union[str, Path],
        DMY: Sequence[str],
        velSigned_depthAvg: np.ndarray,
        floodSign_depthAvg: np.ndarray,
        ebbSign_depthAvg: np.ndarray,
        slackSign_depthAvg: np.ndarray,
        siteID: str,
) -> None:
    vel_arr = np.array(velSigned_depthAvg)
    flood_stats = vel_arr[floodSign_depthAvg]
    ebb_stats = vel_arr[ebbSign_depthAvg]
    slack_stats = vel_arr[slackSign_depthAvg]

    date_label = _dmy_label(DMY)
    fig_title = f"{siteID} {date_label}: Statistical Analysis"
    fig = plt.figure(num=fig_title, figsize=(4.5, 3.5))  # type: ignore
    #fig = plt.figure(num=fig_title, figsize=(800.0, 600.0, "px"))  # type: ignore

    # Axis 1: Velocity Distribution
    ax1 = fig.add_subplot(211)
    ax1.set_axisbelow(True)
    ax1.hist(
        flood_stats,
        bins=20,
        color=FLOOD_COLOR,
        alpha=0.7,
        label="Flood Tide",
        edgecolor="k",
    )
    ax1.hist(
        ebb_stats, bins=20, color=EBB_COLOR, alpha=0.7, label="Ebb Tide", edgecolor="k"
    )
    ax1.hist(
        slack_stats,
        bins=20,
        color=SLACK_COLOR,
        alpha=0.7,
        label="Slack",
        edgecolor="k",
    )

    vel_extent = float(np.nanmax(np.abs(vel_arr)) * 1.1)
    ax1.set_xlim(-vel_extent, vel_extent)

    ax1.set_title(
        f"{siteID} {date_label}: Velocity Distribution by Tidal Phase",
        fontweight="bold",
    )
    ax1.set_xlabel("Velocity (m/s)")
    ax1.set_ylabel("Frequency")
    ax1.legend(loc="best", **LEGEND_STYLE)
    ax1.grid(True, **GRID_STYLE)

    # Axis 2: Flood/Ebb Box Plots
    ax2 = fig.add_subplot(212)
    ax2.set_axisbelow(True)

    flood_magnitudes = np.abs(flood_stats)
    ebb_magnitudes = np.abs(ebb_stats)
    slack_magnitudes = np.abs(slack_stats)
    box_data = [flood_magnitudes, ebb_magnitudes, slack_magnitudes]

    ax2.boxplot(
        box_data,
        whis=1.5,
        boxprops=dict(linestyle="-", linewidth=0.8, color=FLOOD_COLOR),
        whiskerprops=dict(linestyle="--", linewidth=0.8, color="k"),
        capprops=dict(linestyle="-", linewidth=0.8, color="k"),
        medianprops=dict(linestyle="-", linewidth=0.8, color=EBB_COLOR),
        widths=0.25,
    )

    ax2.set_xticks([1, 2, 3])
    ax2.set_xticklabels(["Flood", "Ebb", "Slack"])

    ax2.set_title(
        f"{siteID} {date_label}: Statistical Comparison of Flood and Ebb Magnitudes", fontweight="bold"
    )
    ax2.set_ylabel("Velocity Magnitude (m/s)")
    ax2.grid(True, **GRID_STYLE)

    plt.tight_layout()

    plt.savefig(Path(mainOutputDir) / "_Statistics.png", bbox_inches="tight")
    plt.close(fig)
    print("fig4 (_Statistics.png) generated.")


# Figure 5: Current Rose (_CurrentRose.png)
def generate_figure5(
        mainOutputDir: Union[str, Path],
        DMY: Sequence[str],
        velSigned_depthAvg: np.ndarray,
        velDir_depthAvg: np.ndarray,
        siteID: str,
) -> None:
    directions_rad = np.radians(np.array(velDir_depthAvg))
    magnitudes = np.abs(
        np.array(velSigned_depthAvg))  # Makes sure the NE graph is present. Bug from original matlab code.

    n_dir_bins = 36
    n_speed_bands = 100  # Sets plot gradient density (original matlab code had 4)

    edges = np.linspace(0, 2 * np.pi, n_dir_bins + 1)
    dir_centers_rad = 0.5 * (edges[:-1] + edges[1:])
    bar_width = 2 * np.pi / n_dir_bins

    speed_max = magnitudes.max() * 1.1
    magnitude_edges = np.linspace(0, speed_max, n_speed_bands + 1)

    cmap = plt.colormaps["jet"]
    colors = cmap(np.linspace(0, 1, n_speed_bands))

    counts, _, _ = np.histogram2d(
        np.degrees(directions_rad), magnitudes,
        bins=[np.degrees(edges), magnitude_edges]
    )
    counts = counts.T

    date_label = _dmy_label(DMY)
    fig_title = f"{siteID} {date_label}: Tidal Current Rose"
    fig = plt.figure(num=fig_title, figsize=(7, 6))  # type: ignore
    #fig = plt.figure(num=fig_title, figsize=(700.0, 600.0, "px"))  # type: ignore

    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_zero_location("N")  # type: ignore
    ax.set_theta_direction(-1)  # type: ignore
    ax.set_axisbelow(True)

    bottoms_matrix = np.vstack((np.zeros(n_dir_bins), np.cumsum(counts, axis=0)[:-1]))

    for i in range(n_speed_bands):
        ax.bar(
            dir_centers_rad,
            counts[i],
            width=bar_width,
            bottom=bottoms_matrix[i],
            color=colors[i],
            edgecolor="none",
            align="center",
            antialiased=False,
            zorder=3,
        )

    ax.set_xticks(np.radians(np.arange(0, 360, 45)))
    ax.set_xticklabels(
        ["N", "NE", "E", "SE", "S", "SW", "W", "NW"], fontweight="bold", color="#333333"
    )
    ax.tick_params(axis="x", pad=10)

    ax.set_rlabel_position(22.5)
    ax.tick_params(axis="y", labelsize=8)

    ax.grid(True, **GRID_STYLE, zorder=1)

    ax.set_title(
        f"{siteID} {date_label}: Current Rose (True North)",
        pad=20,
        fontweight="bold",
        color="#222222",
    )

    sm = plt.cm.ScalarMappable(cmap="jet", norm=plt.Normalize(vmin=0, vmax=speed_max))
    sm.set_array([])
    c = fig.colorbar(sm, ax=ax, pad=0.1, shrink=0.7)

    cbar_tick_values = np.linspace(0, speed_max, 5)
    c.set_ticks(cbar_tick_values)
    c.set_ticklabels([f"{v:.1f}" for v in cbar_tick_values])
    c.set_label("Current Speed (m/s)")
    c.outline.set_visible(False)  # type: ignore

    plt.savefig(Path(mainOutputDir) / "_CurrentRose.png", bbox_inches="tight")
    plt.close(fig)
    print("fig5 (_CurrentRose.png) generated.")


# Figure 6: Tidal Cycles (_TidalCycles.png)
def generate_figure6(
        mainOutputDir: Union[str, Path],
        DMY: Sequence[str],
        velSigned_depthAvg: np.ndarray,
        floodSign_depthAvg: np.ndarray,
        ebbSign_depthAvg: np.ndarray,
        slackSign_depthAvg: np.ndarray,
        siteID: str,
) -> None:
    dmy_arr = pd.to_datetime(np.array(DMY)).to_numpy()
    vel_arr = np.array(velSigned_depthAvg)

    fig_title = f"{siteID} {_dmy_label(DMY)}: Tidal Cycles"

    fig = plt.figure(num=fig_title, figsize=(4.5, 3.5))  # type: ignore
    #fig = plt.figure(num=fig_title, figsize=(1200.0, 700.0, "px"))  # type: ignore

    ax1 = fig.add_subplot(211)
    ax1.set_axisbelow(True)
    ax1.plot(dmy_arr, vel_arr, "k-", linewidth=0.5, label="Velocity")
    ax1.plot(
        dmy_arr[floodSign_depthAvg],
        vel_arr[floodSign_depthAvg],
        "b.",
        markersize=4,
        label="Flood",
    )
    ax1.plot(
        dmy_arr[ebbSign_depthAvg],
        vel_arr[ebbSign_depthAvg],
        "r.",
        markersize=4,
        label="Ebb",
    )
    ax1.plot(
        dmy_arr[slackSign_depthAvg],
        vel_arr[slackSign_depthAvg],
        ".",
        color=SLACK_COLOR,
        markersize=4,
        label="Slack",
    )
    ax1.axhline(0, color="k", linestyle="--", linewidth=0.8)

    _apply_time_axis(ax1, DMY, fmt="%m/%d")

    ax1.set_ylabel("Signed Velocity (m/s)")
    ax1.set_title(fig_title, fontweight="bold")
    ax1.legend(loc="upper right", **LEGEND_STYLE)
    ax1.grid(True, **GRID_STYLE)

    ax2 = fig.add_subplot(212)
    ax2.set_axisbelow(True)

    vel_max = np.abs(vel_arr).max()
    edges = np.linspace(-vel_max, vel_max, 30)

    ax2.hist(
        vel_arr[floodSign_depthAvg],
        bins=edges,
        color=FLOOD_COLOR,
        alpha=0.7,
        label="Flood",
        edgecolor="k",
        linewidth=0.4,
    )
    ax2.hist(
        vel_arr[ebbSign_depthAvg],
        bins=edges,
        color=EBB_COLOR,
        alpha=0.7,
        label="Ebb",
        edgecolor="k",
        linewidth=0.4,
    )
    ax2.hist(
        vel_arr[slackSign_depthAvg],
        bins=edges,
        color=SLACK_COLOR,
        alpha=0.7,
        label="Slack",
        edgecolor="k",
        linewidth=0.4,
    )

    ax2.set_xlabel("Signed Velocity (m/s)")
    ax2.set_ylabel("Frequency")
    ax2.legend(loc="best", **LEGEND_STYLE)
    ax2.grid(True, **GRID_STYLE)

    plt.tight_layout()

    plt.savefig(Path(mainOutputDir) / "_TidalCycles.png", bbox_inches="tight")
    plt.close(fig)
    print("fig6 (_TidalCycles.png) generated.")


def load_depthAvg_csv(csv_path: Union[str, Path]) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["Date & Time.2"] = pd.to_datetime(df["Date & Time.2"], errors="coerce")

    bad_rows = df["Date & Time.2"].isna()
    if bad_rows.any():
        print(
            f"Warning: dropping {bad_rows.sum()} row(s) with unparseable "
            f"datetime in {csv_path} (e.g. stray text or blank rows)."
        )
        df = df.loc[~bad_rows].reset_index(drop=True)

    df["phase"] = df["phase"].str.strip().str.lower()
    return df

def inputID():
    user_decision = input('Do you want to continue by defining the site ID? (Y/N): ')

    if user_decision == 'N':
        print('Exiting from FolderRead.'
              'recommendation to revise data in files.')
        return

    siteID = input('\n Please define the site ID to appear in plots (e.g. LIS1001): ')
    print('Continuing with user')
    return siteID

def extractSiteID(filenames):
    extraced_IDs = []
    for name in filenames:
        match = re.match(r'^([a-zA-Z]+)(\d+)', name)
        if match:
            extraced_IDs.append(match.group(1) + match.group(2))
        # non-matching files (e.g. depthAvg_ADCPdata.csv) are skipped,
        # not counted as a conflicting ID

    if not extraced_IDs:
        warnings.warn('No site-tagged CSV filenames found.')
        print('User-defined ID requested for plotting: ')
        return inputID()

    unique_ids = set(extraced_IDs)
    if len(unique_ids) > 1:
        warnings.warn(f'There is a mismatch of site ID within provided data: {unique_ids}')
        print('User-defined ID requested for plotting: ')
        return inputID()

    return extraced_IDs[0]

if __name__ == "__main__":
    # This part is hardcoded for now. This may have to be changed for further implementation.
    siteID = "LIS1016"

    output_directory = "./outputs"
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    mainOutputDir=output_directory
    if not Path(mainOutputDir).is_dir():
        raise FileNotFoundError("The flow visualization function does not receive a valid main output directory.")
    
    csv_file_path = Path(output_directory) / "depthAvg_ADCPdata_labeled.csv"
    #csv_file_path = Path(__file__).resolve().parent.parent / "depthAvg_ADCPdata_labeled.csv"
    # output_directory = "./test_output"
    Path(output_directory).mkdir(parents=True, exist_ok=True)

    print(f"Loading data from {csv_file_path}...")

    df = load_depthAvg_csv(csv_file_path)

    DMY = df["Date & Time.2"].dt.strftime("%m/%d/%Y %H:%M").to_numpy()

    Eas_depthAvg = df["Eas"].to_numpy()
    Nor_depthAvg = df["Nor"].to_numpy()
    velDir_depthAvg = df["Dir"].to_numpy()

    velSigned_depthAvg = df["u_along_overall"].to_numpy()

    floodSign_depthAvg = (df["phase"] == "flood").to_numpy()
    ebbSign_depthAvg = (df["phase"] == "ebb").to_numpy()
    slackSign_depthAvg = (df["phase"] == "slack").to_numpy()

    floodVelMag_depthtimeAvg = float(np.nanmean(df.loc[floodSign_depthAvg, "Mag"]))
    ebbVelMag_depthtimeAvg = float(np.nanmean(df.loc[ebbSign_depthAvg, "Mag"]))

    floodMeanDir = float(
        circmean(df.loc[floodSign_depthAvg, "Dir"], high=360, low=0)
    )
    ebbMeanDir = float(circmean(df.loc[ebbSign_depthAvg, "Dir"], high=360, low=0))

    print(f"Data from {csv_file_path} loaded successfully.\n")

    flowVisualized(
        mainOutputDir=output_directory,
        DMY=DMY,
        velSigned_depthAvg=velSigned_depthAvg,
        velDir_depthAvg=velDir_depthAvg,
        floodSign_depthAvg=floodSign_depthAvg,
        ebbSign_depthAvg=ebbSign_depthAvg,
        slackSign_depthAvg=slackSign_depthAvg,
        Eas_depthAvg=Eas_depthAvg,
        Nor_depthAvg=Nor_depthAvg,
        floodVelMag_depthtimeAvg=floodVelMag_depthtimeAvg,
        ebbVelMag_depthtimeAvg=ebbVelMag_depthtimeAvg,
        floodMeanDir=floodMeanDir,
        ebbMeanDir=ebbMeanDir,
        siteID=siteID,
    )
