from pathlib import Path


SOURCE_FILE = Path(
    r"D:\shesh_cam\DSCN8184.JPG"
)

OUTPUT_DIRECTORY = Path(
    "temp/uploads"
)


def create_fragments():

    if not SOURCE_FILE.exists():

        print(
            f"ERROR: Source file not found:"
        )

        print(
            SOURCE_FILE
        )

        return

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    # Remove old test fragments
    for old_file in OUTPUT_DIRECTORY.glob(
        "DSCN8184_part*.bin"
    ):

        old_file.unlink()

    # Read original JPEG
    with open(
        SOURCE_FILE,
        "rb"
    ) as file:

        data = file.read()

    total_size = len(data)

    print(
        f"Original file: {SOURCE_FILE}"
    )

    print(
        f"Original size: {total_size} bytes"
    )

    # Divide into 3 pieces
    part_size = total_size // 3

    part1 = data[
        0:part_size
    ]

    part2 = data[
        part_size:part_size * 2
    ]

    part3 = data[
        part_size * 2:
    ]

    fragments = {
        "DSCN8184_part1.bin": part1,
        "DSCN8184_part2.bin": part2,
        "DSCN8184_part3.bin": part3
    }

    for filename, content in fragments.items():

        output_path = (
            OUTPUT_DIRECTORY /
            filename
        )

        with open(
            output_path,
            "wb"
        ) as file:

            file.write(content)

        print(
            f"Created: {filename} "
            f"({len(content)} bytes)"
        )

    print()
    print(
        "Fragment creation completed."
    )


if __name__ == "__main__":

    create_fragments()