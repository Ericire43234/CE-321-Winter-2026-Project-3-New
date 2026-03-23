import csv
from pathlib import Path

from Assembly_Trusses import AssembleStiffness, DefineForces
from DoFIndexing_Trusses import EstablishGlobalDOFNum, StoreNodeDisplacements
from ImportCSVData_Trusses import LoadData
from Solver_Trusses import (
    ComputeBucklingLoad,
    ComputeDisplacements,
    ComputeMemberForces,
    ComputeNormalStresses,
    PostprocessReactions,
)
import SectionMaterialConverter as smc


INPUT_GEOMETRY = "csvs/Wind Optimization Input.csv"
SECTION_FILE = "aisc_shapes_database_v16_0.csv"
MATERIAL_FILE = "Material_Data.csv"
OUTPUT_GEOMETRY = "csvs/Optimized_Structure_W26_With_Wind.csv"

# Constrain candidate families by AISC Type column (examples: "W", "HSS", "PIPE", "L").
# Use None to allow all shape families.
# You can pass one string (e.g., "W") or a list/tuple/set (e.g., ["W", "HSS"]).
SHAPE_TYPE_FILTER = 'W'

# Keep the four criteria exactly as used in your original script.
A992_STRESS = 50.0
AXIAL_SAFETY_FACTOR = 1.5
CRITICAL_BUCKLING_SAFETY_FACTOR = 3.0


def load_shape_candidates(section_file, shape_type_filter=None):
    """Load candidate shapes from the AISC database, sorted by increasing area."""
    candidates = []
    seen_sections = set()

    allowed_types = None
    if shape_type_filter is not None:
        if isinstance(shape_type_filter, str):
            allowed_types = {shape_type_filter.strip().upper()}
        else:
            allowed_types = {item.strip().upper() for item in shape_type_filter}

    with open(section_file, "r", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # header
        for row in reader:
            if len(row) < 6:
                continue

            shape_type = row[0].strip()
            shape_name = row[1].strip()
            area_text = row[5].strip()

            if allowed_types is not None and shape_type.upper() not in allowed_types:
                continue

            if not shape_type or not shape_name or not area_text or area_text == "-" or area_text == "- -" or area_text == "- - -":
                continue

            try:
                area = float(area_text)
            except ValueError:
                continue

            section_label = f"{shape_type} Shapes:{shape_name}"
            if section_label in seen_sections:
                continue

            seen_sections.add(section_label)
            candidates.append((area, section_label))

    candidates.sort(key=lambda item: item[0])
    return candidates


def run_truss_analysis(input_geometry, section_overrides=None):
    """Run a full truss analysis with optional per-bar section overrides."""
    if section_overrides is None:
        section_overrides = {}

    nodes, bars = LoadData(input_geometry, SECTION_FILE, MATERIAL_FILE)

    for bar in bars:
        if bar.idx in section_overrides:
            bar.section_type = section_overrides[bar.idx]
            smc.LoadSectionData(bar, bar.section_type, SECTION_FILE)

    n_unknowns, n_knowns = EstablishGlobalDOFNum(nodes)
    n_matrix = n_unknowns + n_knowns

    K = AssembleStiffness(bars, n_matrix)
    F = DefineForces(nodes, n_matrix)
    d = ComputeDisplacements(K, F, n_unknowns)
    StoreNodeDisplacements(nodes, d, n_unknowns)
    PostprocessReactions(K, d, F, n_unknowns, nodes)

    ComputeMemberForces(bars)
    ComputeNormalStresses(bars)
    ComputeBucklingLoad(bars)

    return nodes, bars


def passes_four_criteria(bar):
    """Return True if the bar satisfies all four optimization criteria."""
    # 1) Stress safety criterion
    if abs(bar.normal_stress) > A992_STRESS / AXIAL_SAFETY_FACTOR:
        return False

    # 2) Buckling safety criterion (compression only)
    if bar.axial_load < 0 and abs(bar.axial_load) > bar.buckling_load / CRITICAL_BUCKLING_SAFETY_FACTOR:
        return False

    # 3) 1/3 buckling optimization criterion (compression only)
    if bar.axial_load < 0 and abs(bar.axial_load * AXIAL_SAFETY_FACTOR) > bar.buckling_load * (1 / 3):
        return False

    # 4) 1/3 yield optimization criterion
    if abs(bar.normal_stress * AXIAL_SAFETY_FACTOR) > A992_STRESS * (1 / 3):
        return False

    return True


def write_optimized_geometry(input_geometry, output_geometry, section_overrides):
    """Write a copy of the geometry CSV with updated section assignments."""
    lines_out = []
    in_bars_block = False

    with open(input_geometry, "r") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            comma = line.split(",")
            first = comma[0].strip().lower() if comma else ""

            if first in ("beams", "bars"):
                in_bars_block = True
                lines_out.append(line)
                continue

            if in_bars_block and first == "index":
                lines_out.append(line)
                continue

            if in_bars_block and comma and comma[0].strip() != "":
                try:
                    bar_idx = int(comma[0].strip())
                except ValueError:
                    lines_out.append(line)
                    continue

                if bar_idx in section_overrides and len(comma) > 3:
                    comma[3] = section_overrides[bar_idx]
                    line = ",".join(comma)

            lines_out.append(line)

    output_path = Path(output_geometry)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        f.write("\n".join(lines_out) + "\n")


def optimize_sections(input_geometry, output_geometry, shape_type_filter=None):
    """Greedy per-bar optimization: smallest-area valid section for each bar."""
    candidates = load_shape_candidates(SECTION_FILE, shape_type_filter=shape_type_filter)
    if not candidates:
        raise RuntimeError("No valid section candidates were loaded from the AISC database.")

    _, base_bars = run_truss_analysis(input_geometry)
    bar_ids = [bar.idx for bar in base_bars]
    base_bars_by_id = {bar.idx: bar for bar in base_bars}
    n_bars = len(base_bars)

    optimized_sections = {}

    if shape_type_filter is None:
        print(f"Loaded {len(candidates)} AISC candidate sections.")
    else:
        print(f"Loaded {len(candidates)} AISC candidate sections with SHAPE_TYPE_FILTER={shape_type_filter}.")
    print(f"Optimizing {n_bars} bars...\n")

    for bar_id in bar_ids:
        selected = None

        for area, candidate_section in candidates:
            trial_sections = dict(optimized_sections)
            trial_sections[bar_id] = candidate_section

            _, trial_bars = run_truss_analysis(input_geometry, trial_sections)
            trial_bars_by_id = {bar.idx: bar for bar in trial_bars}
            trial_bar = trial_bars_by_id[bar_id]

            if passes_four_criteria(trial_bar):
                selected = (candidate_section, area, trial_bar)
                break

        if selected is None:
            print(f"Bar {bar_id}: no valid candidate met all four criteria.")
            optimized_sections[bar_id] = base_bars_by_id[bar_id].section_type
            continue

        section_name, area, trial_bar = selected
        optimized_sections[bar_id] = section_name

        print(
            f"Bar {bar_id}: {section_name} | "
            f"A={area:.3f} in^2 | "
            f"axial={trial_bar.axial_load:.3f} kip | "
            f"stress={trial_bar.normal_stress:.3f} ksi"
        )

    write_optimized_geometry(input_geometry, output_geometry, optimized_sections)

    print("\nOptimization complete.")
    print(f"Optimized geometry written to: {output_geometry}")

    return optimized_sections


if __name__ == "__main__":
    optimize_sections(INPUT_GEOMETRY, OUTPUT_GEOMETRY, shape_type_filter=SHAPE_TYPE_FILTER)
