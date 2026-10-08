#!/usr/bin/env python3
"""Prepare the real FlowTrack results for the standalone project page."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

SITE = Path(__file__).resolve().parents[1]
NIPS = SITE.parent
PROJECT = NIPS.parent
WORKSPACE = PROJECT.parent
ASSETS = SITE / "assets"

# Each tuple identifies an existing FiVE-Bench edit, never a generated mockup.
SELECTION = [
    ("beach-zebra", "0081_A_horse", 1, "subject", "Horse", "Zebra", "A new subject. The same stride.", 1.2),
    ("gym-panda", "0042_gym-ball", 2, "creative", "Athlete", "Panda", "Carry the workout into a new character.", 1.6),
    ("playful-dog", "0078_A_cat", 1, "subject", "Cat", "Dog", "Keep the toy, the room, and the playful motion.", 0.5),
    ("yellow-santa", "0061_mbike-santa", 3, "color", "Red outfit", "Yellow outfit", "A local color edit in a moving scene.", 0.7),
    ("red-motorbike", "0038_motorbike", 3, "color", "Motorbike", "Red motorbike", "Change the color along the original ride.", 1.6),
    ("pink-butterfly", "0045_butterfly", 3, "color", "Blue butterfly", "Pink butterfly", "A small subject. A precise color change.", 1.6),
    ("plush-dog", "0089_A_dog", 4, "material", "Dog", "Plush dog", "A softer appearance by the same shoreline.", 0.5),
    ("coastal-jeep", "0096_A_car", 1, "subject", "Car", "Jeep", "Follow the source along a winding coast.", 1.6),
    ("bear-panda", "0009_bear", 1, "subject", "Bear", "Panda", "A new subject with the same movement.", 1.0),
    ("boat-yacht", "0058_boat", 1, "subject", "Fishing boat", "Yacht", "Change the vessel while preserving the wake.", 1.0),
    ("dog-rabbit", "0057_dog", 1, "subject", "Retriever", "Rabbit", "A complete subject change in a moving scene.", 1.0),
    ("swan-duck", "0094_A_swan", 1, "subject", "Swan", "Duck", "Preserve the water motion and reflections.", 1.0),
    ("bear-dinosaur", "0009_bear", 2, "creative", "Bear", "Dinosaur", "Push the subject into a new visual world.", 1.0),
    ("glider-dragon", "0006_paragliding", 2, "creative", "Paraglider", "Dragon", "Transform the airborne subject and keep its path.", 1.0),
    ("dog-robot", "0057_dog", 2, "creative", "Retriever", "Robotic dog", "A robotic redesign with the original motion.", 1.0),
    ("wooden-motorbike", "0038_motorbike", 4, "material", "Motorbike", "Wooden motorbike", "Change the material through a fast ride.", 1.0),
    ("helicopter-ufo", "0035_helicopter", 2, "creative", "Helicopter", "UFO", "A graphic transformation in an open sky.", 1.0),
    ("eagle-nest", "0097_A_bird", 1, "subject", "Bird", "Eagle", "A precise subject change while the nest building continues.", 1.0),
    ("pink-burnout", "0014_burnout", 3, "color", "Black car", "Pink car", "Change the car color through smoke and motion.", 1.0),
    ("yellow-golf", "0013_golf", 3, "color", "Black shirt", "Yellow shirt", "A local wardrobe color change on the move.", 1.0),
    ("pink-boat", "0058_boat", 3, "color", "White boat", "Pink boat", "Change the hull color while preserving the wake.", 1.0),
    ("blue-duck", "0071_mallard-water", 3, "color", "Mallard", "Blue mallard", "A precise color change on rippling water.", 1.0),
    ("red-dress", "0011_lucia", 3, "color", "Black dress", "Red dress", "Change the dress color while keeping the walk.", 1.0),
    ("wooden-bus", "0079_A_bus", 4, "material", "Bus", "Wooden bus", "A material change through a rainy night.", 1.0),
    ("carbon-drift", "0059_drift-straight", 4, "material", "Red sports car", "Carbon-fiber sports car", "A material change through a fast drift.", 1.0),
    ("dog-sunglasses", "0089_A_dog", 5, "addition", "Dog", "Add sunglasses", "Add a clear accessory without losing the pose.", 1.0),
    # Additional qualitative examples from Appendix E.2 of the paper.
    ("silver-jeep-turn", "0015_car-shadow", 1, "subject", "Silver car", "Silver jeep", "A precise vehicle change at an urban intersection.", 1.0),
    ("purple-bicycle", "0075_A_bicycle", 3, "color", "Bicycle", "Purple bicycle", "A local color edit through a steady street roll.", 1.0),
    ("bear-cap", "0009_bear", 5, "addition", "Bear", "Bear with cap", "Add a small accessory while preserving the walk.", 1.0),
    ("woman-to-man", "0011_lucia", 1, "subject", "Woman in black dress", "Man in black suit", "A full subject and outfit change along the same path.", 1.0),
    ("hawk-blue-bird", "0077_A_hawk", 1, "subject", "Hawk", "Blue bird", "A tracked aerial subject change over the canyon.", 1.0),
    ("pink-suv", "0069_car-turn", 3, "color", "Silver SUV", "Pink SUV", "A clean vehicle color change through the mountain turn.", 1.0),
    ("cow-horse", "0034_cows", 1, "subject", "Cow", "Horse", "A rural subject change with the same steady walk.", 1.0),
    ("boat-kayak", "0083_A_boat", 1, "subject", "Boat", "Kayak", "Change the vessel while preserving the calm river motion.", 1.0),
    ("roller-batman", "0024_hockey", 1, "creative", "Rollerblader", "Batman", "A character transformation through the same skating action.", 1.0),
    ("red-snowboarder", "0037_snowboard-sand", 3, "color", "Snowboarder", "Red snowboarder", "A local outfit edit through a long sand descent.", 1.0),
    ("fighter-helicopter", "0021_landing", 1, "subject", "Fighter jet", "Helicopter", "A tracked aircraft change on the carrier deck.", 1.0),
]


def probe(path):
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "format=duration,size:stream=width,height,r_frame_rate,nb_frames",
        "-of", "json", str(path),
    ])
    return json.loads(result)


def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def prepare_video(job, force=False):
    original, video, poster, poster_time = job
    video.parent.mkdir(parents=True, exist_ok=True)
    if force or not video.exists():
        # Keep original geometry, frames, and frame rate; only encode for delivery.
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(original),
             "-map", "0:v:0", "-an", "-c:v", "libx264", "-preset", "medium",
             "-crf", "22", "-threads", "2", "-pix_fmt", "yuv420p",
             "-movflags", "+faststart", str(video)])
    if force or not poster.exists():
        run(["ffmpeg", "-nostdin", "-v", "error", "-y",
             "-ss", str(poster_time), "-i", str(original),
             "-frames:v", "1", "-q:v", "3", str(poster)])
    return {"original": str(original.relative_to(WORKSPACE)),
            "web": str(video.relative_to(SITE)), "original_metadata": probe(original),
            "web_metadata": probe(video)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Re-encode existing assets.")
    options = parser.parse_args()
    ASSETS.mkdir(parents=True, exist_ok=True)
    # Keep the published bundle aligned with the curated positive-only selection.
    selected_ids = {row[0] for row in SELECTION}
    for folder in (ASSETS / "videos", ASSETS / "posters"):
        if folder.exists():
            for path in folder.iterdir():
                if path.is_file() and (path.stem.endswith("-baseline") or path.stem.rsplit("-", 1)[0] not in selected_ids):
                    path.unlink()
    prompts = {}
    data, jobs = [], []
    for slug, video_id, edit, category, before, after, note, poster_time in SELECTION:
        if edit not in prompts:
            path = WORKSPACE / "bench/FiVE-Bench/files" / (
                f"flowtrack_ablation_direct_execution_edit{edit}_existing.json")
            prompts[edit] = {item["id"]: item for item in json.loads(path.read_text())}
        prompt = prompts[edit][video_id]
        original_paths = {
            "source": PROJECT / "videos" / (video_id + ".mp4"),
            "ours": next((NIPS / "FlowTrack/FlowTrack" / f"edit{edit}" / video_id).glob("*.mp4")),
            
        }
        metadata = [probe(path) for path in original_paths.values()]
        shapes = {(m["streams"][0]["width"], m["streams"][0]["height"],
                   m["streams"][0]["r_frame_rate"], m["streams"][0].get("nb_frames"),
                   m["format"]["duration"]) for m in metadata}
        if len(shapes) != 1:
            raise ValueError(f"Unmatched source/result timing or geometry: {video_id}")
        width, height, fps, frames, duration = shapes.pop()
        case = dict(id=slug, videoId=video_id, editType=edit, category=category,
                    before=before, after=after, note=note or prompt["instruction"], width=width, height=height,
                    duration=float(duration), fps=fps, frames=int(frames),
                    instruction=prompt["instruction"], sourcePrompt=prompt["source_prompt"],
                    targetPrompt=prompt["target_prompt"], media={})
        for kind, path in original_paths.items():
            web = ASSETS / "videos" / (slug + "-" + kind + ".mp4")
            poster = ASSETS / "posters" / (slug + "-" + kind + ".jpg")
            poster.parent.mkdir(parents=True, exist_ok=True)
            case["media"][kind] = {"src": str(web.relative_to(SITE)),
                                   "poster": str(poster.relative_to(SITE))}
            jobs.append((path, web, poster, poster_time))
        data.append(case)

    with ThreadPoolExecutor(max_workers=3) as executor:
        provenance = list(executor.map(lambda job: prepare_video(job, options.force), jobs))
    (ASSETS / "cases.js").write_text(
        "// Prepared from matched FiVE-Bench source videos and actual method outputs.\n"
        "window.FLOWTRACK_CASES = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n")
    (ASSETS / "provenance.json").write_text(json.dumps(provenance, indent=2))
    shutil.copyfile(NIPS / "34925_FlowTrack_Controlling_Ed.pdf", ASSETS / "FlowTrack-paper.pdf")
    with zipfile.ZipFile(ASSETS / "FlowTrack-code.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((NIPS / "code").rglob("*")):
            if path.is_file() and not any(part in {".git", "__pycache__"} for part in path.parts):
                archive.write(path, "FlowTrack/" + str(path.relative_to(NIPS / "code")))
    total = sum(path.stat().st_size for path in (ASSETS / "videos").glob("*.mp4"))
    print(f"Prepared {len(data)} matched examples, {len(jobs)} videos, {total / 1024**2:.1f} MiB of video.")


if __name__ == "__main__":
    main()
