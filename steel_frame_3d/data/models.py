"""
Data models for SteelFrame3D project.
Units: Length [m], Force [kN], Stress [kPa], Mass [kg]
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import json


@dataclass
class Vector3D:
    """3D Vector for coordinates and directions."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z]
    
    @classmethod
    def from_list(cls, values: List[float]) -> 'Vector3D':
        if len(values) != 3:
            raise ValueError("Vector3D requires exactly 3 values")
        return cls(x=values[0], y=values[1], z=values[2])


@dataclass
class Node:
    """Structural node in 3D space."""
    id: int
    x: float
    y: float
    z: float
    
    @property
    def coordinates(self) -> Vector3D:
        return Vector3D(self.x, self.y, self.z)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "z": self.z
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Node':
        return cls(
            id=data["id"],
            x=data["x"],
            y=data["y"],
            z=data["z"]
        )


@dataclass
class Material:
    """Material properties."""
    id: int
    name: str
    E: float  # Young's modulus [kPa]
    nu: float  # Poisson's ratio
    density: float  # [kg/m³]
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "E": self.E,
            "nu": self.nu,
            "density": self.density
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Material':
        return cls(
            id=data["id"],
            name=data["name"],
            E=data["E"],
            nu=data["nu"],
            density=data["density"]
        )


@dataclass
class Section:
    """Cross-section properties."""
    id: int
    name: str
    A: float  # Area [m²]
    Iy: float  # Moment of inertia about local y [m⁴]
    Iz: float  # Moment of inertia about local z [m⁴]
    J: float  # Torsional constant [m⁴]
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "A": self.A,
            "Iy": self.Iy,
            "Iz": self.Iz,
            "J": self.J
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Section':
        return cls(
            id=data["id"],
            name=data["name"],
            A=data["A"],
            Iy=data["Iy"],
            Iz=data["Iz"],
            J=data["J"]
        )


@dataclass
class Element:
    """3D beam element connecting two nodes."""
    id: int
    start_node_id: int
    end_node_id: int
    material_id: int
    section_id: int
    orientation_vector: List[float] = field(default_factory=lambda: [0.0, 0.0, 1.0])
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start_node_id": self.start_node_id,
            "end_node_id": self.end_node_id,
            "material_id": self.material_id,
            "section_id": self.section_id,
            "orientation_vector": self.orientation_vector
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Element':
        return cls(
            id=data["id"],
            start_node_id=data["start_node_id"],
            end_node_id=data["end_node_id"],
            material_id=data["material_id"],
            section_id=data["section_id"],
            orientation_vector=data.get("orientation_vector", [0.0, 0.0, 1.0])
        )


@dataclass
class BoundaryCondition:
    """Support/boundary condition at a node."""
    node_id: int
    ux: bool = False  # Restrained in X
    uy: bool = False  # Restrained in Y
    uz: bool = False  # Restrained in Z
    rx: bool = False  # Restrained rotation about X
    ry: bool = False  # Restrained rotation about Y
    rz: bool = False  # Restrained rotation about Z
    
    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "ux": self.ux,
            "uy": self.uy,
            "uz": self.uz,
            "rx": self.rx,
            "ry": self.ry,
            "rz": self.rz
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BoundaryCondition':
        return cls(
            node_id=data["node_id"],
            ux=data.get("ux", False),
            uy=data.get("uy", False),
            uz=data.get("uz", False),
            rx=data.get("rx", False),
            ry=data.get("ry", False),
            rz=data.get("rz", False)
        )


@dataclass
class Load:
    """Base load definition."""
    id: int
    type: str = "unknown"  # "nodal_force", "nodal_moment", "distributed"
    
    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type}


@dataclass
class NodalForce(Load):
    """Point force applied at a node."""
    type: str = "nodal_force"
    node_id: int = 0
    fx: float = 0.0
    fy: float = 0.0
    fz: float = 0.0
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "node_id": self.node_id,
            "fx": self.fx,
            "fy": self.fy,
            "fz": self.fz
        })
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NodalForce':
        return cls(
            id=data["id"],
            node_id=data["node_id"],
            fx=data.get("fx", 0.0),
            fy=data.get("fy", 0.0),
            fz=data.get("fz", 0.0)
        )


@dataclass
class NodalMoment(Load):
    """Point moment applied at a node."""
    type: str = "nodal_moment"
    node_id: int = 0
    mx: float = 0.0
    my: float = 0.0
    mz: float = 0.0
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "node_id": self.node_id,
            "mx": self.mx,
            "my": self.my,
            "mz": self.mz
        })
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NodalMoment':
        return cls(
            id=data["id"],
            node_id=data["node_id"],
            mx=data.get("mx", 0.0),
            my=data.get("my", 0.0),
            mz=data.get("mz", 0.0)
        )


@dataclass
class LoadCase:
    """A single load case containing multiple loads."""
    id: int
    name: str
    loads: List[Load] = field(default_factory=list)
    
    def add_load(self, load: Load):
        self.loads.append(load)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "loads": [load.to_dict() for load in self.loads]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LoadCase':
        load_case = cls(id=data["id"], name=data["name"])
        for load_data in data.get("loads", []):
            load_type = load_data.get("type")
            if load_type == "nodal_force":
                load = NodalForce.from_dict(load_data)
            elif load_type == "nodal_moment":
                load = NodalMoment.from_dict(load_data)
            else:
                continue
            load_case.add_load(load)
        return load_case


@dataclass
class LoadCombination:
    """Linear combination of load cases."""
    id: int
    name: str
    factors: List[Tuple[int, float]] = field(default_factory=list)  # [(load_case_id, factor), ...]
    
    def add_factor(self, load_case_id: int, factor: float):
        self.factors.append((load_case_id, factor))
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "factors": [{"load_case_id": lc_id, "factor": f} for lc_id, f in self.factors]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LoadCombination':
        combo = cls(id=data["id"], name=data["name"])
        for item in data.get("factors", []):
            combo.add_factor(item["load_case_id"], item["factor"])
        return combo


@dataclass
class Model:
    """Complete structural model."""
    version: str = "1.0"
    nodes: List[Node] = field(default_factory=list)
    elements: List[Element] = field(default_factory=list)
    materials: List[Material] = field(default_factory=list)
    sections: List[Section] = field(default_factory=list)
    boundary_conditions: List[BoundaryCondition] = field(default_factory=list)
    load_cases: List[LoadCase] = field(default_factory=list)
    combinations: List[LoadCombination] = field(default_factory=list)
    
    def add_node(self, node: Node):
        self.nodes.append(node)
    
    def add_element(self, element: Element):
        self.elements.append(element)
    
    def add_material(self, material: Material):
        self.materials.append(material)
    
    def add_section(self, section: Section):
        self.sections.append(section)
    
    def add_boundary_condition(self, bc: BoundaryCondition):
        self.boundary_conditions.append(bc)
    
    def add_load_case(self, load_case: LoadCase):
        self.load_cases.append(load_case)
    
    def add_combination(self, combo: LoadCombination):
        self.combinations.append(combo)
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "units": {"length": "m", "force": "kN", "stress": "kPa", "mass": "kg"},
            "materials": [m.to_dict() for m in self.materials],
            "sections": [s.to_dict() for s in self.sections],
            "nodes": [n.to_dict() for n in self.nodes],
            "elements": [e.to_dict() for e in self.elements],
            "boundary_conditions": [bc.to_dict() for bc in self.boundary_conditions],
            "load_cases": [lc.to_dict() for lc in self.load_cases],
            "combinations": [c.to_dict() for c in self.combinations]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Model':
        model = cls(version=data.get("version", "1.0"))
        
        for m_data in data.get("materials", []):
            model.add_material(Material.from_dict(m_data))
        
        for s_data in data.get("sections", []):
            model.add_section(Section.from_dict(s_data))
        
        for n_data in data.get("nodes", []):
            model.add_node(Node.from_dict(n_data))
        
        for e_data in data.get("elements", []):
            model.add_element(Element.from_dict(e_data))
        
        for bc_data in data.get("boundary_conditions", []):
            model.add_boundary_condition(BoundaryCondition.from_dict(bc_data))
        
        for lc_data in data.get("load_cases", []):
            model.add_load_case(LoadCase.from_dict(lc_data))
        
        for c_data in data.get("combinations", []):
            model.add_combination(LoadCombination.from_dict(c_data))
        
        return model
    
    def save_to_json(self, filepath: str):
        """Save model to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_json(cls, filepath: str) -> 'Model':
        """Load model from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
