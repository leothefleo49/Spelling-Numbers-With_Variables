"""Workspace cleanup helper
Removes __pycache__ directories and .pyc files under the repository root.
Run with the project's Python environment:

    & .venv\Scripts\python.exe scripts\clean_workspace.py
"""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(__file__))

def remove_pycache(root):
    removed = []
    for dirpath, dirnames, filenames in os.walk(root):
        if '__pycache__' in dirnames:
            path = os.path.join(dirpath, '__pycache__')
            try:
                shutil.rmtree(path)
                removed.append(path)
            except Exception as e:
                print(f"Failed to remove {path}: {e}")
    return removed

def remove_pyc(root):
    removed = []
    for dirpath, dirnames, filenames in os.walk(root):
        for f in filenames:
            if f.endswith('.pyc') or f.endswith('.pyo'):
                path = os.path.join(dirpath, f)
                try:
                    os.remove(path)
                    removed.append(path)
                except Exception as e:
                    print(f"Failed to remove {path}: {e}")
    return removed

if __name__ == '__main__':
    print(f"Cleaning workspace under {ROOT} ...")
    pyc_removed = remove_pyc(ROOT)
    pc_removed = remove_pycache(ROOT)
    print(f"Removed {len(pyc_removed)} .pyc files and {len(pc_removed)} __pycache__ directories.")
    if pyc_removed:
        for p in pyc_removed:
            print("  ", p)
    if pc_removed:
        for p in pc_removed:
            print("  ", p)
    print("Done.")
