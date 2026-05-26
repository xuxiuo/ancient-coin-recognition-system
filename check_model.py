import torch

checkpoint = torch.load('best_coin_model.pth', map_location='cpu')
print("模型检查点包含的键:", checkpoint.keys())
if 'class_to_idx' in checkpoint:
    print("\n类别映射 (class_to_idx):")
    for class_name, idx in sorted(checkpoint['class_to_idx'].items(), key=lambda x: x[1]):
        print(f"  {idx}: {class_name}")
else:
    print("\n未找到class_to_idx，尝试从数据集获取...")


