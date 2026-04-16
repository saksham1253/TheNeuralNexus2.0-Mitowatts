class HybridClassifier(nn.Module):
    def __init__(self, n_classes):
        super(HybridClassifier, self).__init__()

        self.cnn_backbone = timm.create_model(
            "efficientnet_b5",
            pretrained=True,
            num_classes=0
        )

        self.transformer_backbone = timm.create_model(
            "vit_base_patch16_224",
            pretrained=True,
            num_classes=0
        )

        combined_features = (
            self.cnn_backbone.num_features +
            self.transformer_backbone.num_features
        )

        self.classifier = nn.Linear(combined_features, n_classes)

    def forward(self, x):
        cnn_features = self.cnn_backbone(x)
        vit_features = self.transformer_backbone(x)

        merged = torch.cat((cnn_features, vit_features), dim=1)
        output = self.classifier(merged)

        return output
model = HybridClassifier(len(CLASS_NAMES)).to(DEVICE)
print("Model initialized successfully.")


loss_fn = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LR)


def train_one_epoch(data_loader):
    model.train()
    running_loss = 0.0

    for batch_images, batch_labels in data_loader:
        batch_images = batch_images.to(DEVICE)
        batch_labels = batch_labels.to(DEVICE)

        outputs = model(batch_images)
        loss = loss_fn(outputs, batch_labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    avg_loss = running_loss / len(data_loader)
    return avg_loss



print("\nStarting training...\n")

for epoch_idx in range(EPOCHS):
    epoch_loss = train_one_epoch(train_dl)

    print(f"Epoch {epoch_idx + 1}/{EPOCHS} | Loss: {epoch_loss:.4f}")



print("\nRunning evaluation on test set...\n")

model.eval()
predictions = []
ground_truths = []

with torch.no_grad():
    for batch_images, batch_labels in test_dl:
        batch_images = batch_images.to(DEVICE)

        logits = model(batch_images)
        predicted_classes = torch.argmax(logits, dim=1).cpu().numpy()

        predictions.extend(predicted_classes)
        ground_truths.extend(batch_labels.numpy())



print("\nDetailed Classification Report:\n")
print(classification_report(
    ground_truths,
    predictions,
    target_names=CLASS_NAMES
))


conf_matrix = confusion_matrix(ground_truths, predictions)

plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap="Blues")
plt.title("Confusion Matrix")
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.tight_layout()
plt.show()
