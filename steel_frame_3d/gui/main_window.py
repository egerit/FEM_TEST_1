"""
Main application window for SteelFrame3D.
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMenuBar, QMenu, QToolBar, QStatusBar,
    QSplitter, QTreeWidget, QTreeWidgetItem, QPushButton,
    QLabel, QMessageBox, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.all import (
    vtkRenderer, vtkRenderWindow, vtkAxesActor,
    vtkPolyDataMapper, vtkActor, vtkLineSource,
    vtkSphereSource, vtkArrowSource, vtkTransform
)

from data.models import Model, Node, Element, NodalForce, LoadCase, LoadCombination
from core.analyzer import FrameAnalyzer


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.model = Model()
        self.current_load_case = None
        self.init_ui()
        self.setup_vtk()
        self.create_sample_model()
    
    def init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("SteelFrame3D - MVP")
        self.setGeometry(100, 100, 1400, 900)
        
        # Menu bar
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("File")
        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        edit_menu = menubar.addMenu("Edit")
        add_node_action = QAction("Add Node", self)
        add_node_action.triggered.connect(self.add_node_dialog)
        edit_menu.addAction(add_node_action)
        
        add_element_action = QAction("Add Element", self)
        add_element_action.triggered.connect(self.add_element_dialog)
        edit_menu.addAction(add_element_action)
        
        add_load_action = QAction("Add Nodal Force", self)
        add_load_action.triggered.connect(self.add_load_dialog)
        edit_menu.addAction(add_load_action)
        
        combo_action = QAction("Load Combinations...", self)
        combo_action.triggered.connect(self.open_combinations_editor)
        edit_menu.addAction(combo_action)
        
        analyze_menu = menubar.addMenu("Analyze")
        run_action = QAction("Run Analysis", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self.run_analysis)
        analyze_menu.addAction(run_action)
        
        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.addAction(new_action)
        toolbar.addAction(open_action)
        toolbar.addAction(save_action)
        toolbar.addSeparator()
        toolbar.addAction(run_action)
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Model tree
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Model Tree"])
        splitter.addWidget(self.tree_widget)
        
        # Right panel - 3D viewer
        self.vtk_widget = QVTKRenderWindowInteractor()
        splitter.addWidget(self.vtk_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def setup_vtk(self):
        """Setup VTK renderer."""
        self.renderer = vtkRenderer()
        self.render_window = self.vtk_widget.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        
        # Setup camera and background
        self.renderer.SetBackground(0.95, 0.95, 0.95)
        self.renderer.ResetCamera()
        
        # Add axes
        axes = vtkAxesActor()
        self.renderer.AddActor(axes)
        
        # Initialize interactor
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()
    
    def update_tree_view(self):
        """Update model tree view."""
        self.tree_widget.clear()
        
        # Nodes
        nodes_item = QTreeWidgetItem(self.tree_widget, ["Nodes"])
        for node in self.model.nodes:
            node_child = QTreeWidgetItem(nodes_item, [f"Node {node.id}: ({node.x:.2f}, {node.y:.2f}, {node.z:.2f})"])
            node_child.setData(0, Qt.ItemDataRole.UserRole, ('node', node.id))
        
        # Elements
        elements_item = QTreeWidgetItem(self.tree_widget, ["Elements"])
        for elem in self.model.elements:
            elem_child = QTreeWidgetItem(elements_item, 
                [f"Element {elem.id}: {elem.start_node_id} -> {elem.end_node_id}"])
            elem_child.setData(0, Qt.ItemDataRole.UserRole, ('element', elem.id))
        
        # Boundary conditions
        bc_item = QTreeWidgetItem(self.tree_widget, ["Supports"])
        for bc in self.model.boundary_conditions:
            bc_child = QTreeWidgetItem(bc_item, [f"Support at Node {bc.node_id}"])
            bc_child.setData(0, Qt.ItemDataRole.UserRole, ('support', bc.node_id))
        
        # Load cases
        loads_item = QTreeWidgetItem(self.tree_widget, ["Load Cases"])
        for lc in self.model.load_cases:
            lc_child = QTreeWidgetItem(loads_item, [f"{lc.name} ({len(lc.loads)} loads)"])
            lc_child.setData(0, Qt.ItemDataRole.UserRole, ('loadcase', lc.id))
        
        # Combinations
        combo_item = QTreeWidgetItem(self.tree_widget, ["Combinations"])
        for combo in self.model.combinations:
            combo_child = QTreeWidgetItem(combo_item, [combo.name])
            combo_child.setData(0, Qt.ItemDataRole.UserRole, ('combination', combo.id))
        
        self.tree_widget.expandAll()
    
    def render_model(self):
        """Render the current model in VTK."""
        self.renderer.RemoveAllViewProps()
        
        # Re-add axes
        axes = vtkAxesActor()
        self.renderer.AddActor(axes)
        
        # Render elements as lines
        for element in self.model.elements:
            start_node = next((n for n in self.model.nodes if n.id == element.start_node_id), None)
            end_node = next((n for n in self.model.nodes if n.id == element.end_node_id), None)
            
            if start_node and end_node:
                line_source = vtkLineSource()
                line_source.SetPoint1(start_node.x, start_node.y, start_node.z)
                line_source.SetPoint2(end_node.x, end_node.y, end_node.z)
                
                mapper = vtkPolyDataMapper()
                mapper.SetInputConnection(line_source.GetOutputPort())
                
                actor = vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(0.2, 0.2, 0.8)
                actor.GetProperty().SetLineWidth(2)
                
                self.renderer.AddActor(actor)
        
        # Render nodes as spheres
        for node in self.model.nodes:
            sphere_source = vtkSphereSource()
            sphere_source.SetCenter(node.x, node.y, node.z)
            sphere_source.SetRadius(0.05)
            
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(sphere_source.GetOutputPort())
            
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.8, 0.2, 0.2)
            
            self.renderer.AddActor(actor)
        
        # Render loads as arrows
        for load_case in self.model.load_cases:
            for load in load_case.loads:
                if isinstance(load, NodalForce):
                    node = next((n for n in self.model.nodes if n.id == load.node_id), None)
                    if node:
                        self.render_force_arrow(node, load.fx, load.fy, load.fz)
        
        self.renderer.ResetCamera()
        self.render_window.Render()
    
    def render_force_arrow(self, node: Node, fx: float, fy: float, fz: float):
        """Render a force arrow at a node."""
        import math
        
        magnitude = math.sqrt(fx**2 + fy**2 + fz**2)
        if magnitude < 1e-10:
            return
        
        # Normalize direction
        dx, dy, dz = fx/magnitude, fy/magnitude, fz/magnitude
        
        # Create arrow
        arrow_source = vtkArrowSource()
        arrow_source.SetTipLength(0.3)
        arrow_source.SetTipRadius(0.1)
        arrow_source.SetShaftRadius(0.05)
        
        # Transform arrow to correct position and orientation
        transform = vtkTransform()
        transform.Translate(node.x, node.y, node.z)
        
        # Simple scaling based on magnitude (clamped for visualization)
        scale = min(magnitude / 10.0, 2.0)  # Scale factor, max 2.0
        transform.Scale(scale * dx, scale * dy, scale * dz)
        
        arrow_mapper = vtkPolyDataMapper()
        arrow_mapper.SetInputConnection(arrow_source.GetOutputPort())
        arrow_mapper.SetTransform(transform)
        
        arrow_actor = vtkActor()
        arrow_actor.SetMapper(arrow_mapper)
        arrow_actor.GetProperty().SetColor(0.9, 0.5, 0.1)
        
        self.renderer.AddActor(arrow_actor)
    
    def create_sample_model(self):
        """Create a simple sample model for demonstration."""
        # Material (Steel)
        steel = Material(id=1, name="Steel", E=2.1e8, nu=0.3, density=7850.0)
        self.model.add_material(steel)
        
        # Section (Simple rectangular)
        section = Section(id=1, name="H200x100", A=0.0025, Iy=1.5e-5, Iz=3.0e-5, J=2.0e-6)
        self.model.add_section(section)
        
        # Nodes (simple portal frame)
        self.model.add_node(Node(id=1, x=0.0, y=0.0, z=0.0))
        self.model.add_node(Node(id=2, x=0.0, y=0.0, z=4.0))
        self.model.add_node(Node(id=3, x=5.0, y=0.0, z=4.0))
        self.model.add_node(Node(id=4, x=5.0, y=0.0, z=0.0))
        
        # Elements
        self.model.add_element(Element(id=1, start_node_id=1, end_node_id=2, material_id=1, section_id=1))
        self.model.add_element(Element(id=2, start_node_id=2, end_node_id=3, material_id=1, section_id=1))
        self.model.add_element(Element(id=3, start_node_id=3, end_node_id=4, material_id=1, section_id=1))
        
        # Boundary conditions (fixed supports)
        self.model.add_boundary_condition(BoundaryCondition(node_id=1, ux=True, uy=True, uz=True, rx=True, ry=True, rz=True))
        self.model.add_boundary_condition(BoundaryCondition(node_id=4, ux=True, uy=True, uz=True, rx=True, ry=True, rz=True))
        
        # Load case
        load_case = LoadCase(id=1, name="Dead Load")
        load_case.add_load(NodalForce(id=1, node_id=2, fx=0.0, fy=0.0, fz=-10.0))
        load_case.add_load(NodalForce(id=2, node_id=3, fx=0.0, fy=0.0, fz=-10.0))
        self.model.add_load_case(load_case)
        
        # Combination
        combo = LoadCombination(id=1, name="Ultimate")
        combo.add_factor(1, 1.35)
        self.model.add_combination(combo)
        
        self.update_tree_view()
        self.render_model()
        self.status_bar.showMessage("Sample model loaded")
    
    def new_project(self):
        """Create new project."""
        reply = QMessageBox.question(self, 'New Project', 
            'Clear current model?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.model = Model()
            self.update_tree_view()
            self.render_model()
            self.status_bar.showMessage("New project created")
    
    def open_project(self):
        """Open project from JSON file."""
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "JSON Files (*.json)")
        if filepath:
            try:
                self.model = Model.load_from_json(filepath)
                self.update_tree_view()
                self.render_model()
                self.status_bar.showMessage(f"Loaded: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load project: {str(e)}")
    
    def save_project(self):
        """Save project to JSON file."""
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "JSON Files (*.json)")
        if filepath:
            try:
                self.model.save_to_json(filepath)
                self.status_bar.showMessage(f"Saved: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save project: {str(e)}")
    
    def add_node_dialog(self):
        """Dialog to add a node."""
        QMessageBox.information(self, "Add Node", "Node dialog - To be implemented in next iteration")
    
    def add_element_dialog(self):
        """Dialog to add an element."""
        QMessageBox.information(self, "Add Element", "Element dialog - To be implemented in next iteration")
    
    def add_load_dialog(self):
        """Dialog to add a nodal force."""
        QMessageBox.information(self, "Add Load", "Load dialog - To be implemented in next iteration")
    
    def open_combinations_editor(self):
        """Open load combinations editor."""
        QMessageBox.information(self, "Load Combinations", 
            f"Current combinations: {len(self.model.combinations)}\n\n"
            "Full table editor - To be implemented in next iteration")
    
    def run_analysis(self):
        """Run structural analysis."""
        try:
            analyzer = FrameAnalyzer(self.model)
            results = analyzer.analyze()
            
            msg = (f"Analysis completed successfully!\n\n"
                   f"Nodes: {len(self.model.nodes)}\n"
                   f"Elements: {len(self.model.elements)}\n"
                   f"Max displacement: {max(abs(u) for u in results['displacements']):.6f} m")
            
            QMessageBox.information(self, "Analysis Results", msg)
            self.status_bar.showMessage("Analysis completed")
            
        except Exception as e:
            QMessageBox.critical(self, "Analysis Error", str(e))


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
