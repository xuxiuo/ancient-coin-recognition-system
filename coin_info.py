"""
古钱币信息数据库
包含币种名称、朝代、材质、历史介绍等信息
优化后：只存储币种基础信息，正反面信息动态生成
"""

# 币种基础信息（不包含正反面标识）
COIN_BASE_INFO = {
    "大清铜币": {
        "name": "大清铜币",
        "dynasty": "清朝",
        "material": "铜",
        "history": "大清铜币是清朝末期（1900-1911年）发行的机制铜币，采用机器冲压制造，标志着中国货币从传统手工铸造向现代化机制币的转变。币面设计精美，具有重要的历史价值和收藏价值。"
    },
    "大清银币": {
        "name": "大清银币",
        "dynasty": "清朝",
        "material": "银",
        "history": "大清银币是清朝末期发行的机制银币，是中国近代货币史上的重要币种。币面通常刻有龙纹图案，体现了清朝的皇权象征。这些银币在当时流通广泛，是研究清末经济史的重要实物资料。"
    },
    "道光通宝": {
        "name": "道光通宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "道光通宝是清宣宗道光年间（1821-1850年）铸造的铜钱。道光时期正值清朝由盛转衰的关键时期，这些钱币见证了当时的社会经济状况，具有重要的历史研究价值。"
    },
    "光绪通宝": {
        "name": "光绪通宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "光绪通宝是清德宗光绪年间（1875-1908年）铸造的铜钱。光绪时期是中国近代化的重要阶段，这些钱币反映了当时货币制度的变革，是研究晚清经济史的重要资料。"
    },
    "光绪元宝": {
        "name": "光绪元宝",
        "dynasty": "清朝",
        "material": "银",
        "history": "光绪元宝是清朝光绪年间发行的机制银币，是中国最早的机制银币之一。币面设计精美，通常有龙纹图案，反映了当时中西文化交流的特点。这些银币在收藏市场上非常受欢迎。"
    },
    "光绪重宝": {
        "name": "光绪重宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "光绪重宝是清朝光绪年间铸造的大面额铜钱，主要用于大额交易。这些钱币制作精良，反映了当时货币制度的完善，是研究清代货币体系的重要实物。"
    },
    "嘉庆通宝": {
        "name": "嘉庆通宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "嘉庆通宝是清仁宗嘉庆年间（1796-1820年）铸造的铜钱。嘉庆时期是清朝中期，这些钱币反映了当时相对稳定的社会经济状况，是清代货币体系的重要组成部分。"
    },
    "康熙通宝": {
        "name": "康熙通宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "康熙通宝是清圣祖康熙年间（1662-1722年）铸造的铜钱。康熙时期是清朝的鼎盛时期，这些钱币制作精良，流通广泛，是清代早期货币的代表，具有很高的历史价值和收藏价值。"
    },
    "利用通宝": {
        "name": "利用通宝",
        "dynasty": "清朝（吴三桂）",
        "material": "铜",
        "history": "利用通宝是清初吴三桂在云南地区铸造的地方货币。这些钱币反映了明末清初的政治动荡和割据局面，具有特殊的历史意义，是研究清初政治史的重要实物资料。"
    },
    "祺祥通宝": {
        "name": "祺祥通宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "祺祥通宝是清朝咸丰十一年（1861年）短暂使用的年号钱币。由于祺祥年号仅存在数月就被改为同治，因此祺祥通宝存世量极少，是清代钱币中的珍品，具有极高的收藏价值。"
    },
    "乾隆宝藏": {
        "name": "乾隆宝藏",
        "dynasty": "清朝",
        "material": "银",
        "history": "乾隆宝藏是清朝乾隆年间在西藏地区发行的银币，主要用于西藏地区的贸易流通。这些银币体现了清朝对西藏地区的治理，是研究清代边疆货币制度的重要实物。"
    },
    "乾隆通宝": {
        "name": "乾隆通宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "乾隆通宝是清高宗乾隆年间（1736-1795年）铸造的铜钱。乾隆时期是清朝的鼎盛时期，经济繁荣，这些钱币制作精良，流通广泛，是清代货币的代表性品种之一。"
    },
    "顺治通宝": {
        "name": "顺治通宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "顺治通宝是清世祖顺治年间（1644-1661年）铸造的铜钱，是清朝入关后最早发行的货币之一。这些钱币见证了清朝建立初期的历史，是研究清初货币制度的重要资料。"
    },
    "同治通宝": {
        "name": "同治通宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "同治通宝是清穆宗同治年间（1862-1874年）铸造的铜钱。同治时期正值太平天国运动之后，这些钱币反映了当时社会经济的恢复过程，是研究晚清历史的重要实物。"
    },
    "同治重宝": {
        "name": "同治重宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "同治重宝是清朝同治年间铸造的大面额铜钱，主要用于大额交易。这些钱币制作规范，反映了同治时期货币制度的完善，是清代货币体系的重要组成部分。"
    },
    "咸丰通宝": {
        "name": "咸丰通宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "咸丰通宝是清文宗咸丰年间（1851-1861年）铸造的铜钱。咸丰时期正值太平天国运动和第二次鸦片战争，这些钱币反映了当时动荡的社会经济状况，具有重要的历史研究价值。"
    },
    "咸丰重宝": {
        "name": "咸丰重宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "咸丰重宝是清朝咸丰年间铸造的大面额铜钱，主要用于大额交易。这些钱币在咸丰时期大量发行，反映了当时财政困难的情况，是研究晚清经济史的重要实物。"
    },
    "宣统通宝": {
        "name": "宣统通宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "宣统通宝是清朝末代皇帝宣统年间（1909-1911年）铸造的铜钱，是清朝最后一种年号钱币。这些钱币见证了清朝的终结，具有特殊的历史意义，是研究清代货币史的重要资料。"
    },
    "雍正通宝": {
        "name": "雍正通宝",
        "dynasty": "清朝",
        "material": "铜",
        "history": "雍正通宝是清世宗雍正年间（1723-1735年）铸造的铜钱。雍正时期是清朝的重要发展阶段，这些钱币制作精良，反映了当时严格的质量控制，是清代货币中的精品。"
    },
    "昭武通宝": {
        "name": "昭武通宝",
        "dynasty": "清朝（吴三桂）",
        "material": "铜",
        "history": "昭武通宝是清初吴三桂在湖南地区铸造的地方货币，是吴三桂反清时发行的钱币。这些钱币存世量稀少，具有特殊的历史意义，是研究清初政治史和货币史的重要实物。"
    }
}


def extract_coin_name(class_name):
    """
    从类别名称中提取币种名称（去掉_正、_反等后缀）
    
    Args:
        class_name: 类别名称（如"康熙通宝_正"、"咸丰重宝-反"）
    
    Returns:
        str: 币种名称（如"康熙通宝"、"咸丰重宝"）
    """
    # 处理各种可能的命名格式
    name = class_name.replace("！", "").replace("!", "")
    
    # 检查是否包含正反面标识
    if "_正" in name or "_反" in name or "-正" in name or "-反" in name:
        # 找到正反面标识并分割
        for sep in ["_正", "_反", "-正", "-反"]:
            if sep in name:
                return name.split(sep)[0]
    
    return name


def get_coin_info(class_name):
    """
    根据类别名称获取币种信息
    
    Args:
        class_name: 类别名称（如"康熙通宝_正"、"咸丰重宝-反"）
    
    Returns:
        dict: 币种信息，包含name、dynasty、material、side、history
    """
    # 提取币种名称
    coin_name = extract_coin_name(class_name)
    
    # 获取基础信息
    base_info = COIN_BASE_INFO.get(coin_name)
    
    if base_info is None:
        # 如果找不到，返回基本信息
        return {
            "name": coin_name,
            "dynasty": "未知",
            "material": "未知",
            "side": "未知",
            "history": "暂无历史介绍"
        }
    
    # 动态判断正反面
    class_name_clean = class_name.replace("！", "").replace("!", "")
    if "_正" in class_name_clean or "-正" in class_name_clean:
        side = "正面"
    elif "_反" in class_name_clean or "-反" in class_name_clean:
        side = "反面"
    else:
        side = "未知"
    
    # 合并基础信息和side信息
    return {
        **base_info,
        "side": side
    }


# 为了向后兼容，保留COIN_INFO作为别名（但实际使用COIN_BASE_INFO）
# 如果某些地方直接使用COIN_INFO，可以通过这个映射兼容
def _build_coin_info_dict():
    """构建完整的COIN_INFO字典（用于向后兼容）"""
    coin_info = {}
    for coin_name, base_info in COIN_BASE_INFO.items():
        # 添加正面
        coin_info[f"{coin_name}_正"] = {**base_info, "side": "正面"}
        coin_info[f"{coin_name}_正!"] = {**base_info, "side": "正面"}
        coin_info[f"{coin_name}_正！"] = {**base_info, "side": "正面"}
        # 添加反面
        coin_info[f"{coin_name}_反"] = {**base_info, "side": "反面"}
        coin_info[f"{coin_name}_反!"] = {**base_info, "side": "反面"}
        coin_info[f"{coin_name}_反！"] = {**base_info, "side": "反面"}
        # 处理特殊格式（咸丰重宝使用-）
        if coin_name == "咸丰重宝":
            coin_info[f"{coin_name}-正"] = {**base_info, "side": "正面"}
            coin_info[f"{coin_name}-反"] = {**base_info, "side": "反面"}
    return coin_info


# 为了向后兼容，提供COIN_INFO（但不推荐直接使用）
COIN_INFO = _build_coin_info_dict()


if __name__ == "__main__":
    # 测试
    test_cases = [
        "康熙通宝_正",
        "康熙通宝_反",
        "咸丰重宝-正",
        "咸丰重宝-反",
        "大清铜币_正！",
        "大清铜币_反！",
        "未知币种_正"
    ]
    
    print("=" * 50)
    print("测试币种信息获取功能")
    print("=" * 50)
    
    for test_class in test_cases:
        info = get_coin_info(test_class)
        print(f"\n类别: {test_class}")
        print(f"币种名称: {info['name']}")
        print(f"朝代: {info['dynasty']}")
        print(f"材质: {info['material']}")
        print(f"面: {info['side']}")
        print(f"历史: {info['history'][:50]}...")
    
    print("\n" + "=" * 50)
    print(f"币种总数: {len(COIN_BASE_INFO)} 种")
    print(f"数据量减少: 从 40 条减少到 {len(COIN_BASE_INFO)} 条（减少 50%）")
    print("=" * 50)
