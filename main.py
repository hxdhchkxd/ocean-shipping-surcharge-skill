"""
名称: 欧线海运附加费分析
描述: 根据产品名称和材质分析海运附加费及塑料制品箱数提醒
作者: 渠道专员
版本: 1.0
"""

import pandas as pd
import re

def main(input_file):
    # 读取上传的 Excel 文件
    df = pd.read_excel(input_file)
    
    # 定义附加费规则表（海运部分）
    rules = [
        {"category": "服装", "keywords": ["服装", "袜子", "内裤", "衣服", "裤子", "围巾", "手套", "裙子", "纺织品"], "hs_range": (6101, 6217), "fee": 3, "reject": False},
        {"category": "鞋靴", "keywords": ["鞋", "运动鞋", "皮鞋", "拖鞋", "凉鞋", "鞋类"], "hs_range": (6401, 6405), "fee": 3, "reject": False},
        {"category": "钟表", "keywords": ["钟", "表", "闹钟", "挂钟", "怀表", "手表"], "hs_range": (9101, 9114), "fee": 3, "reject": False, "note": "单个价值超过10欧元不接；手表不接"},
        {"category": "箱包", "keywords": ["包", "手提包", "书包", "电脑包", "皮革包", "袋子", "行李箱"], "hs_range": (4202, 4202), "fee": 2, "reject": False},
        {"category": "其他纺织品", "keywords": ["猫抓柱", "帐篷", "充气床垫", "绳索", "渔网", "纺织品"], "hs_range": (5001, 6310), "fee": 2, "reject": False},
        {"category": "不锈钢刀叉", "keywords": ["刀叉", "勺子", "叉子", "厨房", "餐具", "黄油刀", "糖钳"], "hs_range": (8215, 8215), "fee": 2, "reject": False},
        {"category": "玩具", "keywords": ["玩具", "塑料玩具", "儿童玩具", "填充玩具", "益智玩具", "滑板车"], "hs_range": (9503, 9503), "fee": 2, "reject": False, "note": "英国不接（宠物玩具除外）、欧盟自税不接"},
        {"category": "伞", "keywords": ["伞", "遮阳伞", "折叠伞", "直骨伞"], "hs_range": (6601, 6601), "fee": 2, "reject": False},
        {"category": "机械类产品", "keywords": ["机械", "打印机", "配件"], "hs_range": (8401, 8479), "fee": 2, "reject": False, "note": "高货值不接"},
        {"category": "光学仪器", "keywords": ["摄影", "测量", "检测", "仪器"], "hs_range": (9001, 9033), "fee": 2, "reject": False, "note": "涉医疗不接"},
        {"category": "塑料制品", "keywords": ["塑料", "橡胶", "PVC", "ABS", "硅胶", "合成纤维"], "hs_range": (3901, 3926), "fee": 1, "reject": False, "note": "单箱小于20个可免收；单箱超过40个+2，超过60个+3；一次性塑料英国不接、欧盟含税+3可接"},
        {"category": "玻璃制品", "keywords": ["玻璃"], "hs_range": (7001, 7020), "fee": 1, "reject": False},
        {"category": "笔", "keywords": ["笔", "圆珠笔", "马克笔", "画笔", "蜡笔"], "hs_range": (9608, 9608), "fee": 1, "reject": False},
        {"category": "家用电器及配件", "keywords": ["电器", "微波炉", "电熨斗", "电源线", "数据线", "插座", "逆变器", "电风扇", "冰箱", "电视机", "屏幕"], "hs_range": (8501, 8544), "fee": 0, "reject": False, "note": "逆变器+2，显示器等带屏幕+1"},
        {"category": "纸制品", "keywords": ["纸", "笔记本", "信纸", "纸盒"], "hs_range": (4801, 4911), "fee": 0, "reject": False, "note": "有版权不接，带地图不接"},
        {"category": "体育用品", "keywords": ["体育", "哑铃", "球拍", "瑜伽球", "冲浪板"], "hs_range": (9506, 9506), "fee": 0, "reject": False, "note": "大型锻炼器材+1；带真空产品不接"},
        {"category": "铁、铜制品", "keywords": ["铁", "不锈钢", "铜", "铝", "金属"], "hs_range": (7301, 7616), "fee": 0, "reject": False, "note": "原材料不接；钢铁制品需MTC证书"},
        {"category": "灯", "keywords": ["灯", "吊灯", "壁灯", "吸顶灯", "灯带", "灯条", "台灯", "落地灯", "照明"], "hs_range": (9405, 9405), "fee": 0, "reject": False},
    ]
    
    reject_keywords = [
        ("粘合剂", ["胶水", "环氧树脂", "粘合剂"]),
        ("蜡烛", ["蜡烛", "香薰蜡烛"]),
        ("化妆品", ["化妆品", "香薰", "除臭剂", "洗面奶", "沐浴露", "牙膏"]),
        ("纯电产品", ["电池", "充电宝"]),
        ("赌博用品", ["扑克", "塔罗牌", "麻将", "筹码"]),
        ("高货值", []),  # 需结合货值判断，此处仅作提醒
        ("反倾销", ["自行车", "摩托车", "汽车配件", "轮胎", "轮毂", "割草机", "胶合板", "熨衣板", "螺丝", "太阳能", "光伏", "陶瓷餐具", "瓷砖", "铝箔", "铝散热器", "钢材", "钢缆"]),
        ("管制/敏感品", ["粉末", "液体", "膏体", "仿牌", "侵权", "药物", "医疗", "有毒", "无人机", "望远镜", "迷彩服", "战术背心", "管制刀具", "仿真枪", "警用", "手铐", "电棍", "木炭", "活性炭", "石棉"]),
    ]
    
    results = []
    
    for idx, row in df.iterrows():
        product = str(row.get("发票产品", ""))
        material = str(row.get("材质", ""))
        
        matched_category = None
        matched_fee = 0
        matched_note = ""
        reject_reason = ""
        
        # 先检查拒收关键词
        for reject_cat, keywords in reject_keywords:
            if any(kw in product or kw in material for kw in keywords):
                reject_reason = f"拒收 - {reject_cat}"
                break
        
        if not reject_reason:
            # 匹配正常规则
            for rule in rules:
                # 关键词匹配
                if any(kw in product or kw in material for kw in rule["keywords"]):
                    matched_category = rule["category"]
                    matched_fee = rule["fee"]
                    matched_note = rule.get("note", "")
                    break
        
        # 塑料类额外提醒
        plastic_reminder = ""
        if matched_category == "塑料制品":
            plastic_reminder = "【塑料提醒】单箱小于20个可免附加费；超过20个/箱 +1，超过40个 +2，超过60个 +3"
        
        # 组装输出
        if reject_reason:
            surcharge_info = reject_reason
        elif matched_category:
            surcharge_info = f"+{matched_fee} 元/KG （{matched_category}）"
            if matched_note:
                surcharge_info += f"；备注：{matched_note}"
            if plastic_reminder:
                surcharge_info += f"；{plastic_reminder}"
        else:
            surcharge_info = "未匹配到规则，请人工确认"
        
        results.append({
            "客户单号": row.get("客户单号", ""),
            "发票产品": product,
            "材质": material,
            "海运附加费分析": surcharge_info
        })
    
    output_df = pd.DataFrame(results)
    
    # 保存结果文件
    output_path = "/tmp/附加费分析结果.xlsx"
    output_df.to_excel(output_path, index=False)
    
    return output_path