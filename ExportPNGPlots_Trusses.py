#!/usr/bin/env python3
"""Export truss plots to PNG files in an input-named folder."""

from pathlib import Path
import argparse
import warnings

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt

from ImportCSVData_Trusses import LoadData
from DoFIndexing_Trusses import EstablishGlobalDOFNum
from DoFIndexing_Trusses import StoreNodeDisplacements
from Assembly_Trusses import AssembleStiffness
from Assembly_Trusses import DefineForces
from Solver_Trusses import ComputeDisplacements
from Solver_Trusses import PostprocessReactions
from Solver_Trusses import ComputeMemberForces
from Solver_Trusses import ComputeNormalStresses
from Solver_Trusses import ComputeBucklingLoad

import Plotting_Trusses


DEFAULT_PLOT_TYPES = ("index", "axial", "stress", "disp_in", "buckling")


def resolve_input_geometry(input_geometry):
    base_dir = Path(__file__).resolve().parent
    input_path = Path(input_geometry)

    candidates = []
    if input_path.suffix.lower() == ".csv":
        candidates.append(input_path)
    else:
        candidates.append(input_path.with_suffix(".csv"))
        candidates.append(input_path)

    search_paths = []
    for candidate in candidates:
        if candidate.is_absolute():
            search_paths.append(candidate)
        else:
            search_paths.append(base_dir / candidate)
            search_paths.append(base_dir / "csvs" / candidate.name)

    for candidate in search_paths:
        if candidate.exists() and candidate.suffix.lower() == ".csv":
            return candidate.resolve()

    raise FileNotFoundError(f"Could not find CSV input file for '{input_geometry}'.")


def analyze_truss(input_geometry):
    base_dir = Path(__file__).resolve().parent
    csv_path = resolve_input_geometry(input_geometry)
    section_file = str((base_dir / "aisc_shapes_database_v16_0.csv").resolve())
    material_file = str((base_dir / "Material_Data.csv").resolve())

    nodes, bars = LoadData(str(csv_path), section_file, material_file)
    n_unknowns, n_knowns = EstablishGlobalDOFNum(nodes)
    n_matrix = n_unknowns + n_knowns

    stiffness = AssembleStiffness(bars, n_matrix)
    forces = DefineForces(nodes, n_matrix)
    displacements = ComputeDisplacements(stiffness, forces, n_unknowns)

    StoreNodeDisplacements(nodes, displacements, n_unknowns)
    PostprocessReactions(stiffness, displacements, forces, n_unknowns, nodes)
    ComputeMemberForces(bars)
    ComputeNormalStresses(bars)
    ComputeBucklingLoad(bars)

    return csv_path, nodes, bars


def save_plot_png(nodes, bars, plot_type, output_dir):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="FigureCanvasAgg is non-interactive, and thus cannot be shown",
        )
        Plotting_Trusses.PlotStructureData(nodes, bars, plot_type)
    figure = plt.gcf()
    figure.savefig(output_dir / f"{plot_type}.png", bbox_inches="tight")
    plt.close(figure)


def export_png_plots(input_geometry, plot_types=None):
    csv_path, nodes, bars = analyze_truss(input_geometry)
    output_dir = csv_path.parent / csv_path.stem
    output_dir.mkdir(exist_ok=True)

    selected_plot_types = plot_types or DEFAULT_PLOT_TYPES
    for plot_type in selected_plot_types:
        save_plot_png(nodes, bars, plot_type, output_dir)

    return output_dir


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description="Save truss plots as PNG files in a folder named after the input CSV."
    )
    parser.add_argument(
        "input_geometry",
        help="Input CSV file name or path, with or without the .csv extension.",
    )
    parser.add_argument(
        "--plots",
        nargs="+",
        choices=DEFAULT_PLOT_TYPES,
        default=list(DEFAULT_PLOT_TYPES),
        help="Optional list of plot types to export.",
    )
    return parser


def main():
    parser = build_argument_parser()
    args = parser.parse_args()
    output_dir = export_png_plots(args.input_geometry, tuple(args.plots))
    print(f"Saved PNG plots to: {output_dir}")


if __name__ == "__main__":
    main()