#!/usr/bin/env python3
"""
CRUD – Carteiras Wealth Management
Interface console com psycopg2 / PostgreSQL
"""

import sys
import os
from datetime import date, datetime

# garante que os módulos locais sejam encontrados
sys.path.insert(0, os.path.dirname(__file__))

import crud
import explode as exp
from db import execute, query, explain

LINHA = "─" * 70


# ══════════════════════════════════════════════════════════════════════════════
# helpers de UI
# ══════════════════════════════════════════════════════════════════════════════

def cabecalho(titulo: str):
    print(f"\n{LINHA}")
    print(f"  {titulo}")
    print(LINHA)


def pausar():
    input("\n  [ENTER para continuar]")


def ler_int(prompt: str, minimo: int = None, maximo: int = None) -> int:
    while True:
        try:
            val = int(input(f"  {prompt}: ").strip())
            if minimo is not None and val < minimo:
                print(f"  Valor mínimo: {minimo}")
                continue
            if maximo is not None and val > maximo:
                print(f"  Valor máximo: {maximo}")
                continue
            return val
        except ValueError:
            print("  Informe um número inteiro válido.")


def ler_float(prompt: str) -> float:
    while True:
        try:
            return float(input(f"  {prompt}: ").strip().replace(",", "."))
        except ValueError:
            print("  Informe um número válido.")


def ler_str(prompt: str, obrigatorio: bool = True) -> str:
    while True:
        val = input(f"  {prompt}: ").strip()
        if val or not obrigatorio:
            return val
        print("  Campo obrigatório.")


def ler_data(prompt: str) -> date:
    while True:
        raw = input(f"  {prompt} (AAAA-MM-DD): ").strip()
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("  Formato inválido. Use AAAA-MM-DD.")


def tabela(colunas: list[str], linhas: list[list], larguras: list[int] = None):
    if larguras is None:
        larguras = [max(len(str(c)), max((len(str(l[i])) for l in linhas), default=0))
                    for i, c in enumerate(colunas)]
    fmt = "  " + "  ".join(f"{{:<{w}}}" for w in larguras)
    print(fmt.format(*colunas))
    print("  " + "  ".join("-" * w for w in larguras))
    for linha in linhas:
        print(fmt.format(*[str(v) if v is not None else "" for v in linha]))


def menu(titulo: str, opcoes: list[str]) -> int:
    cabecalho(titulo)
    for i, op in enumerate(opcoes, 1):
        print(f"  {i}. {op}")
    print(f"  0. Voltar / Sair")
    return ler_int("Opção", 0, len(opcoes))


# ══════════════════════════════════════════════════════════════════════════════
# CLIENTES
# ══════════════════════════════════════════════════════════════════════════════

def tela_clientes():
    while True:
        op = menu("CLIENTES", ["Listar todos", "Buscar por ID", "Cadastrar", "Atualizar", "Excluir"])
        if op == 0:
            break
        elif op == 1:
            _listar_clientes()
        elif op == 2:
            _buscar_cliente()
        elif op == 3:
            _criar_cliente()
        elif op == 4:
            _atualizar_cliente()
        elif op == 5:
            _excluir_cliente()


def _listar_clientes():
    cabecalho("LISTA DE CLIENTES")
    clientes = crud.listar_clientes()
    if not clientes:
        print("  Nenhum cliente cadastrado.")
    else:
        tabela(
            ["ID", "Nome", "Código", "Documento"],
            [[c["idcliente"], c["nomecliente"], c["codigocliente"], c["documentocliente"]] for c in clientes],
            [4, 30, 8, 20],
        )
    pausar()


def _buscar_cliente():
    cabecalho("BUSCAR CLIENTE")
    id_c = ler_int("ID do cliente")
    c = crud.buscar_cliente(id_c)
    if not c:
        print(f"  Cliente {id_c} não encontrado.")
    else:
        print(f"\n  ID:        {c['idcliente']}")
        print(f"  Nome:      {c['nomecliente']}")
        print(f"  Código:    {c['codigocliente']}")
        print(f"  Documento: {c['documentocliente']}")
    pausar()


def _criar_cliente():
    cabecalho("CADASTRAR CLIENTE")
    nome = ler_str("Nome")
    codigo = ler_str("Código (sigla)")
    documento = ler_str("CPF/CNPJ")
    novo_id = crud.criar_cliente(nome, codigo, documento)
    print(f"\n  Cliente criado com ID {novo_id}.")
    pausar()


def _atualizar_cliente():
    cabecalho("ATUALIZAR CLIENTE")
    id_c = ler_int("ID do cliente a atualizar")
    c = crud.buscar_cliente(id_c)
    if not c:
        print(f"  Cliente {id_c} não encontrado.")
        pausar()
        return
    print(f"  Atual: {c['nomecliente']} | {c['codigocliente']} | {c['documentocliente']}")
    nome = ler_str("Novo nome")
    codigo = ler_str("Novo código")
    documento = ler_str("Novo documento")
    n = crud.atualizar_cliente(id_c, nome, codigo, documento)
    print(f"\n  {n} registro(s) atualizado(s).")
    pausar()


def _excluir_cliente():
    cabecalho("EXCLUIR CLIENTE")
    id_c = ler_int("ID do cliente a excluir")
    c = crud.buscar_cliente(id_c)
    if not c:
        print(f"  Cliente {id_c} não encontrado.")
        pausar()
        return
    print(f"  Confirma exclusão de '{c['nomecliente']}'? (s/N) ", end="")
    if input().strip().lower() != "s":
        print("  Cancelado.")
    else:
        try:
            crud.deletar_cliente(id_c)
            print("  Cliente excluído.")
        except Exception as e:
            print(f"  Erro: {e}")
    pausar()


# ══════════════════════════════════════════════════════════════════════════════
# ATIVOS
# ══════════════════════════════════════════════════════════════════════════════

def tela_ativos():
    while True:
        op = menu("ATIVOS", ["Listar todos", "Buscar por ID", "Cadastrar", "Atualizar", "Excluir"])
        if op == 0:
            break
        elif op == 1:
            _listar_ativos()
        elif op == 2:
            _buscar_ativo()
        elif op == 3:
            _criar_ativo()
        elif op == 4:
            _atualizar_ativo()
        elif op == 5:
            _excluir_ativo()


def _listar_ativos():
    cabecalho("LISTA DE ATIVOS")
    ativos = crud.listar_ativos()
    tabela(
        ["ID", "Tipo", "Setor", "Descrição"],
        [[a["idativo"], a["tipo"], a["setor"], a["descricao"][:35]] for a in ativos],
        [4, 16, 15, 36],
    )
    pausar()


def _buscar_ativo():
    cabecalho("BUSCAR ATIVO")
    id_a = ler_int("ID do ativo")
    a = crud.buscar_ativo(id_a)
    if not a:
        print(f"  Ativo {id_a} não encontrado.")
    else:
        for k, v in a.items():
            print(f"  {k:<18}: {v}")
    pausar()


def _criar_ativo():
    cabecalho("CADASTRAR ATIVO")
    setor = ler_str("Setor")
    descricao = ler_str("Descrição")
    tipo = ler_str("Tipo (Ação/Debênture/CRI/LCI/Cota de Fundo)")
    cnpj = ler_str("CNPJ Emissor (opcional)", obrigatorio=False) or None
    den = ler_str("Denominação social (opcional)", obrigatorio=False) or None
    isin = ler_str("ISIN (opcional)", obrigatorio=False) or None
    novo_id = crud.criar_ativo(setor, descricao, tipo, cnpj, den, isin)
    print(f"\n  Ativo criado com ID {novo_id}.")
    pausar()


def _atualizar_ativo():
    cabecalho("ATUALIZAR ATIVO")
    id_a = ler_int("ID do ativo")
    a = crud.buscar_ativo(id_a)
    if not a:
        print(f"  Ativo {id_a} não encontrado.")
        pausar()
        return
    print(f"  Atual: {a['descricao']}")
    setor = ler_str("Novo setor")
    descricao = ler_str("Nova descrição")
    tipo = ler_str("Novo tipo")
    cnpj = ler_str("CNPJ Emissor (opcional)", obrigatorio=False) or None
    den = ler_str("Denominação social (opcional)", obrigatorio=False) or None
    isin = ler_str("ISIN (opcional)", obrigatorio=False) or None
    n = crud.atualizar_ativo(id_a, setor, descricao, tipo, cnpj, den, isin)
    print(f"\n  {n} registro(s) atualizado(s).")
    pausar()


def _excluir_ativo():
    cabecalho("EXCLUIR ATIVO")
    id_a = ler_int("ID do ativo")
    a = crud.buscar_ativo(id_a)
    if not a:
        print(f"  Ativo {id_a} não encontrado.")
        pausar()
        return
    print(f"  Confirma exclusão de '{a['descricao']}'? (s/N) ", end="")
    if input().strip().lower() != "s":
        print("  Cancelado.")
    else:
        try:
            crud.deletar_ativo(id_a)
            print("  Ativo excluído.")
        except Exception as e:
            print(f"  Erro: {e}")
    pausar()


# ══════════════════════════════════════════════════════════════════════════════
# FUNDOS
# ══════════════════════════════════════════════════════════════════════════════

def tela_fundos():
    while True:
        op = menu("FUNDOS", ["Listar todos", "Ver carteira do fundo", "Cadastrar fundo", "Atualizar fundo", "Excluir fundo"])
        if op == 0:
            break
        elif op == 1:
            cabecalho("LISTA DE FUNDOS")
            fundos = crud.listar_fundos()
            tabela(
                ["ID", "Nome", "Classe", "CNPJ"],
                [[f["idfundo"], f["nomefundo"], f["classificacaofundo"], f["cnpjfundo"]] for f in fundos],
                [4, 30, 8, 22],
            )
            pausar()
        elif op == 2:
            cabecalho("CARTEIRA DO FUNDO")
            id_f = ler_int("ID do fundo")
            data = ler_data("Data de referência")
            rows = crud.listar_carteira_fundo(id_f, data)
            if not rows:
                print("  Sem dados para essa data/fundo.")
            else:
                tabela(
                    ["Ativo ID", "Descrição", "Tipo", "Qtd", "Valor (R$)"],
                    [[r["idativo"], r["descricao"][:30], r["tipo"], r["qtdcartfundo"], f'{r["vlrcartfundo"]:,.2f}'] for r in rows],
                    [8, 32, 16, 8, 16],
                )
            pausar()
        elif op == 3:
            cabecalho("CADASTRAR FUNDO")
            nome = ler_str("Nome do fundo")
            cnpj = ler_str("CNPJ")
            subclasse = ler_str("Subclasse (opcional)", obrigatorio=False) or None
            classificacao = ler_str("Classificação (FIA/FIDC/FIM/FIRF)")
            novo_id = crud.criar_fundo(nome, cnpj, subclasse, classificacao)
            print(f"\n  Fundo criado com ID {novo_id}.")
            pausar()
        elif op == 4:
            cabecalho("ATUALIZAR FUNDO")
            id_f = ler_int("ID do fundo")
            f = crud.buscar_fundo(id_f)
            if not f:
                print("  Fundo não encontrado.")
                pausar()
                continue
            nome = ler_str("Novo nome")
            cnpj = ler_str("Novo CNPJ")
            subclasse = ler_str("Nova subclasse (opcional)", obrigatorio=False) or None
            classificacao = ler_str("Nova classificação")
            crud.atualizar_fundo(id_f, nome, cnpj, subclasse, classificacao)
            print("  Fundo atualizado.")
            pausar()
        elif op == 5:
            id_f = ler_int("ID do fundo a excluir")
            f = crud.buscar_fundo(id_f)
            if not f:
                print("  Fundo não encontrado.")
            else:
                print(f"  Confirma exclusão de '{f['nomefundo']}'? (s/N) ", end="")
                if input().strip().lower() == "s":
                    try:
                        crud.deletar_fundo(id_f)
                        print("  Fundo excluído.")
                    except Exception as e:
                        print(f"  Erro: {e}")
                else:
                    print("  Cancelado.")
            pausar()


# ══════════════════════════════════════════════════════════════════════════════
# HOLDINGS
# ══════════════════════════════════════════════════════════════════════════════

def tela_holdings():
    while True:
        op = menu("HOLDINGS", ["Listar todas", "Ver carteira da holding", "Cadastrar", "Atualizar", "Excluir"])
        if op == 0:
            break
        elif op == 1:
            cabecalho("LISTA DE HOLDINGS")
            holdings = crud.listar_holdings()
            tabela(
                ["ID", "Nome", "CNPJ"],
                [[h["idholding"], h["nomeholding"], h["cnpjholding"]] for h in holdings],
                [4, 35, 22],
            )
            pausar()
        elif op == 2:
            cabecalho("CARTEIRA DA HOLDING")
            id_h = ler_int("ID da holding")
            data = ler_data("Data de referência")
            rows = crud.listar_carteira_holding(id_h, data)
            if not rows:
                print("  Sem dados para essa data/holding.")
            else:
                tabela(
                    ["Ativo ID", "Descrição", "Tipo", "Qtd", "Valor (R$)"],
                    [[r["idativo"], r["descricao"][:30], r["tipo"], r["qtdcartholding"], f'{r["vlrcartholding"]:,.2f}'] for r in rows],
                    [8, 32, 10, 8, 16],
                )
            pausar()
        elif op == 3:
            cabecalho("CADASTRAR HOLDING")
            nome = ler_str("Nome")
            cnpj = ler_str("CNPJ")
            novo_id = crud.criar_holding(nome, cnpj)
            print(f"\n  Holding criada com ID {novo_id}.")
            pausar()
        elif op == 4:
            id_h = ler_int("ID da holding")
            h = crud.buscar_holding(id_h)
            if not h:
                print("  Holding não encontrada.")
                pausar()
                continue
            nome = ler_str("Novo nome")
            cnpj = ler_str("Novo CNPJ")
            crud.atualizar_holding(id_h, nome, cnpj)
            print("  Holding atualizada.")
            pausar()
        elif op == 5:
            id_h = ler_int("ID da holding a excluir")
            h = crud.buscar_holding(id_h)
            if not h:
                print("  Holding não encontrada.")
            else:
                print(f"  Confirma exclusão de '{h['nomeholding']}'? (s/N) ", end="")
                if input().strip().lower() == "s":
                    try:
                        crud.deletar_holding(id_h)
                        print("  Holding excluída.")
                    except Exception as e:
                        print(f"  Erro: {e}")
                else:
                    print("  Cancelado.")
            pausar()


# ══════════════════════════════════════════════════════════════════════════════
# CARTEIRA CLIENTE (CRUD de posições)
# ══════════════════════════════════════════════════════════════════════════════

def tela_carteira_cliente():
    while True:
        op = menu(
            "CARTEIRA CLIENTE",
            [
                "Ver carteira por cliente/data",
                "Adicionar posição",
                "Atualizar posição",
                "Remover posição",
                "Ver compromissos",
            ],
        )
        if op == 0:
            break
        elif op == 1:
            cabecalho("CARTEIRA DO CLIENTE")
            id_c = ler_int("ID do cliente")
            data = ler_data("Data de referência")
            rows = crud.listar_carteira_cliente(id_c, data)
            if not rows:
                print("  Nenhuma posição encontrada.")
            else:
                c = crud.buscar_cliente(id_c)
                nome_c = c["nomecliente"] if c else f"ID {id_c}"
                print(f"\n  Cliente: {nome_c}  |  Data: {data}")
                tabela(
                    ["Ativo ID", "Descrição", "Tipo", "Qtd", "Valor (R$)", "Gestora"],
                    [
                        [r["idativo"], r["descricao"][:28], r["tipo"], r["qtdcartcliente"],
                         f'{r["vlrcartcliente"]:,.2f}', r["gestora"]]
                        for r in rows
                    ],
                    [8, 30, 16, 6, 16, 14],
                )
                total = sum(float(r["vlrcartcliente"]) for r in rows)
                print(f"\n  TOTAL CARTEIRA: R$ {total:,.2f}")
            pausar()
        elif op == 2:
            cabecalho("ADICIONAR POSIÇÃO")
            data = ler_data("Data")
            id_c = ler_int("ID do cliente")
            id_a = ler_int("ID do ativo")
            qtd = ler_int("Quantidade")
            valor = ler_float("Valor total (R$)")
            gestora = ler_str("Gestora")
            plataforma = ler_str("Plataforma")
            try:
                crud.criar_posicao_cliente(data, id_c, id_a, valor, gestora, qtd, plataforma)
                print("  Posição adicionada.")
            except Exception as e:
                print(f"  Erro: {e}")
            pausar()
        elif op == 3:
            cabecalho("ATUALIZAR POSIÇÃO")
            data = ler_data("Data da posição")
            id_c = ler_int("ID do cliente")
            id_a = ler_int("ID do ativo")
            qtd = ler_int("Nova quantidade")
            valor = ler_float("Novo valor total (R$)")
            gestora = ler_str("Nova gestora")
            plataforma = ler_str("Nova plataforma")
            n = crud.atualizar_posicao_cliente(data, id_c, id_a, valor, gestora, qtd, plataforma)
            print(f"  {n} registro(s) atualizado(s).")
            pausar()
        elif op == 4:
            cabecalho("REMOVER POSIÇÃO")
            data = ler_data("Data da posição")
            id_c = ler_int("ID do cliente")
            id_a = ler_int("ID do ativo")
            print(f"  Confirma remoção? (s/N) ", end="")
            if input().strip().lower() == "s":
                n = crud.deletar_posicao_cliente(data, id_c, id_a)
                print(f"  {n} registro(s) removido(s).")
            else:
                print("  Cancelado.")
            pausar()
        elif op == 5:
            cabecalho("COMPROMISSOS DO CLIENTE")
            id_c = ler_int("ID do cliente (0 = todos)")
            rows = crud.listar_compromissos(id_c if id_c else None)
            if not rows:
                print("  Nenhum compromisso encontrado.")
            else:
                tabela(
                    ["Data", "Cliente", "Ativo", "Valor Compromissado"],
                    [[r["datacompromisso"], r["nomecliente"][:20], r["descricao"][:25], f'{r["valorcompromissado"]:,.2f}'] for r in rows],
                    [12, 22, 27, 20],
                )
            pausar()


# ══════════════════════════════════════════════════════════════════════════════
# EXPLOSÃO DE CARTEIRA
# ══════════════════════════════════════════════════════════════════════════════

def tela_explosao():
    cabecalho("EXPLOSÃO DE CARTEIRA – LOOK-THROUGH")
    print("""
  Esta funcionalidade expande ("explode") a carteira do cliente até os
  ativos finais, atravessando fundos e holdings recursivamente.
  Ciclos de cross-holdings são detectados automaticamente.
""")

    # lista clientes disponíveis
    clientes = crud.listar_clientes()
    tabela(
        ["ID", "Nome", "Documento"],
        [[c["idcliente"], c["nomecliente"], c["documentocliente"]] for c in clientes],
        [4, 28, 20],
    )

    id_c = ler_int("ID do cliente")
    c = crud.buscar_cliente(id_c)
    if not c:
        print("  Cliente não encontrado.")
        pausar()
        return

    # lista datas disponíveis
    datas = crud.listar_datas_disponiveis()
    print("\n  Datas disponíveis:")
    for i, d in enumerate(datas, 1):
        print(f"    {i}. {d}")
    idx = ler_int("Escolha a data (número)", 1, len(datas))
    data = datas[idx - 1]

    print(f"\n  Calculando explosão para {c['nomecliente']} em {data}...")
    ativos_finais = exp.explodir_carteira_cliente(id_c, data)

    if not ativos_finais:
        print("  Sem posições para essa data.")
        pausar()
        return

    # ordenar por valor efetivo decrescente
    ativos_finais.sort(key=lambda a: a.vlr_efetivo, reverse=True)

    cabecalho(f"CARTEIRA EXPLODIDA – {c['nomecliente'].upper()} – {data}")
    print(f"  {'ID':<6} {'Descrição':<35} {'Tipo':<16} {'Qtd Efetiva':>14} {'Valor Efetivo (R$)':>20}")
    print(f"  {'─'*6} {'─'*35} {'─'*16} {'─'*14} {'─'*20}")
    total = 0.0
    for af in ativos_finais:
        print(
            f"  {af.id_ativo:<6} {af.descricao[:35]:<35} {af.tipo[:16]:<16} "
            f"{af.qtd_efetiva:>14.4f} {af.vlr_efetivo:>20,.2f}"
        )
        total += af.vlr_efetivo
    print(f"\n  {'TOTAL LOOK-THROUGH':>57} {total:>20,.2f}")

    # mostrar caminhos se houver expansão
    expandidos = [af for af in ativos_finais if af.caminho]
    if expandidos:
        print(f"\n  Ativos obtidos via expansão de fundo/holding:")
        for af in expandidos:
            print(f"\n    ▶ {af.descricao}")
            for passo in af.caminho:
                print(f"      └─ {passo}")

    # comparar com total direto
    rows_diretos = crud.listar_carteira_cliente(id_c, data)
    total_direto = sum(float(r["vlrcartcliente"]) for r in rows_diretos)
    print(f"\n  Valor carteira direta (sem look-through): R$ {total_direto:,.2f}")
    print(f"  Valor look-through:                       R$ {total:,.2f}")
    if abs(total - total_direto) > 1:
        print(f"""
  OBS: a diferença ocorre porque Carteira_Fundo/Holding contém apenas
  uma amostra dos ativos do fundo/holding neste dataset de demonstração.
  Em produção, com portfólios completos, look-through ≈ carteira direta.""")

    pausar()


# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISE DE ÍNDICE (ponto crítico de performance)
# ══════════════════════════════════════════════════════════════════════════════

def tela_indice():
    cabecalho("ANÁLISE DE ÍNDICE – PONTO CRÍTICO DE PERFORMANCE")
    print("""
  Consulta analisada: buscar TODAS as posições de um cliente ordenadas
  por data (caso de uso: relatório mensal de cliente).

  A chave primária de Carteira_Cliente é (DataCarteiraCliente, IDCliente,
  IDAtivo). Queries por IDCliente precisam filtrar pelo 2º campo da PK,
  o que força Seq Scan ou Index Scan ineficiente em tabelas grandes.

  Índice proposto: (IDCliente, DataCarteiraCliente)
  → acesso O(log n) direto ao cliente, já ordenado por data.

  NOTA: em tabelas pequenas o PostgreSQL escolhe Seq Scan corretamente.
  Nesta demo usamos SET enable_seqscan = OFF para forçar o uso do índice
  e comparar os planos — exatamente o comportamento em produção.
""")
    SQL = "SELECT * FROM carteira_cliente WHERE idcliente = 1 ORDER BY datacarteiracliente"

    print(f"  SQL: {SQL}\n")
    input("  [ENTER] para ver plano ANTES do índice (enable_seqscan=OFF)...")

    cabecalho("PLANO SEM ÍNDICE (Seq Scan forçado OFF)")
    from db import get_conn
    import psycopg2
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SET enable_seqscan = OFF")
                cur.execute("DROP INDEX IF EXISTS idx_cc_cliente_data")
                cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {SQL}")
                plano_antes = "\n".join(r[0] for r in cur.fetchall())
        print(plano_antes)
    except Exception as e:
        print(f"  Erro: {e}")
        pausar()
        return

    input("\n  [ENTER] para criar o índice...")
    try:
        execute(
            "CREATE INDEX IF NOT EXISTS idx_cc_cliente_data "
            "ON carteira_cliente(idcliente, datacarteiracliente)"
        )
        print("\n  Índice idx_cc_cliente_data criado com sucesso!")
    except Exception as e:
        print(f"  Erro ao criar índice: {e}")
        pausar()
        return

    input("  [ENTER] para ver plano APÓS o índice (enable_seqscan=OFF)...")

    cabecalho("PLANO COM ÍNDICE idx_cc_cliente_data")
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SET enable_seqscan = OFF")
                cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {SQL}")
                plano_depois = "\n".join(r[0] for r in cur.fetchall())
        print(plano_depois)
    except Exception as e:
        print(f"  Erro: {e}")
        pausar()
        return

    print(f"""
  ANÁLISE:
  ─────────────────────────────────────────────────────────────────────
  • SEM índice → o plano usa Index Scan no PK (DataCarteiraCliente,
    IDCliente, IDAtivo). O IDCliente não é o primeiro campo, então o
    banco não consegue ir direto ao cliente — percorre o índice PK
    sequencialmente e aplica filtro, com custo O(n).

  • COM índice (IDCliente, DataCarteiraCliente) → Index Scan no novo
    índice: acesso direto às linhas do cliente em O(log n), já
    retornadas na ordem de data sem necessidade de Sort separado.

  Em produção, com milhões de registros de centenas de clientes,
  a diferença de custo é exponencial. O índice elimina tanto o
  filtro quanto o sort, tornando relatórios mensais por cliente
  O(log n + k) onde k é o número de posições do cliente.
  ─────────────────────────────────────────────────────────────────────
""")
    pausar()


# ══════════════════════════════════════════════════════════════════════════════
# CONSULTA SQL LIVRE (para demo do professor)
# ══════════════════════════════════════════════════════════════════════════════

def tela_consulta_livre():
    cabecalho("CONSULTA SQL LIVRE")
    print("  Digite um SELECT para executar no schema carteiras_wm.")
    print("  (deixe em branco para cancelar)\n")
    sql = input("  SQL> ").strip()
    if not sql:
        return
    if not sql.upper().lstrip().startswith("SELECT"):
        print("  Apenas consultas SELECT são permitidas aqui.")
        pausar()
        return
    try:
        rows = query(sql)
        if not rows:
            print("  Sem resultados.")
        else:
            colunas = list(rows[0].keys())
            linhas = [[r[c] for c in colunas] for r in rows]
            tabela(colunas, linhas)
            print(f"\n  {len(rows)} linha(s) retornada(s).")
    except Exception as e:
        print(f"  Erro: {e}")
    pausar()


# ══════════════════════════════════════════════════════════════════════════════
# MENU PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║        SISTEMA CRUD – CARTEIRAS WEALTH MANAGEMENT                   ║
║        Banco: PostgreSQL  |  Conexão: psycopg2                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    while True:
        op = menu(
            "MENU PRINCIPAL",
            [
                "Clientes",
                "Ativos",
                "Fundos",
                "Holdings",
                "Carteira do Cliente",
                "━━ EXPLOSÃO DE CARTEIRA (Look-Through) ━━",
                "━━ ANÁLISE DE ÍNDICE (Performance) ━━",
                "━━ CONSULTA SQL LIVRE ━━",
            ],
        )
        if op == 0:
            print("\n  Até logo!\n")
            break
        elif op == 1:
            tela_clientes()
        elif op == 2:
            tela_ativos()
        elif op == 3:
            tela_fundos()
        elif op == 4:
            tela_holdings()
        elif op == 5:
            tela_carteira_cliente()
        elif op == 6:
            tela_explosao()
        elif op == 7:
            tela_indice()
        elif op == 8:
            tela_consulta_livre()


if __name__ == "__main__":
    main()
