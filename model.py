import os
import random
import numpy as np
from tqdm import tqdm
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler, Dataset
from torchvision import datasets, transforms, models
from torchvision.models import ResNet18_Weights  # 新增：导入权重类
from sklearn.model_selection import train_test_split
from PIL import Image

# ===================== 1. 配置参数 =====================
DATA_ROOT = "数据集"
EPOCHS = 30
BATCH_SIZE = 16
LR = 0.0001
IMG_SIZE = 224
NUM_CLASSES = 40
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SAVE_PATH = "best_coin_model.pth"

# ===================== 2. 数据预处理 =====================
train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE + 20, IMG_SIZE + 20)),
    transforms.RandomCrop((IMG_SIZE, IMG_SIZE)),
    transforms.RandomRotation(degrees=180),
    transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

val_test_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])


class CoinDataset(Dataset):
    def __init__(self, root, transform=None):
        self.dataset = datasets.ImageFolder(root=root)
        self.transform = transform
        self.class_to_idx = self.dataset.class_to_idx
        self.idx_to_class = {v: k for k, v in self.class_to_idx.items()}

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        img, label = self.dataset[idx]
        if self.transform:
            img = self.transform(img)
        return img, label


full_dataset = CoinDataset(root=DATA_ROOT)
train_idx, temp_idx = train_test_split(
    np.arange(len(full_dataset)),
    test_size=0.3,
    random_state=42,
    stratify=[full_dataset.dataset.targets[i] for i in range(len(full_dataset))]
)
val_idx, test_idx = train_test_split(
    temp_idx,
    test_size=1 / 3,
    random_state=42,
    stratify=[full_dataset.dataset.targets[i] for i in temp_idx]
)

train_dataset = torch.utils.data.Subset(CoinDataset(DATA_ROOT, train_transform), train_idx)
val_dataset = torch.utils.data.Subset(CoinDataset(DATA_ROOT, val_test_transform), val_idx)
test_dataset = torch.utils.data.Subset(CoinDataset(DATA_ROOT, val_test_transform), test_idx)

# ===================== 3. 加权采样 =====================
train_targets = [full_dataset.dataset.targets[i] for i in train_idx]
class_counts = np.bincount(train_targets)
class_weights = 1.0 / (class_counts + 1e-6)
sample_weights = class_weights[train_targets]
sampler = WeightedRandomSampler(
    weights=sample_weights,
    num_samples=len(sample_weights),
    replacement=True
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    sampler=sampler,
    num_workers=0,
    pin_memory=True if DEVICE.type == "cuda" else False
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
    pin_memory=True if DEVICE.type == "cuda" else False
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
    pin_memory=True if DEVICE.type == "cuda" else False
)

# ===================== 4. 加载预训练模型（修复pretrained警告） =====================
model = models.resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)  # 修复此处
model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)
model = model.to(DEVICE)

# ===================== 5. 损失函数和优化器 =====================
class_weights_tensor = torch.tensor(class_weights, dtype=torch.float32).to(DEVICE)
criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
optimizer = optim.Adam(model.fc.parameters(), lr=LR)
# 修复：移除verbose参数
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=5)


# ===================== 6. 训练与验证函数 =====================
def train_one_epoch(model, loader, criterion, optimizer, epoch, unfreeze=False):
    if unfreeze and epoch == 5:
        for param in model.parameters():
            param.requires_grad = True
        optimizer = optim.Adam(model.parameters(), lr=LR / 10)
        print("Unfreeze all layers, fine-tuning with lr=1e-5")

    model.train()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    pbar = tqdm(loader, desc=f"Train Epoch {epoch + 1}/{EPOCHS}")
    for images, labels in pbar:
        images, labels = images.to(DEVICE), labels.to(DEVICE)

        outputs = model(images)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        total_correct += torch.sum(preds == labels.data)
        total_samples += images.size(0)

        pbar.set_postfix({
            "loss": total_loss / total_samples,
            "acc": total_correct.item() / total_samples
        })

    train_loss = total_loss / total_samples
    train_acc = total_correct.item() / total_samples
    return train_loss, train_acc, optimizer


def validate(model, loader, criterion):
    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    with torch.no_grad():
        pbar = tqdm(loader, desc="Validate")
        for images, labels in pbar:
            images, labels = images.to(DEVICE), labels.to(DEVICE)

            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            total_correct += torch.sum(preds == labels.data)
            total_samples += images.size(0)

            pbar.set_postfix({
                "loss": total_loss / total_samples,
                "acc": total_correct.item() / total_samples
            })

    val_loss = total_loss / total_samples
    val_acc = total_correct.item() / total_samples
    return val_loss, val_acc


def test_model(model, loader):
    model.eval()
    total_correct = 0
    total_samples = 0
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            total_correct += torch.sum(preds == labels.data)
            total_samples += images.size(0)
    test_acc = total_correct.item() / total_samples
    print(f"\nTest Accuracy: {test_acc:.4f}")
    return test_acc


# ===================== 7. 开始训练 =====================
best_val_acc = 0.0
patience = 8
patience_counter = 0

for epoch in range(EPOCHS):
    train_loss, train_acc, optimizer = train_one_epoch(model, train_loader, criterion, optimizer, epoch, unfreeze=True)
    val_loss, val_acc = validate(model, val_loader, criterion)
    scheduler.step(val_acc)

    print(f"\nEpoch {epoch + 1} Summary:")
    print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
    print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")

    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save({
            "model_state_dict": model.state_dict(),
            "class_to_idx": train_dataset.dataset.class_to_idx,
            "best_acc": best_val_acc,
            "epoch": epoch + 1
        }, SAVE_PATH)
        print(f"Save best model! Val Acc: {best_val_acc:.4f}")
        patience_counter = 0
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print(f"Early stopping at epoch {epoch + 1} (no improvement for {patience} epochs)")
            break

# ===================== 8. 测试评估 =====================
checkpoint = torch.load(SAVE_PATH)
model.load_state_dict(checkpoint["model_state_dict"])
test_acc = test_model(model, test_loader)

print(f"\nTraining Finished! Best Val Acc: {best_val_acc:.4f}, Test Acc: {test_acc:.4f}")
print(f"Model saved to: {SAVE_PATH}")
print(f"Class mapping saved in model checkpoint: {checkpoint['class_to_idx']}")