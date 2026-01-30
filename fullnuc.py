#!/usr/bin/env python3

from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def existing_dir(argument: str) -> Path:
    res = Path(argument)

    if not res.is_dir():
        raise ValueError(f"{argument} is not a directory")

    return res


def isospin_transform(f: int) -> int:
    match f:
        case 1:
            return 2
        case 2:
            return 1
        case -1:
            return -2
        case -2:
            return -1
        case _:
            return f


def main() -> None:

    parser = argparse.ArgumentParser(
        description="Convert bound proton PDFs into full nuclear PDFs"
    )

    parser.add_argument("A", type=int, help="Mass number A")
    parser.add_argument("Z", type=int, help="Atomic number Z")
    parser.add_argument(
        "input_path", type=existing_dir, help="Path to the bound proton PDFs"
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="Path to the full nuclear PDFs. Without --force, this must not be an existing path or must be an empty directory.",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite contents of output_path if output_path is a non-empty directory",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Output to stdout the name of every file that is written inside output_path.",
    )

    args = parser.parse_args()

    A: int = args.A
    Z: int = args.Z
    input_path: Path = args.input_path
    output_path: Path = args.output_path
    force: bool = args.force
    verbose: bool = args.verbose

    logging.basicConfig(
        filename="fullnuc", level=(logging.INFO if verbose else logging.WARNING)
    )

    # fail if output_path exists and output_path is a non-empty directory
    if (
        output_path.exists()
        and not force
        and (not output_path.is_dir() or any(output_path.iterdir()))
    ):
        raise ValueError("output_path must be non-existent or empty directory")

    output_path.mkdir(exist_ok=True)

    shutil.copy(
        input_path / (input_path.name + ".info"),
        output_path / (output_path.name + ".info"),
    )
    logger.info("Written %s", output_path / (output_path.name + ".info"))

    for dat in input_path.glob("*.dat"):
        with open(dat) as f:
            header = "".join(f.readline() for _ in range(6))

        flavors = list(
            pd.read_csv(dat, sep=r"\s+", skiprows=5, header=None, nrows=1).iloc[0]
        )

        data = pd.read_csv(
            dat,
            skiprows=6,
            header=None,
            sep=r"\s+",
            names=flavors,
            skipfooter=1,
            engine="python",
        )

        data_fullnuc = pd.DataFrame()
        for f in data.columns:
            data_fullnuc[f] = (
                Z / A * data[f] + (A - Z) / A * data[isospin_transform(int(f))]
            )

        output_dat = output_path / (dat.name.replace(input_path.name, output_path.name))
        with open(output_dat, "w") as f:
            f.write(header)
            data_fullnuc.to_csv(
                f, sep=" ", header=False, index=False, float_format="%.8e"
            )
            f.write("---\n")

        logger.info("Written %s", output_dat)


if __name__ == "__main__":
    main()
