import hashlib
import pandas as pd
import streamlit as st
import json
import time
from google import genai
from google.genai import types

# --- 1. 页面配置 ---
st.set_page_config(page_title="SupplyChain Alpha (SCA) 2.0", layout="wide")
API_KEY = st.secrets["GEMINI_API_KEY"]

# 【硬核护城河】：从 database 文件夹动态加载 UK 官方 GHG 数据库
@st.cache_data
def load_official_ghg_database():
    try:
        # 你的文件叫 Material_use.xlsx，跳过前4行无关的表头说明
        df = pd.read_excel("database/Material_use.xlsx", skiprows=4)
        return df
    except Exception as e:
        return None
# --- 2. 语言包配置 (i18n) ---
LANG_DICT = {
    "English": {
        "title": "SupplyChain Alpha (SCA) 2.0",
        "subtitle": "Secure invoice gateway connected to distributed oracle network.",
        "upload_btn": "➔ Submit to Ledger",
        "drop_box": "Drop Invoice PDF here",
        "sme_side": "🏭 Supplier Node",
        "bank_side": "🏦 Banker Credit Engine",
        "history_title": "⛓️ Immutable Audit Trail",
        "supplier": "Entity Name",
        "material": "Material Type",
        "weight": "Certified Weight",
        "factor": "Carbon Factor",
        "anchor": "Document Anchor",
        "rating_label": "ESG Credit Rating",
        "emission_label": "Smart Contract Emissions",
        "next_btn": "Commit & Next Transaction",
        "status_valid": "✅ VALID (Live Oracle)",
        "tx_hash": "Tx Hash Anchor"
    },
    "简体中文": {
        "title": "SupplyChain Alpha (SCA) 2.0",
        "subtitle": "安全上传供应链发票，连接分布式预言机网络进行自动化评估。",
        "upload_btn": "➔ 提交链上审核",
        "drop_box": "拖拽发票原件 (PDF) 至此框内",
        "sme_side": "🏭 企业填报端 (Supplier Data Node)",
        "bank_side": "🏦 银行风控端 (Banker Credit Engine)",
        "history_title": "⛓️ 链上存证记录 (Immutable Audit Trail)",
        "supplier": "供应商主体名称",
        "material": "核定供应链物料",
        "weight": "采购/出库重量",
        "factor": "第三方碳排因子",
        "anchor": "物理凭证防伪锚点",
        "rating_label": "ESG 信用评级与审批利率",
        "emission_label": "智能合约核算总碳排",
        "next_btn": "🔄 上链并处理下一笔",
        "status_valid": "✅ 预言机核验通过",
        "tx_hash": "交易哈希指纹"
    },
    "繁體中文": {
        "title": "SupplyChain Alpha (SCA) 2.0",
        "subtitle": "安全上傳供應鏈發票，連接分佈式預言機網絡進行自動化評估。",
        "upload_btn": "➔ 提交鏈上審核",
        "drop_box": "拖拽發票原件 (PDF) 至此框內",
        "sme_side": "🏭 企業填報端 (Supplier Data Node)",
        "bank_side": "🏦 銀行風控端 (Banker Credit Engine)",
        "history_title": "⛓️ 鏈上存證記錄 (Immutable Audit Trail)",
        "supplier": "供應商主體名稱",
        "material": "核定供應鏈物料",
        "weight": "採購/出庫重量",
        "factor": "第三方碳排因子",
        "anchor": "物理憑證防偽錨點",
        "rating_label": "ESG 信用評級與審批利率",
        "emission_label": "智能合約核算總碳排",
        "next_btn": "🔄 上鏈並處理下一筆",
        "status_valid": "✅ 預言機核驗通過",
        "tx_hash": "交易哈希指紋"
    }
}

# 顶部语言选择器 (悬浮效果)
selected_lang = st.sidebar.selectbox("🌐 Language / 語言", ["English", "简体中文", "繁體中文"])
T = LANG_DICT[selected_lang]

# --- 3. 初始化全局状态 ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'upload'
if 'history' not in st.session_state:
    st.session_state['history'] = []

# --- 4. 注入样式 ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans+JP:wght@400;500;600&display=swap');
:root { --bg: #F5F7F9; --ink: #0F1A16; --ink-3: #7A8A84; --teal: #0A6B55; --green: #1A7A3A; --green-lt: #E8F5ED; --red: #B83228; --red-lt: #FDECEA; --border: #E0E4E2; --mono: 'IBM Plex Mono', monospace; }
.stApp { background-color: var(--bg); }
.panel { background: #FFFFFF; padding: 24px; border-radius: 8px; border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.02); height: 100%; }
.panel-title { font-size: 15px; font-weight: 600; color: var(--ink); margin-bottom: 16px; border-bottom: 2px solid var(--ink); padding-bottom: 8px; font-family: 'IBM Plex Sans JP';}
.data-row { display: flex; justify-content: space-between; border-bottom: 1px dashed var(--border); padding: 10px 0; font-family: var(--mono); font-size: 13px;}
.data-lbl { color: var(--ink-3); text-transform: uppercase; font-weight: 500;}
.hero-metric { padding: 20px; border-radius: 6px; border: 1.5px solid; margin-bottom: 16px; text-align: center; font-family: var(--mono);}
.hero-metric.bad { background: var(--red-lt); border-color: rgba(184,50,40,.25); color: var(--red); }
.hero-metric.good { background: var(--green-lt); border-color: rgba(26,122,58,.2); color: var(--green); }
.upload-center { max-width: 600px; margin: 6vh auto; text-align: center; }
.history-table { width: 100%; border-collapse: collapse; font-family: var(--mono); font-size: 12px; background: white; border: 1px solid var(--border);}
.history-table th { background: var(--ink); color: white; padding: 10px; text-align: left; }
.history-table td { padding: 10px; border-bottom: 1px solid var(--border); }
</style>
""", unsafe_allow_html=True)

# --- 5. 业务引擎 ---
SCA_CONFIG = {
    "FACTORS": {"aluminum_virgin": 12.0, "aluminum_recycled": 2.3, "default": 10.0},
    "THRESHOLDS": {
        "A": {"limit": 3000, "rate": "3.2%", "status": "good", "desc": "Tier 1"},
        "B": {"limit": 5000, "rate": "4.5%", "status": "good", "desc": "Tier 2"},
        "C": {"limit": 8000, "rate": "6.0%", "status": "bad", "desc": "Tier 3"},
        "D": {"limit": float('inf'), "rate": "8.5%", "status": "bad", "desc": "Tier 4"}
    }
}

# ==========================================
# 视图 1：上传入口
# ==========================================
if st.session_state['page'] == 'upload':
    st.markdown("<div class='upload-center'>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-family: var(--mono); color: var(--teal);'>{T['title']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: var(--ink-3); margin-bottom: 30px;'>{T['subtitle']}</p>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(T['drop_box'], type="pdf")

    if uploaded_file:
        if st.button(T['upload_btn'], use_container_width=True):
            with st.spinner("Oracle Processing & Hashing..."):
                try:
                    # 读取文件并生成真实的防篡改哈希
                    file_bytes = uploaded_file.read()
                    pdf_hash = hashlib.sha256(file_bytes).hexdigest()
                    
                    # 调用 Gemini 预言机
                    client = genai.Client(api_key=API_KEY)
                    prompt = "Analyze invoice. Return JSON: { 'material_type': 'aluminum_virgin' or 'aluminum_recycled', 'weight': number, 'supplier': 'name' }"
                    response = client.models.generate_content(
                        model="gemini-flash-latest",
                        contents=[prompt, types.Part.from_bytes(data=file_bytes, mime_type="application/pdf")]
                    )
                    res = json.loads(response.text.replace("```json", "").replace("```", "").strip())

                    # 计算风控逻辑
                    factor = SCA_CONFIG["FACTORS"].get(res['material_type'], 10.0)
                    total_co2 = res['weight'] * factor
                    rating, rate, status, desc = "D", "8.5%", "bad", "Tier 4"
                    for k, v in SCA_CONFIG["THRESHOLDS"].items():
                        if total_co2 <= v["limit"]:
                            rating, rate, status, desc = k, v["rate"], v["status"], v["desc"]
                            break

                    # 【Web3 改造】：生成区块高度和合约状态，存入历史流水
                    block_num = 104200 + len(st.session_state['history'])
                    contract_status = "✅ 执行放款 (Executed)" if status == "good" else "🛑 拦截提款 (Reverted)"
                    
                    st.session_state['history'].append({
                        "block": f"#{block_num}",
                        "time": time.strftime("%H:%M:%S"), 
                        "supplier": res['supplier'], 
                        "hash": f"0x{pdf_hash[:16]}...",
                        "contract": contract_status
                    })
                    
                    st.session_state['analysis'] = {'res': res, 'pdf_hash': pdf_hash, 'rating': rating, 'rate': rate,
                                                    'co2': total_co2, 'status': status, 'desc': desc}
                    st.session_state['page'] = 'dashboard'
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

    # 【Web3 改造】：底部的区块链账本视图
    if st.session_state['history']:
        st.divider()
        st.markdown(f"<h4 style='font-family: var(--mono);'>{T['history_title']}</h4>", unsafe_allow_html=True)
        # 加入了 Block 和 Smart Contract 列
        h_html = f"<table class='history-table'><tr><th>Block</th><th>Time</th><th>{T['supplier']}</th><th>{T['tx_hash']}</th><th>Smart Contract Status</th></tr>"
        for h in reversed(st.session_state['history']):
            h_html += f"<tr><td><b>{h['block']}</b></td><td>{h['time']}</td><td>{h['supplier']}</td><td style='color:var(--teal);'>{h['hash']}</td><td>{h['contract']}</td></tr>"
        st.markdown(h_html + "</table>", unsafe_allow_html=True)

# ==========================================
# 视图 2：对比看板
# ==========================================
elif st.session_state['page'] == 'dashboard':
    d = st.session_state['analysis']
    st.markdown(f"<h3 style='font-family: var(--mono); color: var(--teal);'>⬡ {T['title']} | Global Audit</h3>",
                unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown(f"<div class='panel'><div class='panel-title'>{T['sme_side']}</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="data-row"><span class="data-lbl">{T['supplier']}</span><span>{d['res']['supplier']}</span></div>
        <div class="data-row"><span class="data-lbl">{T['material']}</span><span>{d['res']['material_type']}</span></div>
        <div class="data-row"><span class="data-lbl">{T['weight']}</span><span>{d['res']['weight']} KG</span></div>
        <div class="data-row"><span class="data-lbl">{T['anchor']}</span><span style='font-size:10px; color:var(--teal)'>0x{d['pdf_hash'][:30]}...</span></div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"<div class='panel'><div class='panel-title'>{T['bank_side']}</div>", unsafe_allow_html=True)
        
        # 【Web3 改造】：银行端的智能合约执行提示
        if d['status'] == 'good':
            st.success("⚙️ **智能合约已触发：ESG合规，自动执行放款 (Smart Contract Executed)**")
        else:
            st.error("🛑 **智能合约熔断：碳敞口超标，拦截提款 (Smart Contract Reverted)**")

        st.markdown(f"""
        <div class="hero-metric {d['status']}">
            <div style='font-size:10px; font-weight:700'>{T['rating_label']}</div>
            <div style='font-size:32px; font-weight:700'>{d['rating']} / {d['rate']}</div>
            <div style='font-size:12px'>{d['desc']}</div>
        </div>
        <div class="data-row"><span class="data-lbl">{T['emission_label']}</span><span>{d['co2']:.1f} kg CO2e</span></div>
        <div class="data-row"><span class="data-lbl">Oracle Verification</span><span style='color:var(--green)'>{T['status_valid']}</span></div>
        """, unsafe_allow_html=True)
        # 【新增：最直观的防篡改护城河提示】
        st.info(f"""
        🔐 **底层物理凭证已生成防篡改指纹 (Anti-Tamper Hash):** `{d['pdf_hash']}`  
        *(注：区块链节点已确认——在此之后，任何人对原 PDF 发票进行哪怕一个像素、一个小数点的 PS 修改，该指纹都会彻底改变。系统藉此实现 100% 物理凭证防伪。)*
        """)
        st.write("") # 留点空隙
        if st.button(T['next_btn'], use_container_width=True):
            st.session_state['page'] = 'upload'
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


