# 🧩 Puzzle Generator — All-in-One Printable & Interactive Puzzle Suite

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Build Status](https://img.shields.io/badge/Tests-Passing-brightgreen.svg?style=for-the-badge)](tests/)

A high-performance, full-stack web application for generating, previewing, and exporting printable puzzle books and activity sheets. Built with **Python (FastAPI)** and a modern **Glassmorphism web frontend**, it generates mazes, word searches, and crosswords with instant real-time web previews and exports print-ready vector PDFs (Puzzle + Answer Key) bundled into ZIP archives—**100% in-memory** with zero temporary disk clutter.

---

## ✨ Features

### 🌀 1. Maze Generator & Solver
- **Algorithmic Generation**: Depth-First Search (DFS) recursive backtracker algorithm for guaranteed perfect mazes (single path solution, zero loops/islands).
- **Automated Pathfinding**: Breadth-First Search (BFS) solver guarantees the true shortest path for answer key generation.
- **Multiple Shapes**: Standard **Rectangular**, **Circular**, and **Heart-shaped** maze grid geometries.
- **Customization**: Variable grid dimensions, random seeds for exact reproducibility, and customizable titles.

### 🔍 2. Word Search Generator
- **Flexible Grid Layouts**: Customizable row and column dimensions.
- **Multi-Directional Placement**: Supports Horizontal, Vertical, and Diagonal placements (forward & reverse).
- **Custom Word Lists**: Input custom words with automatic text normalization, deduplication, and collision detection.
- **Smart Grid Filling**: Automated letter distribution for optimal difficulty balance.

### ✏️ 3. Crossword Generator
- **Smart Intersection Engine**: Dynamic placement algorithm that maximizes word overlaps and grid compactness.
- **Automatic Clue Formatting**: Standardized Across and Down clue numbering with exact grid coordinate mapping.
- **Intelligent Grid Sizing**: Automatically calculates optimal bounding boxes for placed words.

### ⚡ 4. Real-Time Web Interactive Previews
- **Instant Visualization**: Powered by HTML5 Canvas and SVG. Preview grids directly in your browser before downloading.
- **Solution Toggling**: Interactively hide/show solution paths, word locations, and answer keys with a single click.

### 📄 5. Production-Ready Vector PDF & ZIP Exports
- **High-Resolution Vector Output**: Built using **ReportLab** for crisp line rendering at any print scale.
- **Dual PDF Bundles**: Automatically generates two separate PDFs—one for the **Puzzle** and one for the **Answer Key**.
- **In-Memory Streaming**: Generates and packages everything into a ZIP file in memory, delivering ultra-fast downloads without writing files to disk.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, ReportLab (PDF Engine)
- **Frontend**: Vanilla HTML5, CSS3 (Custom Glassmorphism UI, Responsive Design), Modern JavaScript (ES6+, Canvas API, SVG)
- **Testing**: Pytest, HTTPX, Automated End-to-End Smoke Tests

---

## 📁 Repository Structure

```text
Puzzle Generator/
├── api/
│   ├── models.py           # Pydantic request/response schemas
│   └── routes.py           # FastAPI endpoints for preview & PDF streaming
├── maze/
│   ├── generator.py        # DFS maze algorithm & shape generators
│   └── solver.py           # BFS shortest-path maze solver
├── wordsearch/
│   ├── generator.py        # Word search placement engine & filler logic
│   └── exporter.py         # ReportLab PDF renderer for word searches
├── crossword/
│   ├── generator.py        # Crossword placement & clue mapping engine
│   └── exporter.py         # ReportLab PDF renderer for crosswords
├── pdf/
│   └── canvas.py           # Shared PDF canvas formatting & page layouts
├── frontend/
│   ├── index.html          # Single Page Application HTML shell
│   └── static/             # CSS styles, JS preview logic, and web assets
├── tests/                  # Unit and integration test suite
├── exporter.py             # Maze PDF & ZIP generation pipeline
├── server.py               # FastAPI application entry-point
├── smoke_test.py           # Automated smoke test suite
├── start.sh                # One-click startup script (macOS / Linux)
├── start.bat               # One-click startup script (Windows)
└── requirements.txt        # Python package dependencies
```

---

## 🚀 Quick Start

### Option 1: One-Click Startup (Recommended)

#### **macOS / Linux**:
```bash
chmod +x start.sh
./start.sh
```

#### **Windows**:
Double-click `start.bat` or run in Command Prompt:
```cmd
start.bat
```

The script automatically detects Python, installs required dependencies, and launches the web app at **`http://localhost:8000`**.

---

### Option 2: Manual Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/puzzle-generator.git
   cd puzzle-generator
   ```

2. **Create a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Server**:
   ```bash
   python server.py
   ```
   *Alternatively, using uvicorn directly:*
   ```bash
   uvicorn server:app --reload --port 8000
   ```

5. **Open in Browser**:
   Navigate to **`http://localhost:8000`** in your web browser.

---

## 📡 API Reference & Documentation

FastAPI automatically serves interactive API documentation:

- **Swagger UI**: [`http://localhost:8000/api/docs`](http://localhost:8000/api/docs)
- **ReDoc**: [`http://localhost:8000/api/redoc`](http://localhost:8000/api/redoc)

### Primary API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/preview/maze` | Returns maze JSON grid & solution path for web preview |
| `POST` | `/api/generate` | Streams ZIP containing vector maze puzzle & answer PDFs |
| `POST` | `/api/preview/wordsearch` | Returns word search JSON grid & placements for web preview |
| `POST` | `/api/generate/wordsearch` | Streams ZIP containing word search puzzle & answer PDFs |
| `POST` | `/api/preview/crossword` | Returns crossword JSON grid, clue numbers & layout for web preview |
| `POST` | `/api/generate/crossword` | Streams ZIP containing crossword puzzle & answer PDFs |
| `GET` | `/api/health` | Service health & liveness status |

---

## 🧪 Running Tests

To run the automated test suite:

```bash
# Run pytest unit tests
pytest

# Run end-to-end smoke test
python smoke_test.py
```

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve the puzzle generation algorithms, add new puzzle types (e.g. Sudoku, Kakuro), or enhance the web frontend:

1. Fork the project repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
