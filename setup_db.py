import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configurações de conexão (ajuste conforme seu ambiente local)
DB_NAME = "microgastos_db"
DB_USER = "postgres"
DB_PASS = "suasenha"
DB_HOST = "localhost"

def setup_database():
    try:
        # 1. Conectar ao Postgres para criar o Database
        con = psycopg2.connect(dbname='postgres', user=DB_USER, password=DB_PASS, host=DB_HOST)
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = con.cursor()
        
        # Deleta se já existir e cria um novo (Cuidado em produção!)
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"✅ Banco de dados '{DB_NAME}' criado com sucesso.")
        cursor.close()
        con.close()

        # 2. Conectar ao novo Database para criar a tabela
        con = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cursor = con.cursor()
        
        # Criação da tabela conforme os requisitos de dados do artigo
        table_query = """
        CREATE TABLE IF NOT EXISTS transacoes (
            id SERIAL PRIMARY KEY,
            data TIMESTAMP NOT NULL,
            descricao TEXT NOT NULL,
            valor NUMERIC(10, 2) NOT NULL,
            categoria VARCHAR(100),
            is_microgasto BOOLEAN
        );
        """
        cursor.execute(table_query)
        con.commit()
        print("✅ Tabela 'transacoes' estruturada conforme modelagem do TCC.")
        
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
    finally:
        if con: cursor.close(); con.close()

if __name__ == "__main__":
    setup_database()