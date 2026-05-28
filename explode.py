"""
Explosão recursiva de carteiras WM.

Lógica:
- Se um ativo está em CotasFundo → ele É uma cota do fundo referenciado.
  Proporção = qtd_detida / TotalCotasFundo (TempDataFundo).
  Expande-se recursivamente a Carteira_Fundo desse fundo.

- Se um ativo está em ParticipacaoHolding → ele representa participação
  DIRETA em uma holding (ex: tipo "Participação em Holding").
  Proporção = qtd_detida / TotalAcoesHolding (TempDataHolding).
  Expande-se recursivamente a Carteira_Holding dessa holding.
  OBS: ParticipacaoHolding registra o que a holding POSSUI; só fazemos
  look-through quando o ativo DE FATO representa uma participação
  (CotasFundo é o análogo para fundos). Ações ordinárias que uma holding
  TAMBÉM detém permanecem terminais do ponto de vista do cliente.

- Caso contrário: ativo final (ação, debênture, CRI, LCI …).

Ciclos (cross-holdings) são detectados pelos conjuntos
visited_fundos / visited_holdings propagados na recursão.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from db import query


# ── helpers de lookup ──────────────────────────────────────────────────────────

def _fundo_do_ativo(id_ativo: int) -> Optional[dict]:
    rows = query(
        "SELECT cf.idfundo, f.nomefundo FROM cotasfundo cf JOIN fundo f ON f.idfundo=cf.idfundo WHERE cf.idativo=%s",
        (id_ativo,),
    )
    return rows[0] if rows else None


def _holding_do_ativo(id_ativo: int) -> Optional[dict]:
    rows = query(
        "SELECT ph.idholding, h.nomeholding FROM participacaoholding ph JOIN holding h ON h.idholding=ph.idholding WHERE ph.idativo=%s",
        (id_ativo,),
    )
    return rows[0] if rows else None


def _total_cotas_fundo(id_fundo: int, data) -> float:
    rows = query(
        "SELECT totalcotasfundo FROM tempdatafundo WHERE idfundo=%s AND databasefundo=%s",
        (id_fundo, data),
    )
    if rows:
        return float(rows[0]["totalcotasfundo"])
    # fallback: data mais próxima anterior
    rows = query(
        "SELECT totalcotasfundo FROM tempdatafundo WHERE idfundo=%s AND databasefundo <= %s ORDER BY databasefundo DESC LIMIT 1",
        (id_fundo, data),
    )
    return float(rows[0]["totalcotasfundo"]) if rows else 0.0


def _total_acoes_holding(id_holding: int, data) -> float:
    rows = query(
        "SELECT totalacoeshd FROM tempdataholding WHERE idholding=%s AND dataholding=%s",
        (id_holding, data),
    )
    if rows:
        return float(rows[0]["totalacoeshd"])
    rows = query(
        "SELECT totalacoeshd FROM tempdataholding WHERE idholding=%s AND dataholding <= %s ORDER BY dataholding DESC LIMIT 1",
        (id_holding, data),
    )
    return float(rows[0]["totalacoeshd"]) if rows else 0.0


def _carteira_fundo(id_fundo: int, data) -> list[dict]:
    rows = query(
        """SELECT cf.idativo, cf.qtdcartfundo AS qtd, cf.vlrcartfundo AS vlr,
                  a.descricao, a.tipo
           FROM carteira_fundo cf JOIN ativo a ON a.idativo=cf.idativo
           WHERE cf.idfundo=%s AND cf.datacartfundo=%s""",
        (id_fundo, data),
    )
    if rows:
        return rows
    # fallback data mais próxima
    rows = query(
        """SELECT cf.idativo, cf.qtdcartfundo AS qtd, cf.vlrcartfundo AS vlr,
                  a.descricao, a.tipo
           FROM carteira_fundo cf JOIN ativo a ON a.idativo=cf.idativo
           WHERE cf.idfundo=%s AND cf.datacartfundo = (
               SELECT MAX(datacartfundo) FROM carteira_fundo WHERE idfundo=%s AND datacartfundo <= %s
           )""",
        (id_fundo, id_fundo, data),
    )
    return rows


def _carteira_holding(id_holding: int, data) -> list[dict]:
    rows = query(
        """SELECT ch.idativo, ch.qtdcartholding AS qtd, ch.vlrcartholding AS vlr,
                  a.descricao, a.tipo
           FROM carteira_holding ch JOIN ativo a ON a.idativo=ch.idativo
           WHERE ch.idholding=%s AND ch.datacartholding=%s""",
        (id_holding, data),
    )
    if rows:
        return rows
    rows = query(
        """SELECT ch.idativo, ch.qtdcartholding AS qtd, ch.vlrcartholding AS vlr,
                  a.descricao, a.tipo
           FROM carteira_holding ch JOIN ativo a ON a.idativo=ch.idativo
           WHERE ch.idholding=%s AND ch.datacartholding = (
               SELECT MAX(datacartholding) FROM carteira_holding WHERE idholding=%s AND datacartholding <= %s
           )""",
        (id_holding, id_holding, data),
    )
    return rows


# ── estrutura de resultado ─────────────────────────────────────────────────────

@dataclass
class AtivoFinal:
    id_ativo: int
    descricao: str
    tipo: str
    qtd_efetiva: float
    vlr_efetivo: float
    caminho: list[str] = field(default_factory=list)


# ── recursão principal ─────────────────────────────────────────────────────────

def _explode(
    itens: list[dict],
    data,
    proporcao: float,
    visited_fundos: frozenset,
    visited_holdings: frozenset,
    caminho: list[str],
) -> list[AtivoFinal]:
    """
    itens: lista de dicts com chaves idativo, qtd, vlr, descricao, tipo
    proporcao: fator acumulado de participação relativa ao cliente original
    """
    resultado: dict[int, AtivoFinal] = {}

    for item in itens:
        id_ativo = item["idativo"]
        qtd = float(item["qtd"])
        vlr = float(item["vlr"])

        tipo = item.get("tipo", "")

        # ── Verifica se é cota de fundo ───────────────────────────────
        fundo = _fundo_do_ativo(id_ativo) if tipo == "Cota de Fundo" else None
        if fundo and fundo["idfundo"] not in visited_fundos:
            id_fundo = fundo["idfundo"]
            nome_fundo = fundo["nomefundo"]
            total_cotas = _total_cotas_fundo(id_fundo, data)
            if total_cotas > 0:
                prop_fundo = qtd / total_cotas
                sub_itens = _carteira_fundo(id_fundo, data)
                sub_resultado = _explode(
                    sub_itens,
                    data,
                    proporcao * prop_fundo,
                    visited_fundos | {id_fundo},
                    visited_holdings,
                    caminho + [f"Fundo: {nome_fundo} ({prop_fundo:.4%})"],
                )
                for af in sub_resultado:
                    if af.id_ativo in resultado:
                        resultado[af.id_ativo].qtd_efetiva += af.qtd_efetiva
                        resultado[af.id_ativo].vlr_efetivo += af.vlr_efetivo
                    else:
                        resultado[af.id_ativo] = af
            else:
                # sem dados de cotas → trata como terminal
                _acumula(resultado, id_ativo, item, proporcao, qtd, vlr, caminho)
            continue

        # ── Verifica se é participação em holding ─────────────────────
        # Só expande se o ativo for explicitamente de tipo participação
        # (não expande ações ordinárias que a holding também detém)
        holding = _holding_do_ativo(id_ativo) if "holding" in tipo.lower() or "participação" in tipo.lower() else None
        if holding and holding["idholding"] not in visited_holdings:
            id_holding = holding["idholding"]
            nome_holding = holding["nomeholding"]
            total_acoes = _total_acoes_holding(id_holding, data)
            if total_acoes > 0:
                prop_holding = qtd / total_acoes
                sub_itens = _carteira_holding(id_holding, data)
                sub_resultado = _explode(
                    sub_itens,
                    data,
                    proporcao * prop_holding,
                    visited_fundos,
                    visited_holdings | {id_holding},
                    caminho + [f"Holding: {nome_holding} ({prop_holding:.4%})"],
                )
                for af in sub_resultado:
                    if af.id_ativo in resultado:
                        resultado[af.id_ativo].qtd_efetiva += af.qtd_efetiva
                        resultado[af.id_ativo].vlr_efetivo += af.vlr_efetivo
                    else:
                        resultado[af.id_ativo] = af
            else:
                _acumula(resultado, id_ativo, item, proporcao, qtd, vlr, caminho)
            continue

        # ── Ativo final ───────────────────────────────────────────────
        _acumula(resultado, id_ativo, item, proporcao, qtd, vlr, caminho)

    return list(resultado.values())


def _acumula(resultado, id_ativo, item, proporcao, qtd, vlr, caminho):
    qtd_ef = qtd * proporcao
    vlr_ef = vlr * proporcao
    if id_ativo in resultado:
        resultado[id_ativo].qtd_efetiva += qtd_ef
        resultado[id_ativo].vlr_efetivo += vlr_ef
    else:
        resultado[id_ativo] = AtivoFinal(
            id_ativo=id_ativo,
            descricao=item["descricao"],
            tipo=item["tipo"],
            qtd_efetiva=qtd_ef,
            vlr_efetivo=vlr_ef,
            caminho=list(caminho),
        )


# ── ponto de entrada público ───────────────────────────────────────────────────

def explodir_carteira_cliente(id_cliente: int, data) -> list[AtivoFinal]:
    """
    Retorna a carteira explodida de um cliente em uma data.
    Cada AtivoFinal representa um ativo terminal com quantidade e valor
    efetivos, já proporcionalizados por fundo/holding.
    """
    itens = query(
        """SELECT cc.idativo, cc.qtdcartcliente AS qtd, cc.vlrcartcliente AS vlr,
                  a.descricao, a.tipo
           FROM carteira_cliente cc JOIN ativo a ON a.idativo=cc.idativo
           WHERE cc.idcliente=%s AND cc.datacarteiracliente=%s""",
        (id_cliente, data),
    )
    return _explode(
        itens,
        data,
        proporcao=1.0,
        visited_fundos=frozenset(),
        visited_holdings=frozenset(),
        caminho=[],
    )
