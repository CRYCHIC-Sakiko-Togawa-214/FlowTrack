#!/usr/bin/env python3
"""Check local references and published data without downloading media or using npm."""
import argparse
from fractions import Fraction
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MEDIA = {".mp4", ".jpg", ".jpeg", ".png", ".webp", ".ttf", ".pdf", ".zip"}


class Checker:
    def __init__(self, root=ROOT, tracked_assets=False):
        self.root = root.resolve()
        self.tracked_assets = tracked_assets
        self.errors = []
        self.references = set()
        self.tracked = set(subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=self.root).decode().split("\0"))

    def require(self, condition, message):
        if not condition:
            self.errors.append(message)

    def reference(self, value, source="index.html", anchors=None):
        if not isinstance(value, str) or not value:
            self.require(False, f"{source}: empty asset reference")
            return
        url = urlsplit(value)
        if url.scheme or url.netloc:
            return  # Offline checks intentionally do not probe external services.
        if not url.path:
            if url.fragment and anchors is not None:
                self.require(unquote(url.fragment) in anchors,
                             f"{source}: unknown anchor #{url.fragment}")
            return
        path = (self.root / source).parent / unquote(url.path)
        path = path.resolve()
        try:
            relative = path.relative_to(self.root).as_posix()
        except ValueError:
            self.require(False, f"{source}: reference escapes repository: {value}")
            return
        self.references.add(relative)
        sparse_media = self.tracked_assets and path.suffix.lower() in MEDIA
        self.require(path.is_file() or (path.is_dir() and (path / "index.html").is_file())
                     or (sparse_media and relative in self.tracked),
                     f"{source}: missing local target {value}")
        if path.is_file() and not sparse_media:
            self.require(path.stat().st_size > 0, f"{source}: empty file {value}")

    def documents(self):
        parser = PageParser()
        parser.feed((self.root / "index.html").read_text(encoding="utf-8"))
        self.require(len(parser.ids) == len(set(parser.ids)), "index.html: duplicate element IDs")
        for target in parser.targets:
            self.reference(target, anchors=set(parser.ids))
        for path in self.root.rglob("*.css"):
            if ".git" in path.parts:
                continue
            for target in re.findall(r"url\(\s*['\"]?([^)'\"]+)", path.read_text(encoding="utf-8")):
                self.reference(target.strip(), path.relative_to(self.root).as_posix())
        for path in self.root.rglob("*.md"):
            if ".git" in path.parts:
                continue
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                self.reference(target.split()[0].strip("<>"), path.relative_to(self.root).as_posix())


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.targets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        for key in ("href", "src", "poster"):
            if attrs.get(key):
                self.targets.append(attrs[key])
        if tag == "meta" and attrs.get("property") == "og:image":
            self.targets.append(attrs["content"])


def json_assignment(path, variable):
    text = path.read_text(encoding="utf-8")
    marker = f"window.{variable} = "
    if marker not in text:
        raise ValueError(f"{path}: missing {marker}")
    return json.loads(text.split(marker, 1)[1].strip().removesuffix(";"))


def positive_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def unique(check, values, name):
    check.require(len(values) == len(set(values)), f"{name}: duplicate identifiers")


def validate_data(check):
    cases = json_assignment(check.root / "assets/cases.js", "FLOWTRACK_CASES")
    check.require(bool(cases), "cases: expected at least one example")
    unique(check, [case["id"] for case in cases], "cases")
    provenance = json.loads((check.root / "assets/provenance.json").read_text())
    unique(check, [item["web"] for item in provenance], "provenance")
    by_web = {item["web"]: item for item in provenance}
    def geometry(metadata):
        stream = metadata["streams"][0]
        return (stream["width"], stream["height"], Fraction(stream["r_frame_rate"]),
                int(stream["nb_frames"]), float(metadata["format"]["duration"]))
    for case in cases:
        name = case["id"]
        check.require(case["category"] in {"subject", "creative", "color", "material", "addition"},
                      f"{name}: unknown category")
        for key in ("width", "height", "duration", "frames"):
            check.require(positive_number(case[key]), f"{name}: invalid {key}")
        check.require(Fraction(case["fps"]) > 0, f"{name}: invalid fps")
        for key in ("instruction", "sourcePrompt", "targetPrompt"):
            check.require(isinstance(case[key], str) and bool(case[key].strip()), f"{name}: missing {key}")
        check.require(set(case["media"]) == {"source", "ours"}, f"{name}: expected source/ours pair")
        expected = (case["width"], case["height"], Fraction(case["fps"]), case["frames"], case["duration"])
        for kind, media in case["media"].items():
            check.reference(media["src"])
            check.reference(media["poster"])
            check.require(media["src"] in by_web, f"{name}/{kind}: missing provenance")
            if media["src"] not in by_web:
                continue
            record = by_web[media["src"]]
            original = geometry(record["original_metadata"])
            web = geometry(record["web_metadata"])
            check.require(original[:4] == web[:4] and abs(original[4] - web[4]) < 0.002,
                          f"{name}/{kind}: encoding changed geometry or timing")
            check.require(expected[:4] == web[:4] and abs(expected[4] - web[4]) < 0.002,
                          f"{name}/{kind}: case metadata differs from provenance")



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracked-assets", action="store_true",
                        help="Allow media omitted by sparse checkout if present in the Git index.")
    options = parser.parse_args()
    try:
        check = Checker(tracked_assets=options.tracked_assets)
        check.documents()
        validate_data(check)
    except (KeyError, TypeError, ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        return 1
    if check.errors:
        print("\n".join(f"ERROR: {error}" for error in check.errors), file=sys.stderr)
        return 1
    print(f"Validated data and {len(check.references)} local references"
          + (" (media checked against Git index)." if options.tracked_assets else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
