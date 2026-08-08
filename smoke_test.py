"""
smoke_test.py
─────────────
Quick interactive smoke test — run directly to verify the full pipeline
and inspect the output without needing pytest.

    python smoke_test.py
"""

import io
import zipfile

from exporter import export_maze_zip, get_zip_manifest
from maze.generator import generate_maze
from maze.solver import solve_maze


def main() -> None:
    print("=" * 60)
    print("  Puzzle Generator — Smoke Test")
    print("=" * 60)

    # ── 1. Generator ──────────────────────────────────────────────────────────
    print("\n[1] Generating 21×21 maze (seed=42)…")
    maze = generate_maze(size=21, seed=42)
    print(f"    Grid      : {maze.rows} × {maze.cols}")
    print(f"    Room cells: {maze.cell_count}")
    print(f"    Start     : {maze.start}")
    print(f"    End       : {maze.end}")

    # ── 2. Solver ─────────────────────────────────────────────────────────────
    print("\n[2] Solving with BFS…")
    path = solve_maze(maze)
    print(f"    Solution length : {len(path)} steps")
    print(f"    Path[0] (start) : {path[0]}")
    print(f"    Path[-1] (end)  : {path[-1]}")
    assert path[0] == maze.start, "Solution does not begin at start!"
    assert path[-1] == maze.end,  "Solution does not reach the end!"
    print("    ✓ Start and end verified.")

    # ── 3. Full export ────────────────────────────────────────────────────────
    print("\n[3] Running export_maze_zip (size=21, seed=42)…")
    zip_buf = export_maze_zip(size=21, seed=42, title="Smoke Test Maze")

    assert isinstance(zip_buf, io.BytesIO), "export_maze_zip did not return BytesIO"
    assert zip_buf.tell() == 0, "Buffer not seeked to position 0"
    magic = zip_buf.read(2)
    zip_buf.seek(0)
    assert magic == b"PK", f"Not a valid ZIP (magic={magic!r})"
    print("    ✓ Buffer is valid ZIP (PK magic bytes confirmed).")

    # ── 4. Inspect zip manifest ───────────────────────────────────────────────
    print("\n[4] Zip manifest:")
    manifest = get_zip_manifest(zip_buf)
    for entry in manifest:
        print(
            f"    {entry['filename']:<22} "
            f"raw={entry['file_size']:>8,} B  "
            f"compressed={entry['compress_size']:>8,} B  "
            f"ratio={entry['compress_ratio']}"
        )

    # ── 5. Verify PDF content inside zip ─────────────────────────────────────
    print("\n[5] Verifying PDF headers inside zip entries…")
    zip_buf.seek(0)
    with zipfile.ZipFile(zip_buf) as zf:
        for name in zf.namelist():
            data = zf.read(name)
            assert data[:4] == b"%PDF", f"{name} does not start with %PDF!"
            print(f"    ✓ {name} — starts with %PDF, {len(data):,} bytes")

    # ── 6. Larger maze ────────────────────────────────────────────────────────
    print("\n[6] Generating 41×41 maze (stress test)…")
    big_zip = export_maze_zip(size=41, seed=0)
    big_manifest = get_zip_manifest(big_zip)
    for entry in big_manifest:
        print(f"    {entry['filename']:<22} {entry['file_size']:>10,} B raw")

    print("\n" + "=" * 60)
    print("  All smoke tests passed ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
