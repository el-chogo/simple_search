import dataclasses
import enum
import os
import re
import sys
import typing

import click
import parso


class Mode(enum.Enum):
    SOURCE_FILE = 1
    DIRECTORIES = 2


@dataclasses.dataclass
class Options:
    includes: typing.List[str]
    max_distance: int


def search(content: str, node, options: Options, classname: str = ""):
    results: typing.List[str] = []

    for child in node.children:
        if (
            isinstance(
                child, (parso.python.tree.Class, parso.python.tree.PythonNode)
            )
        ):
            if isinstance(child, (parso.python.tree.Class)):
                results += search(content, child, options, child.name.value)
            else:
                results += search(content, child, options, classname)

        elif isinstance(child, parso.python.tree.Function):
            code: str = child.get_code()
            lines: typing.List[str] = code.split("\n")
            first_line: str = ""

            include_hits: int = 0

            needles = options.includes[:]

            distance = 0

            max_distance: bool = options.max_distance > 0

            for line in lines:
                # if max distance reached clear the counters
                if max_distance and distance >= options.max_distance:
                    distance = 0
                    needles = options.includes[:]
                    include_hits = 0

                # second hit reached
                if max_distance and include_hits >= 1:
                    distance += 1

                if line and not first_line:
                    first_line = line

                for needle in options.includes:
                    if needle in needles and needle.search(line):
                        include_hits += 1
                        needles.remove(needle)

            if include_hits == len(options.includes):
                results.append(
                    (classname, first_line.strip(), child.start_pos[0], child.end_pos[0])
                )

    return results


def file_results(file_path: str, options: Options) -> str:
    content: str

    with open(file_path, "r") as f:
        content = f.read()

    tree = parso.parse(content)

    results = search(content, tree, options)

    for classname, line, start, _ in results:
        yield f"{file_path}@{start} [{classname}]: {line}"


def walk_directories(
    directories: typing.List[str],
    filepath_exclude: str,
    filepath_only: str,
) -> str:
    excludes: typing.List[re.Pattern] = []
    only: typing.List[re.Pattern] = []

    if filepath_exclude:
        excludes = [re.compile(exclude) for exclude in filepath_exclude.split(",")]

    if filepath_only:
        only = [re.compile(o) for o in filepath_only.split(",")]

    for directory in directories:
        for root, _, files in os.walk(directory):
            for f in files:
                skip: bool = False
                skip_only: bool = False

                if only:
                    skip_only = True

                if f.endswith(".py"):
                    filepath: str = os.path.join(root, f)

                    for exclude in excludes:
                        if exclude.search(filepath):
                            skip = True
                            break

                    for o in only:
                        if o.search(filepath):
                            skip_only = False
                            break

                    if skip or skip_only:
                        continue

                    yield filepath


@click.command()
@click.option("--source-file", help="Source file to search")
@click.option("--includes", help="Words to include")
@click.option("--max-distance", default=-1, help="Max distance between words")
@click.option("--directories", default="", help="Directories to include in the search")
@click.option("--filepath-exclude", default="", help="Filepaths to exclude")
@click.option("--filepath-only", default="", help="Only search these filepaths")
def main(
    source_file: str,
    includes: str,
    max_distance: int,
    directories: str,
    filepath_exclude: str,
    filepath_only: str,
):
    mode: Mode = Mode.SOURCE_FILE

    regexes = [re.compile(regex) for regex in includes.split(",")]
    options: Options = Options(
        includes=regexes, max_distance=max_distance
    )

    if directories:
        mode = mode.DIRECTORIES

    source_files: List[str]

    if mode == mode.DIRECTORIES:
        directories = directories.split(",")
        source_files = walk_directories(
            directories,
            filepath_exclude,
            filepath_only,
        )
    else:
        source_files = [source_file]

    for source_file in source_files:
        for result in file_results(source_file, options):
            print(result)


if __name__ == "__main__":
    main()
