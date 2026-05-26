import os
import random
import numpy as np
from tqdm import tqdm
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, transforms
from PIL import Image
# 补全缺失的导入（关键修复）
from sklearn.model_selection import train_test_split

# ===================== 1. 配置参数 =====================
DATA_ROOT = "数据集"
EPOCHS = 25  # 定制CNN训练轮数稍多，充分收敛
BATCH_SIZE = 32
LR = 0.001
IMG_SIZE = 224
NUM_CLASSES = 40
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

BASE_SAVE_NAME = "coin_cnn_model_40class.pth"


# 自动处理重复保存名
def get_unique_save_path(base_path):
    if not os.path.exists(base_path):
        return base_path
    idx = 1
    while True:
        new_path = base_path.replace(".pth", f"_{idx}.pth")
        if not os.path.exists(new_path):
            return new_path
        idx += 1


SAVE_PATH = get_unique_save_path(BASE_SAVE_NAME)
print(f"模型将保存到：{os.path.abspath(SAVE_PATH)}")


# ===================== 2. 定制CNN模型 =====================
class CoinCNN(nn.Module):
    def __init__(self, num_classes=40):
        super(CoinCNN, self).__init__()
        # 特征提取部分（4层卷积+池化）
        self.features = nn.Sequential(
            # 卷积层1：提取边缘特征
            nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 输出：112×112×32

            # 卷积层2：提取纹理特征
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 输出：56×56×64

            # 卷积层3：提取高阶特征
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 输出：28×28×128

            # 卷积层4：强化细节区分
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 输出：14×14×256
        )

        # 分类部分（全局平均池化+Dropout+全连接）
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),  # 输出：1×1×256
            nn.Flatten(),
            nn.Dropout(0.5),  # 防过拟合
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


# 初始化模型
model = CoinCNN(num_classes=NUM_CLASSES).to(DEVICE)

# ===================== 3. 数据预处理（强化钱币特征） =====================
train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomRotation(8),  # 贴合钱币旋转特征
    transforms.RandomAffine(degrees=0, translate=(0.03, 0.03)),  # 轻微平移
    transforms.ColorJitter(brightness=0.15, contrast=0.15),  # 模拟光照变化
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# 加载数据集并划分
full_dataset = datasets.ImageFolder(root=DATA_ROOT, transform=train_transform)
train_idx, val_idx = train_test_split(
    np.arange(len(full_dataset)),
    test_size=0.2,
    random_state=42,
    stratify=full_dataset.targets
)
train_dataset = torch.utils.data.Subset(full_dataset, train_idx)
val_dataset = torch.utils.data.Subset(full_dataset, val_idx)
val_dataset.dataset.transform = val_transform

# 加权采样解决数据不均衡
train_targets = [full_dataset.targets[i] for i in train_idx]
class_counts = np.bincount(train_targets)
class_weights = 1.0 / class_counts
sample_weights = class_weights[train_targets]
sampler = WeightedRandomSampler(
    weights=sample_weights,
    num_samples=len(sample_weights),
    replacement=True
)

# 数据加载器
train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    sampler=sampler,
    num_workers=0 if os.name == 'nt' else 4,
    pin_memory=True
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0 if os.name == 'nt' else 4,
    pin_memory=True
)

# ===================== 4. 训练配置 =====================
# 带类别权重的损失函数
class_weights_tensor = torch.tensor(class_weights, dtype=torch.float32).to(DEVICE)
criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
# AdamW优化器+余弦退火调度器
optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-6)


# ===================== 5. 训练与验证函数 =====================
def train_one_epoch(model, loader, criterion, optimizer, epoch):
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
    return train_loss, train_acc


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


# ===================== 6. 开始训练 =====================
best_val_acc = 0.0
patience = 4  # 定制CNN收敛稍慢，耐心值设4
patience_counter = 0

for epoch in range(EPOCHS):
    train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, epoch)
    val_loss, val_acc = validate(model, val_loader, criterion)
    scheduler.step()

    print(f"\nEpoch {epoch + 1} Summary:")
    print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
    print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")

    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save({
            "model_state_dict": model.state_dict(),
            "class_to_idx": full_dataset.class_to_idx,
            "best_acc": best_val_acc
        }, SAVE_PATH)
        print(f"Save best model! Val Acc: {best_val_acc:.4f}, Path: {SAVE_PATH}")
        patience_counter = 0
    else:
        patience_counter += 1
        print(f"Patience counter: {patience_counter}/{patience}")
        if patience_counter >= patience:
            print("Early stopping! No improvement in validation accuracy.")
            break

print(f"\nTraining Finished! Best Val Acc: {best_val_acc:.4f}")
print(f"Final model saved to: {os.path.abspath(SAVE_PATH)}")