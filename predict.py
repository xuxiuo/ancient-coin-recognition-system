"""
古钱币识别模型推理模块
"""
import torch
import torch.nn as nn
from torchvision import models, transforms
from torchvision.models import ResNet18_Weights
from PIL import Image
import os

# 模型配置
IMG_SIZE = 224
NUM_CLASSES = 40
MODEL_PATH = "best_coin_model.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 图像预处理（与训练时一致）
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])


class CoinPredictor:
    """古钱币识别器"""
    
    def __init__(self, model_path=MODEL_PATH):
        self.device = DEVICE
        self.model = None
        self.class_to_idx = {}
        self.idx_to_class = {}
        self.load_model(model_path)
    
    #调用 load_model→加载模型权重 + 重建模型结构 + 加载类别映射
    #类封装实现 “一次加载、多次预测”，避免每次预测都加载模型，提升 Web 接口响应速度
    def load_model(self, model_path):
        """加载训练好的模型"""
        try:
            # 加载检查点
            checkpoint = torch.load(model_path, map_location=self.device)
            
            # 创建模型结构
            self.model = models.resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
            self.model.fc = nn.Linear(self.model.fc.in_features, NUM_CLASSES)
            
            # 加载权重
            if 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            
            self.model = self.model.to(self.device)
            self.model.eval()
            
            # 加载类别映射
            if 'class_to_idx' in checkpoint:
                self.class_to_idx = checkpoint['class_to_idx']
            else:
                # 如果检查点中没有，从数据集文件夹获取
                self.class_to_idx = self._get_class_mapping_from_dataset()
            
            self.idx_to_class = {v: k for k, v in self.class_to_idx.items()}
            
            print(f"✅ 模型加载成功！共 {len(self.class_to_idx)} 个类别")
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise
    
    def _get_class_mapping_from_dataset(self):
        """从数据集文件夹获取类别映射"""
        dataset_root = "数据集"
        if not os.path.exists(dataset_root):
            raise FileNotFoundError(f"数据集文件夹不存在: {dataset_root}")
        
        class_names = sorted([d for d in os.listdir(dataset_root) 
                             if os.path.isdir(os.path.join(dataset_root, d))])
        return {name: idx for idx, name in enumerate(class_names)}
    
    #打开图片→转 RGB（兼容 PNG/RGBA）→Resize→归一化→加 batch 维度
    # 预处理必须和训练时一致，否则特征对齐失败，识别准确率会暴跌
    def preprocess_image(self, image_path):
        """预处理图像"""
        try:
            # 打开图像
            image = Image.open(image_path)
            
            # 转换为RGB（处理RGBA等格式）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 应用变换
            image_tensor = transform(image).unsqueeze(0)  # 添加batch维度
            return image_tensor.to(self.device)
        except Exception as e:
            raise ValueError(f"图像预处理失败: {e}")
    
    #关闭梯度减少显存占用，softmax 把模型输出转为 0-1 的置信度，方便用户理解
    def predict(self, image_path, top_k=1):
        """
        预测图像类别
        
        Args:
            image_path: 图像路径
            top_k: 返回前k个预测结果
        
        Returns:
            list: [(类别名称, 置信度), ...]
        """
        try:
            # 预处理图像
            image_tensor = self.preprocess_image(image_path)
            
            # 推理
            with torch.no_grad():
                outputs = self.model(image_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                top_probs, top_indices = torch.topk(probabilities, top_k)
            
            # 转换为类别名称和置信度
            results = []
            for prob, idx in zip(top_probs[0], top_indices[0]):
                class_name = self.idx_to_class[idx.item()]
                confidence = prob.item()
                results.append((class_name, confidence))
            
            return results
            
        except Exception as e:
            raise ValueError(f"预测失败: {e}")
    
    def predict_batch(self, image_paths, top_k=1):
        """
        批量预测
        
        Args:
            image_paths: 图像路径列表
            top_k: 返回前k个预测结果
        
        Returns:
            list: 每个图像的预测结果列表
        """
        results = []
        for img_path in image_paths:
            try:
                pred = self.predict(img_path, top_k)
                results.append({
                    'image_path': img_path,
                    'predictions': pred,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'image_path': img_path,
                    'error': str(e),
                    'success': False
                })
        return results


# 全局预测器实例（单例模式）
_predictor = None

def get_predictor():
    """获取预测器实例（单例）"""
    global _predictor
    if _predictor is None:
        _predictor = CoinPredictor()
    return _predictor


if __name__ == "__main__":
    # 测试代码
    predictor = CoinPredictor()
    print("\n模型加载完成，可以开始预测！")
    print(f"可用类别: {len(predictor.class_to_idx)}")

