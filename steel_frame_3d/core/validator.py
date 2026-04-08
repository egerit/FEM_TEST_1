"""
Model validation module for SteelFrame3D.
Checks model integrity before analysis.
"""

from typing import List, Tuple
from data.models import Model, Node, Element


class ModelValidator:
    """Validates structural model for errors and warnings."""
    
    def __init__(self, model: Model):
        self.model = model
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validation checks.
        Returns: (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        self._check_duplicate_nodes()
        self._check_zero_length_elements()
        self._check_missing_materials()
        self._check_missing_sections()
        self._check_missing_boundary_conditions()
        self._check_invalid_section_properties()
        self._check_disconnected_nodes()
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _check_duplicate_nodes(self):
        """Check for nodes at the same location."""
        node_positions = {}
        for node in self.model.nodes:
            pos_key = (round(node.x, 6), round(node.y, 6), round(node.z, 6))
            if pos_key in node_positions:
                self.errors.append(
                    f"Duplicate nodes: Node {node.id} and Node {node_positions[pos_key]} "
                    f"are at the same location ({node.x}, {node.y}, {node.z})"
                )
            else:
                node_positions[pos_key] = node.id
        
        if len(self.model.nodes) != len(node_positions):
            self.warnings.append(
                f"Found {len(self.model.nodes) - len(node_positions)} duplicate node locations"
            )
    
    def _check_zero_length_elements(self):
        """Check for elements with zero or near-zero length."""
        for elem in self.model.elements:
            start_node = next((n for n in self.model.nodes if n.id == elem.start_node_id), None)
            end_node = next((n for n in self.model.nodes if n.id == elem.end_node_id), None)
            
            if start_node and end_node:
                dx = end_node.x - start_node.x
                dy = end_node.y - start_node.y
                dz = end_node.z - start_node.z
                length_sq = dx*dx + dy*dy + dz*dz
                
                if length_sq < 1e-12:
                    self.errors.append(
                        f"Element {elem.id} has zero or near-zero length "
                        f"(connects nodes {elem.start_node_id} and {elem.end_node_id})"
                    )
    
    def _check_missing_materials(self):
        """Check that all elements have valid materials."""
        material_ids = {m.id for m in self.model.materials}
        
        for elem in self.model.elements:
            if elem.material_id not in material_ids:
                self.errors.append(
                    f"Element {elem.id} references non-existent material {elem.material_id}"
                )
        
        if not self.model.materials and self.model.elements:
            self.errors.append("No materials defined in the model")
    
    def _check_missing_sections(self):
        """Check that all elements have valid sections."""
        section_ids = {s.id for s in self.model.sections}
        
        for elem in self.model.elements:
            if elem.section_id not in section_ids:
                self.errors.append(
                    f"Element {elem.id} references non-existent section {elem.section_id}"
                )
        
        if not self.model.sections and self.model.elements:
            self.errors.append("No sections defined in the model")
    
    def _check_missing_boundary_conditions(self):
        """Check if structure has any supports."""
        if not self.model.boundary_conditions and self.model.nodes:
            self.errors.append(
                "No boundary conditions defined. Structure is unconstrained and will be unstable."
            )
    
    def _check_invalid_section_properties(self):
        """Check for invalid section properties."""
        for section in self.model.sections:
            if section.A <= 0:
                self.errors.append(f"Section {section.name} has non-positive area: {section.A}")
            if section.Iy <= 0:
                self.errors.append(f"Section {section.name} has non-positive Iy: {section.Iy}")
            if section.Iz <= 0:
                self.errors.append(f"Section {section.name} has non-positive Iz: {section.Iz}")
            if section.J <= 0:
                self.warnings.append(f"Section {section.name} has non-positive torsional constant J: {section.J}")
    
    def _check_disconnected_nodes(self):
        """Check for nodes not connected to any element."""
        connected_nodes = set()
        for elem in self.model.elements:
            connected_nodes.add(elem.start_node_id)
            connected_nodes.add(elem.end_node_id)
        
        for node in self.model.nodes:
            if node.id not in connected_nodes:
                # Check if node has boundary condition (might be intentional)
                has_bc = any(bc.node_id == node.id for bc in self.model.boundary_conditions)
                if not has_bc:
                    self.warnings.append(
                        f"Node {node.id} at ({node.x}, {node.y}, {node.z}) is not connected to any element"
                    )
