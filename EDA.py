import os
import random
import warnings
from pathlib import Path
from collections import Counter

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import cv2
from tqdm import tqdm


warnings.filterwarnings("ignore")

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

DATA_PATH = "/kaggle/input/datasets/scientifictechz1253/disaster-management/Comprehensive Disaster Dataset(CDD)/CDD_Augmented"
OUTPUT_DIR = "/kaggle/working/pipeline_outputs"

IMG_SIZE = 224
EDA_SAMPLE = 500
VIS_PER_CLS = 3

os.makedirs(os.path.join(OUTPUT_DIR, "eda"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "preprocessing"), exist_ok=True)


def auto_find_data_path(root="/kaggle/input"):
    root = Path(root)
    keywords = {"damaged", "fire", "human", "land", "water", "non"}

    for path in sorted(root.rglob("*")):
        if not path.is_dir():
            continue

        try:
            subdirs = [d.name.lower() for d in path.iterdir() if d.is_dir()]
        except Exception:
            continue

        match_count = 0
        for name in subdirs:
            if any(k in name for k in keywords):
                match_count += 1

        if match_count >= 3:
            print(f"[INFO] dataset detected at: {path}")
            return str(path)

    return None


if not Path(DATA_PATH).exists():
    print(f"[WARN] path not found: {DATA_PATH}")
    detected = auto_find_data_path()

    if detected:
        DATA_PATH = detected
    else:
        raise FileNotFoundError("Dataset not found. Please check input path.")

def collect_image_paths(base_path):
    base_path = Path(base_path)

    class_names = [
        d.name for d in base_path.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]
    class_names = sorted(class_names)

    print(f"\nClasses ({len(class_names)}): {class_names}")

    class_to_idx = {name: idx for idx, name in enumerate(class_names)}

    all_paths = []
    all_labels = []

    for cls_name in class_names:
        folder = base_path / cls_name

        files = []
        for p in folder.rglob("*"):
            if p.suffix.lower() in VALID_EXTENSIONS:
                files.append(p)

        for p in files:
            all_paths.append(str(p))
            all_labels.append(class_to_idx[cls_name])

    print(f"Total images found: {len(all_paths)}")

    return all_paths, all_labels, class_names, class_to_idx


paths, labels, class_names, class_to_idx = collect_image_paths(DATA_PATH)


print("\nClass distribution:")
counts = Counter(labels)
total = len(paths)

for i, name in enumerate(class_names):
    c = counts[i]
    print(f"{name:25s} -> {c:5d} ({(c/total)*100:.1f}%)")


fig, ax = plt.subplots(figsize=(10, 5))

values = [counts[i] for i in range(len(class_names))]
colors = plt.cm.Set2.colors[:len(class_names)]

bars = ax.bar(class_names, values, color=colors, edgecolor="black")

ax.bar_label(bars, fontsize=8)
ax.set_title("Class Distribution")
ax.set_xlabel("Class")
ax.set_ylabel("Count")

plt.xticks(rotation=30, ha="right")
plt.tight_layout()

plt.savefig(os.path.join(OUTPUT_DIR, "eda/1_class_distribution.png"), dpi=150)
plt.show()


sample_paths = random.sample(paths, min(EDA_SAMPLE, total))

widths, heights, ratios = [], [], []
bad_files = []

for p in tqdm(sample_paths, desc="Reading image sizes"):
    try:
        with Image.open(p) as img:
            w, h = img.size
            widths.append(w)
            heights.append(h)
            ratios.append(w / h)
    except Exception:
        bad_files.append(p)

print("\nSize stats:")
print(f"Width  -> min:{min(widths)}, max:{max(widths)}, avg:{int(np.mean(widths))}")
print(f"Height -> min:{min(heights)}, max:{max(heights)}, avg:{int(np.mean(heights))}")
print(f"Corrupt files: {len(bad_files)}")


fig, axes = plt.subplots(1, 3, figsize=(15, 4))

axes[0].hist(widths, bins=40, color="steelblue")
axes[0].set_title("Width")

axes[1].hist(heights, bins=40, color="tomato")
axes[1].set_title("Height")

axes[2].hist(ratios, bins=40, color="green")
axes[2].set_title("Aspect Ratio")

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "eda/2_size_distribution.png"), dpi=150)
plt.show()


class_map = {i: [] for i in range(len(class_names))}
for p, l in zip(paths, labels):
    class_map[l].append(p)


cols = 5
fig = plt.figure(figsize=(cols * 3, len(class_names) * 3))

for row_idx in range(len(class_names)):
    imgs = class_map[row_idx]
    chosen = random.sample(imgs, min(cols, len(imgs)))

    for col_idx, img_path in enumerate(chosen):
        ax = fig.add_subplot(len(class_names), cols, row_idx * cols + col_idx + 1)

        try:
            ax.imshow(Image.open(img_path).convert("RGB"))
        except Exception:
            ax.text(0.5, 0.5, "Error", ha="center")

        ax.axis("off")

        if col_idx == 0:
            ax.set_ylabel(class_names[row_idx], fontsize=8)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "eda/3_sample_grid.png"), dpi=120)
plt.show()


print("\nCalculating RGB averages...")

rgb_data = {i: [] for i in range(len(class_names))}

subset = random.sample(list(zip(paths, labels)), min(300, total))

for p, l in tqdm(subset):
    try:
        img = Image.open(p).convert("RGB").resize((64, 64))
        arr = np.array(img) / 255.0
        rgb_data[l].append(arr.mean(axis=(0, 1)))
    except Exception:
        pass


avg_rgb = {}
for i in rgb_data:
    if len(rgb_data[i]) > 0:
        avg_rgb[class_names[i]] = np.mean(rgb_data[i], axis=0)


fig, ax = plt.subplots(figsize=(10, 4))

names = list(avg_rgb.keys())
x = np.arange(len(names))
w = 0.25

ax.bar(x - w, [avg_rgb[n][0] for n in names], width=w, label="R", color="red", alpha=0.6)
ax.bar(x,     [avg_rgb[n][1] for n in names], width=w, label="G", color="green", alpha=0.6)
ax.bar(x + w, [avg_rgb[n][2] for n in names], width=w, label="B", color="blue", alpha=0.6)

ax.set_xticks(x)
ax.set_xticklabels(names, rotation=30)
ax.set_title("Mean RGB per Class")

ax.legend()
plt.tight_layout()

plt.savefig(os.path.join(OUTPUT_DIR, "eda/4_mean_rgb_per_class.png"), dpi=150)
plt.show()


print("\nAnalyzing brightness and sharpness...")

brightness = []
blur = []
labels_plot = []

subset = random.sample(list(zip(paths, labels)), min(400, total))

for p, l in tqdm(subset):
    try:
        gray = Image.open(p).convert("L").resize((128, 128))
        arr = np.array(gray)

        brightness.append(arr.mean())
        blur.append(cv2.Laplacian(arr, cv2.CV_64F).var())

        labels_plot.append(class_names[l])
    except Exception:
        pass


fig, ax = plt.subplots(1, 2, figsize=(14, 5))

sns.boxplot(x=labels_plot, y=brightness, ax=ax[0])
ax[0].set_title("Brightness")

sns.boxplot(x=labels_plot, y=blur, ax=ax[1])
ax[1].set_title("Sharpness")

for a in ax:
    a.tick_params(axis='x', rotation=30)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "eda/5_brightness_blur.png"), dpi=150)
plt.show()
