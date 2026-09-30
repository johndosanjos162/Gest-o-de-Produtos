import streamlit as st
from supabase import create_client, Client
import pandas as pd
import sqlite3
import requests
from datetime import datetime

# ==========================================
# CONFIGURAÇÕES INICIAIS
# ==========================================
st.set_page_config(page_title="Sistema Integrado - Gestão & Acesso", page_icon="🛡️", layout="wide")

def init_local_db():
    conn = sqlite3.connect("offline_data.db")
    cursor = conn.cursor()
    # Fila de acessos pendentes de sincronização
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros_pendentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id TEXT,
            tipo_acesso TEXT,
            observacoes TEXT,
            data_hora TEXT
        )
    ''')
    # Cache de usuários para uso offline
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios_cache (
            id TEXT PRIMARY KEY,
            nome TEXT,
            email TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_local_db()

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception:
    st.error("Erro nas credenciais do Supabase. Verifique a pasta .streamlit/secrets.toml")
    st.stop()

def check_conexao():
    try:
        requests.get("https://1.1.1.1", timeout=2)
        return True
    except requests.ConnectionError:
        return False

# ==========================================
# FUNÇÕES DE BANCO DE DADOS (CONTROLE DE ACESSO & GESTÃO)
# ==========================================
def buscar_usuarios_com_cache():
    conn = sqlite3.connect("offline_data.db")
    cursor = conn.cursor()
    
    if check_conexao():
        try:
            resposta = supabase.table("usuarios").select("id, nome, email").execute()
            usuarios = resposta.data
            
            cursor.execute("DELETE FROM usuarios_cache")
            for u in usuarios:
                cursor.execute(
                    "INSERT INTO usuarios_cache (id, nome, email) VALUES (?, ?, ?)",
                    (u['id'], u['nome'], u['email'])
                )
            conn.commit()
            conn.close()
            return usuarios
        except Exception:
            pass 
            
    cursor.execute("SELECT id, nome, email FROM usuarios_cache")
    linhas = cursor.fetchall()
    conn.close()
    return [{"id": l[0], "nome": l[1], "email": l[2]} for l in linhas]

def registrar_acesso(usuario_id, tipo_acesso, observacoes):
    data_hora_atual = datetime.utcnow().isoformat()
    
    if check_conexao():
        try:
            dados = {
                "usuario_id": usuario_id,
                "tipo_acesso": tipo_acesso,
                "observacoes": observacoes,
                "data_hora": data_hora_atual,
                "status_sincronizacao": "sincronizado"
            }
            supabase.table("registros_acesso").insert(dados).execute()
            return True, "online"
        except Exception:
            pass 
            
    conn = sqlite3.connect("offline_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO registros_pendentes (usuario_id, tipo_acesso, observacoes, data_hora) VALUES (?, ?, ?, ?)",
        (usuario_id, tipo_acesso, observacoes, data_hora_atual)
    )
    conn.commit()
    conn.close()
    return True, "offline"

def sincronizar_dados():
    if not check_conexao():
        return 0, "Sem conexão de rede para sincronizar no momento."
        
    conn = sqlite3.connect("offline_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, usuario_id, tipo_acesso, observacoes, data_hora FROM registros_pendentes")
    pendentes = cursor.fetchall()
    
    if not pendentes:
        conn.close()
        return 0, "Nenhum dado pendente na fila."
    
    sucessos = 0
    for row in pendentes:
        id_local, uid, tipo, obs, data_hora_local = row
        try:
            dados = {
                "usuario_id": uid,
                "tipo_acesso": tipo,
                "observacoes": obs,
                "data_hora": data_hora_local,
                "status_sincronizacao": "sincronizado_com_atraso"
            }
            supabase.table("registros_acesso").insert(dados).execute()
            
            cursor.execute("DELETE FROM registros_pendentes WHERE id = ?", (id_local,))
            conn.commit()
            sucessos += 1
        except Exception:
            continue
            
    conn.close()
    return sucessos, f"{sucessos} registros sincronizados com o Supabase."

def cadastrar_usuario(nome, email, biometria_hash, consentimento_lgpd):
    if not check_conexao():
        raise Exception("O cadastro de novos usuários exige conexão com a internet.")
        
    dados = {
        "nome": nome,
        "email": email,
        "biometria_hash": biometria_hash,
        "consentimento_lgpd": consentimento_lgpd
    }
    return supabase.table("usuarios").insert(dados).execute()

# --- Funções de Gestão de Produtos/Vendas (Supabase) ---
def cadastrar_produto(nome_prod, categoria, preco, estoque):
    if not check_conexao():
        raise Exception("A gestão de produtos/vendas requer conexão online com o Supabase.")
    dados = {
        "nome": nome_prod,
        "categoria": categoria,
        "preco": float(preco),
        "estoque": int(estoque)
    }
    return supabase.table("produtos").insert(dados).execute()

def buscar_produtos():
    try:
        resposta = supabase.table("produtos").select("*").execute()
        return resposta.data
    except Exception:
        return []

def registrar_venda(produto_id, quantidade, valor_total):
    if not check_conexao():
        raise Exception("O registro de vendas requer conexão online.")
    dados = {
        "produto_id": produto_id,
        "quantidade": int(quantidade),
        "valor_total": float(valor_total),
        "data_venda": datetime.utcnow().isoformat()
    }
    return supabase.table("vendas").insert(dados).execute()

def buscar_vendas():
    try:
        resposta = supabase.table("vendas").select("*, produtos(nome)").order("data_venda", desc=True).execute()
        return resposta.data
    except Exception:
        return []

# ==========================================
# INTERFACE DO USUÁRIO (UI)
# ==========================================
st.title("🛡️ Sistema Integrado: Gestão, Vendas & Acesso")

is_online = check_conexao()
if is_online:
    st.success("🟢 Sistema Online - Conectado ao servidor.")
else:
    st.warning("🔴 Sistema Offline - Operando no banco de dados local para acessos.")

# Organização por Abas Principais
tab_acesso_menu, tab_gestao_menu, tab_vendas_menu = st.tabs([
    "🔑 Controle de Acesso & Usuários", 
    "📦 Gestão de Produtos", 
    "💰 Registro & Histórico de Vendas"
])

# --- ABA 1: CONTROLE DE ACESSO & USUÁRIOS ---
with tab_acesso_menu:
    sub_cad, sub_reg, sub_hist = st.tabs(["👤 Novo Usuário", "🚪 Registrar Acesso", "📊 Histórico e Sincronização"])
    
    with sub_cad:
        st.header("Cadastrar Novo Perfil")
        with st.form("form_cadastro_usuario"):
            col1, col2 = st.columns(2)
            with col1:
                nome_input = st.text_input("Nome Completo *")
            with col2:
                email_input = st.text_input("E-mail *")
                
            biometria_input = st.text_input("Hash Biométrico", placeholder="Referência da captura...")
            st.markdown("---")
            lgpd_checkbox = st.checkbox("Consentimento LGPD: Autorizo o tratamento e armazenamento dos dados biométricos.")
            
            submit_cadastro = st.form_submit_button("Salvar Perfil")
            
            if submit_cadastro:
                if not nome_input or not email_input:
                    st.warning("Preencha Nome e E-mail.")
                elif not lgpd_checkbox:
                    st.error("O consentimento da LGPD é estritamente obrigatório.")
                else:
                    try:
                        cadastrar_usuario(nome_input, email_input, biometria_input, lgpd_checkbox)
                        st.success(f"Usuário {nome_input} registrado com sucesso!")
                    except Exception as e:
                        st.error(str(e))

    with sub_reg:
        st.header("Registro de Movimentação")
        usuarios_db = buscar_usuarios_com_cache()
        
        if usuarios_db:
            opcoes_usuarios = {f"{u['nome']} ({u['email']})": u['id'] for u in usuarios_db}
            
            with st.form("form_acesso"):
                usuario_selecionado = st.selectbox("Selecione o Usuário", options=list(opcoes_usuarios.keys()))
                tipo_input = st.radio("Direção do Movimento", ["entrada", "saida"], horizontal=True)
                obs_input = st.text_area("Observações Extras (Opcional)")
                
                submit_acesso = st.form_submit_button("Registrar Movimento")
                
                if submit_acesso:
                    user_id = opcoes_usuarios[usuario_selecionado]
                    sucesso, modo = registrar_acesso(user_id, tipo_input, obs_input)
                    
                    if modo == "online":
                        st.success(f"✅ {tipo_input.capitalize()} registrada e validada na nuvem!")
                    else:
                        st.warning(f"💾 Rede indisponível. {tipo_input.capitalize()} armazenada no dispositivo local.")
        else:
            st.info("O cache de usuários está vazio. Conecte-se à internet uma vez para baixar a base.")

    with sub_hist:
        col_sync1, col_sync2 = st.columns([3, 1])
        with col_sync1:
            st.header("Status de Sincronização")
        with col_sync2:
            if st.button("🔄 Sincronizar Agora", use_container_width=True):
                with st.spinner("Processando fila..."):
                    qtd, msg = sincronizar_dados()
                    if qtd > 0:
                        st.success(f"✅ {msg}")
                    else:
                        st.info(f"ℹ️ {msg}")
        
        st.subheader("Fila de Envio (Dados Locais Pendentes)")
        conn = sqlite3.connect("offline_data.db")
        df_pendentes = pd.read_sql_query("SELECT id, tipo_acesso, observacoes, data_hora FROM registros_pendentes", conn)
        conn.close()
        
        if not df_pendentes.empty:
            st.dataframe(df_pendentes, use_container_width=True, hide_index=True)
        else:
            st.write("✓ Fila limpa. Nenhum registro pendente.")
            
        st.markdown("---")
        st.subheader("Histórico Consolidado (Nuvem)")
        
        if is_online:
            if st.button("Buscar Últimos Eventos de Acesso"):
                st.rerun()
                
            resposta = supabase.table("registros_acesso").select("*, usuarios(nome)").order("data_hora", desc=True).limit(50).execute()
            registros_nuvem = resposta.data
            
            if registros_nuvem:
                dados_tabela = []
                for r in registros_nuvem:
                    dados_tabela.append({
                        "Data/Hora": r['data_hora'],
                        "Usuário": r['usuarios']['nome'] if r.get('usuarios') else 'Desconhecido',
                        "Movimento": r['tipo_acesso'].upper(),
                        "Status": r['status_sincronizacao']
                    })
                df_nuvem = pd.DataFrame(dados_tabela)
                df_nuvem['Data/Hora'] = pd.to_datetime(df_nuvem['Data/Hora']).dt.tz_convert('America/Sao_Paulo').dt.strftime('%d/%m/%Y %H:%M:%S')
                st.dataframe(df_nuvem, use_container_width=True, hide_index=True)
            else:
                st.write("Nenhum histórico encontrado no Supabase.")
        else:
            st.write("⚠️ Você precisa de internet para visualizar o histórico consolidado do servidor.")

# --- ABA 2: GESTÃO DE PRODUTOS ---
with tab_gestao_menu:
    st.header("📦 Cadastro e Consulta de Produtos")
    
    with st.form("form_produto"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            nome_produto = st.text_input("Nome do Produto *")
            preco_produto = st.number_input("Preço Unitário (R$)", min_value=0.0, format="%.2f")
        with col_p2:
            cat_produto = st.text_input("Categoria")
            estoque_produto = st.number_input("Quantidade em Estoque", min_value=0, step=1)
            
        submit_prod = st.form_submit_button("Cadastrar Produto")
        if submit_prod:
            if not nome_produto:
                st.warning("O nome do produto é obrigatório.")
            else:
                try:
                    cadastrar_produto(nome_produto, cat_produto, preco_produto, estoque_produto)
                    st.success(f"Produto '{nome_produto}' cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao cadastrar produto: {e}")
                    
    st.markdown("---")
    st.subheader("Estoque Atual")
    produtos_db = buscar_produtos()
    if produtos_db:
        df_prod = pd.DataFrame(produtos_db)
        st.dataframe(df_prod, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum produto cadastrado no momento.")

# --- ABA 3: REGISTRO & HISTÓRICO DE VENDAS ---
with tab_vendas_menu:
    st.header("💰 Nova Venda / Saída de Produto")
    produtos_db = buscar_produtos()
    
    if produtos_db:
        opcoes_produtos = {f"{p['nome']} (Estoque: {p['estoque']} | R$ {p['preco']})": p for p in produtos_db}
        
        with st.form("form_venda"):
            prod_selecionado_str = st.selectbox("Selecione o Produto", options=list(opcoes_produtos.keys()))
            prod_info = opcoes_produtos[prod_selecionado_str]
            
            qtd_venda = st.number_input("Quantidade", min_value=1, max_value=max(1, prod_info['estoque']), step=1)
            
            valor_calculado = qtd_venda * prod_info['preco']
            st.write(f"**Valor Total da Venda:** R$ {valor_calculado:.2f}")
            
            submit_venda = st.form_submit_button("Finalizar Venda")
            if submit_venda:
                if prod_info['estoque'] < qtd_venda:
                    st.error("Estoque insuficiente para esta quantidade.")
                else:
                    try:
                        # Registra a venda
                        registrar_venda(prod_info['id'], qtd_venda, valor_calculado)
                        
                        # Opcional: Atualiza o estoque no Supabase
                        novo_estoque = prod_info['estoque'] - qtd_venda
                        supabase.table("produtos").update({"estoque": novo_estoque}).eq("id", prod_info['id']).execute()
                        
                        st.success(f"✅ Venda registrada com sucesso! Total: R$ {valor_calculado:.2f}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao registrar venda: {e}")
    else:
        st.info("Cadastre produtos na aba de Gestão de Produtos antes de realizar vendas.")
        
    st.markdown("---")
    st.subheader("Histórico de Vendas")
    vendas_db = buscar_vendas()
    if vendas_db:
        dados_vendas_tabela = []
        for v in vendas_db:
            dados_vendas_tabela.append({
                "Data/Hora": v['data_venda'],
                "Produto": v['produtos']['nome'] if v.get('produtos') else 'Removido',
                "Quantidade": v['quantidade'],
                "Valor Total (R$)": f"R$ {v['valor_total']:.2f}"
            })
        df_vendas = pd.DataFrame(dados_vendas_tabela)
        df_vendas['Data/Hora'] = pd.to_datetime(df_vendas['Data/Hora']).dt.tz_convert('America/Sao_Paulo').dt.strftime('%d/%m/%Y %H:%M:%S')
        st.dataframe(df_vendas, use_container_width=True, hide_index=True)
    else:
        st.write("Nenhuma venda registrada ainda.")
