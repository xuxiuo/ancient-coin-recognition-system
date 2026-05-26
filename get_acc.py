import torch

checkpoint = torch.load("best_coin_model.pth")
best_accuracy = checkpoint["best_acc"]
print(f"最佳验证准确率: {best_accuracy:.4f}")
