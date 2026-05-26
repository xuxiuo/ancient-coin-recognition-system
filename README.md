### 古钱币识别系统（清币慧眼通）


基于 Flask + PyTorch + ResNet18 的古钱币智能识别系统，支持单币识别、正反面配对验证、批量识别以及古钱币信息查询。



## 项目简介



本项目面向清代古钱币识别场景，利用深度学习图像分类技术实现古钱币自动鉴定。

系统采用 ResNet18 预训练模型进行迁移学习训练，可识别 20 种古钱币（40 个类别，包含正反面），并提供币种信息展示、批量识别和结果分类保存等功能。

<img width="2804" height="1534" alt="屏幕截图 2026-05-26 143549" src="https://github.com/user-attachments/assets/498f90d4-7e1c-4c1c-820b-53eeede3f108" />
------

## 功能特点



### 单币识别



- 上传古钱币正面和反面图片
- 自动识别币种名称
- 正反面自动配对验证
- 显示识别置信度
- 展示朝代、材质及历史介绍

### 批量识别



- 支持批量上传图片
- 自动分批处理（50张/批）
- 按币种自动分类结果
- 自动保存识别结果

### 信息查询



- 查看支持识别的古钱币列表
- 查询币种历史信息
- 查看朝代与材质信息

### 异常处理



- 图片格式校验
- 上传数量限制
- 正反面不匹配提示
- 模型预测异常处理

<img width="2565" height="1546" alt="屏幕截图 2026-05-26 144423" src="https://github.com/user-attachments/assets/fc4adb96-aef5-4af6-9ec4-f033934d70b7" />

<img width="2412" height="1503" alt="屏幕截图 2026-05-26 144512" src="https://github.com/user-attachments/assets/8fe99ede-c4ac-4f36-b118-e36349166354" />
<img width="2504" height="1525" alt="屏幕截图 2026-05-26 144726" src="https://github.com/user-attachments/assets/57ba7147-7aae-453f-aa93-544185b85d19" />
<img width="2415" height="1418" alt="屏幕截图 2026-05-26 144835" src="https://github.com/user-attachments/assets/804eef9a-92c5-45ad-9ef1-c938fbe3ac96" />

------

## 数据集说明



### 数据规模



- 总图片数量：4135张
- 类别数量：40类
- 钱币种类：20种
- 训练集：3308张
- 验证集：827张

### 数据划分



```text
Train : Validation
 8     :    2
```



------

## 模型说明



### 主模型



ResNet18（ImageNet预训练权重微调）

### 训练参数



| 参数       | 数值    |
| ---------- | ------- |
| 输入尺寸   | 224×224 |
| Batch Size | 32      |
| Epoch      | 25      |
| 学习率     | 0.001   |
| 优化器     | Adam    |
| 类别数     | 40      |

### 训练结果



| 指标         | 数值 |
| ------------ | ---- |
| 训练集准确率 | ≈98% |
| 验证集准确率 | ≈93% |

------

## 项目结构



```text
古钱币识别系统
│
├── app.py                     # Flask主程序
├── predict.py                 # 模型推理模块
├── coin_info.py               # 钱币信息数据库
│
├── model.py                   # CNN训练代码
├── model_2.py                 # ResNet18训练代码
├── model_3.py                 # 模型改进实验
│
├── check_model.py             # 模型检查
├── get_acc.py                 # 精度统计
├── count_dataset.py           # 数据集统计
│
├── best_coin_model.pth        # 最优模型
├── best_coin_model_0.pth      # 备份模型
├── coin_cnn_model_40class.pth # CNN模型
│
├── templates/
│   ├── index.html
│   └── intro.html
│
├── uploads/                   # 上传文件
├── results/                   # 识别结果
├── 数据集/                     # 古钱币数据集
│
├── requirements.txt
└── README.md
```



------

## 系统架构



```text
前端界面
    │
    ▼
Flask Web服务
    │
    ▼
模型推理模块
    │
    ▼
ResNet18识别模型
    │
    ▼
结果处理与信息查询
```



------

## 环境要求



### 开发环境



- Windows
- PyCharm

### Python版本



```
Python 3.8+
```



### 主要依赖



```text
Flask==3.0.0
torch>=2.0.0
torchvision>=0.15.0
Pillow>=10.0.0
numpy>=1.24.0
Werkzeug>=3.0.0
```



------

## 安装与运行



### 1. 克隆项目



```
git clone https://github.com/你的用户名/ancient-coin-recognition-system.git
```



### 2. 安装依赖



```
pip install -r requirements.txt
```



### 3. 启动系统



```
python app.py
```



### 4. 浏览器访问



```text
http://127.0.0.1:5000
```



------

## 识别流程



### 单币识别



```text
上传正反面图片
        ↓
图像预处理
        ↓
ResNet18推理
        ↓
正反面匹配验证
        ↓
结果展示
```



### 批量识别



```text
上传多张图片
        ↓
自动分批
        ↓
模型预测
        ↓
结果合并
        ↓
分类保存
```



------

## 技术栈



### 后端



- Flask

### 深度学习



- PyTorch
- torchvision
- ResNet18

### 前端



- HTML
- CSS
- JavaScript

### 图像处理



- Pillow

------

## 项目特色



- 基于 ResNet18 迁移学习
- 支持正反面配对验证
- 支持批量识别
- 自动分类保存结果
- 钱币历史信息展示
- Web可视化操作界面

------

## 作者

xuxiuo

数字图像处理与机器视觉课程实训项目

2025
