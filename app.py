import psycopg2
from psycopg2 import sql

# Configurações de conexão
DB_CONFIG = {
    "dbname": "seu_banco",
    "user": "seu_usuario",
    "password": "sua_senha",
    "host": "localhost",
    "port": "5432"
}

def conectar():
    """Estabelece conexão com o banco de dados."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        # Força o uso do schema correto criado na Fase 3
        with conn.cursor() as cur:
            cur.execute("SET search_path = carteiras_wm;")
        return conn
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return None

def criar_posicao(conn):
    """C (Create) - Insere um novo ativo na carteira do cliente."""
    print("\n--- Adicionar Posição na Carteira ---")
    data = input("Data (YYYY-MM-DD): ")
    id_cliente = input("ID do Cliente: ")
    id_ativo = input("ID do Ativo: ")
    valor = input("Valor Total (R$): ")
    gestora = input("Gestora: ")
    qtd = input("Quantidade: ")
    plataforma = input("Plataforma: ")

    query = """
        INSERT INTO Carteira_Cliente 
        (DataCarteiraCliente, IDCliente, IDAtivo, VlrCartCliente, Gestora, QtdCartCliente, Plataforma)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query, (data, id_cliente, id_ativo, valor, gestora, qtd, plataforma))
        conn.commit()
        print("Posição adicionada com sucesso!")
    except Exception as e:
        conn.rollback()
        print(f"Erro ao inserir: {e}")

def ler_carteira(conn):
    """R (Read) - Visualiza a carteira de um cliente em uma data."""
    print("\n--- Consultar Carteira ---")
    id_cliente = input("ID do Cliente: ")
    data = input("Data (YYYY-MM-DD): ")

    query = """
        SELECT a.Descricao, cc.QtdCartCliente, cc.VlrCartCliente, cc.Plataforma
        FROM Carteira_Cliente cc
        JOIN Ativo a ON cc.IDAtivo = a.IDAtivo
        WHERE cc.IDCliente = %s AND cc.DataCarteiraCliente = %s
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query, (id_cliente, data))
            resultados = cur.fetchall()
            
            print(f"\n--- Posição do Cliente {id_cliente} em {data} ---")
            print(f"{'Ativo':<30} | {'Qtd':<10} | {'Valor (R$)':<15} | {'Plataforma'}")
            print("-" * 75)
            for linha in resultados:
                print(f"{linha[0]:<30} | {linha[1]:<10} | {linha[2]:<15.2f} | {linha[3]}")
    except Exception as e:
        print(f"Erro na consulta: {e}")

def atualizar_valor(conn):
    """U (Update) - Atualiza o valor financeiro de uma posição."""
    print("\n--- Atualizar Valor da Posição ---")
    data = input("Data (YYYY-MM-DD): ")
    id_cliente = input("ID do Cliente: ")
    id_ativo = input("ID do Ativo: ")
    novo_valor = input("Novo Valor Total (R$): ")

    query = """
        UPDATE Carteira_Cliente 
        SET VlrCartCliente = %s
        WHERE DataCarteiraCliente = %s AND IDCliente = %s AND IDAtivo = %s
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query, (novo_valor, data, id_cliente, id_ativo))
            if cur.rowcount > 0:
                print("Valor atualizado com sucesso!")
            else:
                print("Posição não encontrada.")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar: {e}")

def deletar_posicao(conn):
    """D (Delete) - Remove um ativo da carteira (ex: liquidação total)."""
    print("\n--- Remover Posição (Liquidação) ---")
    data = input("Data (YYYY-MM-DD): ")
    id_cliente = input("ID do Cliente: ")
    id_ativo = input("ID do Ativo: ")

    query = """
        DELETE FROM Carteira_Cliente 
        WHERE DataCarteiraCliente = %s AND IDCliente = %s AND IDAtivo = %s
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query, (data, id_cliente, id_ativo))
            if cur.rowcount > 0:
                print("Posição removida com sucesso!")
            else:
                print("Posição não encontrada.")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Erro ao deletar: {e}")

def menu():
    conn = conectar()
    if not conn:
        return

    while True:
        print("\n" + "="*30)
        print(" SISTEMA WEALTH MANAGEMENT")
        print("="*30)
        print("1. Adicionar Posição (Create)")
        print("2. Consultar Carteira (Read)")
        print("3. Atualizar Valor (Update)")
        print("4. Liquidar Posição (Delete)")
        print("5. Sair")
        
        escolha = input("Escolha uma opção: ")
        
        if escolha == '1': criar_posicao(conn)
        elif escolha == '2': ler_carteira(conn)
        elif escolha == '3': atualizar_valor(conn)
        elif escolha == '4': deletar_posicao(conn)
        elif escolha == '5':
            conn.close()
            print("Encerrando...")
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    menu()