#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
import json
import sys
from pathlib import Path

def is_pip_component(comp: dict) -> bool:
    name = comp.get("name", "").lower()
    purl = comp.get("purl", "").lower()
    return name == "pip" or purl.startswith("pkg:pypi/pip@")

def main(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))

    components = data.get("components", [])
    dependencies = data.get("dependencies", [])

    # Identify pip component bom-ref(s)
    pip_refs = {
        comp.get("bom-ref")
        for comp in components
        if is_pip_component(comp)
    }

    if not pip_refs:
        print("SBOM filter: no pip component found (nothing to do)")
        return 0

    # Filter components
    data["components"] = [
        comp for comp in components
        if comp.get("bom-ref") not in pip_refs
    ]

    # Filter dependencies
    filtered_deps = []
    for dep in dependencies:
        if dep.get("ref") in pip_refs:
            continue
        depends_on = dep.get("dependsOn", [])
        dep["dependsOn"] = [
            ref for ref in depends_on
            if ref not in pip_refs
        ]
        filtered_deps.append(dep)

    data["dependencies"] = filtered_deps

    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"SBOM filter: removed pip ({len(pip_refs)} component)")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: filter_sbom.py <sbom.cdx.json>")
        sys.exit(1)

    sys.exit(main(Path(sys.argv[1])))
