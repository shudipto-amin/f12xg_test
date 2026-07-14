#!/usr/bin/env python3

from typing import List, Tuple, Optional, Dict

import argparse
import copy
import re
from fractions import Fraction
from functools import cmp_to_key
from io import StringIO
from dataclasses import dataclass
from enum import IntEnum
from collections import Counter
import os

import numpy as np
from numpy.typing import NDArray

import xarray as xr


def get_slot_perm(slots: List[str]) -> List[int]:
    def compare_slots(lhs: int, rhs: int):
        values = {"P": 0, "V": 1, "H": 2, "X": 3}

        return values[slots[lhs]] - values[slots[rhs]]

    perm = [x for x in range(len(slots))]
    perm = sorted(perm, key=cmp_to_key(compare_slots))

    return perm


class IndexSpace(IntEnum):
    H = 0
    P = 1
    V = 2
    X = 3

    @staticmethod
    def tensor_order_key(space: "IndexSpace") -> int:
        order = {
            IndexSpace.P: 0,
            IndexSpace.H: 2,
            IndexSpace.V: 1,
            IndexSpace.X: 3,
        }

        return order[space]

    @staticmethod
    def gecco_order_key(space: "IndexSpace") -> int:
        order = {
            IndexSpace.P: 0,
            IndexSpace.H: 1,
            IndexSpace.V: 2,
            IndexSpace.X: 3,
        }

        return order[space]


class SlotType(IntEnum):
    Creator = 0
    Annihilator = 1


@dataclass(frozen=True)
class Slot:
    space: IndexSpace
    vertex: int
    type: SlotType


def invert_permutation(perm: List[int]) -> List[int]:
    inverted = [0] * len(perm)
    for idx, image in enumerate(perm):
        inverted[image] = idx

    return inverted


class SlotSpec:
    @staticmethod
    def parse(spec: str) -> "SlotSpec":
        creators, annihilators = parse_slot_stub(stub=spec)

        slots: List[Slot] = []

        num_vertices = len(creators)
        assert len(annihilators) == num_vertices

        for vertex in range(num_vertices):
            for type in range(2):
                group = [creators, annihilators][type]
                for space, multiplicity in enumerate(group[vertex]):
                    for _ in range(multiplicity):
                        slots.append(
                            Slot(
                                space=IndexSpace(space),
                                vertex=vertex,
                                type=SlotType(type),
                            )
                        )

        slot_spec = SlotSpec(slots=slots)

        # We assume that we create the index list in GeCCo order
        assert slot_spec.to_gecco_order() == [x for x in range(len(slots))]

        return slot_spec

    def __init__(self, slots: List[Slot]):
        self.slots = slots

    def __iter__(self):
        return self.slots.__iter__()

    def __getitem__(self, idx: int) -> Slot:
        return self.slots[idx]

    def __len__(self) -> int:
        return len(self.slots)

    def __str__(self, indent_level: int = 0) -> str:
        indent = " " * indent_level

        creator_widths: List[int] = []
        annihilator_widths: List[int] = []
        creators: List[str] = []
        annihilators: List[str] = []
        for slot in self.slots:
            while len(creator_widths) <= slot.vertex:
                creator_widths.append(0)
                annihilator_widths.append(0)
                creators.append("")
                annihilators.append("")

            if slot.type == SlotType.Creator:
                creators[slot.vertex] += slot.space.name
                creator_widths[slot.vertex] += len(slot.space.name)
            else:
                assert slot.type == SlotType.Annihilator
                annihilators[slot.vertex] += slot.space.name
                annihilator_widths[slot.vertex] += len(slot.space.name)

        vertex_widths = [
            max(creator_widths[i], annihilator_widths[i])
            for i in range(len(creator_widths))
        ]

        return (
            indent
            + " | ".join(
                [" " * (vertex_widths[i] - len(x)) + x for i, x in enumerate(creators)]
            )
            + "\n"
            + indent
            + " | ".join(
                [
                    " " * (vertex_widths[i] - len(x)) + x
                    for i, x in enumerate(annihilators)
                ]
            )
        )

    def to_string(self, indent: int) -> str:
        return self.__str__(indent_level=indent)

    def num_vertices(self) -> int:
        return max([x.vertex for x in self.slots]) + 1

    def is_particle_number_conserving(self) -> bool:
        creators = 0
        annihilators = 0

        for slot in self.slots:
            if slot.type == SlotType.Creator:
                creators += 1
            else:
                assert slot.type == SlotType.Annihilator
                annihilators += 1

        return creators == annihilators

    def __compute_sort_perm(self, key_func) -> List[int]:
        def idx_to_slot_key(idx: int):
            return key_func(self.slots[idx])

        perm = [x for x in range(len(self.slots))]

        perm.sort(key=idx_to_slot_key)

        return perm

    def to_gecco_order(self) -> List[int]:
        def slot_to_key(slot: Slot):
            return (slot.vertex, slot.type, IndexSpace.gecco_order_key(slot.space))

        perm = self.__compute_sort_perm(key_func=slot_to_key)

        self.slots = [self.slots[perm[x]] for x in range(len(self.slots))]

        # The perm is now a map such that the i-th element in the
        # original sequence ought to be moved to the perm[i]-th place
        # in the permuted sequence.
        # However, we would like the permutation to instead describe
        # that the i-th element in the permuted sequence is the
        # perm[i]-th element in the original sequence.
        # -> need to invert perm
        return invert_permutation(perm)

    def to_tensor_order(self) -> List[int]:
        def slot_to_key(slot: Slot):
            return (IndexSpace.tensor_order_key(slot.space), slot.type, slot.vertex)

        perm = self.__compute_sort_perm(key_func=slot_to_key)

        self.slots = [self.slots[perm[x]] for x in range(len(self.slots))]

        # The perm is now a map such that the i-th element in the
        # original sequence ought to be moved to the perm[i]-th place
        # in the permuted sequence.
        # However, we would like the permutation to instead describe
        # that the i-th element in the permuted sequence is the
        # perm[i]-th element in the original sequence.
        # -> need to invert perm
        return invert_permutation(perm)


def stringify_ndarray(array: NDArray, indent_level: int = 0) -> str:
    string = ""
    indent = " " * indent_level

    it = np.nditer(array, flags=["multi_index"], order="C")
    i = 0
    while not it.finished:
        value = array[it.multi_index]
        string += indent + f"{i+1:3d}: " + str(it.multi_index) + " "
        if value == 0:
            string += " 0"
        elif abs(value) < 1e-5:
            string += f"{value:+2.4e}"
        else:
            string += f"{value:+10.8f}"

        if i + 1 < array.size:
            string += "\n"

        i += 1
        it.iternext()

    return string


@dataclass
class Distribution:
    spin_case: str
    values: NDArray

    def to_string(self, indent: int = 0) -> str:
        return self.__str__(indent)

    def __str__(self, indent_level: int = 0) -> str:
        indent = " " * indent_level

        str_repr = indent + self.spin_case + "\n"
        str_repr += stringify_ndarray(array=self.values, indent_level=indent_level)

        return str_repr


@dataclass
class SubBlock:
    M_s: Fraction
    irrep: int
    distributions: List[Distribution]

    def to_string(self, indent: int = 0) -> str:
        return self.__str__(indent)

    def __str__(self, indent_level: int = 0) -> str:
        indent = " " * indent_level

        str = indent + f"M_s={self.M_s}, IRREP={self.irrep}\n"

        for i, dist in enumerate(self.distributions):
            str += dist.to_string(indent_level + 2)

            if i + 1 < len(self.distributions):
                str += "\n"

        return str


@dataclass
class GeCCoBlock:
    id: int
    slots: SlotSpec
    subblocks: List[SubBlock]

    def to_string(self, indent: int = 0) -> str:
        return self.__str__(indent)

    def __str__(self, indent_level: int = 0) -> str:
        str = self.slots.to_string(indent=indent_level) + "\n"
        str += (
            " " * indent_level
            + "(stored as "
            + "".join(x.space.name for x in self.slots)
            + ")\n"
        )

        for i, subblock in enumerate(self.subblocks):
            str += subblock.to_string(indent_level + 2)

            if i + 1 < len(self.subblocks):
                str += "\n"

        return str

    def to_data_array(self) -> xr.DataArray:
        data = []
        irreps = []
        spin_cases = []

        for sub in self.subblocks:
            for irrep_idx, irrep in enumerate([sub.irrep]):
                if irrep_idx == len(data):
                    data.append([])
                    irreps.append(irrep)
                for dist in sub.distributions:
                    spin_cases.append(dist.spin_case)

                    data[irrep_idx].append(dist.values)

        assert len(set(spin_cases)) == len(spin_cases)
        assert len(set(irreps)) == len(irreps)

        slot_dims = []
        slot_counter = dict()
        for slot in self.slots:
            if not slot.space in slot_counter:
                slot_counter[slot.space] = 1

            slot_dims.append(slot.space.name + f"_{slot_counter[slot.space]}")
            slot_counter[slot.space] += 1

        return xr.DataArray(
            data=data,
            dims=["irrep", "spin_case", *slot_dims],
            coords={"irrep": irreps, "spin_case": spin_cases},
        )


@dataclass
class GeCCoDump:
    name: str
    blocks: List[GeCCoBlock]

    def to_string(self, indent: int = 0) -> str:
        return self.__str__(indent)

    def __str__(self, indent_level: int = 0) -> str:
        indent = " " * indent_level
        str = indent + f"Dump of GeCCo tensor '{self.name}'\n"

        for i, block in enumerate(self.blocks):
            str += indent + f"Block #{i+1}:\n"

            str += block.to_string(indent_level + 2) + "\n"

        return str

    def to_data_set(self) -> xr.Dataset:
        data_vars = dict()
        for block in self.blocks:
            data = block.to_data_array()
            data_vars["".join(x.space.name for x in block.slots)] = data

        return xr.Dataset(data_vars=data_vars)


@dataclass
class MolproBlock:
    slots: List[IndexSpace]
    irrep: int
    values: NDArray

    def to_string(self, indent: int = 0) -> str:
        return self.__str__(indent_level=indent)

    def __str__(self, indent_level: int = 0) -> str:
        indent = " " * indent_level
        string = indent + "".join([x.name for x in self.slots]) + "\n"
        string += indent + f"IRREP={self.irrep}\n"
        string += stringify_ndarray(array=self.values, indent_level=indent_level + 2)

        return string

    def to_data_array(self) -> xr.DataArray:
        slot_dims = []
        slot_counter = dict()
        for space in self.slots:
            if not space in slot_counter:
                slot_counter[space] = 1

            slot_dims.append(space.name + f"_{slot_counter[space]}")
            slot_counter[space] += 1

        return xr.DataArray(
            data=[self.values],
            dims=["irrep", *slot_dims],
            coords={"irrep": [self.irrep]},
        )


@dataclass
class MolproDump:
    name: str
    blocks: List[MolproBlock]

    def __str__(self) -> str:
        str = f"Dump of Molpro tensor '{self.name}'\n"

        for i, block in enumerate(self.blocks):
            str += f"Block #{i+1}:\n"
            str += block.to_string(indent=2) + "\n"

        return str

    def to_data_set(self) -> xr.Dataset:
        data_vars = dict()

        for block in self.blocks:
            data_vars["".join(x.name for x in block.slots)] = block.to_data_array()

        return xr.Dataset(data_vars=data_vars)


def parse_slot_kinds(spec: str) -> List[List[str]]:
    spec = spec.replace("/", " ").replace("\\", " ")
    spec = spec.strip()

    parts = spec.split()

    assert len(parts) % 4 == 0

    slots: List[List[str]] = []

    for i in range(len(parts) // 4):
        hole = int(parts[4 * i + 0])
        particle = int(parts[4 * i + 1])
        valence = int(parts[4 * i + 2])
        external = int(parts[4 * i + 3])

        vertex_slots: List[str] = []

        if hole > 0:
            vertex_slots.append("H" * hole)
        if particle > 0:
            vertex_slots.append("P" * particle)
        if valence > 0:
            vertex_slots.append("V" * valence)
        if external > 0:
            vertex_slots.append("V" * external)

        slots.append(vertex_slots)

    return slots


def parse_slot_stub(
    stub: str, num_vertices: Optional[int] = None
) -> Tuple[List[List[int]], List[List[int]]]:
    line1 = stub[: stub.index("\n")].strip()
    line2 = stub[stub.index("\n") + 1 :].strip()

    assert line1.startswith("/")
    assert line2.startswith("\\")

    if line1.endswith("\\/"):
        assert line2.endswith("/\\")
        end_idx = -2
    else:
        assert line1.endswith("\\")
        assert line2.endswith("/")
        end_idx = -1

    line1 = line1[1:end_idx].strip()
    line2 = line2[1:end_idx].strip()

    line1_vertices = line1.split("\\/")
    line2_vertices = line2.split("/\\")

    if num_vertices:
        line1_vertices = line1_vertices[:num_vertices]
        line2_vertices = line2_vertices[:num_vertices]

    creator_specs: List[List[int]] = []
    annihilators_specs: List[List[int]] = []

    for vertex in line1_vertices:
        parts = vertex.split()

        creator_specs.append([int(x) for x in parts])

    for vertex in line2_vertices:
        parts = vertex.split()

        annihilators_specs.append([int(x) for x in parts])

    return (creator_specs, annihilators_specs)


def parse_spin_dist(spec: str, slots: SlotSpec) -> str:
    creators, annihilators = parse_slot_stub(spec, num_vertices=slots.num_vertices())

    slots.to_gecco_order()

    spin_str = ""

    occurances = Counter(slots)

    for slot, multiplicity in occurances.items():
        group = [creators, annihilators][slot.type.value]
        ms_val = group[slot.vertex][slot.space.value]

        assert abs(ms_val) in [0, 1, 2]

        if ms_val == 0:
            assert multiplicity % 2 == 0
            spin_str += "ab" * (multiplicity // 2)
        elif ms_val < 0:
            spin_str += "b" * abs(ms_val)
        else:
            assert ms_val > 0
            spin_str += "a" * ms_val

    assert len(spin_str) == len(slots)
    return spin_str


def infer_spin_case(M_s: Fraction, slots: SlotSpec) -> str:
    assert slots.is_particle_number_conserving()

    # Note: M_s is the M_s change of the annihilator string only
    if abs(2 * M_s) == len(slots) / 2:
        if M_s >= 0:
            return "a" * len(slots)
        else:
            return "b" * len(slots)

    assert M_s == 0
    # We assume that every index space appears twice on the same vertex
    assert set(Counter([x for x in slots]).values()) == {2}

    return (len(slots) // 2) * "ab"


def parse_subblock(
    subblock: str, dims: Dict[str, int], max_elements: int, slots: SlotSpec
) -> SubBlock:
    subblock = subblock.strip()
    assert subblock.startswith("Ms")
    subblock = subblock[subblock.index("=") + 1 :].strip()
    M_s = Fraction(subblock[: subblock.index(" ")])

    subblock = subblock[subblock.index("IRREP") :]
    subblock = subblock[subblock.index("=") + 1 :].strip()
    irrep = int(subblock[: subblock.index(" ")])

    subblock = subblock[subblock.index("len = ") + len("len = ") :].strip()
    length = int(subblock[: subblock.index(" ")])

    subblock = subblock[subblock.index("norm = ") + len("norm = ") :].strip()
    norm = float(subblock[: subblock.index("\n")])

    subblock = subblock[subblock.index("+------------") :]
    subblock = subblock[subblock.index("\n") + 1 :]

    distributions = []

    if "only single distribution" in subblock:
        dist_delim = "block contains only single distribution"
    else:
        dist_delim = "Ms-Dst"

    while dist_delim in subblock:
        subblock = subblock[subblock.index(dist_delim) :]

        if dist_delim in subblock[len(dist_delim) :]:
            region = subblock[: subblock.index(dist_delim, len(dist_delim))].strip()
        else:
            region = subblock.strip()

        subblock = subblock[len(dist_delim) + 1 :]

        first_idx_marker = "index of first element: "

        if "block contains only single distribution" in region:
            spin_case = infer_spin_case(M_s=M_s, slots=slots)
            dist_length = length
            dist_norm = norm
        else:
            assert region.startswith("Ms-Dst")
            region = region[region.index("len =") + len("len=") + 1 :].strip()
            dist_length = int(region[: region.index(" ")])
            region = region[region.index("norm =") + len("norm =") + 1 :].strip()
            dist_norm = float(region[: region.index(" ")])
            region = region[region.index("\n") :]
            dist_spec = region[: region.index(first_idx_marker)].strip()
            spin_case = parse_spin_dist(spec=dist_spec, slots=slots)

        if dist_length != max_elements:
            continue

        region = region[region.index(first_idx_marker) + len(first_idx_marker) + 1 :]
        idx = int(region[: region.index("\n")])

        region = region[region.index("+.....") :]
        if "\n" in region:
            region = region[region.index("\n") + 1 :]

        # To ensure we get the permutation from GeCCo order to tensor order we have to
        # ensure that the slots are in GeCCo order first
        slots.to_gecco_order()

        # slot_perm is the permutation that is used to bring the list of slots from
        # GeCCo order to tensor order in the sense that
        # tensor[p[i]] = gecco[i]
        # where p is the permutation.
        slot_perm = slots.to_tensor_order()

        values = np.zeros(shape=[dims[x.space.name] for x in slots])

        for current_line in region.split("\n"):
            current_line = current_line.strip()

            if current_line.startswith("+"):
                # End of element list
                break

            parts = current_line.split()

            # The line has the following format
            # <flat index> <orbital list> <spin dist> <extra info> <value>
            # where <orbital list> contains one entry for every individual slot
            # and <spin dist> and <extra info> have the same length.
            n_slot_groups = len(parts) - 2 - len(slots)
            assert n_slot_groups % 2 == 0
            n_slot_groups //= 2

            orbital_list = [int(x) for x in parts[1 : len(slots) + 1]]
            spin_dist = parts[1 + len(slots) : 1 + len(slots) + n_slot_groups]

            sign = 1

            idx = 0
            for group_spin in spin_dist:
                assert len(group_spin) > 0
                if len(group_spin) > 1:
                    assert group_spin in ["22", "+-", "-+", "++", "--"]

                    if group_spin == "-+":
                        # GeCCo reuses the same indices for the +- and -+ spin cases (differentiating
                        # the elements by explicit spin case). Since we prefer having the same spin case
                        # for all elements, we instead permute the indices to generate different index
                        # tuples for the different spin cases (and hence arrive at a unique indexing)
                        # Note that in this context 22 is to be understood as the same thing as +-
                        sign *= -1

                        if (
                            slots[slot_perm[idx]].space
                            == slots[slot_perm[idx + 1]].space
                        ):
                            # Need to explicitly permute the order of indices
                            # In cases where the exchanged slots belong to different spaces, the
                            # slot ordering is not uniquely defined (we reorder to what we find most
                            # useful) so keeping track of the sign change is sufficient.
                            orbital_list[idx], orbital_list[idx + 1] = (
                                orbital_list[idx + 1],
                                orbital_list[idx],
                            )

                idx += len(group_spin)

            multi_index = [
                orb - dims[slots[slot_perm[i]].space.name + "_offset"]
                for i, orb in enumerate(orbital_list)
            ]

            assert all((x >= 0 for x in multi_index))

            # Resort to match shape
            prev = copy.deepcopy(multi_index)
            for i in range(len(slot_perm)):
                multi_index[slot_perm[i]] = prev[i]

            value = float(parts[-1])

            # Ensure we don't overwrite due to indexing issues
            assert values[tuple(multi_index)] == 0

            values[tuple(multi_index)] = value * sign

        assert values.size == dist_length
        actual_norm = np.linalg.norm(values)
        assert abs(actual_norm - dist_norm) < 1e-5

        # Resort spin_case to match shape
        resorted_spin_case = [" "] * len(spin_case)
        for i, spin in enumerate(spin_case):
            resorted_spin_case[slot_perm[i]] = spin

        distributions.append(
            Distribution(spin_case="".join(resorted_spin_case), values=values)
        )

    return SubBlock(M_s=M_s, irrep=irrep, distributions=distributions)


def parse_block(block: str, dims: Dict[str, int]) -> GeCCoBlock:
    block = block[block.index("block no.") + len("block no.") + 1 :].strip()
    block_id = int(block[: block.index(" ")])

    block = block[block.index("/") :]

    # Parse block kind
    slot_spec = block[: block.index("+")]
    slots = SlotSpec.parse(spec=slot_spec)

    block = block[len(slot_spec) + 1 :]

    assert slots.is_particle_number_conserving()

    max_elements = 1
    for current in slots:
        max_elements *= dims[current.space.name]

    subblocks = []
    subblock_delim = "Ms("
    while subblock_delim in block:
        block = block[block.index(subblock_delim) :]

        if subblock_delim in block[len(subblock_delim) :]:
            region = block[: block.index(subblock_delim, len(subblock_delim))]
        else:
            region = block

        sub = parse_subblock(
            region,
            dims=dims,
            max_elements=max_elements,
            slots=slots,
        )
        if len(sub.distributions) > 0:
            subblocks.append(sub)

        block = block[len(subblock_delim) :]

    return GeCCoBlock(id=block_id, slots=slots, subblocks=subblocks)


def parse_gecco_dump(dump: str, dims: Dict[str, int]) -> GeCCoDump:
    name = dump[: dump.index("\n")].strip()

    if name.startswith("residual"):
        name = name[len("residual") :].strip()

    if name.startswith("ME_"):
        name = name[len("ME_") :]

    blocks = []
    block_delimiter = "block no."
    while block_delimiter in dump:
        dump = dump[dump.index(block_delimiter) :]

        if block_delimiter in dump[len(block_delimiter) :]:
            region = dump[: dump.index(block_delimiter, len(block_delimiter))]
        else:
            region = dump

        # Remove last two lines from region as that would confuse the subblock detection logic
        region = region[: region.rindex("\n")]
        region = region[: region.rindex("\n")]
        blocks.append(parse_block(region, dims=dims))

        dump = dump[len(block_delimiter) :]

    return GeCCoDump(name=name, blocks=blocks)


def parse_gecco_file(path: str) -> List[GeCCoDump]:
    contents = open(path, "r").read()
    contents = contents[contents.find("GeCCo will use these orbital spaces") :]
    contents = contents[contents.find("\n") + 1 :]

    core_idx = contents.index("core")
    core = int(contents[core_idx + len("core") : contents.index("\n", core_idx)])
    inactive_idx = contents.index("inactive")
    closed = int(
        contents[inactive_idx + len("inactive") : contents.index("\n", inactive_idx)]
    )
    active_idx = contents.index("active")
    active = int(
        contents[active_idx + len("active") : contents.index("\n", active_idx)]
    )
    virtual_idx = contents.index("virtual")
    virtual = int(
        contents[virtual_idx + len("virtual") : contents.index("\n", virtual_idx)]
    )

    dumps: List[GeCCoDump] = []

    for current in contents.split("dump of ")[1:]:
        current_dump = parse_gecco_dump(
            current,
            dims={
                "H": closed,
                "P": virtual,
                "V": active,
                # Additional +1 everywhere as GeCCo uses 1-based indexing but we want 0-based
                "H_offset": core + 1,
                "P_offset": core + closed + active + 1,
                "V_offset": core + closed + 1,
            },
        )

        dumps.append(current_dump)

    return dumps


def parse_molpro_dump(dump: str) -> Tuple[str, int, NDArray]:
    name = dump[: dump.index("\n")]
    dump = dump[len(name) + 1 :]
    name = name.strip()

    values: List[float] = []

    dump = dump[: dump.index("===")].strip()
    dump = re.sub(" *Data:.*\n", "", dump)
    block_areas = re.split(r"\w*(?:IrrepBlock|StoredBlock).*", dump)

    assert "Properties" in block_areas[0]
    dims = block_areas[0]
    dims = dims[dims.index("dim: (") + len("dim: (") :]
    dims = dims[: dims.index(")")].strip()
    dims = [int(x) for x in dims.split("x")]

    irrep = block_areas[0]
    # Note: Molpro prints IRREPs 0-based
    irrep = int(irrep[irrep.index("irp :") + len("irp :") : irrep.index("}")]) + 1

    for block in block_areas[1:]:
        block = re.sub(r"\n+", "\n", block)
        block = re.sub(r"^ +", "", block)
        block = re.sub(r"  +", " ", block).strip()

        # Remove top row containing col indices
        # Insert additional dummy index in first row (containing col indices)
        # in order to make all dimensions equal
        block = "0 " + block
        block_array = np.genfromtxt(StringIO(block), dtype=float)
        values.extend(block_array[1:, 1:].flatten(order="F"))

    return (name, irrep, np.reshape(values, shape=dims, order="F"))  # type: ignore


def molpro_slot_to_space(slots: str) -> List[IndexSpace]:
    conversion = {
        "c": IndexSpace.H,
        "e": IndexSpace.P,
        "a": IndexSpace.V,
    }

    spaces = []
    for char in slots:
        spaces.append(conversion[char])

    return spaces


def parse_molpro_file(path: str) -> List[MolproDump]:
    contents = open(path, "r").read()

    dumps: List[MolproDump] = []

    # TODO:
    # - group by tensor (mimicking the different blocks of the tensors)
    # - Include IRREP

    current_name = None
    blocks = []

    for current_dump in contents.split("Dump of tensor:")[1:]:
        name, irrep, values = parse_molpro_dump(current_dump)

        if not ":" in name:
            # This tensor doesn't tell us its slots
            continue

        parts = name.split(":")
        assert len(parts) == 2
        name, slots = parts

        if len(set(slots).difference(["e", "c", "a"])) > 0:
            # This is a non-standard tensor that we (for now) skip
            continue

        slots = molpro_slot_to_space(slots)

        if name != current_name and current_name is not None:
            dumps.append(MolproDump(name=current_name, blocks=copy.deepcopy(blocks)))
            blocks.clear()
            current_name = None

        blocks.append(MolproBlock(slots=slots, irrep=irrep, values=values))
        current_name = name

    if current_name is not None:
        dumps.append(MolproDump(name=current_name, blocks=blocks))

    return dumps


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "input",
        help="Path to the output file from which to extract the tensor dumps",
        metavar="PATH",
    )
    parser.add_argument(
        "--type",
        help="What kind of output file is provided",
        choices=["gecco", "molpro"],
        required=True,
    )
    parser.add_argument(
        "--output",
        help="Path to where the parsed tensor dumps shall be written to",
        metavar="PATH",
    )

    args = parser.parse_args()

    if args.type == "gecco":
        dump_list = parse_gecco_file(path=args.input)
    elif args.type == "molpro":
        dump_list = parse_molpro_file(path=args.input)
    else:
        raise RuntimeError(f"Unhandled file type '{args.type}'")

    dump_trees: Dict[str, xr.DataTree] = dict()
    names = set()
    iteration = 1

    for current_dump in dump_list:
        if current_dump.name in ["K", "J", "g", "f"]:
            name = current_dump.name
        else:
            if current_dump.name in names:
                names.clear()
                iteration += 1
            names.add(current_dump.name)

            name = current_dump.name + f" @ {iteration}"

        dump_trees[name] = xr.DataTree(dataset=current_dump.to_data_set())

        if args.output is None:
            print(current_dump)

    if not args.output is None:
        xr.DataTree(children=dump_trees, name=os.path.basename(args.input)).to_netcdf(
            args.output, engine="h5netcdf"
        )


if __name__ == "__main__":
    main()
