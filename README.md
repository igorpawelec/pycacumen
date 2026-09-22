# pycacumen

<img src="https://raw.githubusercontent.com/igorpawelec/pycacumen/main/www/pycacumen.png" alt="pycacumen logo" align="right" width="200"/>

[![tests](https://github.com/igorpawelec/pycacumen/actions/workflows/tests.yml/badge.svg)](https://github.com/igorpawelec/pycacumen/actions/workflows/tests.yml)
[![Release](https://img.shields.io/github/v/release/igorpawelec/pycacumen)](https://github.com/igorpawelec/pycacumen/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org)

**Individual tree crown delineation from canopy height models, by Hierarchical Region Growing.**

A canopy height model goes in; a crown per tree comes out, as a label raster and as polygons. Pure Python + Numba, no compiled extensions, no external binaries.

> **R users:** the same algorithm lives in [rcacumen](https://github.com/igorpawelec/rcacumen). The two are separate packages by design — installation, tooling and idioms differ too much to share a repository — and are validated against each other: exactly on the shared synthetic suite, and to within 0.25 % of watershed pixels on real canopy height models, where the two break plateau ties differently.

## The problem it solves

Every crown delineation that starts from a canopy height model meets the same obstacle: **tree tops are over-detected**. The upper surface of a broad crown is ragged, so a local-maximum detector finds several peaks on it. The usual remedy is to smooth harder or to raise the detection threshold, and both trade one error for another: the surplus peaks disappear together with the small, suppressed trees that were real.

pycacumen does not try to get the tops right first. It accepts the surplus and corrects it afterwards, in the growing itself:

1. **Watershed.** Every tree top seeds a marker-based watershed on the inverted CHM, so there is exactly one region per top — the regions *are* the detected trees.
2. **Region adjacency graph.** Neighbouring regions are joined by a weighted edge, *w(a,b) = α·|Δμ| + β·|Δσ| + γ/(border+1)*, and the region statistics come from the same single pixel pass.
3. **Growing.** Each tree grows greedily, absorbing neighbours while the combined height variance stays under a threshold. When two trees absorb each other, they were one crown — this is where over-detection is undone.
4. **Arbitration.** Growing runs independently per seed, so two crowns can claim the same region. The claim is settled on the data — the taller tree, the nearer tree, or the better height match — never on iteration order, so the result does not depend on how the tops were sorted.

<img src="https://raw.githubusercontent.com/igorpawelec/pycacumen/main/www/pipeline.png" alt="A 0.5 m canopy height model of a circular sample plot; the same tile with 253 local maxima of which 213 are kept as tree tops; and the 212 crowns delineated from them, drawn as outlines over the height model" width="100%"/>

*A 100 × 100 m tile of a 0.5 m canopy height model (`test_data/chm_150_2014.tif`, a mature stand on a circular sample plot). Left: the input. Middle: 253 local maxima after median smoothing (`hmin` 7 m, 5 px window), of which 213 survive merging within 5 px and screening below 10 m — the filled markers. Right: the 212 crowns grown from them at the default `variance_thresh` of 2. Made by `www/figures.py`.*

## The one parameter that matters

`variance_thresh` is the height variance (σ², in m²) a single crown may contain. It sets how readily a tree absorbs its neighbours, and therefore how many of the surplus tops are merged back. Everything else has a sensible default; this one you choose per stand.

<img src="https://raw.githubusercontent.com/igorpawelec/pycacumen/main/www/variance_thresh.png" alt="The same tile delineated at variance_thresh 2, 8 and 20: 212, 203 and 123 crowns; the tree tops absorbed into a neighbouring crown are drawn as hollow rings and cluster where crowns merged" width="100%"/>

*The same 213 tree tops grown at `variance_thresh` 2, 8 and 20. Filled markers are tops that ended up as a crown of their own; hollow rings are tops absorbed into a neighbour — 1, 10 and 90 of them. At 2 almost nothing merges and every peak on a broad crown stays a separate tree; at 20 the merging reaches across real crown boundaries in the dense south-east of the plot. The right value lies where the absorbed tops are the ragged-surface duplicates and not the suppressed neighbours, which is a judgement made by looking, and the point of drawing them.*

Two further controls shape the outcome:

- **`conflict_rule`** decides who gets contested canopy: the taller tree (`'height'`, the default — dominant trees overtop their neighbours), the nearer seed (`'distance'`, classic ITC behaviour, splits rather than merges) or the better height match (`'similarity'`).
- **`protect_seeds=True`** switches merging off entirely: every top keeps its crown. Use it when the tops are trusted, for instance field-measured stem positions.

The number of regions claimed by more than one crown is reported after every run (`grower.n_contested`); it grows with the threshold and is the quickest sign that a setting is too loose.

## When to use it, and when not

Use pycacumen when you have a canopy height model — from ALS, from photogrammetric point clouds, at any resolution around 0.25–1 m — and want one crown per tree with a defensible answer to over-detection. Bring your own tree tops if you have better ones; the growing works from any set of seeds.

Do not reach for it when you need Dalponte & Coomes delineation, or want to work on the point cloud directly: [PyCrown](https://github.com/manaakiwhenua/pycrown), [lidR](https://github.com/r-lidar/lidR) and [itcSegment](https://cran.r-project.org/package=itcSegment) do that well, and pycacumen deliberately does not duplicate them.

pycacumen began as a fork of PyCrown (Zörner et al. 2018) and keeps its pipeline shape — smooth the CHM, find tree tops as local maxima, delineate crowns — but hierarchical region growing is the only delineation here.

| | PyCrown | pycacumen |
|---|---|---|
| Delineation | Dalponte & Coomes | Hierarchical Region Growing |
| Over-detected tops | filtered out beforehand | merged by the growing |
| Contested canopy | n/a | arbitrated explicitly, reproducibly |
| Point cloud I/O | yes (laspy) | no — CHM raster in, crowns out |

### The package family

pycacumen is one step of a longer chain; the other steps are separate packages, each with a Python and an R twin.

| Step | Python | R |
|---|---|---|
| Colour-space conversion of orthophotos | [pygeopalette](https://github.com/igorpawelec/pygeopalette) | [rgeopalette](https://github.com/igorpawelec/rgeopalette) |
| Adaptive superpixels and seeded growing on orthophotos | [pygeoadaptels](https://github.com/igorpawelec/pygeoadaptels) | [rgeoadaptels](https://github.com/igorpawelec/rgeoadaptels) |
| Crowns from a canopy height model | **pycacumen** | [rcacumen](https://github.com/igorpawelec/rcacumen) |
| Standing dead trees on orthophotos | [pygeosnag](https://github.com/igorpawelec/pygeosnag) | — |
| The same, inside QGIS | [qgis-geoadaptels-geopalette](https://github.com/igorpawelec/qgis-geoadaptels-geopalette), [qgis-geosnag](https://github.com/igorpawelec/qgis-geosnag) | |
| Polish national geodata (GUGiK, BDL) | — | [rgeopl](https://github.com/igorpawelec/rgeopl) |

## Installation

Native dependencies come from conda; pip then installs the package without touching them.

```bash
conda install -c conda-forge numpy numba scipy scikit-image rasterio fiona
pip install --no-deps git+https://github.com/igorpawelec/pycacumen.git
```

The algorithm itself needs only numpy, numba, scipy and scikit-image. `rasterio` and `fiona` are used solely for reading and writing files — the array API works without them.

## Quick start

```python
from pycacumen import CrownDelineator

cd = CrownDelineator.from_file("chm.tif")
cd.smooth(ws=3).detect(hmin=7, ws=5).merge(5.0).screen(10.0)
crowns = cd.delineate(variance_thresh=2.0)

cd.to_raster("crowns.tif")
cd.to_vector("out/", name="crowns")
```

One call, if you do not need the intermediate state:

```python
from pycacumen import delineate_crowns

crowns, tops = delineate_crowns("chm.tif", hmin=7, merge_distance=5.0,
                                variance_thresh=2.0)
```

From the command line:

```bash
pycacumen -i chm.tif -o crowns.tif --hmin 7 --variance-thresh 2.0
pycacumen -i chm.tif -o crowns.tif --vector out/ --merge-distance 5 --screen-hmin 10
python -m pycacumen --help
```

### Arrays, without touching the disk

Every stage is a plain function. Nothing in the algorithm needs a file path:

```python
import numpy as np
from pycacumen import smooth_chm, detect_tops, as_pixels, HierarchicalRegionGrower

chm = np.load("chm.npy")
smoothed = smooth_chm(chm, ws=3, method="median")
tops = detect_tops(smoothed, hmin=7, ws=5)          # (n, 2) subpixel row/col

grower = HierarchicalRegionGrower(smoothed)
crowns = grower.run_all(as_pixels(tops), variance_thresh=2.0)
print(f"{grower.n_contested} regions were claimed by more than one crown")
```

### Large rasters

Read a window; the geotransform is shifted to match, so exported crowns stay georeferenced.

```python
# 2000 x 2000 px starting at col=1000, row=500
cd = CrownDelineator.from_file("big_chm.tif", window=(1000, 500, 2000, 2000))
```

## Reference

### Parameters

**Smoothing** — `smooth_chm(chm, ws, method)`

| Parameter | Default | Description |
|---|---|---|
| `ws` | 3 | Window size (px). Larger = fewer false tops, but merges close crowns |
| `method` | `'median'` | `median`, `mean`, `gaussian`, `maximum`. Median keeps crown edges sharp |

**Tree tops** — `detect_tops`, `merge_tops`, `screen_tops`

| Parameter | Default | Description |
|---|---|---|
| `hmin` | 2.0 | Minimum height (m) for a pixel to be a candidate |
| `ws` | 3 | Local-maximum window (px) = minimum spacing between tops |
| `distance` | 5.0 | Merge radius (px). Grouping is transitive — keep below crown diameter |

**Growing** — `delineate` / `run_all`

| Parameter | Default | Description |
|---|---|---|
| `variance_thresh` | 2.0 | Max height variance (σ²) within a crown. **The main lever** |
| `mask_thresh` | 0.0 | Minimum CHM height treated as canopy (m) |
| `morpho_radius` | 0 | Disk radius for opening/closing the mask. 0 = off |
| `alpha`, `beta`, `gamma` | 1.0, 0.5, 0.1 | Edge weights: mean diff, σ diff, inverse border length |
| `anneal_lambda` | 1.0 | Per-iteration tightening of the threshold. 1.0 = constant |
| `max_iters` | `None` | Cap on grow iterations per seed. `None` grows to natural termination |
| `conflict_rule` | `'height'` | Who wins contested canopy — see above |
| `protect_seeds` | `False` | If True, no tree is ever absorbed; every top yields a crown |
| `retry_rejected` | `False` | Reconsider regions rejected earlier in the same grow |
| `n_jobs` | 1 | Parallel processes. -1 = all cores |

Ties in the conflict rules resolve to the lower crown id, so output is fully reproducible.

<details>
<summary><b>Notes on behaviour</b></summary>

**The crown count can be lower than the tree-top count.** That is the point: merged trees leave gaps in the id sequence. If you need one crown per top, use `protect_seeds=True`.

**`retry_rejected` only bites in the middle.** A rejected region can become admissible later, because absorbing a large homogeneous neighbour can *lower* a crown's variance. On a 1105-tree synthetic scene this changed nothing at `variance_thresh` 2 or 8 (rejections are final anyway) and nothing at 120 (everything merges regardless), but changed ~17% of the raster at 20. The direction is not predictable — the crown count moved both up and down.

**`n_jobs > 1` is worth it only on large scenes.** The graph is shared per worker rather than per task, but process start-up still costs ~0.1 s each, and growing is cheap per tree (~0.4 s for 1150 trees). Results are identical to sequential either way.

</details>

<details>
<summary><b>Performance</b></summary>

Numba compiles the one place that touches every pixel: the single pass that builds the region adjacency graph and the per-region statistics together. On a 1000x1000 px CHM with 4900 trees that pass takes **9.7 ms**, against 128 ms for an equivalent written with `numpy.bincount` — a 13x gap, mostly because it does in one pass what numpy needs several for.

The grow loop is deliberately *not* compiled. It is driven by a heap and set membership, which Numba does not handle well, and it runs once per tree rather than once per pixel — roughly 0.4 s for 1150 trees. It is not the bottleneck.

First call in a session pays the JIT compilation cost (~2 s); `cache=True` means later runs read the compiled code from disk.

</details>

<details>
<summary><b>Testing, repository layout, requirements</b></summary>

```bash
pip install -e ".[test]"
pytest tests/ -v
```

The README figures are remade with `python www/figures.py` from the tiles in `test_data/`.

```
pycacumen/
├── pycacumen/
│   ├── __init__.py      # public API (lazy imports)
│   ├── __main__.py      # python -m pycacumen
│   ├── chm.py           # CHM smoothing
│   ├── treetops.py      # detection, merging, screening
│   ├── hrg.py           # the algorithm: watershed, RAG, growing, arbitration
│   ├── delineate.py     # CrownDelineator pipeline
│   ├── io.py            # raster/vector I/O (rasterio, fiona)
│   └── cli.py           # command line
├── tests/
├── test_data/           # seven 0.5 m CHM tiles of circular sample plots
├── www/                 # logo and the README figures, with the script that makes them
├── examples/
├── pyproject.toml
├── environment.yaml
├── CITATION.cff
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE
```

- Python ≥ 3.9
- NumPy ≥ 1.21, Numba ≥ 0.56, SciPy ≥ 1.7, scikit-image ≥ 0.19
- Rasterio ≥ 1.3, Fiona ≥ 1.9 *(only for file I/O)*

</details>

## Citation

If you use pycacumen in your research, please cite the software and the work it builds on:

**This implementation**

> Pawelec, I. (2026). *pycacumen: individual tree crown delineation from canopy height models by Hierarchical Region Growing* [Software]. https://github.com/igorpawelec/pycacumen

**Upstream project.** pycacumen is a derivative of PyCrown and keeps its pipeline structure:

> Zörner, J., Dymond, J., Shepherd, J., Jolly, B. (2018). *PyCrown — Fast raster-based individual tree segmentation for LiDAR data.* Landcare Research NZ Ltd. https://doi.org/10.7931/M0SR-DN55
>
> Zörner, J., Dymond, J.R., Shepherd, J.D., Wiser, S.K., Bunting, P., Jolly, B. (2018). LiDAR-based regional inventory of tall trees — Wellington, New Zealand. *Forests* 9(11), 702. https://doi.org/10.3390/f9110702

**Methods used**

> Chan, T.F., Golub, G.H., LeVeque, R.J. (1983). Algorithms for computing the sample variance: analysis and recommendations. *The American Statistician* 37(3), 242–247. — the pairwise formula that merges two regions' statistics in O(1). Note this is *not* Welford's update, which adds one sample at a time; a crown absorbs a whole region at once.
>
> Beucher, S., Meyer, F. (1993). The morphological approach to segmentation: the watershed transformation. In: *Mathematical Morphology in Image Processing*, 433–481. — the marker-based watershed, via scikit-image.
>
> Popescu, S.C., Wynne, R.H. (2004). Seeing the trees in the forest. *Photogrammetric Engineering & Remote Sensing* 70(5), 589–604. — local-maxima tree detection on a smoothed CHM.

See [CITATION.cff](CITATION.cff) for machine-readable metadata.

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).

pycacumen derives from PyCrown, which is published under GPLv3; the licence carries over.

## Contributing

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).
