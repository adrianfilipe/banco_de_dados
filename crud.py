"""Operações CRUD para todas as entidades do schema carteiras_wm."""

from db import query, execute, execute_returning

# ──────────────────────────────────────────────
# CLIENTE
# ──────────────────────────────────────────────

def listar_clientes():
    return query("SELECT * FROM cliente ORDER BY idcliente")


def buscar_cliente(id_cliente):
    rows = query("SELECT * FROM cliente WHERE idcliente = %s", (id_cliente,))
    return rows[0] if rows else None


def criar_cliente(nome, codigo, documento):
    rows = query("SELECT COALESCE(MAX(idcliente),0)+1 AS novo FROM cliente")
    novo_id = rows[0]["novo"]
    execute(
        "INSERT INTO cliente (idcliente, nomecliente, codigocliente, documentocliente) VALUES (%s,%s,%s,%s)",
        (novo_id, nome, codigo, documento),
    )
    return novo_id


def atualizar_cliente(id_cliente, nome, codigo, documento):
    return execute(
        "UPDATE cliente SET nomecliente=%s, codigocliente=%s, documentocliente=%s WHERE idcliente=%s",
        (nome, codigo, documento, id_cliente),
    )


def deletar_cliente(id_cliente):
    return execute("DELETE FROM cliente WHERE idcliente=%s", (id_cliente,))


# ──────────────────────────────────────────────
# ATIVO
# ──────────────────────────────────────────────

def listar_ativos():
    return query("SELECT * FROM ativo ORDER BY idativo")


def buscar_ativo(id_ativo):
    rows = query("SELECT * FROM ativo WHERE idativo = %s", (id_ativo,))
    return rows[0] if rows else None


def criar_ativo(setor, descricao, tipo, cnpj_emissor=None, den_soc_em=None, isin=None):
    rows = query("SELECT COALESCE(MAX(idativo),0)+1 AS novo FROM ativo")
    novo_id = rows[0]["novo"]
    execute(
        """INSERT INTO ativo (idativo, setor, descricao, tipo, cnpjemissor, den_soc_em, isin)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (novo_id, setor, descricao, tipo, cnpj_emissor, den_soc_em, isin),
    )
    return novo_id


def atualizar_ativo(id_ativo, setor, descricao, tipo, cnpj_emissor=None, den_soc_em=None, isin=None):
    return execute(
        """UPDATE ativo SET setor=%s, descricao=%s, tipo=%s, cnpjemissor=%s,
           den_soc_em=%s, isin=%s WHERE idativo=%s""",
        (setor, descricao, tipo, cnpj_emissor, den_soc_em, isin, id_ativo),
    )


def deletar_ativo(id_ativo):
    return execute("DELETE FROM ativo WHERE idativo=%s", (id_ativo,))


# ──────────────────────────────────────────────
# FUNDO
# ──────────────────────────────────────────────

def listar_fundos():
    return query("SELECT * FROM fundo ORDER BY idfundo")


def buscar_fundo(id_fundo):
    rows = query("SELECT * FROM fundo WHERE idfundo=%s", (id_fundo,))
    return rows[0] if rows else None


def criar_fundo(nome, cnpj, subclasse, classificacao):
    rows = query("SELECT COALESCE(MAX(idfundo),0)+1 AS novo FROM fundo")
    novo_id = rows[0]["novo"]
    execute(
        "INSERT INTO fundo (idfundo, nomefundo, cnpjfundo, subclassefundo, classificacaofundo) VALUES (%s,%s,%s,%s,%s)",
        (novo_id, nome, cnpj, subclasse or None, classificacao),
    )
    return novo_id


def atualizar_fundo(id_fundo, nome, cnpj, subclasse, classificacao):
    return execute(
        "UPDATE fundo SET nomefundo=%s, cnpjfundo=%s, subclassefundo=%s, classificacaofundo=%s WHERE idfundo=%s",
        (nome, cnpj, subclasse or None, classificacao, id_fundo),
    )


def deletar_fundo(id_fundo):
    return execute("DELETE FROM fundo WHERE idfundo=%s", (id_fundo,))


# ──────────────────────────────────────────────
# HOLDING
# ──────────────────────────────────────────────

def listar_holdings():
    return query("SELECT * FROM holding ORDER BY idholding")


def buscar_holding(id_holding):
    rows = query("SELECT * FROM holding WHERE idholding=%s", (id_holding,))
    return rows[0] if rows else None


def criar_holding(nome, cnpj):
    rows = query("SELECT COALESCE(MAX(idholding),0)+1 AS novo FROM holding")
    novo_id = rows[0]["novo"]
    execute(
        "INSERT INTO holding (idholding, cnpjholding, nomeholding) VALUES (%s,%s,%s)",
        (novo_id, cnpj, nome),
    )
    return novo_id


def atualizar_holding(id_holding, nome, cnpj):
    return execute(
        "UPDATE holding SET nomeholding=%s, cnpjholding=%s WHERE idholding=%s",
        (nome, cnpj, id_holding),
    )


def deletar_holding(id_holding):
    return execute("DELETE FROM holding WHERE idholding=%s", (id_holding,))


# ──────────────────────────────────────────────
# CARTEIRA CLIENTE
# ──────────────────────────────────────────────

def listar_carteira_cliente(id_cliente=None, data=None):
    sql = """
        SELECT cc.*, a.descricao, a.tipo
        FROM carteira_cliente cc
        JOIN ativo a ON a.idativo = cc.idativo
        WHERE 1=1
    """
    params = []
    if id_cliente:
        sql += " AND cc.idcliente = %s"
        params.append(id_cliente)
    if data:
        sql += " AND cc.datacarteiracliente = %s"
        params.append(data)
    sql += " ORDER BY cc.datacarteiracliente, cc.idcliente, cc.idativo"
    return query(sql, params or None)


def criar_posicao_cliente(data, id_cliente, id_ativo, valor, gestora, quantidade, plataforma):
    return execute(
        """INSERT INTO carteira_cliente
           (datacarteiracliente, idcliente, idativo, vlrcartcliente, gestora, qtdcartcliente, plataforma)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (data, id_cliente, id_ativo, valor, gestora, quantidade, plataforma),
    )


def atualizar_posicao_cliente(data, id_cliente, id_ativo, valor, gestora, quantidade, plataforma):
    return execute(
        """UPDATE carteira_cliente
           SET vlrcartcliente=%s, gestora=%s, qtdcartcliente=%s, plataforma=%s
           WHERE datacarteiracliente=%s AND idcliente=%s AND idativo=%s""",
        (valor, gestora, quantidade, plataforma, data, id_cliente, id_ativo),
    )


def deletar_posicao_cliente(data, id_cliente, id_ativo):
    return execute(
        "DELETE FROM carteira_cliente WHERE datacarteiracliente=%s AND idcliente=%s AND idativo=%s",
        (data, id_cliente, id_ativo),
    )


# ──────────────────────────────────────────────
# CARTEIRA FUNDO
# ──────────────────────────────────────────────

def listar_carteira_fundo(id_fundo=None, data=None):
    sql = """
        SELECT cf.*, a.descricao, a.tipo, f.nomefundo
        FROM carteira_fundo cf
        JOIN ativo a ON a.idativo = cf.idativo
        JOIN fundo f ON f.idfundo = cf.idfundo
        WHERE 1=1
    """
    params = []
    if id_fundo:
        sql += " AND cf.idfundo = %s"
        params.append(id_fundo)
    if data:
        sql += " AND cf.datacartfundo = %s"
        params.append(data)
    sql += " ORDER BY cf.datacartfundo, cf.idfundo, cf.idativo"
    return query(sql, params or None)


# ──────────────────────────────────────────────
# CARTEIRA HOLDING
# ──────────────────────────────────────────────

def listar_carteira_holding(id_holding=None, data=None):
    sql = """
        SELECT ch.*, a.descricao, a.tipo, h.nomeholding
        FROM carteira_holding ch
        JOIN ativo a ON a.idativo = ch.idativo
        JOIN holding h ON h.idholding = ch.idholding
        WHERE 1=1
    """
    params = []
    if id_holding:
        sql += " AND ch.idholding = %s"
        params.append(id_holding)
    if data:
        sql += " AND ch.datacartholding = %s"
        params.append(data)
    sql += " ORDER BY ch.datacartholding, ch.idholding, ch.idativo"
    return query(sql, params or None)


# ──────────────────────────────────────────────
# COMPROMISSO CLIENTE
# ──────────────────────────────────────────────

def listar_compromissos(id_cliente=None):
    sql = """
        SELECT cc.*, a.descricao, c.nomecliente
        FROM compromisso_cliente cc
        JOIN ativo a ON a.idativo = cc.idativo
        JOIN cliente c ON c.idcliente = cc.idcliente
        WHERE 1=1
    """
    params = []
    if id_cliente:
        sql += " AND cc.idcliente = %s"
        params.append(id_cliente)
    sql += " ORDER BY cc.datacompromisso, cc.idcliente"
    return query(sql, params or None)


# ──────────────────────────────────────────────
# DADOS TEMPORAIS
# ──────────────────────────────────────────────

def listar_datas_disponiveis():
    """Retorna datas com dados de carteira cliente."""
    rows = query("SELECT DISTINCT datacarteiracliente FROM carteira_cliente ORDER BY 1")
    return [r["datacarteiracliente"] for r in rows]


def get_preco_ativo(id_ativo, data):
    rows = query(
        "SELECT precoativo FROM tempdataativo WHERE idativo=%s AND databaseativo=%s",
        (id_ativo, data),
    )
    return float(rows[0]["precoativo"]) if rows else None
