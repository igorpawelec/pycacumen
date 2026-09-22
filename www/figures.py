"""The README figures, generated from test_data so they can be remade.

    python www/figures.py            # from the repository root; no install needed

Writes www/pipeline.png (CHM, tree tops, crowns) and www/variance_thresh.png
(the same scene at three settings of the main lever, with the tops the
growing absorbed drawn hollow) and prints the numbers the README captions
quote. One tile, chm_150_2014.tif: a dense mature stand where over-detected
tops are plentiful, so the merging has something to do.
"""
import os
import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from pycacumen import CrownDelineator, detect_tops, merge_tops, screen_tops  # noqa: E402

TILE = os.path.join(ROOT, "test_data", "chm_150_2014.tif")
# One blue ramp for magnitude, one orange for the crown outlines, ink for tops.
BLUES = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
         "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
CMAP = LinearSegmentedColormap.from_list("height", BLUES)
ORANGE, INK, MUTED = "#eb6834", "#1f1f1f", "#6b6b6b"
HMIN, WS_TOPS, MERGE, SCREEN = 7.0, 5, 5.0, 10.0


def outlines(crowns):
    """Crown boundaries as pixel-space polygons (exteriors and holes)."""
    from rasterio.features import shapes
    polys = []
    for geom, val in shapes(crowns.astype(np.int32), mask=crowns > 0):
        for ring in geom["coordinates"]:
            polys.append(np.asarray(ring))
    return polys


def panel(ax, chm, vmax, label=None):
    ax.imshow(chm, cmap=CMAP, vmin=0, vmax=vmax, interpolation="nearest")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor("#d9d9d9")
    if label:
        ax.set_xlabel(label, fontsize=9.5, color=INK, labelpad=7)


def draw_crowns(ax, crowns):
    for ring in outlines(crowns):
        ax.add_patch(Polygon(ring - 0.5, closed=True, fill=False, ec=ORANGE, lw=0.9))


def draw_tops(ax, tops, size=16, filled=True):
    if len(tops) == 0:
        return
    ax.scatter(tops[:, 1], tops[:, 0], s=size, c=INK if filled else "none",
               edgecolors="white" if filled else INK, linewidths=0.8 if filled else 1.1, zorder=3)


def absorbed_mask(crowns, tops):
    """True for a top whose crown id (index + 1) no longer exists: it was merged into a neighbour."""
    present = np.zeros(len(tops) + 1, bool)
    present[np.unique(crowns[crowns > 0])] = True
    gone = ~present[1:]
    for i in np.nonzero(gone)[0]:            # every absorbed top sits inside somebody else's crown
        r, c = int(round(tops[i, 0])), int(round(tops[i, 1]))
        assert crowns[r, c] > 0 and crowns[r, c] != i + 1, (i, crowns[r, c])
    return gone


cd = CrownDelineator.from_file(TILE, quiet=True)
chm = cd.chm.copy()
chm[~np.isfinite(chm)] = 0.0
vmax = float(np.nanpercentile(chm, 99.5))
cd.smooth(ws=3)
raw = detect_tops(cd.smoothed, hmin=HMIN, ws=WS_TOPS)
kept = screen_tops(cd.smoothed, merge_tops(raw, distance=MERGE), hmin=SCREEN)
cd.tops = kept
runs = {}
for vt in (2.0, 8.0, 20.0):
    cd.delineate(variance_thresh=vt)
    gone = absorbed_mask(cd.crowns, kept)
    runs[vt] = (cd.crowns.copy(), int(len(np.unique(cd.crowns[cd.crowns > 0]))), int(gone.sum()), gone)
n_raw, n_kept = len(raw), len(kept)
print(f"tile {os.path.basename(TILE)}: {chm.shape[1]} x {chm.shape[0]} px at 0.5 m, heights to {np.nanmax(chm):.1f} m")
print(f"tops: {n_raw} local maxima (hmin {HMIN:g} m, window {WS_TOPS} px) -> {n_kept} after merging within "
      f"{MERGE:g} px and screening below {SCREEN:g} m")
for vt, (_, n, a, _) in runs.items():
    print(f"variance_thresh {vt:>4g}: {n} crowns from {n_kept} tops, {a} tops absorbed")

# ---- figure 1: the pipeline ----------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(11.4, 4.1))
panel(axes[0], chm, vmax, "canopy height model, 0.5 m")
panel(axes[1], cd.smoothed, vmax, f"{n_raw} local maxima, {n_kept} kept as tree tops")
draw_tops(axes[1], raw, size=10, filled=False)
draw_tops(axes[1], kept, size=16)
crowns2, n2, _, _ = runs[2.0]
panel(axes[2], cd.smoothed, vmax, f"{n2} crowns")
draw_crowns(axes[2], crowns2)
draw_tops(axes[2], kept, size=9)
fig.subplots_adjust(wspace=0.05)
sm = plt.cm.ScalarMappable(cmap=CMAP, norm=plt.Normalize(0, vmax))
cb = fig.colorbar(sm, ax=axes, fraction=0.018, pad=0.012, shrink=0.82)
cb.set_label("height [m]", fontsize=9, color=MUTED)
cb.ax.tick_params(labelsize=8, colors=MUTED)
cb.outline.set_edgecolor("#d9d9d9")
fig.savefig(os.path.join(HERE, "pipeline.png"), dpi=160, bbox_inches="tight", facecolor="white")

# ---- figure 2: the main lever --------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(11.4, 4.1))
for ax, (vt, (crowns, n, a, gone)) in zip(axes, runs.items()):
    panel(ax, cd.smoothed, vmax, f"variance_thresh = {vt:g}\n{n} crowns, {a} top{'s' if a != 1 else ''} absorbed")
    draw_crowns(ax, crowns)
    draw_tops(ax, kept[~gone], size=8)
    draw_tops(ax, kept[gone], size=30, filled=False)
fig.subplots_adjust(wspace=0.05)
fig.savefig(os.path.join(HERE, "variance_thresh.png"), dpi=160, bbox_inches="tight", facecolor="white")
print("written: www/pipeline.png, www/variance_thresh.png")
