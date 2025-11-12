"""Small utility: convert a simple log/CSV with 8 columns into a WiGLE-style CSV.

Usage examples:
  python "log_csv copy.py" /path/to/file.log    # pass file on command line (can drag into terminal)
  python "log_csv copy.py"                     # interactive prompt

This file improves the original script by providing a clear CLI, validation and
an interactive prompt loop so users get helpful messages instead of a single
"drag or write file here" prompt.
"""

import argparse
import csv
import os
import sys
import textwrap
from typing import Optional


def _normalize_path(s: str) -> str:
    """Strip surrounding quotes and whitespace from a dragged/pasted path."""
    return s.strip().strip('"').strip("'")


def prompt_for_file() -> Optional[str]:
    """Interactively prompt the user until they provide a valid file or quit.

    Returns the validated path or None if the user quits.
    """
    while True:
        try:
            # simpler prompt to match original behaviour where users drag the file into the terminal
            s = input("Drag or write file here (or type 'q' to quit): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if not s:
            print("Please type a path or drag a file into the terminal. Type 'q' to quit.")
            continue

        if s.lower() in ("q", "quit", "exit"):
            return None

        p = _normalize_path(s)
        if os.path.isfile(p):
            return p
        print(f"❌ File not found: {p}\nPlease try again or type 'q' to quit.")


def convert_to_wigle_csv(file_path: str) -> Optional[str]:
    """Read the input file and write a WiGLE-style CSV next to it.

    Returns the output path on success, or None on failure.
    """
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(os.path.dirname(file_path), f"{base_name}.wigle.csv")

    try:
        total_bytes = None
        try:
            total_bytes = os.path.getsize(file_path)
        except Exception:
            total_bytes = None

        print(f"Starting conversion:\n  input: {file_path}\n  output: {output_file}")

        with open(file_path, "r", encoding="utf-8", errors="ignore") as infile, \
             open(output_file, "w", newline="", encoding="utf-8") as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            writer.writerow(["MAC", "SSID", "AuthMode", "FirstSeen", "Channel", "RSSI", "CurrentLatitude", "CurrentLongitude"])

            processed = 0
            last_printed_pct = -1.0
            # update every N rows to avoid too-frequent prints
            update_every = 500

            for row in reader:
                if len(row) < 8:
                    continue  # skip malformed lines
                mac, ssid, authmode, firstseen, channel, rssi, lat, lon = row[:8]
                writer.writerow([mac, ssid, authmode, firstseen, channel, rssi, lat, lon])
                processed += 1

                if processed % update_every == 0:
                    pct = 0.0
                    if total_bytes and total_bytes > 0:
                        try:
                            pct = min(100.0, infile.tell() / total_bytes * 100.0)
                        except Exception:
                            pct = 0.0

                    # only redraw when percent changed meaningfully to reduce flicker
                    if abs(pct - last_printed_pct) >= 0.1 or last_printed_pct < 0:
                        print(f"Processing... rows: {processed}  ({pct:.1f}% )", end="\r", flush=True)
                        last_printed_pct = pct

            # final flush line
            if total_bytes and total_bytes > 0:
                try:
                    final_pct = min(100.0, infile.tell() / total_bytes * 100.0)
                except Exception:
                    final_pct = 100.0
            else:
                final_pct = 100.0

            # clear the progress line and print final summary
            print(" " * 80, end="\r")
            print(f"Processed {processed} rows. ({final_pct:.1f}%)")

    except Exception as exc:
        print(f"❌ Error processing file: {exc}")
        return None

    return output_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a simple .log (CSV-like) file into a WiGLE-compatible CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """Examples:
  python "log_csv copy.py" /path/to/file.log
  python "log_csv copy.py"     # interactive prompt
"""),
    )

    parser.add_argument("file", nargs="?", help="path to .log file (you can drag file into the terminal)")
    args = parser.parse_args()

    file_path = args.file
    if file_path:
        file_path = _normalize_path(file_path)
        if not os.path.isfile(file_path):
            print(f"❌ File not found: {file_path}")
            return 2
    else:
        file_path = prompt_for_file()
        if not file_path:
            print("No file provided. Exiting.")
            return 0

    out = convert_to_wigle_csv(file_path)
    if out:
        print(f"✅ Done! WiGLE CSV saved as:\n{out}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
