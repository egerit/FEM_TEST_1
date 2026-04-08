# SteelFrame3D - 3D Steel Frame Analysis Software

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup Virtual Environment (Recommended)

```bash
cd steel_frame_3d
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
# From the project root directory:
python steel_frame_3d/main.py

# Or as a module:
python -m steel_frame_3d.main
```

## Features (MVP v0.1.0)

### Core Functionality
- ✅ 3D frame modeling with nodes and beam elements
- ✅ Material and cross-section definitions
- ✅ Boundary conditions (fixed, pinned, custom supports)
- ✅ Nodal forces and moments
- ✅ Load cases and load combinations (table editor ready)
- ✅ Vector-based section orientation (Vx, Vy, Vz)
- ✅ Finite Element Analysis engine
- ✅ JSON project file format with versioning

### Visualization
- ✅ Interactive 3D viewer (VTK-based)
- ✅ Model tree navigation
- ✅ Force arrow visualization
- ✅ Real-time model rendering

### Units System
- Fixed SI units: Length [m], Force [kN], Stress [kPa], Mass [kg]

## Project Structure

```
steel_frame_3d/
├── core/               # Analysis engine
│   ├── __init__.py
│   └── analyzer.py     # FEM solver
├── data/               # Data models
│   ├── __init__.py
│   └── models.py       # Model classes
├── gui/                # User interface
│   ├── __init__.py
│   └── main_window.py  # Main application window
├── tests/              # Test suite
│   └── examples/       # Reference models
├── main.py             # Application entry point
└── requirements.txt    # Python dependencies
```

## Quick Start Example

1. Launch the application
2. A sample portal frame is loaded automatically
3. Navigate the model tree to see nodes, elements, supports, and loads
4. Rotate/zoom the 3D view using mouse controls
5. Click "Run Analysis" (F5) to perform structural analysis
6. View results in the popup dialog

## File Format

Projects are saved as JSON files with the following structure:
- `version`: File format version
- `units`: Unit system definition
- `materials`: Material properties
- `sections`: Cross-section properties  
- `nodes`: Node coordinates
- `elements`: Element connectivity and properties
- `boundary_conditions`: Support definitions
- `load_cases`: Load definitions
- `combinations`: Load combination factors

## Next Steps (Roadmap)

### Phase 2
- Full dialog editors for nodes, elements, and loads
- Basic model validation (duplicate nodes, missing supports)
- Results visualization (displacement shapes, force diagrams)

### Phase 3
- Distributed loads on elements
- Advanced result visualization
- Export reports

### Phase 4
- Standalone executable (PyInstaller)
- Automatic code compliance checks

## License

MIT License

## Support

For issues and feature requests, please refer to the project documentation.
