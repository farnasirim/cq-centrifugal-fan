# CadQuery Centrifugal Fan Builder

![cq-centrifugal-fan](https://github.com/farnasirim/cq-centrifugal-fan/assets/8123364/b78fca85-f5bb-4bd4-8e88-affff62adfcb)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Fully parametric centrifugal fan builder in CadQuery

## Quick run

```bash
docker run -ti cadquery/cadquery \
bash -c 'pip install cq_centrifugal_fan; python -m cq_centrifugal_fan.use_cases.default'
```

```text
    ...
    7/ 13 Face (1x Wire), Wire (4x Edges) length: ...
        1/  4 Line: (  10.055, -1.78,  100) -> (  ...
        2/  4 Line: (  11.858, -1.78,  100) -> (  ...
        3/  4 Line: (  10.055, -1.78,  100) -> (  ...
        4/  4 Line: (  10.055, -1.78,  94.66) ->  ...

    8/ 13 Face (1x Wire), Wire (4x Edges) length: ...
        1/  4 Line: (  11.858, -1.78,  100) -> (  ...
        2/  4 Line: (  14.654, -1.78,  100) -> (  ...
        3/  4 Line: (  11.858, -1.78,  100) -> (  ...
        4/  4 Line: (  11.858, -1.78,  101.78) -> ...
    ...
```

Make sure you include `--platform=linux/amd64` on arm macs.

## Installation and Usage

Install using `pip install cq_centrifugal_fan`. Then run the default use case which provides an example parametrization.

`python -m cq_centrifugal_fan.use_case.default`

```python
...
class PenMeasurements:
    OUTER_RADIUS = np.median([7.10, 7.10, 7.06, 7.12, 7.11])
    THICKNESS = np.median([0.85, 0.89, 0.93])

...

phb = cf_shapes.PenHolderBuilder(
    PM.THICKNESS * 2, PM.OUTER_RADIUS / 2, PM.OUTER_RADIUS * 3 / 4
)
obj = phb.build()
```

## Development

Refer to `cq_centrifugal_fan/use_case/default.py` to find visualization calls. Install `cq_centrifugal_fan[dev]` and use either a [notebook](https://github.com/bernhard-42/jupyter-cadquery) or [vscode](https://github.com/bernhard-42/vscode-ocp-cad-viewer) for live visualization.

## Notes

Assemblies are not used and various corners are cut since everything is done in a rush. All improvements are welcome.
