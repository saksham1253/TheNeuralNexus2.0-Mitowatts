import os
import random
import warnings
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter
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
IMG_SIZE   = 224  
EDA_SAMPLE = 500  
VIS_PER_CLS = 3  

os.makedirs(f"{OUTPUT_DIR}/eda",            exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/preprocessing",  exist_ok=True)

def auto_find_data_path(root="/kaggle/input"):
    keywords = {"damaged", "fire", "human", "land", "water", "non"}
    root = Path(root)
    for dirpath in sorted(root.rglob("*")):
        if dirpath.is_dir():
            subdirs = [d.name.lower() for d in dirpath.iterdir() if d.is_dir()]
            matches = sum(any(k in s for k in keywords) for s in subdirs)
            if matches >= 3:
                print(f"Auto-detected data path: {dirpath}")
                return str(dirpath)
    return None

if not Path(DATA_PATH).exists():
    print(f"Manual path not found: {DATA_PATH}")
    detected = auto_find_data_path()
    if detected:
        DATA_PATH = detected
    else:
        print("Could not find dataset")
        raise FileNotFoundError("Dataset not found.")


def collect_image_paths(data_path):
    data_path = Path(data_path)
    class_names = sorted([
        d.name for d in data_path.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])
    print(f"\nClasses found ({len(class_names)}): {class_names}")

    class_to_idx = {c: i for i, c in enumerate(class_names)}
    paths, labels = [], []
    for cls in class_names:
        imgs = [p for p in (data_path / cls).rglob("*") if p.suffix.lower() in VALID_EXTENSIONS]
        for p in imgs:
            paths.append(str(p))
            labels.append(class_to_idx[cls])

    print(f"Total images: {len(paths)}")
    return paths, labels, class_names, class_to_idx

paths, labels, class_names, class_to_idx = collect_image_paths(DATA_PATH)

counts = Counter(labels)
total  = len(paths)

print("\nClass Distribution")
for i, cls in enumerate(class_names):
    cnt = counts[i]
    print(f"   {cls:30s}: {cnt:5d}  ({cnt/total*100:.1f}%)")

fig, ax = plt.subplots(figsize=(10, 5))
cls_counts = [counts[i] for i in range(len(class_names))]
colors = plt.cm.Set2.colors[:len(class_names)]
bars = ax.bar(class_names, cls_counts, color=colors, edgecolor='black', linewidth=0.8)
ax.bar_label(bars, fmt='%d', padding=4, fontsize=9)
ax.set_title("Class Distribution", fontsize=14, fontweight='bold')
ax.set_xlabel("Class"); ax.set_ylabel("Count")
plt.xticks(rotation=30, ha='right')
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/eda/1_class_distribution.png", dpi=150)
plt.show()
print(f"Saved: {OUTPUT_DIR}/eda/1_class_distribution.png")

sample_paths = random.sample(paths, min(EDA_SAMPLE, total))
widths, heights, aspects, corrupt = [], [], [], []

for p in tqdm(sample_paths, desc="Reading sizes"):
    try:
        with Image.open(p) as img:
            w, h = img.size
            widths.append(w); heights.append(h); aspects.append(w / h)
    except Exception:
        corrupt.append(p)

print(f"Width→min:{min(widths)}  max:{max(widths)}  mean:{np.mean(widths):.0f}")
print(f"Height → min:{min(heights)}  max:{max(heights)}  mean:{np.mean(heights):.0f}")
print(f"Corrupt files found: {len(corrupt)}")

fig,axes=plt.subplots(1, 3, figsize=(15, 4))
axes[0].hist(widths,   bins=40, color='steelblue',     edgecolor='black')
axes[0].set_title("Width Distribution");  axes[0].set_xlabel("Width (px)")
axes[1].hist(heights,  bins=40, color='tomato',         edgecolor='black')
axes[1].set_title("Height Distribution"); axes[1].set_xlabel("Height (px)")
axes[2].hist(aspects,  bins=40, color='mediumseagreen', edgecolor='black')
axes[2].set_title("Aspect Ratio");        axes[2].set_xlabel("W / H")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/eda/2_size_distribution.png", dpi=150)
plt.show()

class_path_map = {i: [] for i in range(len(class_names))}
for p, l in zip(paths, labels):
    class_path_map[l].append(p)

n_cols = 5
fig = plt.figure(figsize=(n_cols * 3, len(class_names) * 3))
fig.suptitle("Sample Images per Class", fontsize=15, fontweight='bold', y=1.005)

for row, cls_idx in enumerate(range(len(class_names))):
    chosen = random.sample(class_path_map[cls_idx], min(n_cols, len(class_path_map[cls_idx])))
    for col, img_path in enumerate(chosen):
        ax = fig.add_subplot(len(class_names), n_cols, row * n_cols + col + 1)
        try:
            ax.imshow(Image.open(img_path).convert("RGB"))
        except Exception:
            ax.text(0.5, 0.5, "Corrupt", ha='center', va='center', color='red')
        ax.axis("off")
        if col == 0:
            ax.set_ylabel(class_names[cls_idx], fontsize=8, rotation=90, labelpad=5)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/eda/3_sample_grid.png", dpi=120, bbox_inches='tight')
plt.show()
print("\nComputing mean RGB per class...")
class_rgb = {i: [] for i in range(len(class_names))}
for p, l in tqdm(random.sample(list(zip(paths, labels)), min(300, total)), desc="RGB"):
    try:
        arr = np.array(Image.open(p).convert("RGB").resize((64, 64))) / 255.0
        class_rgb[l].append(arr.mean(axis=(0, 1)))
    except Exception:
        pass

mean_rgbs = {class_names[i]: np.mean(class_rgb[i], axis=0) for i in range(len(class_names)) if class_rgb[i]}
fig, ax = plt.subplots(figsize=(10, 4))
x = np.arange(len(mean_rgbs)); w = 0.25
names = list(mean_rgbs.keys())
ax.bar(x - w, [mean_rgbs[n][0] for n in names], width=w, label='R', color='red',   alpha=0.7)
ax.bar(x,     [mean_rgbs[n][1] for n in names], width=w, label='G', color='green', alpha=0.7)
ax.bar(x + w, [mean_rgbs[n][2] for n in names], width=w, label='B', color='blue',  alpha=0.7)
ax.set_xticks(x); ax.set_xticklabels(names, rotation=30, ha='right')
ax.set_title("Mean RGB per Class", fontsize=13, fontweight='bold')
ax.set_ylabel("Mean Pixel (0–1)"); ax.legend()
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/eda/4_mean_rgb_per_class.png", dpi=150)
plt.show()

print("\nBrightness & Blur analysis...")
brightness_list, blur_list, labels_plot = [], [], []
for p, l in tqdm(random.sample(list(zip(paths, labels)), min(400, total)), desc="Brightness/Blur"):
    try:
        arr = np.array(Image.open(p).convert("L").resize((128, 128)))
        brightness_list.append(arr.mean())
        blur_list.append(cv2.Laplacian(arr, cv2.CV_64F).var())
        labels_plot.append(class_names[l])
    except Exception:
        pass

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.boxplot(x=labels_plot, y=brightness_list, ax=axes[0], palette="Set2")
axes[0].set_title("Brightness per Class", fontweight='bold')
axes[0].set_xlabel("Class"); axes[0].set_ylabel("Mean Pixel Intensity")
axes[0].tick_params(axis='x', rotation=30)

sns.boxplot(x=labels_plot, y=blur_list, ax=axes[1], palette="Set3")
axes[1].set_title("Sharpness (Laplacian Variance)", fontweight='bold')
axes[1].set_xlabel("Class"); axes[1].set_ylabel("Laplacian Variance")
axes[1].tick_params(axis='x', rotation=30)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/eda/5_brightness_blur.png", dpi=150)
plt.show()

