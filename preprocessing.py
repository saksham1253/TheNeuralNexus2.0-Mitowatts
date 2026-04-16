
def resize_with_padding(img, target_size=(224, 224), pad_color=(0, 0, 0)):
    h, w = img.shape[:2]
    th, tw = target_size

    scale = min(tw / w, th / h)

    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    pad_top = (th - new_h) // 2
    pad_bottom = th - new_h - pad_top

    pad_left = (tw - new_w) // 2
    pad_right = tw - new_w - pad_left

    img_out = cv2.copyMakeBorder(
        resized,
        pad_top, pad_bottom,
        pad_left, pad_right,
        cv2.BORDER_CONSTANT,
        value=pad_color
    )

    return img_out


def preprocess_image(path, target_size=(224, 224)):
    try:
        img = Image.open(path).convert("RGB")
        img = np.array(img)

        img = resize_with_padding(img, target_size)

        img = cv2.fastNlMeansDenoisingColored(
            img, None, 10, 10, 7, 21
        )

        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)

        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        lab = cv2.merge((l, a, b))
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

        img = img.astype(np.float32) / 255.0

        return img

    except Exception:
        return None


print("\nChecking preprocessing output visually...")

rows = len(class_names) * VIS_PER_CLS
fig, axes = plt.subplots(rows, 2, figsize=(8, rows * 2.5))

fig.suptitle("Before vs After", fontsize=14)

r = 0

for i, name in enumerate(class_names):

    choices = class_path_map[i]
    samples = random.sample(choices, min(VIS_PER_CLS, len(choices)))

    for p in samples:
        try:
            original = np.array(Image.open(p).convert("RGB"))
            processed = preprocess_image(p, (IMG_SIZE, IMG_SIZE))

            axes[r, 0].imshow(original)
            axes[r, 0].set_title(f"{name}\n{original.shape[1]}x{original.shape[0]}", fontsize=7)
            axes[r, 0].axis("off")

            if processed is not None:
                axes[r, 1].imshow(processed)
                axes[r, 1].set_title(f"{IMG_SIZE}x{IMG_SIZE}", fontsize=7)

            axes[r, 1].axis("off")

        except Exception:
            axes[r, 0].axis("off")
            axes[r, 1].axis("off")

        r += 1

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/preprocessing/before_after.png", dpi=120)
plt.show()


print(f"\nRunning preprocessing on {len(paths)} images...")

processed_imgs = []
processed_lbls = []
bad_files = []

for p, lbl in tqdm(zip(paths, labels), total=len(paths)):

    img = preprocess_image(p, (IMG_SIZE, IMG_SIZE))

    if img is None:
        bad_files.append(p)
        continue

    processed_imgs.append(img)
    processed_lbls.append(lbl)

print("\nGetting normalization values...")

if len(processed_imgs) > 0:
    sample_n = min(200, len(processed_imgs))
    subset = random.sample(processed_imgs, sample_n)

    data = np.stack(subset)

    mean_val = data.mean(axis=(0, 1, 2))
    std_val = data.std(axis=(0, 1, 2))

    print("Mean:", mean_val.round(4))
    print("Std :", std_val.round(4))

    print("\nUse these values:")
    print("mean =", mean_val.tolist())
    print("std  =", std_val.tolist())


    stats_file = f"{OUTPUT_DIR}/preprocessing/normalization_stats.txt"

    with open(stats_file, "w") as f:
        f.write(f"mean = {mean_val.tolist()}\n")
        f.write(f"std  = {std_val.tolist()}\n")

    print("Stats saved at:", stats_file)

print("\nSaving processed data...")

np.save(
    f"{OUTPUT_DIR}/preprocessing/images.npy",
    np.array(processed_imgs, dtype=np.float32)
)

np.save(
    f"{OUTPUT_DIR}/preprocessing/labels.npy",
    np.array(processed_lbls)
)

print("Done.")
