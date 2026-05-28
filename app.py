"""
Interface Streamlit – Carteiras Wealth Management
Execute: streamlit run app.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

import crud
import explode as exp
from db import execute, query, get_conn

# ──────────────────────────────────────────────────────────────────────────────
# Configuração da página
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Carteiras WM",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS mínimo para melhorar visual das tabelas e métricas
st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 1.4rem; }
.stDataFrame { border-radius: 8px; }
div[data-testid="column"] > div { padding: 0.25rem 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar – navegação
# ──────────────────────────────────────────────────────────────────────────────

PAGINAS = {
    "🏠 Visão Geral":          "geral",
    "👤 Clientes":             "clientes",
    "📊 Ativos":               "ativos",
    "🏦 Fundos":               "fundos",
    "🏢 Holdings":             "holdings",
    "💼 Carteira do Cliente":  "carteira_cliente",
    "🔍 Explosão Look-Through":"explosao",
    "⚡ Análise de Índice":    "indice",
    "🛠️ SQL Livre":            "sql",
}

with st.sidebar:
    st.title("💼 Carteiras WM")
    st.caption("Wealth Management · PostgreSQL + Streamlit")
    st.divider()
    pagina = st.radio("Navegação", list(PAGINAS.keys()), label_visibility="collapsed")
    st.divider()
    st.caption("psycopg2 · schema carteiras_wm")

secao = PAGINAS[pagina]

# ──────────────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────────────

def df_vazio(colunas):
    return pd.DataFrame(columns=colunas)

def moeda(v):
    return f"R$ {v:,.2f}"

def pct(v):
    return f"{v:.2%}"

@st.cache_data(ttl=5)
def _clientes():
    return crud.listar_clientes()

@st.cache_data(ttl=5)
def _ativos():
    return crud.listar_ativos()

@st.cache_data(ttl=5)
def _fundos():
    return crud.listar_fundos()

@st.cache_data(ttl=5)
def _holdings():
    return crud.listar_holdings()

@st.cache_data(ttl=5)
def _datas():
    return crud.listar_datas_disponiveis()

def limpar_cache():
    st.cache_data.clear()

# ──────────────────────────────────────────────────────────────────────────────
# VISÃO GERAL
# ──────────────────────────────────────────────────────────────────────────────

if secao == "geral":
    st.title("🏠 Visão Geral")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clientes", len(_clientes()))
    c2.metric("Ativos cadastrados", len(_ativos()))
    c3.metric("Fundos", len(_fundos()))
    c4.metric("Holdings", len(_holdings()))

    st.divider()

    # Valor total por cliente (última data disponível)
    datas = _datas()
    if datas:
        ultima = max(datas)
        st.subheader(f"Patrimônio por Cliente – {ultima}")

        rows = query("""
            SELECT c.nomecliente, SUM(cc.vlrcartcliente) AS total
            FROM carteira_cliente cc
            JOIN cliente c ON c.idcliente = cc.idcliente
            WHERE cc.datacarteiracliente = %s
            GROUP BY c.nomecliente
            ORDER BY total DESC
        """, (ultima,))

        if rows:
            df_pat = pd.DataFrame(rows)
            df_pat["total"] = df_pat["total"].astype(float)

            col1, col2 = st.columns([1, 1])
            with col1:
                fig = px.bar(
                    df_pat, x="nomecliente", y="total",
                    labels={"nomecliente": "Cliente", "total": "Valor (R$)"},
                    color="nomecliente",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig.update_layout(showlegend=False, height=340,
                                  yaxis_tickformat=",.0f", xaxis_title="")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig2 = px.pie(
                    df_pat, names="nomecliente", values="total",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    hole=0.4,
                )
                fig2.update_layout(height=340)
                st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Evolução temporal do patrimônio total
    st.subheader("Evolução do Patrimônio Total")
    rows_ev = query("""
        SELECT datacarteiracliente AS data, SUM(vlrcartcliente) AS total
        FROM carteira_cliente
        GROUP BY datacarteiracliente
        ORDER BY datacarteiracliente
    """)
    if rows_ev:
        df_ev = pd.DataFrame(rows_ev)
        df_ev["total"] = df_ev["total"].astype(float)
        fig3 = px.area(df_ev, x="data", y="total",
                       labels={"data": "Data", "total": "Patrimônio Total (R$)"},
                       color_discrete_sequence=["#2196F3"])
        fig3.update_layout(height=300, yaxis_tickformat=",.0f")
        st.plotly_chart(fig3, use_container_width=True)

    # Composição por tipo de ativo
    st.subheader("Composição por Tipo de Ativo (todas as datas)")
    rows_tipo = query("""
        SELECT a.tipo, SUM(cc.vlrcartcliente) AS total
        FROM carteira_cliente cc
        JOIN ativo a ON a.idativo = cc.idativo
        GROUP BY a.tipo
        ORDER BY total DESC
    """)
    if rows_tipo:
        df_tipo = pd.DataFrame(rows_tipo)
        df_tipo["total"] = df_tipo["total"].astype(float)
        fig4 = px.bar(df_tipo, x="tipo", y="total",
                      labels={"tipo": "Tipo", "total": "Volume Total (R$)"},
                      color="tipo",
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig4.update_layout(showlegend=False, height=300, yaxis_tickformat=",.0f")
        st.plotly_chart(fig4, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# CLIENTES
# ──────────────────────────────────────────────────────────────────────────────

elif secao == "clientes":
    st.title("👤 Clientes")
    aba_list, aba_add, aba_edit, aba_del = st.tabs(["📋 Listar", "➕ Cadastrar", "✏️ Editar", "🗑️ Excluir"])

    with aba_list:
        df = pd.DataFrame(_clientes())
        if df.empty:
            st.info("Nenhum cliente cadastrado.")
        else:
            df.columns = ["ID", "Nome", "Código", "Documento"]
            st.dataframe(df, use_container_width=True, hide_index=True)

    with aba_add:
        st.subheader("Novo Cliente")
        with st.form("form_add_cliente"):
            nome = st.text_input("Nome completo *")
            col1, col2 = st.columns(2)
            codigo = col1.text_input("Código (sigla) *")
            documento = col2.text_input("CPF / CNPJ *")
            submitted = st.form_submit_button("Salvar", type="primary")
        if submitted:
            if not all([nome, codigo, documento]):
                st.error("Preencha todos os campos obrigatórios.")
            else:
                try:
                    novo_id = crud.criar_cliente(nome, codigo, documento)
                    limpar_cache()
                    st.success(f"Cliente criado com ID {novo_id}.")
                except Exception as e:
                    st.error(f"Erro: {e}")

    with aba_edit:
        st.subheader("Editar Cliente")
        clientes = _clientes()
        opcoes = {f"{c['idcliente']} – {c['nomecliente']}": c for c in clientes}
        sel = st.selectbox("Selecione o cliente", list(opcoes.keys()), key="edit_cli_sel")
        if sel:
            c = opcoes[sel]
            with st.form("form_edit_cliente"):
                nome = st.text_input("Nome", value=c["nomecliente"])
                col1, col2 = st.columns(2)
                codigo = col1.text_input("Código", value=c["codigocliente"])
                documento = col2.text_input("Documento", value=c["documentocliente"])
                submitted = st.form_submit_button("Atualizar", type="primary")
            if submitted:
                try:
                    crud.atualizar_cliente(c["idcliente"], nome, codigo, documento)
                    limpar_cache()
                    st.success("Cliente atualizado!")
                except Exception as e:
                    st.error(f"Erro: {e}")

    with aba_del:
        st.subheader("Excluir Cliente")
        clientes = _clientes()
        opcoes_del = {f"{c['idcliente']} – {c['nomecliente']}": c for c in clientes}
        sel_del = st.selectbox("Selecione o cliente", list(opcoes_del.keys()), key="del_cli")
        if sel_del:
            c = opcoes_del[sel_del]
            st.warning(f"Esta ação excluirá **{c['nomecliente']}** e todas as suas posições de carteira.")
            if st.button("Confirmar exclusão", type="primary"):
                try:
                    crud.deletar_cliente(c["idcliente"])
                    limpar_cache()
                    st.success("Cliente excluído.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# ATIVOS
# ──────────────────────────────────────────────────────────────────────────────

elif secao == "ativos":
    st.title("📊 Ativos")
    aba_list, aba_add, aba_edit, aba_del = st.tabs(["📋 Listar", "➕ Cadastrar", "✏️ Editar", "🗑️ Excluir"])

    with aba_list:
        ativos = _ativos()
        df = pd.DataFrame(ativos)
        if df.empty:
            st.info("Nenhum ativo cadastrado.")
        else:
            df = df[["idativo", "tipo", "setor", "descricao", "cnpjemissor", "isin"]]
            df.columns = ["ID", "Tipo", "Setor", "Descrição", "CNPJ Emissor", "ISIN"]
            # filtro por tipo
            tipos = ["Todos"] + sorted(df["Tipo"].unique().tolist())
            tipo_filtro = st.selectbox("Filtrar por tipo", tipos, key="filter_tipo_ativo")
            df_show = df if tipo_filtro == "Todos" else df[df["Tipo"] == tipo_filtro]
            st.dataframe(df_show, use_container_width=True, hide_index=True)

            # gráfico de pizza por tipo
            df_g = df.groupby("Tipo").size().reset_index(name="Qtd")
            fig = px.pie(df_g, names="Tipo", values="Qtd", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

    TIPOS_ATIVO = ["Ação", "Debênture", "CRI", "CRA", "LCI", "LCA", "Cota de Fundo", "Participação em Holding", "Outro"]

    with aba_add:
        st.subheader("Novo Ativo")
        with st.form("form_add_ativo"):
            col1, col2 = st.columns(2)
            descricao = col1.text_input("Descrição *")
            tipo = col2.selectbox("Tipo *", TIPOS_ATIVO, key="add_ativo_tipo")
            col3, col4 = st.columns(2)
            setor = col3.text_input("Setor *")
            cnpj = col4.text_input("CNPJ Emissor")
            col5, col6 = st.columns(2)
            den = col5.text_input("Denominação Social")
            isin = col6.text_input("ISIN")
            submitted = st.form_submit_button("Salvar", type="primary")
        if submitted:
            if not all([descricao, tipo, setor]):
                st.error("Preencha Descrição, Tipo e Setor.")
            else:
                try:
                    novo_id = crud.criar_ativo(setor, descricao, tipo, cnpj or None, den or None, isin or None)
                    limpar_cache()
                    st.success(f"Ativo criado com ID {novo_id}.")
                except Exception as e:
                    st.error(f"Erro: {e}")

    with aba_edit:
        st.subheader("Editar Ativo")
        ativos = _ativos()
        opcoes = {f"{a['idativo']} – {a['descricao']}": a for a in ativos}
        sel = st.selectbox("Selecione o ativo", list(opcoes.keys()), key="edit_ativo_sel")
        if sel:
            a = opcoes[sel]
            with st.form("form_edit_ativo"):
                col1, col2 = st.columns(2)
                descricao = col1.text_input("Descrição", value=a["descricao"])
                tipo = col2.selectbox("Tipo", TIPOS_ATIVO,
                                      index=TIPOS_ATIVO.index(a["tipo"]) if a["tipo"] in TIPOS_ATIVO else 0, key="edit_ativo_tipo")
                col3, col4 = st.columns(2)
                setor = col3.text_input("Setor", value=a["setor"])
                cnpj = col4.text_input("CNPJ Emissor", value=a["cnpjemissor"] or "")
                col5, col6 = st.columns(2)
                den = col5.text_input("Denominação Social", value=a["den_soc_em"] or "")
                isin = col6.text_input("ISIN", value=a["isin"] or "")
                submitted = st.form_submit_button("Atualizar", type="primary")
            if submitted:
                try:
                    crud.atualizar_ativo(a["idativo"], setor, descricao, tipo,
                                         cnpj or None, den or None, isin or None)
                    limpar_cache()
                    st.success("Ativo atualizado!")
                except Exception as e:
                    st.error(f"Erro: {e}")

    with aba_del:
        st.subheader("Excluir Ativo")
        ativos = _ativos()
        opcoes_del = {f"{a['idativo']} – {a['descricao']}": a for a in ativos}
        sel_del = st.selectbox("Selecione o ativo", list(opcoes_del.keys()), key="del_at")
        if sel_del:
            a = opcoes_del[sel_del]
            st.warning(f"Excluir **{a['descricao']}** removerá todas as referências a esse ativo.")
            if st.button("Confirmar exclusão", type="primary"):
                try:
                    crud.deletar_ativo(a["idativo"])
                    limpar_cache()
                    st.success("Ativo excluído.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# FUNDOS
# ──────────────────────────────────────────────────────────────────────────────

elif secao == "fundos":
    st.title("🏦 Fundos")
    aba_list, aba_cart, aba_add, aba_edit, aba_del = st.tabs(
        ["📋 Listar", "📁 Carteira", "➕ Cadastrar", "✏️ Editar", "🗑️ Excluir"]
    )

    with aba_list:
        df = pd.DataFrame(_fundos())
        if not df.empty:
            df = df[["idfundo", "nomefundo", "classificacaofundo", "subclassefundo", "cnpjfundo"]]
            df.columns = ["ID", "Nome", "Classe", "Subclasse", "CNPJ"]
            st.dataframe(df, use_container_width=True, hide_index=True)

    with aba_cart:
        st.subheader("Carteira do Fundo")
        fundos = _fundos()
        opcoes_f = {f["nomefundo"]: f["idfundo"] for f in fundos}
        sel_f = st.selectbox("Fundo", list(opcoes_f.keys()), key="cart_fundo_sel")
        datas = _datas()
        data_sel = st.selectbox("Data", datas, format_func=str, key="cart_fundo_dt")

        if st.button("Consultar", key="btn_cart_fundo"):
            rows = crud.listar_carteira_fundo(opcoes_f[sel_f], data_sel)
            if not rows:
                st.warning("Sem dados para essa combinação.")
            else:
                df_cf = pd.DataFrame(rows)[["idativo", "descricao", "tipo", "qtdcartfundo", "vlrcartfundo"]]
                df_cf.columns = ["ID Ativo", "Descrição", "Tipo", "Qtd", "Valor (R$)"]
                df_cf["Valor (R$)"] = df_cf["Valor (R$)"].astype(float)
                st.dataframe(df_cf, use_container_width=True, hide_index=True)

                total = df_cf["Valor (R$)"].sum()
                st.metric("Valor total da carteira (amostra)", moeda(total))

                fig = px.pie(df_cf, names="Descrição", values="Valor (R$)",
                             title="Composição da carteira",
                             color_discrete_sequence=px.colors.qualitative.Set2, hole=0.35)
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

    CLASSES = ["FIA", "FIDC", "FIM", "FIRF", "FII", "FICFI", "Outro"]

    with aba_add:
        st.subheader("Novo Fundo")
        with st.form("form_add_fundo"):
            nome = st.text_input("Nome do fundo *")
            col1, col2, col3 = st.columns(3)
            cnpj = col1.text_input("CNPJ *")
            classificacao = col2.selectbox("Classificação *", CLASSES, key="add_fundo_classe")
            subclasse = col3.text_input("Subclasse (opcional)")
            submitted = st.form_submit_button("Salvar", type="primary")
        if submitted:
            if not all([nome, cnpj, classificacao]):
                st.error("Preencha Nome, CNPJ e Classificação.")
            else:
                try:
                    novo_id = crud.criar_fundo(nome, cnpj, subclasse or None, classificacao)
                    limpar_cache()
                    st.success(f"Fundo criado com ID {novo_id}.")
                except Exception as e:
                    st.error(f"Erro: {e}")

    with aba_edit:
        st.subheader("Editar Fundo")
        fundos = _fundos()
        opcoes = {f"{f['idfundo']} – {f['nomefundo']}": f for f in fundos}
        sel = st.selectbox("Selecione o fundo", list(opcoes.keys()), key="edit_fundo_sel")
        if sel:
            f = opcoes[sel]
            with st.form("form_edit_fundo"):
                nome = st.text_input("Nome", value=f["nomefundo"])
                col1, col2, col3 = st.columns(3)
                cnpj = col1.text_input("CNPJ", value=f["cnpjfundo"])
                classificacao = col2.selectbox("Classificação", CLASSES,
                                               index=CLASSES.index(f["classificacaofundo"]) if f["classificacaofundo"] in CLASSES else 0, key="edit_fundo_classe")
                subclasse = col3.text_input("Subclasse", value=f["subclassefundo"] or "")
                submitted = st.form_submit_button("Atualizar", type="primary")
            if submitted:
                try:
                    crud.atualizar_fundo(f["idfundo"], nome, cnpj, subclasse or None, classificacao)
                    limpar_cache()
                    st.success("Fundo atualizado!")
                except Exception as e:
                    st.error(f"Erro: {e}")

    with aba_del:
        st.subheader("Excluir Fundo")
        fundos = _fundos()
        opcoes_del = {f"{f['idfundo']} – {f['nomefundo']}": f for f in fundos}
        sel_del = st.selectbox("Selecione", list(opcoes_del.keys()), key="del_fundo")
        if sel_del:
            f = opcoes_del[sel_del]
            st.warning(f"Excluir **{f['nomefundo']}**?")
            if st.button("Confirmar exclusão", type="primary"):
                try:
                    crud.deletar_fundo(f["idfundo"])
                    limpar_cache()
                    st.success("Fundo excluído.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# HOLDINGS
# ──────────────────────────────────────────────────────────────────────────────

elif secao == "holdings":
    st.title("🏢 Holdings")
    aba_list, aba_cart, aba_add, aba_edit, aba_del = st.tabs(
        ["📋 Listar", "📁 Carteira", "➕ Cadastrar", "✏️ Editar", "🗑️ Excluir"]
    )

    with aba_list:
        df = pd.DataFrame(_holdings())
        if not df.empty:
            df = df[["idholding", "nomeholding", "cnpjholding"]]
            df.columns = ["ID", "Nome", "CNPJ"]
            st.dataframe(df, use_container_width=True, hide_index=True)

    with aba_cart:
        st.subheader("Carteira da Holding")
        holdings = _holdings()
        opcoes_h = {h["nomeholding"]: h["idholding"] for h in holdings}
        sel_h = st.selectbox("Holding", list(opcoes_h.keys()), key="cart_hold_sel")
        datas = _datas()
        data_sel = st.selectbox("Data", datas, format_func=str, key="dt_hold")

        if st.button("Consultar", key="btn_cart_hold"):
            rows = crud.listar_carteira_holding(opcoes_h[sel_h], data_sel)
            if not rows:
                st.warning("Sem dados para essa combinação.")
            else:
                df_ch = pd.DataFrame(rows)[["idativo", "descricao", "tipo", "qtdcartholding", "vlrcartholding"]]
                df_ch.columns = ["ID Ativo", "Descrição", "Tipo", "Qtd", "Valor (R$)"]
                df_ch["Valor (R$)"] = df_ch["Valor (R$)"].astype(float)
                st.dataframe(df_ch, use_container_width=True, hide_index=True)
                total = df_ch["Valor (R$)"].sum()
                st.metric("Valor total da carteira (amostra)", moeda(total))

                fig = px.bar(df_ch, x="Descrição", y="Valor (R$)",
                             color="Tipo", title="Composição por ativo",
                             color_discrete_sequence=px.colors.qualitative.Set1)
                fig.update_layout(height=320, yaxis_tickformat=",.0f", xaxis_title="")
                st.plotly_chart(fig, use_container_width=True)

    with aba_add:
        st.subheader("Nova Holding")
        with st.form("form_add_holding"):
            nome = st.text_input("Nome da holding *")
            cnpj = st.text_input("CNPJ *")
            submitted = st.form_submit_button("Salvar", type="primary")
        if submitted:
            if not all([nome, cnpj]):
                st.error("Preencha Nome e CNPJ.")
            else:
                try:
                    novo_id = crud.criar_holding(nome, cnpj)
                    limpar_cache()
                    st.success(f"Holding criada com ID {novo_id}.")
                except Exception as e:
                    st.error(f"Erro: {e}")

    with aba_edit:
        st.subheader("Editar Holding")
        holdings = _holdings()
        opcoes = {f"{h['idholding']} – {h['nomeholding']}": h for h in holdings}
        sel = st.selectbox("Selecione", list(opcoes.keys()), key="edit_hold_sel")
        if sel:
            h = opcoes[sel]
            with st.form("form_edit_holding"):
                nome = st.text_input("Nome", value=h["nomeholding"])
                cnpj = st.text_input("CNPJ", value=h["cnpjholding"])
                submitted = st.form_submit_button("Atualizar", type="primary")
            if submitted:
                try:
                    crud.atualizar_holding(h["idholding"], nome, cnpj)
                    limpar_cache()
                    st.success("Holding atualizada!")
                except Exception as e:
                    st.error(f"Erro: {e}")

    with aba_del:
        st.subheader("Excluir Holding")
        holdings = _holdings()
        opcoes_del = {f"{h['idholding']} – {h['nomeholding']}": h for h in holdings}
        sel_del = st.selectbox("Selecione", list(opcoes_del.keys()), key="del_hold")
        if sel_del:
            h = opcoes_del[sel_del]
            st.warning(f"Excluir **{h['nomeholding']}**?")
            if st.button("Confirmar exclusão", type="primary"):
                try:
                    crud.deletar_holding(h["idholding"])
                    limpar_cache()
                    st.success("Holding excluída.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# CARTEIRA DO CLIENTE
# ──────────────────────────────────────────────────────────────────────────────

elif secao == "carteira_cliente":
    st.title("💼 Carteira do Cliente")

    aba_ver, aba_evol, aba_add, aba_edit, aba_del, aba_comp = st.tabs(
        ["📋 Ver Posições", "📈 Evolução", "➕ Adicionar", "✏️ Editar", "🗑️ Remover", "📌 Compromissos"]
    )

    with aba_ver:
        clientes = _clientes()
        opcoes_c = {c["nomecliente"]: c["idcliente"] for c in clientes}
        datas = _datas()

        col1, col2 = st.columns(2)
        sel_c = col1.selectbox("Cliente", list(opcoes_c.keys()), key="ver_cc_cli")
        data_sel = col2.selectbox("Data", datas, format_func=str, key="ver_cc_dt")
        id_c = opcoes_c[sel_c]

        rows = crud.listar_carteira_cliente(id_c, data_sel)
        if not rows:
            st.info("Nenhuma posição para essa combinação.")
        else:
            df_cc = pd.DataFrame(rows)[["idativo", "descricao", "tipo", "qtdcartcliente", "vlrcartcliente", "gestora", "plataforma"]]
            df_cc.columns = ["ID Ativo", "Descrição", "Tipo", "Qtd", "Valor (R$)", "Gestora", "Plataforma"]
            df_cc["Valor (R$)"] = df_cc["Valor (R$)"].astype(float)

            total = df_cc["Valor (R$)"].sum()
            st.metric(f"Patrimônio de {sel_c} em {data_sel}", moeda(total))

            st.dataframe(df_cc, use_container_width=True, hide_index=True)

            col_g, col_p = st.columns(2)
            with col_g:
                fig = px.pie(df_cc, names="Descrição", values="Valor (R$)",
                             title="Por ativo", hole=0.35,
                             color_discrete_sequence=px.colors.qualitative.Set2)
                fig.update_layout(height=320)
                st.plotly_chart(fig, use_container_width=True)
            with col_p:
                fig2 = px.bar(df_cc, x="Gestora", y="Valor (R$)",
                              color="Tipo", title="Por gestora",
                              color_discrete_sequence=px.colors.qualitative.Pastel)
                fig2.update_layout(height=320, yaxis_tickformat=",.0f")
                st.plotly_chart(fig2, use_container_width=True)

    with aba_evol:
        st.subheader("Evolução Temporal da Carteira")
        clientes = _clientes()
        opcoes_c2 = {c["nomecliente"]: c["idcliente"] for c in clientes}
        sel_c2 = st.selectbox("Cliente", list(opcoes_c2.keys()), key="evol_cli")

        rows_ev = query("""
            SELECT cc.datacarteiracliente AS data, a.descricao, a.tipo,
                   SUM(cc.vlrcartcliente) AS valor
            FROM carteira_cliente cc
            JOIN ativo a ON a.idativo = cc.idativo
            WHERE cc.idcliente = %s
            GROUP BY cc.datacarteiracliente, a.descricao, a.tipo
            ORDER BY cc.datacarteiracliente
        """, (opcoes_c2[sel_c2],))

        if rows_ev:
            df_ev2 = pd.DataFrame(rows_ev)
            df_ev2["valor"] = df_ev2["valor"].astype(float)

            fig3 = px.bar(df_ev2, x="data", y="valor", color="descricao",
                          labels={"data": "Data", "valor": "Valor (R$)", "descricao": "Ativo"},
                          title=f"Evolução de {sel_c2}",
                          color_discrete_sequence=px.colors.qualitative.Set1,
                          barmode="stack")
            fig3.update_layout(height=380, yaxis_tickformat=",.0f", xaxis_title="")
            st.plotly_chart(fig3, use_container_width=True)

            # total por data
            df_tot = df_ev2.groupby("data")["valor"].sum().reset_index()
            fig4 = px.line(df_tot, x="data", y="valor",
                           labels={"data": "Data", "valor": "Total (R$)"},
                           title="Total da carteira por data",
                           markers=True, color_discrete_sequence=["#2196F3"])
            fig4.update_layout(height=280, yaxis_tickformat=",.0f")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Sem histórico.")

    with aba_add:
        st.subheader("Adicionar Posição")
        clientes = _clientes()
        ativos = _ativos()
        opcoes_cli = {c["nomecliente"]: c["idcliente"] for c in clientes}
        opcoes_at = {f"{a['idativo']} – {a['descricao']}": a["idativo"] for a in ativos}

        with st.form("form_add_posicao"):
            data_pos = st.date_input("Data", value=date.today())
            col1, col2 = st.columns(2)
            sel_cli = col1.selectbox("Cliente", list(opcoes_cli.keys()), key="add_pos_cli")
            sel_at = col2.selectbox("Ativo", list(opcoes_at.keys()), key="add_pos_at")
            col3, col4 = st.columns(2)
            qtd = col3.number_input("Quantidade", min_value=1, step=1, value=100)
            valor = col4.number_input("Valor total (R$)", min_value=0.01, step=0.01, value=1000.0)
            col5, col6 = st.columns(2)
            gestora = col5.text_input("Gestora")
            plataforma = col6.text_input("Plataforma")
            submitted = st.form_submit_button("Salvar", type="primary")

        if submitted:
            try:
                crud.criar_posicao_cliente(
                    data_pos, opcoes_cli[sel_cli], opcoes_at[sel_at],
                    valor, gestora, qtd, plataforma
                )
                limpar_cache()
                st.success("Posição adicionada!")
            except Exception as e:
                st.error(f"Erro: {e}")

    with aba_edit:
        st.subheader("Atualizar Posição")
        clientes = _clientes()
        opcoes_cli3 = {c["nomecliente"]: c["idcliente"] for c in clientes}
        datas3 = _datas()

        col1, col2 = st.columns(2)
        sel_c3 = col1.selectbox("Cliente", list(opcoes_cli3.keys()), key="edit_cli")
        data_e = col2.selectbox("Data", datas3, key="edit_dt")
        rows_e = crud.listar_carteira_cliente(opcoes_cli3[sel_c3], data_e)

        if rows_e:
            opcoes_at_e = {f"{r['idativo']} – {r['descricao']}": r for r in rows_e}
            sel_at_e = st.selectbox("Ativo", list(opcoes_at_e.keys()), key="edit_pos_at")
            r = opcoes_at_e[sel_at_e]
            with st.form("form_edit_posicao"):
                col3, col4 = st.columns(2)
                qtd = col3.number_input("Quantidade", value=int(r["qtdcartcliente"]), step=1)
                valor = col4.number_input("Valor total (R$)", value=float(r["vlrcartcliente"]), step=0.01)
                col5, col6 = st.columns(2)
                gestora = col5.text_input("Gestora", value=r["gestora"])
                plataforma = col6.text_input("Plataforma", value=r["plataforma"])
                submitted_e = st.form_submit_button("Atualizar", type="primary")
            if submitted_e:
                try:
                    crud.atualizar_posicao_cliente(
                        data_e, opcoes_cli3[sel_c3], r["idativo"],
                        valor, gestora, qtd, plataforma
                    )
                    limpar_cache()
                    st.success("Posição atualizada!")
                except Exception as e:
                    st.error(f"Erro: {e}")
        else:
            st.info("Nenhuma posição nessa data/cliente.")

    with aba_del:
        st.subheader("Remover Posição")
        clientes = _clientes()
        opcoes_cli4 = {c["nomecliente"]: c["idcliente"] for c in clientes}
        datas4 = _datas()

        col1, col2 = st.columns(2)
        sel_c4 = col1.selectbox("Cliente", list(opcoes_cli4.keys()), key="del_cc_cli")
        data_d = col2.selectbox("Data", datas4, key="del_cc_dt")
        rows_d = crud.listar_carteira_cliente(opcoes_cli4[sel_c4], data_d)

        if rows_d:
            opcoes_at_d = {f"{r['idativo']} – {r['descricao']}": r for r in rows_d}
            sel_at_d = st.selectbox("Ativo", list(opcoes_at_d.keys()), key="del_pos_at")
            rd = opcoes_at_d[sel_at_d]
            st.warning(f"Remover **{rd['descricao']}** da carteira de {sel_c4} em {data_d}?")
            if st.button("Confirmar remoção", type="primary"):
                try:
                    crud.deletar_posicao_cliente(data_d, opcoes_cli4[sel_c4], rd["idativo"])
                    limpar_cache()
                    st.success("Posição removida.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
        else:
            st.info("Nenhuma posição para remover.")

    with aba_comp:
        st.subheader("Compromissos do Cliente")
        clientes = _clientes()
        opcoes_cli5 = {"Todos": None} | {c["nomecliente"]: c["idcliente"] for c in clientes}
        sel_c5 = st.selectbox("Cliente", list(opcoes_cli5.keys()), key="comp_cli")
        rows_comp = crud.listar_compromissos(opcoes_cli5[sel_c5])
        if rows_comp:
            df_comp = pd.DataFrame(rows_comp)[["datacompromisso", "nomecliente", "descricao", "valorcompromissado"]]
            df_comp.columns = ["Data", "Cliente", "Ativo", "Valor Compromissado (R$)"]
            df_comp["Valor Compromissado (R$)"] = df_comp["Valor Compromissado (R$)"].astype(float)
            st.dataframe(df_comp, use_container_width=True, hide_index=True)

            total_comp = df_comp["Valor Compromissado (R$)"].sum()
            st.metric("Total comprometido", moeda(total_comp))
        else:
            st.info("Nenhum compromisso encontrado.")

# ──────────────────────────────────────────────────────────────────────────────
# EXPLOSÃO LOOK-THROUGH
# ──────────────────────────────────────────────────────────────────────────────

elif secao == "explosao":
    st.title("🔍 Explosão Look-Through")

    st.info("""
**O que é Look-Through?**
Expande a carteira do cliente até os ativos finais (ações, debêntures, CRI/CRA, LCI/LCA),
atravessando fundos e holdings recursivamente.
Ciclos de cross-holdings são detectados automaticamente.
""")

    clientes = _clientes()
    datas = _datas()
    opcoes_c = {c["nomecliente"]: c for c in clientes}

    col1, col2 = st.columns(2)
    sel_c = col1.selectbox("Cliente", list(opcoes_c.keys()), key="exp_cli")
    data_sel = col2.selectbox("Data de referência", datas, format_func=str, key="exp_dt")
    c = opcoes_c[sel_c]

    if st.button("🔍 Calcular Look-Through", type="primary", use_container_width=True):
        with st.spinner("Calculando explosão recursiva..."):
            ativos_finais = exp.explodir_carteira_cliente(c["idcliente"], data_sel)
            rows_diretos = crud.listar_carteira_cliente(c["idcliente"], data_sel)

        if not ativos_finais:
            st.warning("Nenhuma posição encontrada para essa data.")
        else:
            ativos_finais.sort(key=lambda a: a.vlr_efetivo, reverse=True)
            total_lt = sum(a.vlr_efetivo for a in ativos_finais)
            total_dir = sum(float(r["vlrcartcliente"]) for r in rows_diretos)
            n_expandidos = sum(1 for a in ativos_finais if a.caminho)

            # métricas
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Ativos finais (look-through)", len(ativos_finais))
            m2.metric("Ativos expandidos via fundo/holding", n_expandidos)
            m3.metric("Valor look-through", moeda(total_lt))
            m4.metric("Valor carteira direta", moeda(total_dir))

            st.divider()

            # tabela detalhada
            df_lt = pd.DataFrame([{
                "ID": a.id_ativo,
                "Descrição": a.descricao,
                "Tipo": a.tipo,
                "Qtd Efetiva": round(a.qtd_efetiva, 4),
                "Valor Efetivo (R$)": round(a.vlr_efetivo, 2),
                "% do Total": f"{a.vlr_efetivo/total_lt:.1%}" if total_lt else "–",
                "Via": " → ".join(a.caminho) if a.caminho else "Direto",
            } for a in ativos_finais])

            st.subheader("Composição after Look-Through")
            st.dataframe(df_lt, use_container_width=True, hide_index=True,
                         column_config={
                             "Valor Efetivo (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                             "Qtd Efetiva": st.column_config.NumberColumn(format="%.4f"),
                         })

            st.divider()

            # gráficos
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                fig_pie = px.pie(df_lt, names="Descrição", values="Valor Efetivo (R$)",
                                 title="Distribuição look-through por ativo",
                                 hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Set2)
                fig_pie.update_layout(height=380)
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_g2:
                fig_tipo = px.pie(
                    df_lt.groupby("Tipo")["Valor Efetivo (R$)"].sum().reset_index(),
                    names="Tipo", values="Valor Efetivo (R$)",
                    title="Distribuição por tipo de ativo",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                fig_tipo.update_layout(height=380)
                st.plotly_chart(fig_tipo, use_container_width=True)

            # comparação direto vs look-through
            if n_expandidos > 0:
                st.subheader("Carteira Direta vs Look-Through")

                # agrupa direto
                df_dir_agg = pd.DataFrame(rows_diretos)
                df_dir_agg["vlrcartcliente"] = df_dir_agg["vlrcartcliente"].astype(float)
                df_dir_agg = df_dir_agg.groupby("descricao")["vlrcartcliente"].sum().reset_index()
                df_dir_agg.columns = ["Ativo", "Valor"]
                df_dir_agg["Visão"] = "Direta"

                df_lt_agg = df_lt[["Descrição", "Valor Efetivo (R$)"]].copy()
                df_lt_agg.columns = ["Ativo", "Valor"]
                df_lt_agg["Visão"] = "Look-Through"

                df_comp_all = pd.concat([df_dir_agg, df_lt_agg])
                fig_comp = px.bar(df_comp_all, x="Ativo", y="Valor", color="Visão",
                                  barmode="group",
                                  color_discrete_map={"Direta": "#64B5F6", "Look-Through": "#FF8A65"},
                                  labels={"Valor": "Valor (R$)"},
                                  title="Composição: posição direta vs ativos finais look-through")
                fig_comp.update_layout(height=380, yaxis_tickformat=",.0f", xaxis_title="")
                st.plotly_chart(fig_comp, use_container_width=True)

                # fluxo de expansão (Sankey)
                st.subheader("Fluxo de Expansão (Sankey)")
                expandidos = [a for a in ativos_finais if a.caminho]
                if expandidos:
                    labels, sources, targets, values = [], [], [], []
                    label_idx = {}

                    def idx(label):
                        if label not in label_idx:
                            label_idx[label] = len(labels)
                            labels.append(label)
                        return label_idx[label]

                    for af in expandidos:
                        caminho_full = [sel_c] + af.caminho + [af.descricao]
                        for i in range(len(caminho_full) - 1):
                            src = idx(caminho_full[i])
                            tgt = idx(caminho_full[i + 1])
                            sources.append(src)
                            targets.append(tgt)
                            values.append(max(af.vlr_efetivo, 1))

                    fig_sankey = go.Figure(go.Sankey(
                        node=dict(label=labels, pad=15, thickness=20,
                                  color="#2196F3"),
                        link=dict(source=sources, target=targets, value=values,
                                  color="rgba(33,150,243,0.3)"),
                    ))
                    fig_sankey.update_layout(height=420,
                                             title="Fluxo de expansão de carteira")
                    st.plotly_chart(fig_sankey, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# ANÁLISE DE ÍNDICE
# ──────────────────────────────────────────────────────────────────────────────

elif secao == "indice":
    st.title("⚡ Análise de Índice – Performance")

    st.markdown("""
### Caso de uso crítico
Consulta: buscar todas as posições de um cliente ordenadas por data
(relatório mensal, tela de extrato).

**PK atual:** `(DataCarteiraCliente, IDCliente, IDAtivo)`
→ IDCliente é o **2º campo**; filtrar por ele percorre o índice sem poder
ir diretamente ao cliente, custando uma passagem parcial — análogo a
procurar por sobrenome num índice ordenado por nome.

**Índice proposto:** `(IDCliente, DataCarteiraCliente)`
→ acesso **O(log n)** direto ao cliente, já ordenado por data.
""")

    SQL = "SELECT * FROM carteira_cliente WHERE idcliente = 1 ORDER BY datacarteiracliente"
    st.code(SQL, language="sql")

    col_antes, col_depois = st.columns(2)

    with col_antes:
        if st.button("▶ Ver plano SEM índice", use_container_width=True):
            try:
                execute("DROP INDEX IF EXISTS idx_cc_cliente_data")
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SET enable_seqscan = OFF")
                        cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {SQL}")
                        plano = "\n".join(r[0] for r in cur.fetchall())
                st.session_state["plano_antes"] = plano
                st.session_state["indice_criado"] = False
            except Exception as e:
                st.error(str(e))

        if "plano_antes" in st.session_state:
            st.subheader("Sem índice")
            st.code(st.session_state["plano_antes"], language="text")

    with col_depois:
        if st.button("▶ Criar índice e ver plano", use_container_width=True, type="primary"):
            try:
                execute(
                    "CREATE INDEX IF NOT EXISTS idx_cc_cliente_data "
                    "ON carteira_cliente(idcliente, datacarteiracliente)"
                )
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SET enable_seqscan = OFF")
                        cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {SQL}")
                        plano = "\n".join(r[0] for r in cur.fetchall())
                st.session_state["plano_depois"] = plano
                st.session_state["indice_criado"] = True
            except Exception as e:
                st.error(str(e))

        if "plano_depois" in st.session_state:
            st.subheader("Com idx_cc_cliente_data")
            st.code(st.session_state["plano_depois"], language="text")

    st.divider()

    # comparação visual de custo
    if "plano_antes" in st.session_state and "plano_depois" in st.session_state:
        import re

        def extrair_custo(plano_text):
            m = re.search(r"cost=[\d.]+\.\.([\d.]+)", plano_text)
            return float(m.group(1)) if m else None

        def extrair_tempo(plano_text):
            m = re.search(r"Execution Time: ([\d.]+) ms", plano_text)
            return float(m.group(1)) if m else None

        def extrair_buffers(plano_text):
            m = re.search(r"shared hit=(\d+)", plano_text)
            return int(m.group(1)) if m else None

        custo_antes  = extrair_custo(st.session_state["plano_antes"])
        custo_depois = extrair_custo(st.session_state["plano_depois"])
        tempo_antes  = extrair_tempo(st.session_state["plano_antes"])
        tempo_depois = extrair_tempo(st.session_state["plano_depois"])
        buf_antes    = extrair_buffers(st.session_state["plano_antes"])
        buf_depois   = extrair_buffers(st.session_state["plano_depois"])

        st.subheader("Comparação de métricas")
        m1, m2, m3 = st.columns(3)
        if custo_antes and custo_depois:
            delta_c = f"{((custo_depois - custo_antes) / custo_antes * 100):.1f}%"
            m1.metric("Custo estimado (sem índice)", f"{custo_antes:.2f}")
            m1.metric("Custo estimado (com índice)", f"{custo_depois:.2f}", delta=delta_c, delta_color="inverse")
        if tempo_antes and tempo_depois:
            m2.metric("Tempo execução (sem)", f"{tempo_antes:.3f} ms")
            m2.metric("Tempo execução (com)", f"{tempo_depois:.3f} ms")
        if buf_antes is not None and buf_depois is not None:
            m3.metric("Shared buffers (sem)", buf_antes)
            m3.metric("Shared buffers (com)", buf_depois)

        if custo_antes and custo_depois:
            df_bar = pd.DataFrame({
                "Situação": ["Sem índice", "Com índice"],
                "Custo estimado": [custo_antes, custo_depois],
            })
            fig_idx = px.bar(df_bar, x="Situação", y="Custo estimado",
                             color="Situação",
                             color_discrete_map={"Sem índice": "#EF5350", "Com índice": "#66BB6A"},
                             title="Custo do plano de execução (menor é melhor)",
                             text_auto=True)
            fig_idx.update_layout(showlegend=False, height=320)
            st.plotly_chart(fig_idx, use_container_width=True)

    st.divider()
    st.markdown("""
**Por que esse índice importa em produção?**

| Cenário | Sem índice | Com índice |
|---|---|---|
| 1 000 clientes, 360 posições/cliente | Percorre 360 000 registros | Salta direto aos ~360 do cliente |
| Complexidade | O(n) com n = total de registros | O(log n + k) com k = posições do cliente |
| Sort adicional | Necessário (DataCarteiraCliente não era 1ª coluna) | Eliminado (já ordenado no índice) |
""")

# ──────────────────────────────────────────────────────────────────────────────
# SQL LIVRE
# ──────────────────────────────────────────────────────────────────────────────

elif secao == "sql":
    st.title("🛠️ Consulta SQL Livre")

    st.info("Execute qualquer SELECT no schema `carteiras_wm`. Útil para demonstrações ao vivo.")

    EXEMPLOS = {
        "── selecione um exemplo ──": "",
        "Patrimônio por cliente na última data": """SELECT c.nomecliente,
       SUM(cc.vlrcartcliente) AS patrimonio
FROM carteira_cliente cc
JOIN cliente c ON c.idcliente = cc.idcliente
WHERE cc.datacarteiracliente = (SELECT MAX(datacarteiracliente) FROM carteira_cliente)
GROUP BY c.nomecliente
ORDER BY patrimonio DESC;""",
        "Composição da carteira de João Silva (jan/25)": """SELECT a.descricao, a.tipo, a.setor,
       cc.qtdcartcliente AS qtd,
       cc.vlrcartcliente AS valor,
       cc.gestora, cc.plataforma
FROM carteira_cliente cc
JOIN ativo a ON a.idativo = cc.idativo
JOIN cliente c ON c.idcliente = cc.idcliente
WHERE c.nomecliente = 'João Silva'
  AND cc.datacarteiracliente = '2025-01-31'
ORDER BY valor DESC;""",
        "Carteira completa do Fundo FIA Alpha (fev/25)": """SELECT f.nomefundo, a.descricao, a.tipo,
       cf.qtdcartfundo AS qtd,
       cf.vlrcartfundo AS valor
FROM carteira_fundo cf
JOIN fundo f ON f.idfundo = cf.idfundo
JOIN ativo a ON a.idativo = cf.idativo
WHERE f.nomefundo = 'FIA Alpha Ações'
  AND cf.datacartfundo = '2025-02-28'
ORDER BY valor DESC;""",
        "Evolução mensal por cliente": """SELECT c.nomecliente,
       cc.datacarteiracliente AS data,
       SUM(cc.vlrcartcliente) AS total
FROM carteira_cliente cc
JOIN cliente c ON c.idcliente = cc.idcliente
GROUP BY c.nomecliente, cc.datacarteiracliente
ORDER BY c.nomecliente, data;""",
        "Ativos comuns entre clientes e fundos": """SELECT a.descricao, a.tipo,
       COUNT(DISTINCT cc.idcliente) AS clientes_diretos,
       COUNT(DISTINCT cf.idfundo)  AS fundos
FROM ativo a
LEFT JOIN carteira_cliente cc ON cc.idativo = a.idativo
LEFT JOIN carteira_fundo   cf ON cf.idativo = a.idativo
GROUP BY a.idativo, a.descricao, a.tipo
HAVING COUNT(DISTINCT cc.idcliente) > 0 OR COUNT(DISTINCT cf.idfundo) > 0
ORDER BY clientes_diretos DESC, fundos DESC;""",
        "Compromissos futuros por cliente": """SELECT c.nomecliente,
       a.descricao AS ativo,
       cc2.datacompromisso AS data,
       cc2.valorcompromissado AS valor
FROM compromisso_cliente cc2
JOIN cliente c ON c.idcliente = cc2.idcliente
JOIN ativo   a ON a.idativo   = cc2.idativo
ORDER BY cc2.datacompromisso, c.nomecliente;""",
    }

    exemplo_sel = st.selectbox("Carregar exemplo", list(EXEMPLOS.keys()), key="sql_exemplo")
    sql_default = EXEMPLOS[exemplo_sel] if exemplo_sel in EXEMPLOS else ""

    sql_input = st.text_area("SQL", value=sql_default, height=180,
                              placeholder="SELECT ... FROM ... WHERE ...")

    col_run, col_exp = st.columns([1, 1])
    rodar = col_run.button("▶ Executar", type="primary", use_container_width=True)
    explain_check = col_exp.checkbox("Mostrar EXPLAIN ANALYZE", value=False)

    if rodar and sql_input.strip():
        sql_clean = sql_input.strip()
        if not sql_clean.upper().lstrip().startswith("SELECT"):
            st.error("Apenas SELECT é permitido.")
        else:
            try:
                if explain_check:
                    with get_conn() as conn:
                        with conn.cursor() as cur:
                            cur.execute(f"EXPLAIN (ANALYZE, FORMAT TEXT) {sql_clean}")
                            plano = "\n".join(r[0] for r in cur.fetchall())
                    st.subheader("Plano de Execução")
                    st.code(plano, language="text")

                rows = query(sql_clean)
                if not rows:
                    st.info("A consulta não retornou linhas.")
                else:
                    df_sql = pd.DataFrame(rows)
                    st.success(f"{len(rows)} linha(s) retornada(s).")
                    st.dataframe(df_sql, use_container_width=True, hide_index=True)

                    # download CSV
                    csv = df_sql.to_csv(index=False).encode("utf-8")
                    st.download_button("⬇ Baixar CSV", csv, "resultado.csv", "text/csv")

            except Exception as e:
                st.error(f"Erro na consulta: {e}")
