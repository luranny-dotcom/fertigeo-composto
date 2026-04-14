"""
app.py — Fertigeo | Simulador de Composto Orgânico
Multi-propriedade: cada propriedade tem seus próprios cenários e histórico.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
from supabase import create_client

from business_logic import (
    Material, ParametrosOperacionais, ParametrosComerciais,
    ParametrosAdubacaoQuimica, ParametrosAdubacaoSafrinha,
    MATERIAIS_CENARIO_A, MATERIAIS_CENARIO_B,
    calcular_formulacao, calcular_producao,
    calcular_comercial, rodar_simulacao_completa, analise_sensibilidade,
)

st.set_page_config(page_title="Fertigeo | Composto Orgânico", page_icon="🌱",
                   layout="wide", initial_sidebar_state="expanded")

AZUL="#00313C"; VERDE="#A2B34C"; BRANCO="#FFFFFF"; CINZA="#F5F5F2"; CINZA2="#E8E8E3"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{{font-family:'DM Sans',sans-serif;color:{AZUL};}}
.stApp{{background-color:{CINZA};}}
[data-testid="stSidebar"]{{background-color:{AZUL}!important;}}
[data-testid="stSidebar"] *{{color:{BRANCO}!important;}}
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div{{
    background-color:rgba(255,255,255,0.12)!important;
    border-color:rgba(255,255,255,0.25)!important;
    border-radius:6px!important;
}}
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] span{{
    color:{BRANCO}!important;
}}
[data-testid="stSidebar"] .stSelectbox svg{{
    fill:{BRANCO}!important;
}}
/* lista de opções do dropdown — fundo branco, texto escuro */
[data-testid="stSidebar"] ul[data-testid="stSelectboxVirtualDropdown"]{{
    background-color:{BRANCO}!important;
}}
[data-testid="stSidebar"] ul li span{{
    color:{AZUL}!important;
}}
[data-testid="stSidebar"] ul li:hover{{
    background-color:{CINZA}!important;
}}
[data-testid="stSidebar"] .stSelectbox label{{color:#A2B34C!important;font-weight:600;font-size:.78rem;letter-spacing:.05em;text-transform:uppercase;}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{{color:rgba(255,255,255,.7)!important;font-size:.8rem;}}
[data-testid="stSidebar"] h3{{color:{VERDE}!important;font-size:.8rem!important;letter-spacing:.06em;text-transform:uppercase;margin:0!important;}}
.hero{{background:{AZUL};color:white;padding:1.5rem 2.5rem 1.2rem;border-radius:0 0 16px 16px;margin-bottom:1.5rem;}}
.hero h1{{font-family:'DM Serif Display',serif;font-size:1.8rem;margin:0;line-height:1.2;}}
.hero p{{color:{VERDE};font-size:.85rem;margin:.3rem 0 0;font-weight:500;letter-spacing:.04em;}}
.prop-badge{{display:inline-block;background:rgba(162,179,76,.2);color:{VERDE};border:1px solid rgba(162,179,76,.4);border-radius:20px;padding:2px 12px;font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-bottom:.5rem;}}
.kpi-card{{background:{BRANCO};border:1px solid {CINZA2};border-top:3px solid {VERDE};border-radius:10px;padding:.9rem 1rem;margin-bottom:.5rem;min-height:100px;display:flex;flex-direction:column;justify-content:space-between;}}
.kpi-label{{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:#7A8C6E;margin-bottom:.4rem;line-height:1.3;}}
.kpi-value{{font-family:'DM Serif Display',serif;font-size:clamp(1rem,1.8vw,1.45rem);color:{AZUL};line-height:1.1;word-break:break-word;}}
.kpi-sub{{font-size:.68rem;color:#AAA;margin-top:.3rem;line-height:1.2;}}
.kpi-card.destaque{{border-top-color:{AZUL};background:{AZUL};}}
.kpi-card.destaque .kpi-label{{color:{VERDE};}}
.kpi-card.destaque .kpi-value{{color:{BRANCO};}}
.kpi-card.destaque .kpi-sub{{color:rgba(255,255,255,.55);}}
.kpi-card.positivo{{border-top-color:{VERDE};}}
.kpi-card.positivo .kpi-value{{color:#4A7A1A;}}
.kpi-card.negativo{{border-top-color:#C0392B;}}
.kpi-card.negativo .kpi-value{{color:#C0392B;}}
.secao-titulo{{font-family:'DM Serif Display',serif;font-size:1.25rem;color:{AZUL};border-bottom:2px solid {VERDE};padding-bottom:.4rem;margin:1.5rem 0 1rem;}}
.prop-card{{background:{BRANCO};border:1px solid {CINZA2};border-left:4px solid {VERDE};border-radius:8px;padding:.8rem 1rem;margin-bottom:.5rem;cursor:pointer;}}
.prop-card.ativa{{border-left-color:{AZUL};background:{AZUL};color:white;}}
.prop-card.ativa *{{color:white!important;}}
.rodape{{text-align:center;font-size:.72rem;color:#AAA;margin-top:2rem;padding-top:1rem;border-top:1px solid {CINZA2};}}
/* radio buttons na sidebar */
[data-testid="stSidebar"] .stRadio label{{
    color:{BRANCO}!important;
    font-size:.85rem!important;
    padding:3px 0!important;
    cursor:pointer;
}}
[data-testid="stSidebar"] .stRadio label:hover span{{
    color:{VERDE}!important;
}}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p{{
    color:{BRANCO}!important;
}}
/* dropdown popup global fix */
div[data-baseweb="popover"] ul li span{{
    color:{AZUL}!important;
}}
div[data-baseweb="popover"] ul{{
    background:{BRANCO}!important;
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── HELPERS ──────────────────────────────────────
def fmt_brl(v):
    if v is None: return "—"
    if abs(v) >= 1_000_000: return f"R$ {v/1_000_000:,.2f} M".replace(",","X").replace(".",",").replace("X",".")
    if abs(v) >= 1_000: return f"R$ {v:,.0f}".replace(",","X").replace(".",",").replace("X",".")
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
def fmt_ton(v): return f"{v:,.2f} ton".replace(",","X").replace(".",",").replace("X",".")
def fmt_pct(v): return f"{v:.2f}%"
def kpi(label,value,sub="",tipo=""):
    return f'<div class="kpi-card {tipo}"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>{"<div class=kpi-sub>"+sub+"</div>" if sub else ""}</div>'
def secao(t): st.markdown(f'<div class="secao-titulo">{t}</div>',unsafe_allow_html=True)

CORES=[AZUL,VERDE,"#D6CCA6","#4A7A8A","#8FA840","#2C5F6E","#B8C870","#C4B890","#1A4A56","#E0A050","#7A5A3A"]

# ── SUPABASE ──────────────────────────────────────
SUPABASE_URL = "https://rrkunsulkjhnlzwsrpqc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJya3Vuc3Vsa2pobmx6d3NycHFjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxODkxNzAsImV4cCI6MjA5MTc2NTE3MH0.AgRBpMT9M9oYk-h2mcdEh6ir3HQky364JqnXceDuQp0"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def material_para_dict(m):
    return {"nome":m.nome,"volume_ton":m.volume_ton,"preco_ton":m.preco_ton,
            "N":m.N,"P":m.P,"K":m.K,"B":m.B,"S":m.S,"Zn":m.Zn,"Mg":m.Mg}

def dict_para_material(d):
    return Material(d["nome"],d["volume_ton"],d["preco_ton"],
                    d.get("N",0),d.get("P",0),d.get("K",0),
                    d.get("B",0),d.get("S",0),d.get("Zn",0),d.get("Mg",0))

def params_op_para_dict(p):
    return {"area_ha":p.area_ha,"biotecnologia_ton":p.biotecnologia_ton,
            "fertigeo_ton":p.fertigeo_ton,"processamento_ton":p.processamento_ton,
            "mao_obra_ton":p.mao_obra_ton,"embalagem_ton":p.embalagem_ton,
            "frete_ton":p.frete_ton,"overhead_pct":p.overhead_pct}

def dict_para_params_op(d):
    return ParametrosOperacionais(
        d.get("area_ha",1000),d.get("biotecnologia_ton",0),d.get("fertigeo_ton",0),
        d.get("processamento_ton",0),d.get("mao_obra_ton",0),d.get("embalagem_ton",0),
        d.get("frete_ton",0),d.get("overhead_pct",0))

def salvar_dados():
    try:
        dados = []
        for prop in st.session_state.propriedades:
            cenarios_json = []
            for cen in prop["cenarios"]:
                cenarios_json.append({
                    "nome": cen["nome"],
                    "materiais": [material_para_dict(m) for m in cen["materiais"]],
                    "params_op": params_op_para_dict(cen["params_op"]),
                })
            dados.append({
                "nome": prop["nome"],
                "responsavel": prop.get("responsavel",""),
                "area_ha": prop.get("area_ha",1000),
                "cenarios": cenarios_json,
                "historico": prop.get("historico",[]),
            })
        payload = {"propriedades": dados, "prop_idx": st.session_state.prop_idx}
        sb = get_supabase()
        # Atualiza o único registro existente
        res = sb.table("propriedades").select("id").limit(1).execute()
        if res.data:
            sb.table("propriedades").update({"dados": payload}).eq("id", res.data[0]["id"]).execute()
        else:
            sb.table("propriedades").insert({"dados": payload}).execute()
    except Exception as e:
        st.warning(f"Erro ao salvar: {e}")

def carregar_dados():
    try:
        sb = get_supabase()
        res = sb.table("propriedades").select("dados").limit(1).execute()
        if not res.data:
            return None
        raw = res.data[0]["dados"]
        propriedades = []
        for p in raw.get("propriedades",[]):
            cenarios = []
            for cen in p.get("cenarios",[]):
                cenarios.append({
                    "nome": cen["nome"],
                    "materiais": [dict_para_material(m) for m in cen.get("materiais",[])],
                    "params_op": dict_para_params_op(cen.get("params_op",{})),
                })
            propriedades.append({
                "nome": p["nome"],
                "responsavel": p.get("responsavel",""),
                "area_ha": p.get("area_ha",1000),
                "cenarios": cenarios,
                "historico": p.get("historico",[]),
            })
        return {"propriedades": propriedades, "prop_idx": raw.get("prop_idx",0)}
    except Exception:
        return None

# ── SESSION STATE ─────────────────────────────────
def nova_propriedade(nome, responsavel=""):
    return {
        "nome": nome,
        "responsavel": responsavel,
        "area_ha": 1000.0,
        "cenarios": [
            {"nome":"Com Cama de Frango","materiais":deepcopy(MATERIAIS_CENARIO_A),"params_op":ParametrosOperacionais(area_ha=1000.0)},
            {"nome":"Resíduo Interno","materiais":deepcopy(MATERIAIS_CENARIO_B),"params_op":ParametrosOperacionais(area_ha=500.0)},
        ],
        "historico": [],
    }

def init_state():
    if "propriedades" not in st.session_state:
        dados = carregar_dados()
        if dados:
            st.session_state.propriedades = dados["propriedades"]
            st.session_state.prop_idx = min(dados["prop_idx"], len(dados["propriedades"])-1)
        else:
            st.session_state.propriedades = [nova_propriedade("Fazenda Brasilanda")]
            st.session_state.prop_idx = 0
init_state()

def prop_atual():
    idx = st.session_state.prop_idx
    return st.session_state.propriedades[idx]

# ── SIDEBAR ───────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div style="text-align:center;padding:.8rem 0 1.2rem;"><div style="font-family:DM Serif Display,serif;font-size:1.4rem;color:white;">🌱 Fertigeo</div><div style="color:#A2B34C;font-size:.72rem;margin-top:4px;letter-spacing:.06em;">SIMULADOR DE COMPOSTO</div></div>', unsafe_allow_html=True)

    # Seleção de propriedade
    st.markdown("### 🏡 PROPRIEDADE")
    nomes_props = [p["nome"] for p in st.session_state.propriedades]
    novo_idx = st.radio("", range(len(nomes_props)),
                         format_func=lambda i: nomes_props[i],
                         index=st.session_state.prop_idx,
                         label_visibility="collapsed", key="sb_prop")
    if novo_idx != st.session_state.prop_idx:
        st.session_state.prop_idx = novo_idx
        st.rerun()

    p = prop_atual()
    st.markdown(f'<p>📍 {len(p["cenarios"])} cenário(s) · {len(p["historico"])} simulação(ões)</p>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📄 PÁGINA")
    pagina = st.radio("", [
        "🏠 Dashboard Executivo",
        "🏡 Gerenciar Propriedades",
        "⚙️ Gerenciar Cenários",
        "💰 Simulação Comercial",
        "📊 Comparação de Cenários",
        "📈 Análise de Sensibilidade",
        "📋 Proposta Comercial",
    ], label_visibility="collapsed", key="sb_pag")

    st.markdown("---")
    if st.button("💾 Salvar Dados", use_container_width=True, key="btn_salvar"):
        salvar_dados()
        st.success("Salvo!")
    st.markdown('<p>Fertigeo · Agência de Inteligência no Agronegócio</p>', unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────
titulos = {
    "🏠 Dashboard Executivo":     ("Dashboard Executivo",      "Indicadores estratégicos em tempo real"),
    "🏡 Gerenciar Propriedades":  ("Gerenciar Propriedades",   "Cadastre, edite e alterne entre propriedades"),
    "⚙️ Gerenciar Cenários":      ("Gerenciar Cenários",       "Formulações e parâmetros operacionais"),
    "💰 Simulação Comercial":     ("Simulação Comercial",      "Preço, margem e lucro em tempo real"),
    "📊 Comparação de Cenários":  ("Comparação de Cenários",   "Compare todos os cenários desta propriedade"),
    "📈 Análise de Sensibilidade":("Análise de Sensibilidade", "Impacto de variação de custos"),
    "📋 Proposta Comercial":      ("Proposta Comercial",       "Gere proposta formatada para o cliente"),
}
h1, h2 = titulos.get(pagina, ("",""))
p = prop_atual()
st.markdown(f"""
<div class="hero">
  <div class="prop-badge">🏡 {p['nome']}</div>
  <h1>{h1}</h1>
  <p>{h2}{' · Responsável: ' + p['responsavel'] if p.get('responsavel') else ''}</p>
</div>
""", unsafe_allow_html=True)


# ── FORMULÁRIOS ───────────────────────────────────
def _mats_para_df(materiais):
    return pd.DataFrame([{
        "Material": m.nome, "Volume (ton)": float(m.volume_ton),
        "Preço/ton (R$)": float(m.preco_ton),
        "N %": round(float(m.N*100),4), "P %": round(float(m.P*100),4),
        "K %": round(float(m.K*100),4), "B %": round(float(m.B*100),4),
        "S %": round(float(m.S*100),4), "Zn %": round(float(m.Zn*100),4),
        "Mg %": round(float(m.Mg*100),4),
    } for m in materiais])

def _df_para_mats(df):
    novos = []
    for _, row in df.iterrows():
        def v(col, r=row): return r[col] if pd.notna(r.get(col, None)) else 0.0
        novos.append(Material(
            nome=str(row["Material"]) if pd.notna(row.get("Material")) else "—",
            volume_ton=float(v("Volume (ton)")), preco_ton=float(v("Preço/ton (R$)")),
            N=float(v("N %"))/100, P=float(v("P %"))/100, K=float(v("K %"))/100,
            B=float(v("B %"))/100, S=float(v("S %"))/100,
            Zn=float(v("Zn %"))/100, Mg=float(v("Mg %"))/100,
        ))
    return novos

def formulario_materiais(materiais, prefixo):
    _df_key = f"{prefixo}_df"
    if _df_key not in st.session_state:
        st.session_state[_df_key] = _mats_para_df(materiais)

    col_config = {
        "Material":       st.column_config.TextColumn("Material", width="large"),
        "Volume (ton)":   st.column_config.NumberColumn("Volume (ton)",   min_value=0.0, step=10.0,  format="%.2f"),
        "Preço/ton (R$)": st.column_config.NumberColumn("Preço/ton (R$)", min_value=0.0, step=10.0,  format="%.2f"),
        "N %":  st.column_config.NumberColumn("N %",  min_value=0.0, max_value=100.0, step=0.1, format="%.2f"),
        "P %":  st.column_config.NumberColumn("P %",  min_value=0.0, max_value=100.0, step=0.1, format="%.2f"),
        "K %":  st.column_config.NumberColumn("K %",  min_value=0.0, max_value=100.0, step=0.1, format="%.2f"),
        "B %":  st.column_config.NumberColumn("B %",  min_value=0.0, max_value=100.0, step=0.1, format="%.3f"),
        "S %":  st.column_config.NumberColumn("S %",  min_value=0.0, max_value=100.0, step=0.1, format="%.2f"),
        "Zn %": st.column_config.NumberColumn("Zn %", min_value=0.0, max_value=100.0, step=0.1, format="%.3f"),
        "Mg %": st.column_config.NumberColumn("Mg %", min_value=0.0, max_value=100.0, step=0.1, format="%.3f"),
    }

    # Usa st.form para evitar reruns enquanto digita — resolve bug de linhas alternadas
    with st.form(key=f"{prefixo}_form"):
        edited = st.data_editor(
            st.session_state[_df_key], column_config=col_config,
            use_container_width=True, num_rows="dynamic",
            hide_index=True,
        )
        fc1, fc2 = st.columns([1, 5])
        submitted = fc1.form_submit_button("💾 Aplicar alterações", use_container_width=True)

    if submitted:
        st.session_state[_df_key] = edited
        st.rerun()

    # Totais baseados no df salvo
    df_atual = st.session_state[_df_key]
    vol_total   = df_atual["Volume (ton)"].fillna(0).sum()
    custo_total = (df_atual["Volume (ton)"].fillna(0) * df_atual["Preço/ton (R$)"].fillna(0)).sum()
    vol_fmt = f"{vol_total:,.2f}".replace(",","X").replace(".",",").replace("X",".")
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:1rem;padding:.55rem 1.2rem;background:#F0F0EC;border:1px solid #E8E8E3;border-top:2px solid #00313C;border-radius:0 0 8px 8px;margin-top:-2px;">
        <span style="font-size:.72rem;font-weight:700;color:#7A8C6E;text-transform:uppercase;letter-spacing:.07em;margin-right:.5rem;">TOTAL</span>
        <div style="background:#00313C;color:white;border-radius:6px;padding:.3rem .9rem;font-weight:700;font-size:.85rem;">{vol_fmt} ton</div>
        <div style="background:#A2B34C;color:white;border-radius:6px;padding:.3rem .9rem;font-weight:700;font-size:.85rem;">{fmt_brl(custo_total)}</div>
    </div>
    """, unsafe_allow_html=True)

    return _df_para_mats(df_atual)
def formulario_params_op(prefixo, defaults=None):
    if defaults is None: defaults = ParametrosOperacionais()
    c1,c2,c3,c4 = st.columns(4)
    area  = c1.number_input("Área de Aplicação (ha)",        value=float(defaults.area_ha),           min_value=1.0, step=50.0, key=f"{prefixo}_area")
    mo    = c2.number_input("Mão de Obra (R$/ton)",          value=float(defaults.mao_obra_ton),      min_value=0.0, step=5.0,  key=f"{prefixo}_mo")
    emb   = c3.number_input("Embalagem (R$/ton)",            value=float(defaults.embalagem_ton),     min_value=0.0, step=5.0,  key=f"{prefixo}_emb")
    frete = c4.number_input("Frete (R$/ton)",                value=float(defaults.frete_ton),         min_value=0.0, step=5.0,  key=f"{prefixo}_frete")
    c5,c6,c7,c8 = st.columns(4)
    bio   = c5.number_input("Biotecnologia (R$/ton)",        value=float(defaults.biotecnologia_ton), min_value=0.0, step=5.0,  key=f"{prefixo}_bio")
    fert  = c6.number_input("Consultoria Fertigeo (R$/ton)", value=float(defaults.fertigeo_ton),      min_value=0.0, step=5.0,  key=f"{prefixo}_fert")
    proc  = c7.number_input("Processamento (R$/ton)",        value=float(defaults.processamento_ton), min_value=0.0, step=5.0,  key=f"{prefixo}_proc")
    oh    = c8.number_input("Overhead (%)",                  value=float(defaults.overhead_pct),      min_value=0.0, max_value=50.0, step=0.5, key=f"{prefixo}_oh")
    return ParametrosOperacionais(area,bio,fert,proc,mo,emb,frete,oh)

# ── GRÁFICOS ──────────────────────────────────────
def g_composicao(mats, titulo):
    f = calcular_formulacao(mats)
    labels = [r["nome"] for r in f["materiais"] if r["volume_ton"]>0]
    values = [r["pct_uso"]*100 for r in f["materiais"] if r["volume_ton"]>0]
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.55,
                            marker=dict(colors=CORES[:len(labels)]),
                            textinfo="label+percent", textfont_size=11))
    fig.update_layout(title=dict(text=titulo, font=dict(family="DM Serif Display",size=14,color=AZUL)),
                      showlegend=False, margin=dict(t=50,b=10,l=10,r=10),
                      paper_bgcolor="rgba(0,0,0,0)", height=300)
    return fig

def g_custo(mats, params_op):
    f = calcular_formulacao(mats); prod = calcular_producao(f, params_op)
    labels=[]; values=[]
    for r in f["materiais"]:
        if r["custo_total"]>0: labels.append(r["nome"]); values.append(r["custo_total"]/f["total_volume_ton"])
    for nome,val in [("Mão de Obra",params_op.mao_obra_ton),("Embalagem",params_op.embalagem_ton),
                     ("Frete",params_op.frete_ton),("Biotecnologia",params_op.biotecnologia_ton),
                     ("Fertigeo",params_op.fertigeo_ton),("Processamento",params_op.processamento_ton),
                     ("Overhead",prod["custo_overhead_ton"])]:
        if val>0: labels.append(nome); values.append(val)
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h",
                            marker_color=CORES[:len(labels)],
                            text=[f"R$ {v:.2f}" for v in values], textposition="outside"))
    fig.update_layout(title=dict(text="Custo por Componente (R$/ton)", font=dict(family="DM Serif Display",size=14,color=AZUL)),
                      xaxis_title="R$/ton", margin=dict(t=50,b=20,l=180,r=80),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=320, xaxis=dict(showgrid=True,gridcolor=CINZA2))
    return fig

def g_nutrientes(prod):
    nuts = {"N":prod["N_kg_ha"],"P":prod["P_kg_ha"],"K":prod["K_kg_ha"],
            "B":prod["B_kg_ha"],"S":prod["S_kg_ha"],"Zn":prod["Zn_kg_ha"]}
    fig = go.Figure(go.Bar(x=list(nuts.keys()), y=list(nuts.values()),
                            marker_color=[AZUL,VERDE,"#D6CCA6","#4A7A8A","#8FA840","#B8C870"],
                            text=[f"{v:.1f}" for v in nuts.values()], textposition="outside"))
    fig.update_layout(title=dict(text="Nutrientes por Hectare (kg/ha)", font=dict(family="DM Serif Display",size=14,color=AZUL)),
                      yaxis_title="kg/ha", margin=dict(t=50,b=30,l=40,r=20),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=300, yaxis=dict(showgrid=True,gridcolor=CINZA2))
    return fig

def g_quimico(q):
    fig = go.Figure(go.Bar(
        x=["Químico (Safra)","Químico (Safrinha)","Orgânico"],
        y=[q["custo_safra_ha"],q["custo_safrinha_ha"],q["custo_organico_total_ha"]],
        marker_color=["#C0392B","#E07060",VERDE],
        text=[fmt_brl(v) for v in [q["custo_safra_ha"],q["custo_safrinha_ha"],q["custo_organico_total_ha"]]],
        textposition="outside"))
    fig.update_layout(title=dict(text="Custo/ha: Orgânico vs Químico", font=dict(family="DM Serif Display",size=14,color=AZUL)),
                      yaxis_title="R$/ha", margin=dict(t=50,b=30,l=60,r=20),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=320, yaxis=dict(showgrid=True,gridcolor=CINZA2))
    return fig

def g_waterfall(com):
    fig = go.Figure(go.Waterfall(orientation="v",
        measure=["absolute","relative","relative","total"],
        x=["Receita Bruta","- Impostos","- Custo Total","Lucro Líquido"],
        y=[com["receita_bruta"],-com["impostos_valor"],-com["custo_venda"],None],
        connector=dict(line=dict(color=CINZA2)),
        increasing=dict(marker=dict(color=VERDE)),
        decreasing=dict(marker=dict(color="#C0392B")),
        totals=dict(marker=dict(color=AZUL)),
        text=[fmt_brl(v) for v in [com["receita_bruta"],-com["impostos_valor"],-com["custo_venda"],com["lucro_liquido"]]],
        textposition="outside"))
    fig.update_layout(title=dict(text="Resultado Comercial", font=dict(family="DM Serif Display",size=14,color=AZUL)),
                      margin=dict(t=50,b=30,l=60,r=20),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=360, yaxis=dict(showgrid=True,gridcolor=CINZA2))
    return fig

def g_sens(resultados, label):
    variacoes=[r["variacao_pct"] for r in resultados]; custos=[r["custo_ton"] for r in resultados]
    base = resultados[len(resultados)//2]["custo_ton"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=variacoes, y=custos, mode="lines+markers",
                              line=dict(color=AZUL,width=2), marker=dict(color=VERDE,size=7)))
    fig.add_hline(y=base, line_dash="dash", line_color="#999", annotation_text="Base")
    fig.update_layout(title=dict(text=label, font=dict(family="DM Serif Display",size=13,color=AZUL)),
                      xaxis_title="Variação (%)", yaxis_title="Custo/ton (R$)",
                      margin=dict(t=50,b=40,l=60,r=20),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=280, xaxis=dict(showgrid=True,gridcolor=CINZA2),
                      yaxis=dict(showgrid=True,gridcolor=CINZA2))
    return fig


# ═══════════════════════════════════════════════════════
# PÁGINA 0: GERENCIAR PROPRIEDADES
# ═══════════════════════════════════════════════════════
if pagina == "🏡 Gerenciar Propriedades":

    secao("➕ Nova Propriedade")
    np1, np2, np3 = st.columns([3,2,1])
    novo_prop_nome = np1.text_input("Nome da propriedade", placeholder="Ex: Fazenda Santa Maria")
    novo_prop_resp = np2.text_input("Responsável", placeholder="Ex: João Silva")
    if np3.button("✅ Criar", use_container_width=True):
        if not novo_prop_nome.strip():
            st.error("Digite um nome para a propriedade.")
        elif novo_prop_nome.strip() in [p["nome"] for p in st.session_state.propriedades]:
            st.error("Já existe uma propriedade com esse nome.")
        else:
            st.session_state.propriedades.append(nova_propriedade(novo_prop_nome.strip(), novo_prop_resp.strip()))
            st.session_state.prop_idx = len(st.session_state.propriedades) - 1
            salvar_dados()
            st.success(f"Propriedade '{novo_prop_nome}' criada e selecionada!")
            st.rerun()

    st.markdown("---")
    secao("📋 Propriedades Cadastradas")

    for i, prop in enumerate(st.session_state.propriedades):
        ativa = (i == st.session_state.prop_idx)
        with st.container():
            ca, cb, cc, cd, ce = st.columns([3,2,1,1,1])
            # Nome editável
            _kn = f"prop_nome_{i}"
            _kr = f"prop_resp_{i}"
            if _kn not in st.session_state:
                st.session_state[_kn] = prop["nome"]
            if _kr not in st.session_state:
                st.session_state[_kr] = prop.get("responsavel","")

            def _salvar_prop_nome(i=i):
                st.session_state.propriedades[i]["nome"] = st.session_state[f"prop_nome_{i}"]
            def _salvar_prop_resp(i=i):
                st.session_state.propriedades[i]["responsavel"] = st.session_state[f"prop_resp_{i}"]

            ca.text_input("", key=_kn, label_visibility="collapsed", on_change=_salvar_prop_nome)
            cb.text_input("", key=_kr, placeholder="Responsável", label_visibility="collapsed", on_change=_salvar_prop_resp)

            cc.markdown(f"<small style='color:#888'>{len(prop['cenarios'])} cenários<br>{len(prop['historico'])} simulações</small>", unsafe_allow_html=True)

            if not ativa:
                if cd.button("🔀 Selecionar", key=f"sel_prop_{i}", use_container_width=True):
                    st.session_state.prop_idx = i
                    st.rerun()
            else:
                cd.markdown("<small style='color:#A2B34C;font-weight:700;'>✅ Ativa</small>", unsafe_allow_html=True)

            if len(st.session_state.propriedades) > 1:
                if ce.button("🗑️", key=f"del_prop_{i}", use_container_width=True):
                    st.session_state.propriedades.pop(i)
                    st.session_state.prop_idx = max(0, st.session_state.prop_idx - 1)
                    salvar_dados()
                    st.rerun()
            else:
                ce.caption("mín. 1")

        st.markdown("---")

    st.info("💡 Para editar os cenários e matérias-primas de uma propriedade, selecione-a e vá para ⚙️ Gerenciar Cenários.")


# ═══════════════════════════════════════════════════════
# PÁGINA 1: DASHBOARD
# ═══════════════════════════════════════════════════════
elif pagina == "🏠 Dashboard Executivo":
    p = prop_atual()
    if not p["cenarios"]: st.warning("Crie um cenário em ⚙️ Gerenciar Cenários."); st.stop()

    nomes = [c["nome"] for c in p["cenarios"]]
    c1,c2,c3,c4,c5 = st.columns(5)
    idx   = c1.selectbox("Cenário", range(len(nomes)), format_func=lambda i:nomes[i], key="d_cen")
    area  = c2.number_input("Área (ha)", value=float(p["cenarios"][idx]["params_op"].area_ha), min_value=1.0, step=50.0, key="d_area")
    frete = c3.number_input("Frete (R$/ton)", value=0.0, min_value=0.0, step=5.0, key="d_frete")
    margem= c4.number_input("Margem (%)", value=20.0, min_value=0.0, max_value=100.0, step=1.0, key="d_margem")
    vol   = c5.number_input("Vol. negociado (ton)", value=1000.0, min_value=0.0, step=100.0, key="d_vol")

    cen = p["cenarios"][idx]
    op  = ParametrosOperacionais(area_ha=area, frete_ton=frete,
                                  mao_obra_ton=float(cen["params_op"].mao_obra_ton),
                                  embalagem_ton=float(cen["params_op"].embalagem_ton))
    res = rodar_simulacao_completa(cen["materiais"], op,
                                   ParametrosComerciais(margem_desejada_pct=margem, volume_negociado_ton=vol),
                                   ParametrosAdubacaoQuimica(), ParametrosAdubacaoSafrinha())
    f,prod,q,c = res["formulacao"],res["producao"],res["quimica"],res["comercial"]

    secao(f"🔑 Indicadores-Chave — {cen['nome']}")
    cols = st.columns(5)
    for col,(label,val,sub,tipo) in zip(cols,[
        ("Custo Total/Ton",     fmt_brl(prod["custo_total_ton"]),       "MP + operacional",              "destaque"),
        ("Custo Total Prod.",   fmt_brl(prod["custo_total_producao"]),  fmt_ton(f["total_volume_ton"]),  ""),
        ("Preço Sugerido/Ton",  fmt_brl(c["preco_sugerido"]),           f"margem {fmt_pct(margem)}",     ""),
        ("Custo/Hectare",       fmt_brl(prod["custo_ha"]),              f"dose {prod['dose_kg_ha']:.0f} kg/ha",""),
        ("Saldo vs Químico/ha", fmt_brl(q["saldo_ha"]),                 f"economia {fmt_pct(q['economia_pct'])}", "positivo" if q["saldo_ha"]>0 else "negativo"),
    ]):
        col.markdown(kpi(label,val,sub,tipo), unsafe_allow_html=True)

    st.markdown("")
    cols2 = st.columns(5)
    for col,(label,val,sub,tipo) in zip(cols2,[
        ("Lucro Estimado",    fmt_brl(c["lucro_bruto"]),           fmt_ton(c["vol_negociado"]),         "positivo" if c["lucro_bruto"]>0 else "negativo"),
        ("Margem Bruta Real", fmt_pct(c["margem_bruta_pct"]),      f"markup {fmt_pct(c['markup_pct'])}", ""),
        ("Ponto Equilíbrio",  fmt_ton(c["ponto_equilibrio_ton"]), "volume mínimo rentável",             ""),
        ("ROI",               fmt_pct(c["roi_pct"]),               "retorno sobre custo",               ""),
        ("Vol. Total Prod.",  fmt_ton(f["total_volume_ton"]),      f"{len([m for m in cen['materiais'] if m.volume_ton>0])} insumos",""),
    ]):
        col.markdown(kpi(label,val,sub,tipo), unsafe_allow_html=True)

    st.markdown("---")
    cg1,cg2 = st.columns(2)
    with cg1: st.plotly_chart(g_composicao(cen["materiais"],f"Composição — {cen['nome']}"), use_container_width=True)
    with cg2: st.plotly_chart(g_custo(cen["materiais"],op), use_container_width=True)
    cg3,cg4 = st.columns(2)
    with cg3: st.plotly_chart(g_nutrientes(prod), use_container_width=True)
    with cg4: st.plotly_chart(g_quimico(q), use_container_width=True)

    secao("🌿 Garantia de Nutrientes")
    for col,(label,grt,dose) in zip(st.columns(7),[
        ("N",  f"{f['garantia_N']*100:.3f}%",  f"{prod['N_kg_ha']:.1f} kg/ha"),
        ("P",  f"{f['garantia_P']*100:.3f}%",  f"{prod['P_kg_ha']:.1f} kg/ha"),
        ("K",  f"{f['garantia_K']*100:.3f}%",  f"{prod['K_kg_ha']:.1f} kg/ha"),
        ("B",  f"{f['garantia_B']*100:.4f}%",  f"{prod['B_kg_ha']:.2f} kg/ha"),
        ("S",  f"{f['garantia_S']*100:.3f}%",  f"{prod['S_kg_ha']:.1f} kg/ha"),
        ("Zn", f"{f['garantia_Zn']*100:.4f}%", f"{prod['Zn_kg_ha']:.2f} kg/ha"),
        ("Mg", f"{f['garantia_Mg']*100:.3f}%", f"{prod['Mg_kg_ha']:.1f} kg/ha"),
    ]):
        col.markdown(kpi(label,grt,dose), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# PÁGINA 2: GERENCIAR CENÁRIOS
# ═══════════════════════════════════════════════════════
elif pagina == "⚙️ Gerenciar Cenários":
    p = prop_atual()
    pi = st.session_state.prop_idx

    secao("➕ Criar Novo Cenário")
    cn1,cn2,cn3 = st.columns([3,2,1])
    novo_nome = cn1.text_input("Nome do novo cenário", placeholder="Ex: Alta Cama de Frango")
    base_opcoes = ["Em branco"] + [c["nome"] for c in p["cenarios"]]
    base_sel = cn2.selectbox("Copiar base de", base_opcoes)
    if cn3.button("✅ Criar", use_container_width=True):
        if not novo_nome.strip(): st.error("Digite um nome.")
        else:
            if base_sel=="Em branco": nm=[Material("Nova Matéria-Prima",0.0,0.0)]; np_op=ParametrosOperacionais()
            else:
                bi = base_opcoes.index(base_sel)-1
                nm = deepcopy(p["cenarios"][bi]["materiais"]); np_op = deepcopy(p["cenarios"][bi]["params_op"])
            st.session_state.propriedades[pi]["cenarios"].append({"nome":novo_nome.strip(),"materiais":nm,"params_op":np_op})
            salvar_dados()
            st.success(f"Cenário '{novo_nome}' criado!"); st.rerun()

    st.markdown("---")
    if not p["cenarios"]: st.info("Nenhum cenário cadastrado."); st.stop()

    nomes = [c["nome"] for c in p["cenarios"]]
    idx_edit = st.selectbox("Selecione o cenário para editar",
                             range(len(nomes)), format_func=lambda i: f"Cenário {i+1}: {nomes[i]}")
    cen = p["cenarios"][idx_edit]

    col_nome, col_del = st.columns([5,1])
    # Inicializa key apenas se não existe (não resetar enquanto usuário digita)
    _key_nome = f"nome_edit_{pi}_{idx_edit}"
    if _key_nome not in st.session_state:
        st.session_state[_key_nome] = cen["nome"]

    def _salvar_nome_cen():
        st.session_state.propriedades[pi]["cenarios"][idx_edit]["nome"] = st.session_state[_key_nome]

    col_nome.text_input("✏️ Nome do Cenário", key=_key_nome, on_change=_salvar_nome_cen)

    if len(p["cenarios"]) > 1:
        if col_del.button("🗑️ Excluir", key=f"del_cen_{pi}_{idx_edit}", use_container_width=True):
            st.session_state.propriedades[pi]["cenarios"].pop(idx_edit)
            salvar_dados()
            st.success("Excluído."); st.rerun()
    else:
        col_del.caption("(mín. 1)")

    secao("📦 Matérias-Primas")
    st.caption("Clique na célula para editar. Última linha em branco: nova matéria-prima. Selecione a linha e Delete para remover.")
    st.session_state.propriedades[pi]["cenarios"][idx_edit]["materiais"] = \
        formulario_materiais(cen["materiais"], f"p{pi}c{idx_edit}")

    secao("⚙️ Parâmetros Operacionais")
    st.session_state.propriedades[pi]["cenarios"][idx_edit]["params_op"] = \
        formulario_params_op(f"op_{pi}_{idx_edit}", cen["params_op"])

    secao("👁️ Preview Rápido")
    fp = calcular_formulacao(st.session_state.propriedades[pi]["cenarios"][idx_edit]["materiais"])
    pp = calcular_producao(fp, st.session_state.propriedades[pi]["cenarios"][idx_edit]["params_op"])
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Volume Total", fmt_ton(fp["total_volume_ton"]))
    c2.metric("Custo MP", fmt_brl(fp["total_custo_materiais"]))
    c3.metric("Custo/Ton", fmt_brl(pp["custo_total_ton"]))
    c4.metric("Custo/ha", fmt_brl(pp["custo_ha"]))

    with st.expander("🔍 Conferência detalhada do cálculo de garantia"):
        rows_conf = []
        vol_total = fp["total_volume_ton"]
        for r in fp["materiais"]:
            m_obj = next((m for m in st.session_state.propriedades[pi]["cenarios"][idx_edit]["materiais"] if m.nome == r["nome"]), None)
            rows_conf.append({
                "Material":     r["nome"],
                "Volume (ton)": f"{r['volume_ton']:,.0f}".replace(",","."),
                "% Uso":        f"{r['pct_uso']*100:.2f}%",
                "N% entrada":   f"{m_obj.N*100:.3f}%" if m_obj else "?",
                "Contrib N":    f"{r['contrib_N']*100:.4f}%",
                "P% entrada":   f"{m_obj.P*100:.3f}%" if m_obj else "?",
                "Contrib P":    f"{r['contrib_P']*100:.4f}%",
                "K% entrada":   f"{m_obj.K*100:.3f}%" if m_obj else "?",
                "Contrib K":    f"{r['contrib_K']*100:.4f}%",
                "Mg% entrada":  f"{m_obj.Mg*100:.3f}%" if m_obj else "?",
                "Contrib Mg":   f"{r['contrib_Mg']*100:.4f}%",
            })
        # Linha de totais
        rows_conf.append({
            "Material": "TOTAL",
            "Volume (ton)": f"{vol_total:,.0f}".replace(",","."),
            "% Uso": "100%",
            "N% entrada": "—",
            "Contrib N": f"{fp['garantia_N']*100:.4f}%",
            "P% entrada": "—",
            "Contrib P": f"{fp['garantia_P']*100:.4f}%",
            "K% entrada": "—",
            "Contrib K": f"{fp['garantia_K']*100:.4f}%",
            "Mg% entrada": "—",
            "Contrib Mg": f"{fp['garantia_Mg']*100:.4f}%",
        })
        st.dataframe(pd.DataFrame(rows_conf), use_container_width=True, hide_index=True)
        st.caption("Contrib = % Uso × concentração entrada. A soma das Contrib é a Garantia do produto final.")


# ═══════════════════════════════════════════════════════
# PÁGINA 3: SIMULAÇÃO COMERCIAL
# ═══════════════════════════════════════════════════════
elif pagina == "💰 Simulação Comercial":
    p = prop_atual(); pi = st.session_state.prop_idx
    if not p["cenarios"]: st.warning("Crie um cenário primeiro."); st.stop()

    nomes = [c["nome"] for c in p["cenarios"]]
    idx = st.selectbox("Cenário Base", range(len(nomes)), format_func=lambda i:nomes[i], key="sim_cen")
    cen = p["cenarios"][idx]

    secao("Parâmetros Operacionais")
    op_sim = formulario_params_op(f"sim_{pi}_{idx}", cen["params_op"])

    secao("Parâmetros Comerciais")
    cc1,cc2,cc3,cc4 = st.columns(4)
    margem   = cc1.slider("Margem desejada (%)",      0.0, 80.0, 20.0, 0.5)
    impostos = cc2.slider("Impostos sobre venda (%)", 0.0, 30.0,  0.0, 0.5)
    desconto = cc3.slider("Desconto comercial (%)",   0.0, 30.0,  0.0, 0.5)
    vol_neg  = cc4.number_input("Volume negociado (ton)",
                                 value=float(calcular_formulacao(cen["materiais"])["total_volume_ton"]),
                                 min_value=0.0, step=50.0)

    com_p = ParametrosComerciais(margem_desejada_pct=margem, impostos_pct=impostos,
                                  desconto_comercial_pct=desconto, volume_negociado_ton=vol_neg)
    fs = calcular_formulacao(cen["materiais"])
    ps = calcular_producao(fs, op_sim)
    cs = calcular_comercial(fs, ps, com_p)

    st.markdown("---"); secao("📊 Resultado")
    r1,r2 = st.columns([2,1])
    with r1: st.plotly_chart(g_waterfall(cs), use_container_width=True)
    with r2:
        for label,val,sub,tipo in [
            ("Custo/Ton Total",    fmt_brl(cs["custo_ton"]),        "MP + operacional",              "destaque"),
            ("Preço Sugerido/Ton", fmt_brl(cs["preco_sugerido"]),   "antes do desconto",             ""),
            ("Preço Líquido/Ton",  fmt_brl(cs["preco_liquido"]),    f"desconto {fmt_pct(desconto)}", ""),
            ("Receita Bruta",      fmt_brl(cs["receita_bruta"]),    fmt_ton(cs["vol_negociado"]),    ""),
            ("Lucro Bruto",        fmt_brl(cs["lucro_bruto"]),      f"margem {fmt_pct(cs['margem_bruta_pct'])}", "positivo" if cs["lucro_bruto"]>0 else "negativo"),
            ("Ponto de Equilíbrio",fmt_ton(cs["ponto_equilibrio_ton"]), "volume mínimo",             ""),
        ]:
            st.markdown(kpi(label,val,sub,tipo), unsafe_allow_html=True)

    secao("📋 Detalhamento")
    df = pd.DataFrame({"Indicador":["Custo/Ton","Preço Sugerido/Ton","Preço Líquido/Ton","Receita Bruta","Impostos","Receita Líquida","Custo de Venda","Lucro Bruto","Lucro Líquido","Margem Bruta","Margem Líquida","Markup","ROI"],
                        "Valor":[fmt_brl(cs["custo_ton"]),fmt_brl(cs["preco_sugerido"]),fmt_brl(cs["preco_liquido"]),fmt_brl(cs["receita_bruta"]),fmt_brl(cs["impostos_valor"]),fmt_brl(cs["receita_liquida"]),fmt_brl(cs["custo_venda"]),fmt_brl(cs["lucro_bruto"]),fmt_brl(cs["lucro_liquido"]),fmt_pct(cs["margem_bruta_pct"]),fmt_pct(cs["margem_liquida_pct"]),fmt_pct(cs["markup_pct"]),fmt_pct(cs["roi_pct"])]})
    st.dataframe(df, use_container_width=True, hide_index=True)

    if st.button("📌 Salvar no Histórico desta Propriedade"):
        st.session_state.propriedades[pi]["historico"].append({
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Cenário": cen["nome"],
            "Custo/Ton": fmt_brl(cs["custo_ton"]),
            "Preço/Ton": fmt_brl(cs["preco_liquido"]),
            "Margem %": fmt_pct(cs["margem_bruta_pct"]),
            "Lucro": fmt_brl(cs["lucro_bruto"]),
            "Volume": fmt_ton(cs["vol_negociado"]),
        })
        salvar_dados()
        st.success(f"Salvo no histórico de {p['nome']}!")

    if p["historico"]:
        secao(f"📜 Histórico — {p['nome']}")
        st.dataframe(pd.DataFrame(p["historico"]), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════
# PÁGINA 4: COMPARAÇÃO
# ═══════════════════════════════════════════════════════
elif pagina == "📊 Comparação de Cenários":
    p = prop_atual()
    if len(p["cenarios"]) < 2: st.warning("Crie pelo menos 2 cenários para comparar."); st.stop()

    pc1,pc2,pc3 = st.columns(3)
    area_c   = pc1.number_input("Área (ha)",              value=1000.0, min_value=1.0, step=50.0,  key="cmp_area")
    margem_c = pc2.number_input("Margem (%)",             value=20.0,   min_value=0.0, step=1.0,   key="cmp_margem")
    vol_c    = pc3.number_input("Volume negociado (ton)", value=1000.0, min_value=0.0, step=100.0, key="cmp_vol")

    com_c = ParametrosComerciais(margem_desejada_pct=margem_c, volume_negociado_ton=vol_c)
    resultados = []
    for cen in p["cenarios"]:
        op_c = ParametrosOperacionais(area_ha=area_c,
            mao_obra_ton=float(cen["params_op"].mao_obra_ton), embalagem_ton=float(cen["params_op"].embalagem_ton),
            frete_ton=float(cen["params_op"].frete_ton), biotecnologia_ton=float(cen["params_op"].biotecnologia_ton),
            fertigeo_ton=float(cen["params_op"].fertigeo_ton), processamento_ton=float(cen["params_op"].processamento_ton),
            overhead_pct=float(cen["params_op"].overhead_pct))
        res = rodar_simulacao_completa(cen["materiais"],op_c,com_c,ParametrosAdubacaoQuimica(),ParametrosAdubacaoSafrinha())
        resultados.append({"nome":cen["nome"],**res})

    secao("⚖️ Comparativo")
    indicadores=[
        ("Volume Total (ton)",    lambda r:r["formulacao"]["total_volume_ton"],     "ton", True),
        ("Custo MP Total (R$)",   lambda r:r["formulacao"]["total_custo_materiais"],"R$",  False),
        ("Custo/Ton Total (R$)",  lambda r:r["producao"]["custo_total_ton"],        "R$",  False),
        ("Custo/ha (R$)",         lambda r:r["producao"]["custo_ha"],               "R$",  False),
        ("Dose (kg/ha)",          lambda r:r["producao"]["dose_kg_ha"],             "kg",  True),
        ("N/ha (kg)",             lambda r:r["producao"]["N_kg_ha"],                "kg",  True),
        ("P/ha (kg)",             lambda r:r["producao"]["P_kg_ha"],                "kg",  True),
        ("K/ha (kg)",             lambda r:r["producao"]["K_kg_ha"],                "kg",  True),
        ("Preço/Ton (R$)",        lambda r:r["comercial"]["preco_sugerido"],        "R$",  False),
        ("Lucro Bruto (R$)",      lambda r:r["comercial"]["lucro_bruto"],           "R$",  True),
        ("Margem Bruta (%)",      lambda r:r["comercial"]["margem_bruta_pct"],      "%",   True),
        ("Saldo vs Químico/ha",   lambda r:r["quimica"]["saldo_ha"],                "R$",  True),
    ]
    cols_h = st.columns([3]+[2]*len(resultados))
    cols_h[0].markdown("<b>Indicador</b>", unsafe_allow_html=True)
    for j,r in enumerate(resultados): cols_h[j+1].markdown(f"<b>{r['nome']}</b>", unsafe_allow_html=True)
    for label,ext,tipo,maior_melhor in indicadores:
        valores = [ext(r) for r in resultados]
        melhor = max(valores) if maior_melhor else min(valores)
        cols_r = st.columns([3]+[2]*len(resultados))
        cols_r[0].write(label)
        for j,v in enumerate(valores):
            if tipo=="R$": txt=fmt_brl(v)
            elif tipo=="%": txt=fmt_pct(v)
            else: txt=f"{v:,.1f} {tipo}".replace(",","X").replace(".",",").replace("X",".")
            cols_r[j+1].markdown(f"{'✅ ' if v==melhor else ''}{txt}")

    st.markdown("")
    fig_c = go.Figure()
    for i,r in enumerate(resultados):
        fig_c.add_trace(go.Bar(name=r["nome"],
            x=["Custo/Ton","Preço/Ton","Lucro/Ton"],
            y=[r["producao"]["custo_total_ton"],r["comercial"]["preco_sugerido"],r["comercial"]["lucro_bruto"]/max(vol_c,1)],
            marker_color=CORES[i%len(CORES)]))
    fig_c.update_layout(barmode="group",
        title=dict(text="Custo, Preço e Lucro (R$/ton)", font=dict(family="DM Serif Display",size=14,color=AZUL)),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=360,
        yaxis=dict(showgrid=True,gridcolor=CINZA2), margin=dict(t=50,b=30,l=60,r=20))
    st.plotly_chart(fig_c, use_container_width=True)


# ═══════════════════════════════════════════════════════
# PÁGINA 5: SENSIBILIDADE
# ═══════════════════════════════════════════════════════
elif pagina == "📈 Análise de Sensibilidade":
    p = prop_atual()
    if not p["cenarios"]: st.warning("Crie um cenário primeiro."); st.stop()

    nomes = [c["nome"] for c in p["cenarios"]]
    sc1,sc2,sc3 = st.columns(3)
    area_s  = sc1.number_input("Área (ha)", value=1000.0, min_value=1.0, step=50.0, key="sens_area")
    var_max = sc2.slider("Variação máxima (%)", 5.0, 50.0, 30.0, 5.0)
    idx_s   = sc3.selectbox("Cenário", range(len(nomes)), format_func=lambda i:nomes[i], key="sens_cen")
    cen_s   = p["cenarios"][idx_s]
    op_s    = ParametrosOperacionais(area_ha=area_s)

    variaveis = {
        "Preço Cama de Frango":    "cama_frango_preco",
        "Preço Fosfato/Fosforita": "fosforita_preco",
        "Preço Cloreto K":         "cloreto_preco",
        "Volume Total Produzido":  "volume_total",
        "Custo do Frete":          "frete",
    }
    secao("📈 Curvas de Sensibilidade")
    cols_s = st.columns(2)
    for i,(label,key) in enumerate(variaveis.items()):
        with cols_s[i%2]:
            st.plotly_chart(g_sens(analise_sensibilidade(cen_s["materiais"],op_s,key,var_max),label), use_container_width=True)

    secao(f"📋 Tabela de Impacto (±{int(var_max)}%)")
    rows = []
    for label,key in variaveis.items():
        rt = analise_sensibilidade(cen_s["materiais"],op_s,key,var_max,passos=3)
        base=rt[1]["custo_ton"]; neg=rt[0]["custo_ton"]; pos=rt[2]["custo_ton"]
        rows.append({"Variável":label,"Base (R$/ton)":fmt_brl(base),
                     f"-{int(var_max)}%":fmt_brl(neg), f"+{int(var_max)}%":fmt_brl(pos),
                     "Δ+":fmt_brl(pos-base), "Δ-":fmt_brl(neg-base)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════
# PÁGINA 6: PROPOSTA COMERCIAL
# ═══════════════════════════════════════════════════════
elif pagina == "📋 Proposta Comercial":
    p = prop_atual()
    if not p["cenarios"]: st.warning("Crie um cenário primeiro."); st.stop()

    secao("Dados da Proposta")
    pa1,pa2 = st.columns(2)
    cliente     = pa1.text_input("Nome do Cliente / Fazenda", value="")
    responsavel = pa2.text_input("Responsável Fertigeo", value=p.get("responsavel",""))
    pa3,pa4 = st.columns(2)
    data_prop = pa3.date_input("Data da Proposta", value=datetime.today())
    validade  = pa4.number_input("Validade (dias)", value=30, min_value=1)

    secao("Parâmetros")
    nomes = [c["nome"] for c in p["cenarios"]]
    idx_p = st.selectbox("Cenário para Proposta", range(len(nomes)), format_func=lambda i:nomes[i], key="prop_cen")
    cen_p = p["cenarios"][idx_p]

    q1,q2,q3,q4 = st.columns(4)
    area_p   = q1.number_input("Área (ha)",              value=float(cen_p["params_op"].area_ha), min_value=1.0, step=50.0, key="prop_area")
    margem_p = q2.number_input("Margem (%)",             value=20.0,   min_value=0.0, step=1.0,  key="prop_margem")
    vol_p    = q3.number_input("Volume negociado (ton)", value=1000.0, min_value=0.0, step=50.0, key="prop_vol")
    frete_p  = q4.number_input("Frete (R$/ton)",         value=0.0,    min_value=0.0, step=5.0,  key="prop_frete")

    op_p   = ParametrosOperacionais(area_ha=area_p, frete_ton=frete_p)
    com_pp = ParametrosComerciais(margem_desejada_pct=margem_p, volume_negociado_ton=vol_p)
    res_p  = rodar_simulacao_completa(cen_p["materiais"],op_p,com_pp,ParametrosAdubacaoQuimica(),ParametrosAdubacaoSafrinha())
    fp,pp_r,qp,cp = res_p["formulacao"],res_p["producao"],res_p["quimica"],res_p["comercial"]

    st.markdown("---"); secao("📄 Preview da Proposta")
    nome_cliente = cliente or p["nome"]
    html = f"""<div style="background:white;border:1px solid #E0E0D8;border-radius:12px;padding:2.5rem;font-family:'DM Sans',sans-serif;max-width:860px;margin:auto;">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:2rem;">
        <div><div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:{AZUL};">🌱 Fertigeo</div><div style="color:{VERDE};font-size:.8rem;font-weight:600;letter-spacing:.06em;">AGÊNCIA DE INTELIGÊNCIA NO AGRONEGÓCIO</div></div>
        <div style="text-align:right;font-size:.82rem;color:#666;"><b>Proposta Comercial</b><br>Data: {data_prop.strftime('%d/%m/%Y')}<br>Validade: {validade} dias<br>Responsável: {responsavel or '—'}</div>
    </div>
    <div style="background:{AZUL};color:white;padding:1rem 1.5rem;border-radius:8px;margin-bottom:1.5rem;">
        <div style="font-size:.75rem;letter-spacing:.06em;color:{VERDE};margin-bottom:4px;">PROPOSTA PARA</div>
        <div style="font-family:'DM Serif Display',serif;font-size:1.3rem;">{nome_cliente}</div>
        <div style="font-size:.82rem;opacity:.8;margin-top:2px;">{p['nome']} · Área: {area_p:,.0f} ha · {cen_p['nome']}</div>
    </div>
    <table style="width:100%;border-collapse:collapse;margin-bottom:1.5rem;font-size:.88rem;">
        <tr style="background:{AZUL};color:white;"><th style="padding:8px 12px;text-align:left;">Indicador</th><th style="padding:8px 12px;text-align:right;">Valor</th></tr>
        <tr style="background:{CINZA};"><td style="padding:8px 12px;font-weight:600;">Volume do Composto Orgânico</td><td style="padding:8px 12px;text-align:right;">{fmt_ton(fp['total_volume_ton'])}</td></tr>
        <tr><td style="padding:8px 12px;">Dose por Hectare</td><td style="padding:8px 12px;text-align:right;">{pp_r['dose_kg_ha']:,.0f} kg/ha</td></tr>
        <tr style="background:{CINZA};"><td style="padding:8px 12px;">Custo de Produção por Tonelada</td><td style="padding:8px 12px;text-align:right;">{fmt_brl(pp_r['custo_total_ton'])}</td></tr>
        <tr><td style="padding:8px 12px;font-weight:600;color:{AZUL};">Preço de Venda por Tonelada</td><td style="padding:8px 12px;text-align:right;font-weight:700;color:{AZUL};">{fmt_brl(cp['preco_sugerido'])}</td></tr>
        <tr style="background:{CINZA};"><td style="padding:8px 12px;">Volume Negociado</td><td style="padding:8px 12px;text-align:right;">{fmt_ton(cp['vol_negociado'])}</td></tr>
        <tr><td style="padding:8px 12px;font-weight:600;">Receita Total</td><td style="padding:8px 12px;text-align:right;font-weight:700;">{fmt_brl(cp['receita_bruta'])}</td></tr>
    </table>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;margin-bottom:1.5rem;">
        <div style="background:{VERDE};color:white;padding:1rem;border-radius:8px;text-align:center;"><div style="font-size:.7rem;opacity:.9;margin-bottom:4px;">GARANTIA N</div><div style="font-size:1.2rem;font-weight:700;">{pp_r['N_kg_ha']:.1f} kg/ha</div></div>
        <div style="background:{VERDE};color:white;padding:1rem;border-radius:8px;text-align:center;"><div style="font-size:.7rem;opacity:.9;margin-bottom:4px;">GARANTIA P</div><div style="font-size:1.2rem;font-weight:700;">{pp_r['P_kg_ha']:.1f} kg/ha</div></div>
        <div style="background:{VERDE};color:white;padding:1rem;border-radius:8px;text-align:center;"><div style="font-size:.7rem;opacity:.9;margin-bottom:4px;">GARANTIA K</div><div style="font-size:1.2rem;font-weight:700;">{pp_r['K_kg_ha']:.1f} kg/ha</div></div>
    </div>
    <div style="background:#F0F4E0;border-left:4px solid {VERDE};padding:1rem 1.2rem;border-radius:4px;margin-bottom:1.5rem;">
        <div style="font-weight:600;color:{AZUL};margin-bottom:4px;">💡 Vantagem Econômica</div>
        <div style="font-size:.88rem;color:#4A6A10;">Substituição parcial da adubação química gera economia de <b>{fmt_brl(qp['saldo_ha'])} por hectare</b> ({fmt_pct(qp['economia_pct'])} de redução), totalizando <b>{fmt_brl(qp['saldo_total'])}</b> em {area_p:,.0f} ha.</div>
    </div>
    <div style="text-align:center;font-size:.75rem;color:#AAA;border-top:1px solid #E0E0D8;padding-top:1rem;">Proposta gerada por Fertigeo · {data_prop.strftime('%d/%m/%Y')}</div>
    </div>"""
    st.markdown(html, unsafe_allow_html=True)
    st.download_button(label="⬇️ Baixar Proposta em HTML",
                        data=html.encode("utf-8"),
                        file_name=f"Proposta_{nome_cliente.replace(' ','_')}_{data_prop.strftime('%Y%m%d')}.html",
                        mime="text/html")

st.markdown(f'<div class="rodape">Fertigeo · Simulador de Composto Orgânico · {datetime.now().strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)
