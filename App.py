import streamlit as st
from supabase import create_client, Client
import pandas as pd
import sqlite3
import requests
from datetime import datetime

# ==========================================
# CONFIGURAÇÕES INICIAIS
# ==========================================
st.set_page_config(page_title="Controle de Acesso - Híbrido", page_icon="🛡️", layout="wide")

def init_local_db():
    conn = sqlite3.connect("offline_data.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros_pendentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id TEXT,
            tipo_acesso TEXT,
            observacoes TEXT,
            data_hora TEXT
        )
    ''')
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
# REGRAS DE NEGÓCIO E ROTEAMENTO DE DADOS
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

# ==========================================
# INTERFACE DO USUÁRIO (UI)
# ==========================================
st.title("🛡️ Sistema de Controle de Acesso (Offline-First)")

is_online = check_conexao()
if is_online:
    st.success("🟢 Sistema Online - Conectado ao servidor.")
else:
    st.warning("🔴 Sistema Offline - Operando no banco de dados local da máquina.")

tab_cadastro, tab_acesso, tab_relatorio = st.tabs(["👤 Novo Usuário", "🔑 Registrar Acesso", "📊 Sincronização e Histórico"])

with tab_cadastro:
    st.header("Cadastrar Novo Perfil")
    with st.form("form_cadastro"):
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

with tab_acesso:
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

with tab_relatorio:
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
    
    st.subheader("Fila de Envio (Dados Locais)")
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
        if st.button("Buscar Últimos Eventos"):
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
