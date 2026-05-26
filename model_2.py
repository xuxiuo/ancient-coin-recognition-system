import os
import random
import numpy as np
from tqdm import tqdm
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, transforms, models
from sklearn.model_selection import train_test_split
from PIL import Image

# ===================== 1. 配置参数 =====================
# 数据集根路径（train文件夹下是40个子文件夹）
DATA_ROOT = "数据集"
# 训练轮数
EPOCHS = 20
# 批次大小
BATCH_SIZE = 32
# 学习率
LR = 0.001
# 图片尺寸（ResNet要求的输入尺寸）
IMG_SIZE = 224
# 类别数（修改为40类）
NUM_CLASSES = 40
# 设备（自动使用GPU，没有则用CPU）
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# 模型保存路径
SAVE_PATH = "best_coin_model_2.pth"

# ===================== 2. 数据预处理与划分 =====================
# 定义数据增强（训练集增强，验证集仅基础变换）
train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomRotation(15),  # 随机旋转
    transforms.RandomHorizontalFlip(p=0.5),  # 随机水平翻转
    transforms.ColorJitter(brightness=0.2, contrast=0.2),  # 亮度/对比度调整
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],  # ImageNet预训练均值/方差
                         std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# 加载完整数据集并划分训练/验证集（8:2）
full_dataset = datasets.ImageFolder(root=DATA_ROOT, transform=train_transform)
# 按样本划分索引
train_idx, val_idx = train_test_split(
    np.arange(len(full_dataset)),
    test_size=0.2,
    random_state=42,
    stratify=full_dataset.targets  # 分层采样，保证类别分布一致
)

# 构建训练/验证数据集
train_dataset = torch.utils.data.Subset(full_dataset, train_idx)
val_dataset = torch.utils.data.Subset(full_dataset, val_idx)
# 替换验证集的transform（避免增强）
val_dataset.dataset.transform = val_transform

# ===================== 3. 加权采样（解决数据不均衡） =====================
# 统计训练集每个类别的样本数
train_targets = [full_dataset.targets[i] for i in train_idx]
class_counts = np.bincount(train_targets)
# 计算每个样本的权重（样本数越少，权重越高）
class_weights = 1.0 / class_counts
sample_weights = class_weights[train_targets]
# 构建加权采样器
sampler = WeightedRandomSampler(
    weights=sample_weights,
    num_samples=len(sample_weights),
    replacement=True  # 过采样少样本类别
)

# 构建数据加载器
train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    sampler=sampler,  # 使用加权采样
    num_workers=0 if os.name == 'nt' else 4,  # Windows下num_workers设0避免报错
    pin_memory=True  # GPU加速（新增）
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0 if os.name == 'nt' else 4,
    pin_memory=True  # GPU加速（新增）
)

# ===================== 4. 加载预训练模型（修复PyTorch新版本兼容） =====================
# 使用ResNet18（轻量，适合多类别分类）
model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)  # 新版写法，替代pretrained=True
# 修改最后一层，适配40个类别
model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)
model = model.to(DEVICE)

# ===================== 5. 定义损失函数和优化器 =====================
# 带类别权重的交叉熵损失（进一步解决不均衡）
class_weights_tensor = torch.tensor(class_weights, dtype=torch.float32).to(DEVICE)
criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
# 优化器
optimizer = optim.Adam(model.parameters(), lr=LR)
# 学习率调度器（训练后期降低学习率）
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)


# ===================== 6. 训练与验证函数 =====================
def train_one_epoch(model, loader, criterion, optimizer, epoch):
    model.train()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    pbar = tqdm(loader, desc=f"Train Epoch {epoch + 1}/{EPOCHS}")
    for images, labels in pbar:
        images, labels = images.to(DEVICE), labels.to(DEVICE)

        # 前向传播
        outputs = model(images)
        loss = criterion(outputs, labels)

        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # 统计指标
        total_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        total_correct += torch.sum(preds == labels.data)
        total_samples += images.size(0)

        # 更新进度条
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


# ===================== 7. 开始训练（新增早停机制） =====================
best_val_acc = 0.0  # 保存最优验证集准确率
patience = 3  # 连续3轮不提升则早停
patience_counter = 0

for epoch in range(EPOCHS):
    # 训练
    train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, epoch)
    # 验证
    val_loss, val_acc = validate(model, val_loader, criterion)
    # 学习率调度
    scheduler.step()

    # 打印本轮结果
    print(f"\nEpoch {epoch + 1} Summary:")
    print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
    print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")

    # 保存最优模型
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save({
            "model_state_dict": model.state_dict(),
            "class_to_idx": full_dataset.class_to_idx,  # 保存类别映射关系
            "best_acc": best_val_acc
        }, SAVE_PATH)
        print(f"Save best model! Val Acc: {best_val_acc:.4f}")
        patience_counter = 0  # 重置早停计数器
    else:
        patience_counter += 1
        print(f"Patience counter: {patience_counter}/{patience}")
        if patience_counter >= patience:
            print("Early stopping! No improvement in validation accuracy.")
            break

print(f"\nTraining Finished! Best Val Acc: {best_val_acc:.4f}")
print(f"Model saved to: {SAVE_PATH}")