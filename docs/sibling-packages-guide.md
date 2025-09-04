# Sibling Package Imports in Python

This guide shows **all supported ways** to import between *sibling* packages (e.g., `conf/` and `exceptions/`) and how to run your code reliably.

---

## 0) Baseline layout
```
project_root/
├─ conf/
│  ├─ __init__.py
│  └─ module_a.py
└─ exceptions/
   ├─ __init__.py
   └─ errors.py
```
> Ensure each package has an `__init__.py` (unless using namespace packages).

---

## 1) Recommended: One top-level package + absolute imports
Create a single application package and place both under it:
```
project_root/
└─ myapp/
   ├─ __init__.py
   ├─ conf/
   │  ├─ __init__.py
   │  └─ module_a.py
   └─ exceptions/
      ├─ __init__.py
      └─ errors.py
```
**Import**
```python
# myapp/conf/module_a.py
from myapp.exceptions.errors import DataFetchError
```
**Run**
```bash
cd project_root
python -m myapp.conf.module_a
```
**Or install once and run anywhere**
```bash
pip install -e .
python -c "from myapp.exceptions.errors import DataFetchError; print('ok')"
```

---

## 2) Relative imports (same parent package)
When both packages live under the same parent (`myapp`), use relative imports:
```python
# myapp/conf/module_a.py
from ..exceptions.errors import DataFetchError
```
Run as a **package module** (not as a file):
```bash
python -m myapp.conf.module_a
```

---

## 3) Keep siblings without a common package (temporary)
If you must keep `conf/` and `exceptions/` directly under the project root, add the root to `PYTHONPATH`.

**macOS/Linux**
```bash
cd project_root
PYTHONPATH=. python -m conf.module_a
```

**Windows PowerShell**
```powershell
cd project_root
$env:PYTHONPATH = "."
python -m conf.module_a
```

**Windows cmd.exe**
```bat
cd project_root
set PYTHONPATH=.
python -m conf.module_a
```

---

## 4) As a last resort: tweak `sys.path`
```python
# conf/module_a.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from exceptions.errors import DataFetchError
```
This works but is **brittle**. Prefer options 1–3.

---

## 5) Packaging-based approach (recommended for teams/CI)
Add `pyproject.toml` (or `setup.py`) at the project root and install in editable mode.

**pyproject.toml (src-layout with modules)**
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "your-app"
version = "0.1.0"
requires-python = ">=3.8"

[tool.setuptools]
package-dir = {"" = "src"}

# If you have flat modules under src/ (not a package dir):
py-modules = ["conf.module_a", "exceptions.errors"]
```

Then:
```bash
pip install -e .
python -c "from exceptions.errors import DataFetchError; print('installed')"
```

---

## IDE tips
- **VS Code**: set `PYTHONPATH` in `.vscode/launch.json`:
  ```json
  {
    "configurations": [
      {
        "name": "Run module_a",
        "type": "python",
        "request": "launch",
        "module": "conf.module_a",
        "env": { "PYTHONPATH": "${workspaceFolder}" }
      }
    ]
  }
  ```
- **PyCharm**: mark `project_root` as **Sources Root** (adds to `sys.path`).

---

## Common gotchas
- Missing `__init__.py` prevents package recognition (unless using namespace packages).
- Running files directly (`python conf/module_a.py`) breaks relative imports. Use `python -m package.module`.
- After restructuring, re-install (or re-set `PYTHONPATH`) so imports resolve.

---

## Quick checklist
- [ ] Add `__init__.py` files.
- [ ] Choose one strategy (absolute, relative, or PYTHONPATH).
- [ ] Run with `python -m ...` from the project root.
- [ ] Consider packaging + `pip install -e .` for team environments.
