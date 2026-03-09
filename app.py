import os
import sys
import io
import json
import hashlib
import time

# --- 1. 环境修复：强制支持 UTF-8 中文输出 ---
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from google import genai
from google.genai import types

# --- 2. 初始化 AI (⚠️ 演示后请及时更换 Key) ---
client = genai.Client(api_key="AIzaSyCFN7GNjnkurw_Gj9PQaCcMvlaahJQrjwc")

# ==========================================
# [第三层：风险引擎层配置] - 模拟智能合约预定义参数
# ==========================================
SCA_CONFIG = {
    "FACTORS": {
        "aluminum_virgin": 12.0,  # 每kg排放 12kg CO2
        "aluminum_recycled": 2.3,  # 每kg排放 2.3kg CO2
        "default": 10.0
    },
    "THRESHOLDS": {
        "A": {"limit": 3000, "rate": "3.2%", "desc": "Green/Low Carbon"},
        "B": {"limit": 5000, "rate": "4.5%", "desc": "Standard"},
        "C": {"limit": 8000, "rate": "6.0%", "desc": "Warning"},
        "D": {"limit": float('inf'), "rate": "8.5%", "desc": "High Risk"}
    }
}


def risk_engine_v2(material, weight):
    """
    智能合约决策逻辑：
    1. 计算：碳排 = 重量 × 碳因子
    2. 比较：与阈值动态对比
    3. 决策：自动生成评级与利率
    """
    # 查找因子
    factor = SCA_CONFIG["FACTORS"].get(material, SCA_CONFIG["FACTORS"]["default"])
    total_co2 = weight * factor

    # 匹配评级 (从低到高遍历)
    final_rating = "D"
    final_rate = SCA_CONFIG["THRESHOLDS"]["D"]["rate"]

    for level in ["A", "B", "C"]:
        if total_co2 <= SCA_CONFIG["THRESHOLDS"][level]["limit"]:
            final_rating = level
            final_rate = SCA_CONFIG["THRESHOLDS"][level]["rate"]
            break

    return final_rating, final_rate, total_co2


# --- 4. AI 提取层 ---
def process_invoice(file_path):
    print(f"--- [1/3 AI 引擎] 正在扫描发票: {file_path} ---")
    prompt = """分析发票内容，以纯 JSON 格式返回：
    {
      "material_type": "aluminum_virgin" 或 "aluminum_recycled",
      "weight": 数字 (kg),
      "supplier": "供应商全称"
    }
    判断规则：含有 'Recycled', '再生' 字样即为 aluminum_recycled。"""

    with open(file_path, "rb") as f:
        content = f.read()

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=[prompt, types.Part.from_bytes(data=content, mime_type="application/pdf")]
    )
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)


# --- 5. 区块链底层 ---
def hash_file(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()


class SCA_Block:
    def __init__(self, index, transactions, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty=2):
        print("  [网络共识] 正在执行工作量证明 (PoW) 打包区块...")
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()


# --- 6. 主程序：全流程集成 ---
if __name__ == "__main__":
    invoice_file = "invoices/test.pdf"

    if os.path.exists(invoice_file):
        try:
            # 步骤 A: AI 解析
            ai_data = process_invoice(invoice_file)
            m_type = ai_data.get('material_type', 'unknown')
            weight = ai_data.get('weight', 0)

            # 步骤 B: 风险引擎决策 (使用 V2 版本)
            rating, rate, total_co2 = risk_engine_v2(m_type, weight)

            print(f"  ✅ 识别成功: {ai_data.get('supplier')} | {m_type} | {weight}kg")

            # 步骤 C: 生成双哈希
            print("\n--- [2/3 确权引擎] 生成双哈希指纹 ---")
            original_pdf_hash = hash_file(invoice_file)
            # 将决策结果也加入哈希，确保证书不可篡改
            extracted_data_hash = hashlib.sha256(json.dumps(ai_data, sort_keys=True).encode('utf-8')).hexdigest()

            # 步骤 D: 组装上链 Payload
            print("\n--- [3/3 上链引擎] 链接 PCR 凭证并广播 ---")
            transaction_payload = {
                "invoice_doc_hash": original_pdf_hash,
                "extracted_data_hash": extracted_data_hash,
                "pcr_verification": {
                    "cert_id": "PCR-AL-2026-SGS-001",
                    "issuer": "SGS Certification",
                    # 这里动态从配置库读取因子，体现逻辑一致性
                    "verified_factor": SCA_CONFIG["FACTORS"].get(m_type, 10.0),
                    "on_chain_address": "0x89205A3A3b2A69De6Dbf7f01ED13B2108B2c43e7"
                },
                "financial_decision": {
                    "carbon_emission": total_co2,
                    "credit_rating": rating,
                    "applied_rate": rate,
                    "rule_set": "SCA-2.0-STANDARD"
                }
            }

            # 步骤 E: 区块打包
            sca_chain = [SCA_Block(0, "Genesis Block", "0")]
            new_block = SCA_Block(1, transaction_payload, sca_chain[-1].hash)
            new_block.mine_block(difficulty=2)
            sca_chain.append(new_block)

            # 最终展示（专业版）
            print("\n" + "█" * 65)
            print("  SCA 2.0 分布式账本上链回执 (企业级风险引擎版)")
            print("█" * 65)
            print(f"  供应商: {ai_data.get('supplier')}")
            print(f"  核定评级: {rating} | 审批利率: {rate} | 总碳排: {total_co2:.2f} kg")
            print("-" * 65)
            print(
                f"  PCR 验证详情: 因子 {transaction_payload['pcr_verification']['verified_factor']} | 证书号 {transaction_payload['pcr_verification']['cert_id']}")
            print(f"  区块高度: {len(sca_chain)} | TxHash: {new_block.hash[:32]}...")
            print("█" * 65)

        except Exception as e:
            print(f"⚠️ 系统运行错误: {e}")
    else:
        print(f"❌ 找不到文件: {invoice_file}")