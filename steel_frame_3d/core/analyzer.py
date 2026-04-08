"""
Core analysis module for SteelFrame3D.
Implements Finite Element Method for 3D frame analysis.
Units: Length [m], Force [kN], Stress [kPa]
"""

import numpy as np
from typing import Dict, Tuple, List
from data.models import Model, Element, Node, BoundaryCondition, LoadCombination
from core.validator import ModelValidator


class FrameAnalyzer:
    """Main analyzer class for 3D frame structures."""
    
    def __init__(self, model: Model):
        self.model = model
        self.num_nodes = len(model.nodes)
        self.num_elements = len(model.elements)
        self.dof_per_node = 6  # UX, UY, UZ, RX, RY, RZ
        self.total_dof = self.num_nodes * self.dof_per_node
        
        # Mapping from node ID to index
        self.node_id_to_idx = {node.id: idx for idx, node in enumerate(self.nodes_list)}
        
        # Results storage
        self.displacements = None
        self.reactions = None
        self.element_forces = None
    
    @property
    def nodes_list(self) -> List[Node]:
        return self.model.nodes
    
    @property
    def elements_list(self) -> List[Element]:
        return self.model.elements
    
    def get_material_properties(self, element: Element) -> Tuple[float, float]:
        """Get E and nu for an element."""
        material = next((m for m in self.model.materials if m.id == element.material_id), None)
        if material is None:
            raise ValueError(f"Material {element.material_id} not found")
        return material.E, material.nu
    
    def get_section_properties(self, element: Element) -> Dict[str, float]:
        """Get section properties for an element."""
        section = next((s for s in self.model.sections if s.id == element.section_id), None)
        if section is None:
            raise ValueError(f"Section {element.section_id} not found")
        return {
            'A': section.A,
            'Iy': section.Iy,
            'Iz': section.Iz,
            'J': section.J
        }
    
    def compute_element_length_and_direction(self, element: Element) -> Tuple[float, np.ndarray]:
        """Compute element length and direction cosines."""
        start_node = next((n for n in self.nodes_list if n.id == element.start_node_id), None)
        end_node = next((n for n in self.nodes_list if n.id == element.end_node_id), None)
        
        if start_node is None or end_node is None:
            raise ValueError(f"Nodes for element {element.id} not found")
        
        dx = end_node.x - start_node.x
        dy = end_node.y - start_node.y
        dz = end_node.z - start_node.z
        
        length = np.sqrt(dx**2 + dy**2 + dz**2)
        
        if length < 1e-10:
            raise ValueError(f"Element {element.id} has zero or near-zero length")
        
        direction = np.array([dx/length, dy/length, dz/length])
        return length, direction
    
    def compute_transformation_matrix(self, element: Element) -> np.ndarray:
        """
        Compute 12x12 transformation matrix from local to global coordinates.
        Uses orientation vector to define local coordinate system.
        """
        length, ex_local = self.compute_element_length_and_direction(element)
        
        # Orientation vector (defines local Y direction approximately)
        v_orient = np.array(element.orientation_vector)
        v_orient = v_orient / np.linalg.norm(v_orient)
        
        # Local X is along the element
        x_local = ex_local
        
        # Local Z = X × V_orient (perpendicular to both)
        z_local = np.cross(x_local, v_orient)
        if np.linalg.norm(z_local) < 1e-10:
            # If orientation vector is parallel to element, use alternative
            v_alternative = np.array([0.0, 1.0, 0.0])
            if np.abs(np.dot(x_local, v_alternative)) > 0.9:
                v_alternative = np.array([1.0, 0.0, 0.0])
            z_local = np.cross(x_local, v_alternative)
        z_local = z_local / np.linalg.norm(z_local)
        
        # Local Y = Z × X (completes right-handed system)
        y_local = np.cross(z_local, x_local)
        
        # Rotation matrix (3x3) from local to global
        R = np.array([
            x_local,
            y_local,
            z_local
        ])
        
        # Full 12x12 transformation matrix for 2 nodes with 6 DOF each
        T = np.zeros((12, 12))
        for i in range(4):  # 4 blocks of 3x3
            T[i*3:(i+1)*3, i*3:(i+1)*3] = R
        
        return T
    
    def compute_element_stiffness_local(self, element: Element) -> np.ndarray:
        """Compute 12x12 element stiffness matrix in local coordinates."""
        E, _ = self.get_material_properties(element)
        props = self.get_section_properties(element)
        L, _ = self.compute_element_length_and_direction(element)
        
        A = props['A']
        Iy = props['Iy']
        Iz = props['Iz']
        J = props['J']
        
        # Axial stiffness
        EA_L = E * A / L
        
        # Bending stiffness about local y and z
        EIy_L3 = E * Iy / (L**3)
        EIz_L3 = E * Iz / (L**3)
        
        # Torsional stiffness
        GJ_L = (E / (2 * (1 + 0.3))) * J / L  # Assuming nu = 0.3 for steel
        
        # Local stiffness matrix (12x12) for 3D beam
        k_local = np.zeros((12, 12))
        
        # Axial terms (DOF 0, 6 - local x displacement)
        k_local[0, 0] = EA_L
        k_local[0, 6] = -EA_L
        k_local[6, 0] = -EA_L
        k_local[6, 6] = EA_L
        
        # Torsion terms (DOF 3, 9 - local x rotation)
        k_local[3, 3] = GJ_L
        k_local[3, 9] = -GJ_L
        k_local[9, 3] = -GJ_L
        k_local[9, 9] = GJ_L
        
        # Bending about local z (DOF 1, 4, 7, 10 - local y displacement, z rotation)
        k_local[1, 1] = 12 * EIz_L3
        k_local[1, 4] = 6 * EIz_L3 * L
        k_local[1, 7] = -12 * EIz_L3
        k_local[1, 10] = 6 * EIz_L3 * L
        
        k_local[4, 1] = 6 * EIz_L3 * L
        k_local[4, 4] = 4 * EIz_L3 * L**2
        k_local[4, 7] = -6 * EIz_L3 * L
        k_local[4, 10] = 2 * EIz_L3 * L**2
        
        k_local[7, 1] = -12 * EIz_L3
        k_local[7, 4] = -6 * EIz_L3 * L
        k_local[7, 7] = 12 * EIz_L3
        k_local[7, 10] = -6 * EIz_L3 * L
        
        k_local[10, 1] = 6 * EIz_L3 * L
        k_local[10, 4] = 2 * EIz_L3 * L**2
        k_local[10, 7] = -6 * EIz_L3 * L
        k_local[10, 10] = 4 * EIz_L3 * L**2
        
        # Bending about local y (DOF 2, 5, 8, 11 - local z displacement, y rotation)
        k_local[2, 2] = 12 * EIy_L3
        k_local[2, 5] = -6 * EIy_L3 * L
        k_local[2, 8] = -12 * EIy_L3
        k_local[2, 11] = -6 * EIy_L3 * L
        
        k_local[5, 2] = -6 * EIy_L3 * L
        k_local[5, 5] = 4 * EIy_L3 * L**2
        k_local[5, 8] = 6 * EIy_L3 * L
        k_local[5, 11] = 2 * EIy_L3 * L**2
        
        k_local[8, 2] = -12 * EIy_L3
        k_local[8, 5] = 6 * EIy_L3 * L
        k_local[8, 8] = 12 * EIy_L3
        k_local[8, 11] = 6 * EIy_L3 * L
        
        k_local[11, 2] = -6 * EIy_L3 * L
        k_local[11, 5] = 2 * EIy_L3 * L**2
        k_local[11, 8] = 6 * EIy_L3 * L
        k_local[11, 11] = 4 * EIy_L3 * L**2
        
        return k_local
    
    def assemble_global_stiffness(self) -> np.ndarray:
        """Assemble global stiffness matrix."""
        K_global = np.zeros((self.total_dof, self.total_dof))
        
        for element in self.elements_list:
            # Get transformation matrix
            T = self.compute_transformation_matrix(element)
            
            # Get local stiffness
            k_local = self.compute_element_stiffness_local(element)
            
            # Transform to global
            k_global = T.T @ k_local @ T
            
            # Get DOF indices for this element
            start_idx = self.node_id_to_idx[element.start_node_id] * 6
            end_idx = self.node_id_to_idx[element.end_node_id] * 6
            
            dofs = list(range(start_idx, start_idx + 6)) + list(range(end_idx, end_idx + 6))
            
            # Assemble
            for i, dof_i in enumerate(dofs):
                for j, dof_j in enumerate(dofs):
                    K_global[dof_i, dof_j] += k_global[i, j]
        
        return K_global
    
    def apply_boundary_conditions(self, K: np.ndarray, F: np.ndarray) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """Apply boundary conditions using penalty method or reduction."""
        # Find restrained DOFs
        restrained_dofs = []
        
        for bc in self.model.boundary_conditions:
            node_idx = self.node_id_to_idx[bc.node_id]
            
            if bc.ux:
                restrained_dofs.append(node_idx * 6 + 0)
            if bc.uy:
                restrained_dofs.append(node_idx * 6 + 1)
            if bc.uz:
                restrained_dofs.append(node_idx * 6 + 2)
            if bc.rx:
                restrained_dofs.append(node_idx * 6 + 3)
            if bc.ry:
                restrained_dofs.append(node_idx * 6 + 4)
            if bc.rz:
                restrained_dofs.append(node_idx * 6 + 5)
        
        # Create reduced system
        free_dofs = [i for i in range(self.total_dof) if i not in restrained_dofs]
        
        K_reduced = K[np.ix_(free_dofs, free_dofs)]
        F_reduced = F[free_dofs]
        
        return K_reduced, F_reduced, free_dofs
    
    def build_load_vector(self, combination: LoadCombination = None) -> np.ndarray:
        """Build global load vector for a load case or combination."""
        F = np.zeros(self.total_dof)
        
        if combination is None:
            # Use first load case if no combination specified
            if not self.model.load_cases:
                return F
            load_case = self.model.load_cases[0]
            factors = [(load_case.id, 1.0)]
        else:
            factors = combination.factors
        
        for lc_id, factor in factors:
            load_case = next((lc for lc in self.model.load_cases if lc.id == lc_id), None)
            if load_case is None:
                continue
            
            for load in load_case.loads:
                node_idx = self.node_id_to_idx.get(load.node_id)
                if node_idx is None:
                    continue
                
                base_dof = node_idx * 6
                
                if hasattr(load, 'fx'):
                    F[base_dof + 0] += load.fx * factor
                if hasattr(load, 'fy'):
                    F[base_dof + 1] += load.fy * factor
                if hasattr(load, 'fz'):
                    F[base_dof + 2] += load.fz * factor
                
                if hasattr(load, 'mx'):
                    F[base_dof + 3] += load.mx * factor
                if hasattr(load, 'my'):
                    F[base_dof + 4] += load.my * factor
                if hasattr(load, 'mz'):
                    F[base_dof + 5] += load.mz * factor
        
        return F
    
    def analyze(self, combination_id: int = None) -> Dict:
        """
        Perform structural analysis.
        Returns displacements, reactions, and element forces.
        """
        # Validate model before analysis
        validator = ModelValidator(self.model)
        is_valid, errors, warnings = validator.validate()
        
        if not is_valid:
            raise ValueError(f"Model validation failed:\\n" + "\\n".join(errors))
        
        for warning in warnings:
            print(f"Warning: {warning}")
        
        # Assemble global stiffness
        K = self.assemble_global_stiffness()
        
        # Build load vector
        if combination_id is not None:
            combo = next((c for c in self.model.combinations if c.id == combination_id), None)
            if combo is None:
                raise ValueError(f"Combination {combination_id} not found")
            F = self.build_load_vector(combo)
        else:
            F = self.build_load_vector()
        
        # Apply boundary conditions
        K_red, F_red, free_dofs = self.apply_boundary_conditions(K, F)
        
        # Check for singular matrix (kinematic instability)
        if K_red.shape[0] == 0:
            raise ValueError("Structure is fully restrained or has no free DOFs")
        
        try:
            # Solve for displacements
            U_red = np.linalg.solve(K_red, F_red)
        except np.linalg.LinAlgError:
            raise ValueError("Global stiffness matrix is singular. "
                           "Structure may be kinematically unstable.")
        
        # Reconstruct full displacement vector
        U = np.zeros(self.total_dof)
        U[free_dofs] = U_red
        
        # Calculate reactions
        R = K @ U - F
        
        # Store results
        self.displacements = U
        self.reactions = R
        
        # Calculate element forces
        self.element_forces = self.compute_element_forces(U)
        
        return {
            'displacements': U,
            'reactions': R,
            'element_forces': self.element_forces,
            'free_dofs': free_dofs
        }
    
    def compute_element_forces(self, U: np.ndarray) -> List[Dict]:
        """Compute internal forces for each element."""
        results = []
        
        for element in self.elements_list:
            # Get transformation matrix
            T = self.compute_transformation_matrix(element)
            
            # Get element DOFs
            start_idx = self.node_id_to_idx[element.start_node_id] * 6
            end_idx = self.node_id_to_idx[element.end_node_id] * 6
            
            dofs = list(range(start_idx, start_idx + 6)) + list(range(end_idx, end_idx + 6))
            U_element_global = U[dofs]
            
            # Transform to local
            U_element_local = T @ U_element_global
            
            # Get local stiffness
            k_local = self.compute_element_stiffness_local(element)
            
            # Compute local forces
            F_element_local = k_local @ U_element_local
            
            results.append({
                'element_id': element.id,
                'local_forces': F_element_local.tolist(),
                'local_displacements': U_element_local.tolist()
            })
        
        return results
