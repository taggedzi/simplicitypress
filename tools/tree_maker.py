# SPDX-License-Identifier: MIT
# Path: scripts/tree_maker.py
"""Print a tree of a project's files and directories, using a custom .treeignore style filter."""
from pathlib import Path
import argparse
import pathspec


def find_project_root(script_location: Path) -> Path:
    """Assumes the script is inside 'scripts/' and returns the project root."""
    return script_location.parent.parent.resolve()


def load_pathspec_file(file_path: Path) -> pathspec.PathSpec:
    """Load pathspec-compatible ignore rules from a file."""
    if not file_path.exists():
        return pathspec.PathSpec.from_lines('gitwildmatch', [])
    with file_path.open('r') as f:
        return pathspec.PathSpec.from_lines('gitwildmatch', f)


def should_ignore(path: Path, base_path: Path, ignore_spec: pathspec.PathSpec) -> bool:
    """Return True if path should be ignored."""
    relative = path.relative_to(base_path).as_posix()
    return ignore_spec.match_file(relative)


def print_tree(
    path: Path,
    prefix: str = '',
    base_path: Path = None,
    ignore_spec: pathspec.PathSpec = None) -> None:
    """
    Recursively print a visual tree of files and directories starting from the given path.

    Directories are printed with a trailing slash ('/'). Entries that match the ignore_spec
    (e.g., from a .treeignore file) are excluded from the output.

    Args:
        path (Path): The current directory or file path to start printing from.
        prefix (str, optional): The visual indentation prefix used to align tree branches.
        base_path (Path, optional): The root of the tree for computing relative ignore paths.
                                    Defaults to `path` on first call.
        ignore_spec (PathSpec, optional): A compiled PathSpec object used to filter out
                                          ignored files and folders. Can be empty.

    Returns:
        None: This function prints directly to stdout.
    """
    base_path = base_path or path
    ignore_spec = ignore_spec or pathspec.PathSpec.from_lines('gitwildmatch', [])

    entries = [
        p for p in sorted(path.iterdir())
        if not should_ignore(p, base_path, ignore_spec)
    ]

    for i, entry in enumerate(entries):
        connector = '└── ' if i == len(entries) - 1 else '├── '
        display_name = entry.name + '\\' if entry.is_dir() else entry.name
        print(prefix + connector + display_name)

        if entry.is_dir():
            extension = '    ' if i == len(entries) - 1 else '│   '
            print_tree(entry, prefix + extension, base_path, ignore_spec)



def main():
    """The main function to run the script."""
    script_location = Path(__file__).resolve()
    project_root = find_project_root(script_location)

    parser = argparse.ArgumentParser(description='Project Tree Viewer (respects .treeignore)')
    parser.add_argument('--treeignore', type=str, default='.treeignore',
                        help='Path to treeignore-style file (default: .treeignore)')
    args = parser.parse_args()

    treeignore_file = project_root / args.treeignore
    ignore_spec = load_pathspec_file(treeignore_file)

    print_tree(project_root, ignore_spec=ignore_spec)


if __name__ == '__main__':
    main()
