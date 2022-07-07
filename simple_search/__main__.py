import dataclasses
import re
import sys
import typing

import click
import parso


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


@click.command()
@click.option("--source-file", help="Source file to search")
@click.option("--includes", help="Words to include")
@click.option("--max-distance", default=-1, help="Max distance between words")
def main(source_file: str, includes: typing.List[str], max_distance: int):
    content: str

    with open(source_file, "r") as f:
        content = f.read()

    tree = parso.parse(content)
    regexes = [re.compile(regex) for regex in includes.split(",")]
    options: Options = Options(
        includes=regexes, max_distance=max_distance
    )

    results = search(content, tree, options)

    for classname, line, start, _ in results:
        print(f"{source_file}@{start} [{classname}]: {line}")


if __name__ == "__main__":
    main()
