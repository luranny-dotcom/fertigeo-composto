"""
business_logic.py — Fertigeo | Simulador de Composto Orgânico
"""

from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Material:
    nome: str
    volume_ton: float
    preco_ton: float
    N: float = 0.0
    P: float = 0.0
    K: float = 0.0
    B: float = 0.0
    S: float = 0.0
    Zn: float = 0.0
    Mg: float = 0.0   # ← NOVO

@dataclass
class ParametrosOperacionais:
    area_ha: float = 1000.0
    biotecnologia_ton: float = 0.0
    fertigeo_ton: float = 0.0
    processamento_ton: float = 0.0
    mao_obra_ton: float = 0.0
    embalagem_ton: float = 0.0
    frete_ton: float = 0.0
    overhead_pct: float = 0.0

@dataclass
class ParametrosComerciais:
    margem_desejada_pct: float = 20.0
    impostos_pct: float = 0.0
    volume_negociado_ton: float = 0.0
    desconto_comercial_pct: float = 0.0

@dataclass
class ParametrosAdubacaoQuimica:
    garantia_N: float = 0.45
    preco_N_ton: float = 0.0
    garantia_P: float = 0.21
    preco_P_ton: float = 1080.0
    garantia_K: float = 0.60
    preco_K_ton: float = 1300.0

@dataclass
class ParametrosAdubacaoSafrinha:
    volume_P_ton: float = 80.0
    garantia_P: float = 0.50
    preco_P_ton: float = 1800.0
    volume_K_ton: float = 166.67
    garantia_K: float = 0.60
    preco_K_ton: float = 1300.0


MATERIAIS_CENARIO_A = [
    Material("Composto Bovino",     3000, 0,    N=0.020, P=0.020, K=0.045),
    Material("Feno",                  50, 0,    N=0.005, P=0.000, K=0.003),
    Material("Cloreto K",             90, 1300, N=0.000, P=0.000, K=0.600),
    Material("Fosfato (Fosforita)",  450, 400,  N=0.000, P=0.200, K=0.000),
    Material("Resíduo: sabugo/casca", 50, 0,    N=0.005, P=0.005, K=0.005),
    Material("Cama de Frango",      1600, 120,  N=0.015, P=0.030, K=0.030),
    Material("Ulexita",               15, 1790, B=0.100),
    Material("Sulfurgran",            50, 2100, S=0.900),
    Material("Zincogran",              0, 1490, Zn=0.150),
]

MATERIAIS_CENARIO_B = [
    Material("Composto Bovino",     3000, 0,    N=0.020, P=0.020, K=0.045),
    Material("Feno",                  80, 0,    N=0.005, P=0.000, K=0.003),
    Material("Cloreto K",             10, 1300, N=0.000, P=0.000, K=0.600),
    Material("Fosfato (Fosforita)",  250, 400,  N=0.000, P=0.200, K=0.000),
    Material("Resíduo: sabugo/casca",150, 0,    N=0.005, P=0.005, K=0.005),
    Material("Cama de Frango",         0, 120,  N=0.015, P=0.030, K=0.040),
    Material("Ulexita",                8, 1790, B=0.100),
    Material("Sulfurgran",            25, 2100, S=0.900),
    Material("Zincogran",              0, 1490, Zn=0.150),
]


def calcular_formulacao(materiais: List[Material]) -> Dict:
    total_volume = sum(m.volume_ton for m in materiais)
    if total_volume == 0:
        total_volume = 1e-9

    resultado = []
    for m in materiais:
        pct_uso = m.volume_ton / total_volume
        resultado.append({
            "nome": m.nome,
            "volume_ton": m.volume_ton,
            "preco_ton": m.preco_ton,
            "pct_uso": pct_uso,
            "custo_total": m.volume_ton * m.preco_ton,
            "contrib_N":  pct_uso * m.N,
            "contrib_P":  pct_uso * m.P,
            "contrib_K":  pct_uso * m.K,
            "contrib_B":  pct_uso * m.B,
            "contrib_S":  pct_uso * m.S,
            "contrib_Zn": pct_uso * m.Zn,
            "contrib_Mg": pct_uso * m.Mg,
        })

    return {
        "materiais": resultado,
        "total_volume_ton": total_volume,
        "total_custo_materiais": sum(r["custo_total"] for r in resultado),
        "garantia_N":  sum(r["contrib_N"]  for r in resultado),
        "garantia_P":  sum(r["contrib_P"]  for r in resultado),
        "garantia_K":  sum(r["contrib_K"]  for r in resultado),
        "garantia_B":  sum(r["contrib_B"]  for r in resultado),
        "garantia_S":  sum(r["contrib_S"]  for r in resultado),
        "garantia_Zn": sum(r["contrib_Zn"] for r in resultado),
        "garantia_Mg": sum(r["contrib_Mg"] for r in resultado),
    }


def calcular_producao(formulacao: Dict, params_op: ParametrosOperacionais) -> Dict:
    vol  = formulacao["total_volume_ton"]
    area = params_op.area_ha if params_op.area_ha > 0 else 1

    dose_ton_ha = vol / area
    dose_kg_ha  = dose_ton_ha * 1000

    N_kg_ha  = dose_kg_ha * formulacao["garantia_N"]
    P_kg_ha  = dose_kg_ha * formulacao["garantia_P"]
    K_kg_ha  = dose_kg_ha * formulacao["garantia_K"]
    B_kg_ha  = dose_kg_ha * formulacao["garantia_B"]
    S_kg_ha  = dose_kg_ha * formulacao["garantia_S"]
    Zn_kg_ha = dose_kg_ha * formulacao["garantia_Zn"]
    Mg_kg_ha = dose_kg_ha * formulacao["garantia_Mg"]

    custo_mp_ton = formulacao["total_custo_materiais"] / vol if vol > 0 else 0
    custo_adicional_ton = (
        params_op.biotecnologia_ton + params_op.fertigeo_ton +
        params_op.processamento_ton + params_op.mao_obra_ton +
        params_op.embalagem_ton + params_op.frete_ton
    )
    custo_base_ton    = custo_mp_ton + custo_adicional_ton
    custo_overhead_ton = custo_base_ton * (params_op.overhead_pct / 100)
    custo_total_ton   = custo_base_ton + custo_overhead_ton
    custo_ha          = custo_total_ton * dose_ton_ha

    return {
        "dose_ton_ha": dose_ton_ha, "dose_kg_ha": dose_kg_ha,
        "N_kg_ha": N_kg_ha, "P_kg_ha": P_kg_ha, "K_kg_ha": K_kg_ha,
        "B_kg_ha": B_kg_ha, "S_kg_ha": S_kg_ha, "Zn_kg_ha": Zn_kg_ha,
        "Mg_kg_ha": Mg_kg_ha,
        "custo_mp_ton": custo_mp_ton, "custo_adicional_ton": custo_adicional_ton,
        "custo_overhead_ton": custo_overhead_ton, "custo_total_ton": custo_total_ton,
        "custo_ha": custo_ha,
        "custo_total_producao": custo_total_ton * formulacao["total_volume_ton"],
    }


def calcular_adubacao_quimica(producao, params_op, params_quimica, params_safrinha) -> Dict:
    area = params_op.area_ha if params_op.area_ha > 0 else 1

    N_total_kg = producao["N_kg_ha"] * area
    P_total_kg = producao["P_kg_ha"] * area
    K_total_kg = producao["K_kg_ha"] * area

    vol_N = (N_total_kg / 1000) / params_quimica.garantia_N if params_quimica.garantia_N > 0 else 0
    vol_P = (P_total_kg / 1000) / params_quimica.garantia_P if params_quimica.garantia_P > 0 else 0
    vol_K = (K_total_kg / 1000) / params_quimica.garantia_K if params_quimica.garantia_K > 0 else 0

    custo_N = vol_N * params_quimica.preco_N_ton
    custo_P = vol_P * params_quimica.preco_P_ton
    custo_K = vol_K * params_quimica.preco_K_ton
    custo_safra = custo_N + custo_P + custo_K
    custo_safra_ha = custo_safra / area

    custo_P_saf = params_safrinha.volume_P_ton * params_safrinha.preco_P_ton
    custo_K_saf = params_safrinha.volume_K_ton * params_safrinha.preco_K_ton
    custo_safrinha_ha = (custo_P_saf + custo_K_saf) / area

    custo_quimico_ha  = custo_safra_ha + custo_safrinha_ha
    custo_organico_ha = producao["custo_ha"]
    saldo_ha = custo_quimico_ha - custo_organico_ha

    return {
        "vol_N_quimico_ton": vol_N, "vol_P_quimico_ton": vol_P, "vol_K_quimico_ton": vol_K,
        "custo_N_safra": custo_N, "custo_P_safra": custo_P, "custo_K_safra": custo_K,
        "custo_safra_total": custo_safra, "custo_safra_ha": custo_safra_ha,
        "custo_P_safrinha": custo_P_saf, "custo_K_safrinha": custo_K_saf,
        "custo_safrinha_total": custo_P_saf + custo_K_saf, "custo_safrinha_ha": custo_safrinha_ha,
        "custo_quimico_total_ha": custo_quimico_ha, "custo_organico_total_ha": custo_organico_ha,
        "saldo_ha": saldo_ha, "saldo_total": saldo_ha * area,
        "economia_pct": (saldo_ha / custo_quimico_ha * 100) if custo_quimico_ha > 0 else 0,
    }


def calcular_comercial(formulacao, producao, params_com) -> Dict:
    custo_ton = producao["custo_total_ton"]
    vol_total = formulacao["total_volume_ton"]
    vol_neg   = params_com.volume_negociado_ton if params_com.volume_negociado_ton > 0 else vol_total

    preco_sugerido = custo_ton * (1 + params_com.margem_desejada_pct / 100)
    preco_liquido  = preco_sugerido * (1 - params_com.desconto_comercial_pct / 100)
    receita_bruta  = preco_liquido * vol_neg
    impostos_valor = receita_bruta * (params_com.impostos_pct / 100)
    receita_liquida = receita_bruta - impostos_valor
    custo_venda    = custo_ton * vol_neg
    lucro_bruto    = receita_bruta - custo_venda
    lucro_liquido  = receita_liquida - custo_venda

    return {
        "custo_ton": custo_ton, "preco_sugerido": preco_sugerido, "preco_liquido": preco_liquido,
        "receita_bruta": receita_bruta, "impostos_valor": impostos_valor,
        "receita_liquida": receita_liquida, "custo_venda": custo_venda,
        "lucro_bruto": lucro_bruto, "lucro_liquido": lucro_liquido,
        "margem_bruta_pct": (lucro_bruto / receita_bruta * 100) if receita_bruta > 0 else 0,
        "margem_liquida_pct": (lucro_liquido / receita_liquida * 100) if receita_liquida > 0 else 0,
        "markup_pct": ((preco_liquido - custo_ton) / custo_ton * 100) if custo_ton > 0 else 0,
        "ponto_equilibrio_ton": custo_ton / preco_liquido * vol_neg if preco_liquido > 0 else 0,
        "roi_pct": (lucro_liquido / custo_venda * 100) if custo_venda > 0 else 0,
        "vol_negociado": vol_neg,
    }


def analise_sensibilidade(materiais, params_op, variavel, variacao_pct=10.0, passos=11):
    resultados = []
    variacoes = [-variacao_pct + i * (2 * variacao_pct / (passos - 1)) for i in range(passos)]
    for v in variacoes:
        fator = 1 + v / 100
        mats_mod = [Material(m.nome, m.volume_ton, m.preco_ton,
                             m.N, m.P, m.K, m.B, m.S, m.Zn, m.Mg) for m in materiais]
        if variavel == "cama_frango_preco":
            for m in mats_mod:
                if "Frango" in m.nome: m.preco_ton *= fator
        elif variavel == "fosforita_preco":
            for m in mats_mod:
                if "Fosfato" in m.nome or "Fosforita" in m.nome: m.preco_ton *= fator
        elif variavel == "cloreto_preco":
            for m in mats_mod:
                if "Cloreto" in m.nome: m.preco_ton *= fator
        elif variavel == "frete":
            pm = ParametrosOperacionais(
                area_ha=params_op.area_ha, biotecnologia_ton=params_op.biotecnologia_ton,
                fertigeo_ton=params_op.fertigeo_ton, processamento_ton=params_op.processamento_ton,
                mao_obra_ton=params_op.mao_obra_ton, embalagem_ton=params_op.embalagem_ton,
                frete_ton=params_op.frete_ton * fator, overhead_pct=params_op.overhead_pct)
            form = calcular_formulacao(mats_mod)
            prod = calcular_producao(form, pm)
            resultados.append({"variacao_pct": v, "custo_ton": prod["custo_total_ton"]})
            continue
        elif variavel == "volume_total":
            for m in mats_mod: m.volume_ton *= fator
        form = calcular_formulacao(mats_mod)
        prod = calcular_producao(form, params_op)
        resultados.append({"variacao_pct": v, "custo_ton": prod["custo_total_ton"]})
    return resultados


def rodar_simulacao_completa(materiais, params_op, params_com, params_quimica, params_safrinha):
    formulacao = calcular_formulacao(materiais)
    producao   = calcular_producao(formulacao, params_op)
    quimica    = calcular_adubacao_quimica(producao, params_op, params_quimica, params_safrinha)
    comercial  = calcular_comercial(formulacao, producao, params_com)
    return {"formulacao": formulacao, "producao": producao, "quimica": quimica, "comercial": comercial}
