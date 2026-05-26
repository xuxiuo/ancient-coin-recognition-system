import os

def count_all_images_per_folder(root_dir):
    folder_counts = {}
    total = 0
    # 支持所有常见图片格式
    img_extensions = ('.jpg', '.jpeg', '.png')

    for folder_name in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, folder_name)
        if os.path.isdir(folder_path):
            count = 0
            for file in os.listdir(folder_path):
                if os.path.isfile(os.path.join(folder_path, file)) and file.lower().endswith(img_extensions):
                    count += 1
            folder_counts[folder_name] = count
            total += count

    return folder_counts, total

if __name__ == "__main__":
    DATASET_ROOT = r"数据集"
    if not os.path.exists(DATASET_ROOT):
        print("错误：未找到数据集文件夹！")
    else:
        folder_counts, total = count_all_images_per_folder(DATASET_ROOT)
        print("=== 数据集图片数量统计（所有格式）===")
        for folder, count in sorted(folder_counts.items()):
            print(f"{folder}：{count} 张图片")
        print(f"\n总图片数量：{total} 张")