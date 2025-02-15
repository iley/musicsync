#!/usr/bin/env python3
import argparse
import logging
import os
import os.path
import subprocess


logger = logging.getLogger()


def main() -> None:
    parser = argparse.ArgumentParser("musicsync")

    parser.add_argument("source",  help="source directory")
    parser.add_argument("destination",  help="destination directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose logging")
    parser.add_argument("-d", "--dry-run", action="store_true", help="dry-run mode")

    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)

    sync_files(args.source, args.destination, args.dry_run)


def sync_files(source_directory: str, destination_directory: str, dry_run=False) -> None:
    logger.info("Syncing %s -> %s", source_directory, destination_directory)

    input_files = [os.path.relpath(path, source_directory) for path in walk_directory(source_directory, ".flac")]
    output_files = [ replace_extension(path, ".mp3") for path in input_files ]
    existing_output_files = [os.path.relpath(path, destination_directory) for path in walk_directory(destination_directory, ".mp3")]

    missing_output_files = sorted(set(output_files) - set(existing_output_files))

    print("Input FLAC files: %d, existing MP3 files: %d. Will convert %d files." %
          (len(input_files), len(existing_output_files), len(missing_output_files)))

    converted = 0

    for relative_path in missing_output_files:
        source_path = os.path.join(source_directory, replace_extension(relative_path, ".flac"))
        destination_path = os.path.join(destination_directory, relative_path)
        print("%s -> %s" % (source_path, destination_path))
        if dry_run:
            continue
        success = convert_file(source_path, destination_path)
        if success:
            converted += 1
        else:
            print("Failed to convert %s. Stopping" % source_path)
            break

    if converted > 0:
        print("Successfully converted %d files" % converted)
    else:
        print("Failed to convert any files")


def replace_extension(path: str, new_extension: str) -> str:
    name_without_ext, _ = os.path.splitext(path)
    return name_without_ext + new_extension


def walk_directory(directory: str, extension: str) -> list[str]:
    matching_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                matching_files.append(os.path.join(root, file))
    return matching_files


def convert_file(source_path: str, destination_path: str) -> bool:
    ensure_parent_directory(destination_path)
    return run_command(["ffmpeg", "-i", source_path, "-c:a", "libmp3lame", "-qscale:a", "0", "-map_metadata", "0", destination_path])


def run_command(command: list[str]) -> bool:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        return True
    else:
        print("Error: command failed: %s" % (command,))
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        return False


def ensure_parent_directory(file_path: str):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)


if __name__ == '__main__':
    main()
