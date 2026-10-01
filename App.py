import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from supabase import create_client, Client
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# ==========================================
# CONFIGURAÇÕES INICIAIS E TEMA
# ==========================================
st.set_page_config(layout="wide", page_title="Sistema ERP Integrado", page_icon="📦")

st.markdown("""
<style>
    /* ===== Reset e tipografia ===== */
    html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
    .main { padding: 1.5rem 2rem; }
    
    /* ===== Título ===== */
    .title-text {
        font-weight: 800;
        font-size: 2.4rem;
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1.5rem;
        letter-spacing: -0.5px;
    }
    
    /* ===== Cards de métricas (KPI) ===== */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #4f46e5;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(79,70,229,0.15);
    }
    div[data-testid="stMetricLabel"] { font-size: 0.85rem; color: #64748b; font-weight: 600; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #0f172a; font-weight: 700; }
    
    /* ===== Abas ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #f1f5f9;
        padding: 6px;
        border-radius: 10px;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        color: #475569;
        transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4f46e5 !important;
        color: white !important;
    }
    
    /* ===== Botões ===== */
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(135deg, #4f46e5, #6366f1);
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.6rem 1.2rem;
        box-shadow: 0 2px 6px rgba(79,70,229,0.25);
        transition: all 0.2s;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(79,70,229,0.35);
    }
    
    /* ===== Inputs ===== */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px !important;
    }
    
    /* ===== DataFrames ===== */
    .dataframe { border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
    
    /* ===== Formulários ===== */
    div[data-testid="stForm"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%);
    }
    section[data-testid="stSidebar"] * { color: #e0e7ff !important; }
    section[data-testid="stSidebar"] .stButton>button {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* ===== Divider ===== */
    hr { border-color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# PALETA E UTILITÁRIOS DE DESIGN
# ==========================================
PALETA = ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

def tema_altair(chart):
    """Aplica tema padronizado em qualquer gráfico Altair."""
    return chart.configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=True,
        gridColor='#e2e8f0',
        gridDash=[3, 3],
        domain=False,
        labelColor='#475569',
        titleColor='#1e293b',
        labelFontSize=11,
        titleFontSize=12,
        titleFontWeight='bold'
    ).configure_title(
        fontSize=14, fontWeight='bold', color='#1e293b', anchor='start'
    ).configure_legend(
        orient='bottom', titleFontSize=11, labelFontSize=10
    ).configure_range(
        category={'scheme': 'tableau10'}
    )

def secao(titulo, subtitulo=None):
    """Cabeçalho de seção padronizado."""
    st.markdown(f"""
    <div style="border-left: 4px solid #4f46e5; padding-left: 1rem; margin: 1rem 0;">
        <h2 style="margin: 0; color: #1e293b; font-size: 1.5rem;">{titulo}</h2>
        {f'<p style="margin: 0.2rem 0 0 0; color: #64748b;">{subtitulo}</p>' if subtitulo else ''}
    </div>
    """, unsafe_allow_html=True)

def empty_state(icone, mensagem, dica=None):
    """Estado vazio estilizado."""
    st.markdown(f"""
    <div style="text-align:center; padding: 3rem 1rem; background:#f8fafc; 
                border: 2px dashed #cbd5e1; border-radius: 12px;">
        <div style="font-size: 3rem;">{icone}</div>
        <h3 style="color:#475569; margin: 0.5rem 0;">{mensagem}</h3>
        {f'<p style="color:#94a3b8;">{dica}</p>' if dica else ''}
    </div>
    """, unsafe_allow_html=True)

def moeda(v):
    """Formata valor monetário no padrão brasileiro."""
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# ==========================================
# CONEXÃO COM O SUPABASE
# ==========================================
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Erro ao conectar com o Supabase. Verifique as secrets. Erro: {e}")
    st.stop()

# ==========================================
# CONTROLE DE SESSÃO / AUTENTICAÇÃO
# ==========================================
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

def tela_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<p class="title-text">🔐 Acesso Restrito</p>', unsafe_allow_html=True)
        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            botao_login = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if botao_login:
                if usuario == "JOHN" and senha == "fgxv4VP0":
                    st.session_state.autenticado = True
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

if not st.session_state.autenticado:
    tela_login()
    st.stop()

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0;">
        <div style="font-size: 2.5rem;">📦</div>
        <h2 style="color: white; margin: 0.3rem 0;">ERP Nuvem</h2>
        <p style="color: #a5b4fc; margin: 0;">v2.0 • Supabase</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("👤 **Administrador**")
    st.caption(datetime.now().strftime("📅 %d/%m/%Y • %H:%M"))
    st.markdown("---")
    st.success("🟢 Supabase Conectado")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Sair do Sistema", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

st.markdown('<p class="title-text">📦 Sistema ERP Integrado</p>', unsafe_allow_html=True)

# ==========================================
# FUNÇÕES DE BUSCA DO BANCO DE DADOS
# ==========================================
def carregar_dados_tabela(nome_tabela):
    try:
        resposta = supabase.table(nome_tabela).select("*").execute()
        df = pd.DataFrame(resposta.data)
        if not df.empty and 'id' in df.columns:
            df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        return pd.DataFrame()

# Carregamento inicial
df_estoque = carregar_dados_tabela("estoque")
df_vendas = carregar_dados_tabela("vendas")
df_financeiro = carregar_dados_tabela("financeiro")
df_clientes = carregar_dados_tabela("clientes")

# ==========================================
# NORMALIZAÇÃO DE COLUNAS
# ==========================================
if df_estoque.empty:
    df_estoque = pd.DataFrame(columns=['id', 'Produto', 'Categoria', 'Quantidade', 'Limite Mínimo', 'Valor Unitário', 'Preço de Custo'])
else:
    col_map_est = {}
    for col in df_estoque.columns:
        c_lower = col.lower().strip()
        if c_lower in ['produto', 'nome']: col_map_est[col] = 'Produto'
        elif c_lower in ['categoria']: col_map_est[col] = 'Categoria'
        elif c_lower in ['quantidade', 'qtd']: col_map_est[col] = 'Quantidade'
        elif c_lower in ['limite_minimo', 'limiteminimo', 'limite']: col_map_est[col] = 'Limite Mínimo'
        elif c_lower in ['valor_unitario', 'valorunitario', 'preco', 'valor']: col_map_est[col] = 'Valor Unitário'
        elif c_lower in ['preco_custo', 'precocusto', 'custo']: col_map_est[col] = 'Preço de Custo'
    df_estoque = df_estoque.rename(columns=col_map_est)

if df_vendas.empty:
    df_vendas = pd.DataFrame(columns=['id', 'Data', 'Produto', 'Quantidade', 'Valor Total', 'Lucro'])
else:
    col_map_vendas = {}
    for col in df_vendas.columns:
        c_lower = col.lower().strip()
        if c_lower == 'data': col_map_vendas[col] = 'Data'
        elif c_lower == 'produto': col_map_vendas[col] = 'Produto'
        elif c_lower == 'quantidade': col_map_vendas[col] = 'Quantidade'
        elif c_lower in ['valor_total', 'valortotal']: col_map_vendas[col] = 'Valor Total'
        elif c_lower == 'lucro': col_map_vendas[col] = 'Lucro'
    df_vendas = df_vendas.rename(columns=col_map_vendas)

if df_financeiro.empty:
    df_financeiro = pd.DataFrame(columns=['id', 'Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])
else:
    col_map_fin = {}
    for col in df_financeiro.columns:
        c_lower = col.lower().strip()
        if c_lower == 'data': col_map_fin[col] = 'Data'
        elif c_lower in ['descricao', 'descrição']: col_map_fin[col] = 'Descrição'
        elif c_lower == 'tipo': col_map_fin[col] = 'Tipo'
        elif c_lower == 'categoria': col_map_fin[col] = 'Categoria'
        elif c_lower == 'valor': col_map_fin[col] = 'Valor'
    df_financeiro = df_financeiro.rename(columns=col_map_fin)

if df_clientes.empty:
    df_clientes = pd.DataFrame(columns=['id', 'nome', 'cpf_cnpj', 'telefone', 'email', 'endereco', 'observacoes'])

# Garante colunas de apoio
if 'Preço de Custo' not in df_estoque.columns: df_estoque['Preço de Custo'] = 0.00
if 'Limite Mínimo' not in df_estoque.columns: df_estoque['Limite Mínimo'] = 0
if 'Valor Unitário' not in df_estoque.columns: df_estoque['Valor Unitário'] = 0.00
if 'Categoria' not in df_estoque.columns: df_estoque['Categoria'] = 'Geral'
if 'Quantidade' not in df_estoque.columns: df_estoque['Quantidade'] = 0

# ==========================================
# FUNÇÃO DE GERAÇÃO DE RELATÓRIO PDF
# ==========================================
def gerar_relatorio_pdf():
    """Gera um PDF completo com todas as seções do ERP integrado ao Supabase."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=1 * cm, rightMargin=1 * cm,
        topMargin=1 * cm, bottomMargin=1 * cm
    )

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'Titulo', parent=styles['Heading1'], fontSize=18,
        alignment=1, spaceAfter=10, textColor=colors.HexColor('#4f46e5')
    )
    sub_style = ParagraphStyle(
        'Sub', parent=styles['Heading2'], fontSize=13,
        spaceAfter=6, spaceBefore=10, textColor=colors.HexColor('#4338ca')
    )
    normal = styles['Normal']

    elementos = []
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    elementos.append(Paragraph("Sistema ERP Integrado - Relatório Geral", titulo_style))
    elementos.append(Paragraph(f"Gerado em: {agora}", normal))
    elementos.append(Spacer(1, 0.5 * cm))

    # ---------- 1. ESTOQUE ----------
    elementos.append(Paragraph("1. Estoque (com Custo Total e Venda Total)", sub_style))
    if not df_estoque.empty:
        dados = [['Produto', 'Categoria', 'Qtd',
                  'Preço Custo (R$)', 'Valor Unit. (R$)',
                  'Valor Custo Total (R$)', 'Valor Venda Total (R$)']]
        total_qtd = 0
        total_custo = 0.0
        total_venda = 0.0

        for _, row in df_estoque.iterrows():
            q = int(pd.to_numeric(row['Quantidade'], errors='coerce') or 0)
            pc = float(pd.to_numeric(row['Preço de Custo'], errors='coerce') or 0)
            pv = float(pd.to_numeric(row['Valor Unitário'], errors='coerce') or 0)
            vct = q * pc
            vvt = q * pv
            total_qtd += q
            total_custo += vct
            total_venda += vvt
            dados.append([
                str(row['Produto'])[:35],
                str(row['Categoria'])[:20],
                str(q),
                f"{pc:.2f}",
                f"{pv:.2f}",
                f"{vct:.2f}",
                f"{vvt:.2f}",
            ])

        dados.append([
            'TOTAIS GERAIS', '', str(total_qtd), '', '',
            f"R$ {total_custo:.2f}", f"R$ {total_venda:.2f}"
        ])

        t = Table(dados, repeatRows=1,
                  colWidths=[6*cm, 3.2*cm, 1.6*cm, 2.7*cm, 2.7*cm, 3.4*cm, 3.4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e7ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('SPAN', (0, -1), (1, -1)),
        ]))
        elementos.append(t)

        elementos.append(Spacer(1, 0.2 * cm))
        elementos.append(Paragraph(
            f"<b>Resumo do Inventário:</b> "
            f"Total de itens em estoque: <b>{total_qtd}</b> | "
            f"Capital Investido (Custo): <b>R$ {total_custo:.2f}</b> | "
            f"Potencial de Venda: <b>R$ {total_venda:.2f}</b> | "
            f"Lucro Potencial: <b>R$ {total_venda - total_custo:.2f}</b>",
            normal
        ))
    else:
        elementos.append(Paragraph("Nenhum produto cadastrado no estoque.", normal))
    elementos.append(Spacer(1, 0.4 * cm))

    # ---------- 2. VENDAS ----------
    elementos.append(Paragraph("2. Vendas", sub_style))
    if not df_vendas.empty:
        dados = [['ID', 'Data', 'Produto', 'Qtd', 'Valor Total (R$)', 'Lucro (R$)']]
        for _, row in df_vendas.iterrows():
            dados.append([
                str(row['id']),
                str(row['Data'])[:19],
                str(row['Produto'])[:35],
                str(int(row['Quantidade'])),
                f"{float(row['Valor Total']):.2f}",
                f"{float(row['Lucro']):.2f}"
            ])
        total_fat = df_vendas['Valor Total'].sum()
        total_luc = df_vendas['Lucro'].sum()
        dados.append(['', '', 'TOTAIS', '', f"R$ {total_fat:.2f}", f"R$ {total_luc:.2f}"])

        t = Table(dados, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e7ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('SPAN', (0, -1), (2, -1)),
        ]))
        elementos.append(t)
    else:
        elementos.append(Paragraph("Nenhuma venda registrada.", normal))
    elementos.append(Spacer(1, 0.4 * cm))

    # ---------- 3. FINANCEIRO ----------
    elementos.append(Paragraph("3. Financeiro", sub_style))
    if not df_financeiro.empty:
        dados = [['ID', 'Data', 'Tipo', 'Categoria', 'Descrição', 'Valor (R$)']]
        for _, row in df_financeiro.iterrows():
            dados.append([
                str(row['id']),
                str(row['Data'])[:19],
                str(row['Tipo']),
                str(row['Categoria'])[:25],
                str(row['Descrição'])[:40],
                f"{float(row['Valor']):.2f}"
            ])
        ent = df_financeiro[df_financeiro['Tipo'] == 'Entrada']['Valor'].sum()
        sai = df_financeiro[df_financeiro['Tipo'] == 'Saída']['Valor'].sum()
        dados.append(['', '', '', '', f'Entradas: R$ {ent:.2f} | Saídas: R$ {sai:.2f} | Saldo: R$ {ent - sai:.2f}', ''])

        t = Table(dados, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
            ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e7ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('SPAN', (0, -1), (4, -1)),
        ]))
        elementos.append(t)
    else:
        elementos.append(Paragraph("Nenhum registro financeiro.", normal))
    elementos.append(Spacer(1, 0.4 * cm))

    # ---------- 4. CLIENTES ----------
    elementos.append(Paragraph("4. Clientes", sub_style))
    if not df_clientes.empty:
        dados = [['Nome', 'CPF/CNPJ', 'Telefone', 'E-mail', 'Endereço']]
        for _, row in df_clientes.iterrows():
            dados.append([
                str(row['nome'])[:30],
                str(row['cpf_cnpj'] or ''),
                str(row['telefone'] or ''),
                str(row['email'] or '')[:30],
                str(row['endereco'] or '')[:35]
            ])
        t = Table(dados, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ]))
        elementos.append(t)
    else:
        elementos.append(Paragraph("Nenhum cliente cadastrado.", normal))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# ABAS PRINCIPAIS DO ERP
# ==========================================
tab_estoque, tab_planilhas_prod, tab_vendas, tab_calculadora, tab_despesas, tab_financeiro, tab_clientes, tab_dashboard, tab_relatorio = st.tabs([
    "📦 Estoque", 
    "📑 Fichas por Produto",
    "🛒 Vendas", 
    "🧮 Calculadora & Troco",
    "💡 Despesas",
    "💰 Financeiro", 
    "👥 Clientes",
    "📈 Dashboard",
    "📄 Relatório PDF"
])

# ==========================================
# 1. ESTOQUE
# ==========================================
with tab_estoque:
    secao("📦 Gestão de Estoque", "Controle de produtos, custo e potencial de venda")
    
    # Alerta de estoque baixo
    if not df_estoque.empty and 'Quantidade' in df_estoque.columns and 'Limite Mínimo' in df_estoque.columns:
        criticos = df_estoque[df_estoque['Quantidade'] <= df_estoque['Limite Mínimo']]
        if not criticos.empty:
            nomes = ', '.join(criticos['Produto'].head(5).tolist())
            st.warning(f"⚠️ **{len(criticos)} produto(s)** abaixo do limite mínimo: {nomes}")
    
    if not df_estoque.empty and 'Quantidade' in df_estoque.columns and 'Preço de Custo' in df_estoque.columns:
        total_investido_custo = (df_estoque['Quantidade'] * df_estoque['Preço de Custo']).sum()
        total_valor_venda = (df_estoque['Quantidade'] * df_estoque['Valor Unitário']).sum()
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("💰 Capital Investido (Custo)", moeda(total_investido_custo))
        c_m2.metric("🏷 Valor Potencial de Venda", moeda(total_valor_venda))
        c_m3.metric("📈 Lucro Potencial Estimado", moeda(total_valor_venda - total_investido_custo))
        st.markdown("---")
        
    sub_est_cad, sub_est_ger = st.tabs(["➕ Cadastrar Produto", "✏️ Gerenciar, Editar e Excluir"])
    
    with sub_est_cad:
        with st.form("form_produto"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Produto")
                categoria = st.selectbox("Categoria", ["Grãos", "Massas", "Óleos e Condimentos", "Bebidas", "Outros"])
                preco_custo = st.number_input("Preço de Mercado / Custo Unitário (R$)", min_value=0.0, step=0.01)
                preco = st.number_input("Valor de Venda / Revenda Unitário (R$)", min_value=0.0, step=0.01)
            with col2:
                qtd = st.number_input("Quantidade Inicial em Estoque", min_value=0, step=1)
                limite = st.number_input("Limite Mínimo de Alerta", min_value=0, step=1)
            
            if st.form_submit_button("Cadastrar Produto", use_container_width=True) and nome:
                try:
                    supabase.table("estoque").insert({
                        "produto": nome.strip(), "categoria": categoria, "quantidade": int(qtd),
                        "limite_minimo": int(limite), "valor_unitario": float(preco), "preco_custo": float(preco_custo)
                    }).execute()
                    st.success("✅ Produto cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    with sub_est_ger:
        if not df_estoque.empty and 'Produto' in df_estoque.columns:
            prod_sel_ed = st.selectbox("Selecione o produto para Editar ou Excluir:", df_estoque['Produto'].tolist(), key="sel_ed_est")
            item_e = df_estoque[df_estoque['Produto'] == prod_sel_ed].iloc[0]
            
            with st.form("form_edit_est"):
                e_nome = st.text_input("Nome do Produto", value=str(item_e['Produto']))
                e_cat = st.text_input("Categoria", value=str(item_e['Categoria']))
                e_qtd = st.number_input("Quantidade", value=int(item_e['Quantidade']), min_value=0, step=1)
                e_lim = st.number_input("Limite Mínimo", value=int(item_e['Limite Mínimo']), min_value=0, step=1)
                e_custo = st.number_input("Preço de Mercado / Custo (R$)", value=float(item_e['Preço de Custo']), min_value=0.0, step=0.01)
                e_venda = st.number_input("Valor de Venda / Revenda (R$)", value=float(item_e['Valor Unitário']), min_value=0.0, step=0.01)
                
                col_b1, col_b2 = st.columns(2)
                salvar_ed = col_b1.form_submit_button("💾 Salvar Alterações", use_container_width=True)
                excluir_prod = col_b2.form_submit_button("🗑️ Excluir Produto", use_container_width=True)
                
                if salvar_ed:
                    supabase.table("estoque").update({
                        "produto": e_nome, "categoria": e_cat, "quantidade": int(e_qtd),
                        "limite_minimo": int(e_lim), "preco_custo": float(e_custo), "valor_unitario": float(e_venda)
                    }).eq("id", int(item_e['id'])).execute()
                    st.success("Produto atualizado com sucesso!")
                    st.rerun()
                    
                if excluir_prod:
                    supabase.table("estoque").delete().eq("id", int(item_e['id'])).execute()
                    st.success("Produto excluído!")
                    st.rerun()
                    
            st.markdown("---")
            dados_est = df_estoque.copy()
            dados_est['Valor Custo Total'] = dados_est['Quantidade'] * dados_est['Preço de Custo']
            dados_est['Valor Venda Total'] = dados_est['Quantidade'] * dados_est['Valor Unitário']
            st.dataframe(dados_est[['Produto', 'Categoria', 'Quantidade', 'Preço de Custo', 'Valor Unitário', 'Valor Custo Total', 'Valor Venda Total']].style.format({'Preço de Custo': 'R$ {:.2f}', 'Valor Unitário': 'R$ {:.2f}', 'Valor Custo Total': 'R$ {:.2f}', 'Valor Venda Total': 'R$ {:.2f}'}), hide_index=True, use_container_width=True)
        else:
            empty_state("📦", "Nenhum produto cadastrado", "Vá em ➕ Cadastrar Produto para começar")

# ==========================================
# 2. PLANILHAS ESPECÍFICAS POR PRODUTO
# ==========================================
with tab_planilhas_prod:
    secao("📑 Ficha e Simulação Individual", "Visualize especificações, preço de revenda e faturamento projetado por produto")
    
    if not df_estoque.empty and 'Produto' in df_estoque.columns:
        produto_escolhido = st.selectbox("Escolha o produto:", df_estoque['Produto'].tolist(), key="sel_ficha_prod")
        
        p_info = df_estoque[df_estoque['Produto'] == produto_escolhido].iloc[0]
        
        qtd_atual = int(p_info['Quantidade'])
        preco_mercado = float(p_info['Preço de Custo'])
        preco_revenda_atual = float(p_info['Valor Unitário'])
        
        st.markdown("---")
        st.markdown(f"### 📋 Ficha Técnica: **{produto_escolhido}** ({p_info['Categoria']})")
        
        with st.form(f"form_ficha_{p_info['id']}"):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                st.metric("📦 Estoque Atual", f"{qtd_atual} un")
            with col_f2:
                novo_preco_revenda = st.number_input("Valor de Venda / Revenda (R$)", value=preco_revenda_atual, min_value=0.0, step=0.01)
            with col_f3:
                st.metric("🏷️ Valor de Mercado (Custo)", moeda(preco_mercado))
                
            atualizar_preco_isolado = st.form_submit_button("Atualizar Valor de Revenda", use_container_width=True)
            if atualizar_preco_isolado:
                supabase.table("estoque").update({"valor_unitario": float(novo_preco_revenda)}).eq("id", int(p_info['id'])).execute()
                st.success(f"Preço de revenda de '{produto_escolhido}' atualizado com sucesso!")
                st.rerun()
                
        custo_total_prod = qtd_atual * preco_mercado
        faturamento_total_prod = qtd_atual * novo_preco_revenda if 'novo_preco_revenda' in locals() else qtd_atual * preco_revenda_atual
        lucro_total_prod = faturamento_total_prod - custo_total_prod
        margem_lucro_pct = ((novo_preco_revenda - preco_mercado) / preco_mercado * 100) if preco_mercado > 0 else 0.0
        
        st.markdown("#### 💰 Resumo Financeiro Projetado (Com o Estoque Atual)")
        cp1, cp2, cp3, cp4 = st.columns(4)
        cp1.metric("Total Investido (Custo)", moeda(custo_total_prod))
        cp2.metric("Total da Venda (Revenda)", moeda(faturamento_total_prod))
        cp3.metric("Lucro Total Estimado", moeda(lucro_total_prod))
        cp4.metric("Margem Unitária", f"{margem_lucro_pct:.1f}%")
        
        st.markdown("---")
        st.markdown("#### 📊 Tabela de Simulação de Venda em Lote")
        
        simulacao_dados = []
        for q in [1, 5, 10, 20, 50, 100, qtd_atual if qtd_atual > 0 else 1]:
            if q <= qtd_atual or q == [1, 5, 10, 20, 50, 100, qtd_atual if qtd_atual > 0 else 1][-1]:
                fat_q = q * novo_preco_revenda
                custo_q = q * preco_mercado
                lucro_q = fat_q - custo_q
                simulacao_dados.append({
                    "Quantidade": q,
                    "Preço de Mercado (Unit.)": preco_mercado,
                    "Preço de Revenda (Unit.)": novo_preco_revenda,
                    "Faturamento Total": fat_q,
                    "Custo Total": custo_q,
                    "Lucro Líquido": lucro_q
                })
        df_simulacao = pd.DataFrame(simulacao_dados).drop_duplicates(subset=['Quantidade'])
        st.dataframe(df_simulacao.style.format({
            'Preço de Mercado (Unit.)': 'R$ {:.2f}',
            'Preço de Revenda (Unit.)': 'R$ {:.2f}',
            'Faturamento Total': 'R$ {:.2f}',
            'Custo Total': 'R$ {:.2f}',
            'Lucro Líquido': 'R$ {:.2f}'
        }), hide_index=True, use_container_width=True)
        
    else:
        empty_state("📑", "Sem produtos cadastrados", "Cadastre produtos no estoque para visualizar as fichas individuais")

# ==========================================
# 3. VENDAS
# ==========================================
with tab_vendas:
    secao("🛒 Registro de Vendas", "Apuração automática de lucro por operação")
    
    if not df_vendas.empty and 'Lucro' in df_vendas.columns and 'Valor Total' in df_vendas.columns:
        total_faturamento = df_vendas['Valor Total'].sum()
        total_lucro_apurado = df_vendas['Lucro'].sum()
        c_v1, c_v2 = st.columns(2)
        c_v1.metric("💵 Faturamento Total", moeda(total_faturamento))
        c_v2.metric("📈 Lucro Real Apurado", moeda(total_lucro_apurado))
        st.markdown("---")

    sub_v_reg, sub_v_ger = st.tabs(["➕ Registrar Venda", "📋 Histórico e Exclusão"])
    
    with sub_v_reg:
        with st.form("form_venda"):
            if not df_estoque.empty and 'Produto' in df_estoque.columns:
                prod_venda = st.selectbox("Produto Vendido", df_estoque['Produto'].tolist())
                qtd_venda = st.number_input("Quantidade", min_value=1, step=1)
                
                item_est_preview = df_estoque[df_estoque['Produto'] == prod_venda].iloc[0]
                p_unit = float(item_est_preview['Valor Unitário'])
                c_unit = float(item_est_preview['Preço de Custo'])
                est_atual = int(item_est_preview['Quantidade'])
                
                st.info(f"💡 **Prévia:** Revenda Unit.: {moeda(p_unit)} | Custo Unit.: {moeda(c_unit)} | Lucro Unit.: {moeda(p_unit - c_unit)}")
                
                if st.form_submit_button("Confirmar e Registrar Venda", use_container_width=True):
                    if qtd_venda <= est_atual:
                        vlr_total = qtd_venda * p_unit
                        lucro_venda = (p_unit - c_unit) * qtd_venda
                        data_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        supabase.table("estoque").update({"quantidade": est_atual - qtd_venda}).eq("id", int(item_est_preview['id'])).execute()
                        supabase.table("vendas").insert({"data": data_str, "produto": prod_venda, "quantidade": int(qtd_venda), "valor_total": float(vlr_total), "lucro": float(lucro_venda)}).execute()
                        supabase.table("financeiro").insert({"data": data_str, "descricao": f"Venda: {prod_venda} ({qtd_venda} un)", "tipo": "Entrada", "categoria": "Vendas de Produtos", "valor": float(vlr_total)}).execute()
                        
                        st.success(f"✅ Venda registrada! Lucro obtido: {moeda(lucro_venda)}")
                        st.rerun()
                    else:
                        st.error("Estoque insuficiente para essa quantidade!")
            else:
                st.warning("Cadastre produtos no estoque primeiro.")

    with sub_v_ger:
        if not df_vendas.empty and 'Valor Total' in df_vendas.columns:
            st.dataframe(df_vendas[['id', 'Data', 'Produto', 'Quantidade', 'Valor Total', 'Lucro']].style.format({'Valor Total': 'R$ {:.2f}', 'Lucro': 'R$ {:.2f}'}), hide_index=True, use_container_width=True)
            st.markdown("---")
            lista_ids_vendas = [str(x) for x in df_vendas['id'].tolist()]
            v_id_del_str = st.selectbox("Selecione o ID da venda para excluir:", lista_ids_vendas, key="del_venda")
            if st.button("Excluir Venda Selecionada", use_container_width=True):
                supabase.table("vendas").delete().eq("id", int(v_id_del_str)).execute()
                st.success("Venda excluída com sucesso!")
                st.rerun()
        else:
            empty_state("🛒", "Nenhuma venda registrada", "Registre sua primeira venda na aba acima")

# ==========================================
# 4. CALCULADORA DE VENDA & TROCO (CARRINHO MULTI-ITENS)
# ==========================================
with tab_calculadora:
    secao("🧮 Calculadora de Venda & Troco", "Monte o carrinho, informe o valor recebido e veja o troco")

    if df_estoque.empty or 'Produto' not in df_estoque.columns:
        empty_state("🧮", "Nenhum produto cadastrado", "Cadastre produtos no estoque primeiro")
    else:
        if 'carrinho' not in st.session_state:
            st.session_state.carrinho = []

        st.markdown("#### ➕ Adicionar produtos ao carrinho")
        ca, cb, cc = st.columns([3, 1, 1])
        with ca:
            prod_add = st.selectbox("Produto:", df_estoque['Produto'].tolist(), key="cart_prod")
        with cb:
            qtd_add = st.number_input("Qtd:", min_value=1, value=1, step=1, key="cart_qtd")
        with cc:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Adicionar", use_container_width=True):
                item_add = df_estoque[df_estoque['Produto'] == prod_add].iloc[0]
                ja_existe = next((x for x in st.session_state.carrinho if x['id'] == int(item_add['id'])), None)
                if ja_existe:
                    ja_existe['quantidade'] += int(qtd_add)
                else:
                    st.session_state.carrinho.append({
                        'id': int(item_add['id']),
                        'produto': prod_add,
                        'preco': float(item_add['Valor Unitário']),
                        'custo': float(item_add['Preço de Custo']),
                        'quantidade': int(qtd_add),
                        'estoque': int(item_add['Quantidade'])
                    })
                st.toast(f"✅ {qtd_add}x {prod_add} adicionado!", icon="🛒")
                st.rerun()

        st.markdown("---")

        if st.session_state.carrinho:
            st.markdown("#### 🛒 Itens no Carrinho")

            df_carrinho = pd.DataFrame(st.session_state.carrinho)
            df_carrinho['Subtotal'] = df_carrinho['preco'] * df_carrinho['quantidade']

            st.dataframe(
                df_carrinho[['produto', 'quantidade', 'preco', 'Subtotal']].rename(columns={
                    'produto': 'Produto', 'quantidade': 'Qtd',
                    'preco': 'Preço Unit.', 'Subtotal': 'Subtotal'
                }).style.format({'Preço Unit.': 'R$ {:.2f}', 'Subtotal': 'R$ {:.2f}'}),
                hide_index=True, use_container_width=True
            )

            total_carrinho = df_carrinho['Subtotal'].sum()

            cd1, cd2, cd3 = st.columns(3)
            cd1.metric("🛍 Itens", f"{df_carrinho['quantidade'].sum()} un")
            cd2.metric("💰 Total do Carrinho", moeda(total_carrinho))
            with cd3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Limpar Carrinho", use_container_width=True):
                    st.session_state.carrinho = []
                    st.rerun()

            st.markdown("---")
            st.markdown("#### 💵 Pagamento do Cliente")

            cp1, cp2 = st.columns([1, 1])
            with cp1:
                valor_pago_carrinho = st.number_input(
                    "Valor recebido (R$):", min_value=0.0, step=0.50,
                    value=float(total_carrinho), key="valor_cart", format="%.2f"
                )
            with cp2:
                troco_carrinho = round(valor_pago_carrinho - total_carrinho, 2)
                if troco_carrinho >= 0:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #10b981, #059669); color:white; padding:1rem; border-radius:12px; text-align:center;">
                        <p style="margin:0; font-size:0.85rem; opacity:0.9;">🪙 TROCO</p>
                        <h2 style="margin:0.2rem 0;">{moeda(troco_carrinho)}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    falta = abs(troco_carrinho)
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #ef4444, #dc2626); color:white; padding:1rem; border-radius:12px; text-align:center;">
                        <p style="margin:0; font-size:0.85rem; opacity:0.9;">⚠️ FALTA PAGAR</p>
                        <h2 style="margin:0.2rem 0;">{moeda(falta)}</h2>
                    </div>
                    """, unsafe_allow_html=True)

            # Verificar estoque
            erros_estoque = [
                item for item in st.session_state.carrinho
                if item['quantidade'] > item['estoque']
            ]
            if erros_estoque:
                for it in erros_estoque:
                    st.error(f"❌ Estoque insuficiente: **{it['produto']}** — disponível: {it['estoque']}, pedido: {it['quantidade']}")

            st.markdown("---")
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                if st.button("✅ Registrar Venda Completa", type="primary", use_container_width=True, disabled=bool(erros_estoque)):
                    if valor_pago_carrinho < total_carrinho:
                        st.error("⛔ Valor recebido menor que o total. Não é possível registrar.")
                    else:
                        try:
                            data_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            for it in st.session_state.carrinho:
                                vlr_t = it['preco'] * it['quantidade']
                                lucro_v = (it['preco'] - it['custo']) * it['quantidade']

                                supabase.table("estoque").update({
                                    "quantidade": it['estoque'] - it['quantidade']
                                }).eq("id", it['id']).execute()

                                supabase.table("vendas").insert({
                                    "data": data_str, "produto": it['produto'],
                                    "quantidade": int(it['quantidade']),
                                    "valor_total": float(vlr_t), "lucro": float(lucro_v)
                                }).execute()

                                supabase.table("financeiro").insert({
                                    "data": data_str,
                                    "descricao": f"Venda (Carrinho): {it['produto']} ({it['quantidade']} un)",
                                    "tipo": "Entrada", "categoria": "Vendas de Produtos",
                                    "valor": float(vlr_t)
                                }).execute()

                            troco_final = valor_pago_carrinho - total_carrinho
                            st.success(f"✅ Venda de {len(st.session_state.carrinho)} item(ns) registrada! Troco: **{moeda(troco_final)}**")
                            st.balloons()
                            st.session_state.carrinho = []
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao registrar venda: {e}")
            with col_btn2:
                if st.button("🧹 Cancelar e Limpar", use_container_width=True):
                    st.session_state.carrinho = []
                    st.rerun()
        else:
            empty_state("🛒", "Carrinho vazio", "Adicione produtos acima para começar a venda")

# ==========================================
# 5. DESPESAS
# ==========================================
with tab_despesas:
    secao("💡 Despesas do Comércio", "Lançamento e gestão de custos operacionais")
    sub_d_cad, sub_d_ger = st.tabs(["➕ Lançar Despesa", "📋 Gerenciar / Excluir Despesas"])
    
    with sub_d_cad:
        with st.form("form_desp"):
            c1, c2 = st.columns(2)
            with c1:
                cat_d = st.selectbox("Categoria", ["Energia / Luz", "Água", "Internet", "Aluguel", "Manutenção", "Impostos", "Outros"])
                desc_d = st.text_input("Descrição / Referência")
            with c2:
                vlr_d = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
                data_d = st.date_input("Data", value=datetime.now())
                
            if st.form_submit_button("Lançar Despesa", use_container_width=True):
                supabase.table("financeiro").insert({
                    "data": f"{data_d} {datetime.now().strftime('%H:%M:%S')}",
                    "descricao": desc_d, "tipo": "Saída", "categoria": f"Despesa: {cat_d}", "valor": float(vlr_d)
                }).execute()
                st.success("Despesa lançada!")
                st.rerun()

    with sub_d_ger:
        df_despesas_apenas = df_financeiro[df_financeiro['Tipo'] == 'Saída'] if not df_financeiro.empty and 'Tipo' in df_financeiro.columns else pd.DataFrame()
        if not df_despesas_apenas.empty:
            st.dataframe(df_despesas_apenas[['id', 'Data', 'Categoria', 'Descrição', 'Valor']].style.format({'Valor': 'R$ {:.2f}'}), hide_index=True, use_container_width=True)
            st.markdown("---")
            lista_ids_desp = [str(x) for x in df_despesas_apenas['id'].tolist()]
            id_desp_del_str = st.selectbox("Selecione o ID da despesa para excluir:", lista_ids_desp, key="del_desp")
            if st.button("Excluir Despesa", use_container_width=True):
                supabase.table("financeiro").delete().eq("id", int(id_desp_del_str)).execute()
                st.success("Despesa excluída!")
                st.rerun()
        else:
            empty_state("💡", "Nenhuma despesa lançada", "Comece lançando sua primeira despesa na aba acima")

# ==========================================
# 6. FINANCEIRO
# ==========================================
with tab_financeiro:
    secao("💰 Fluxo de Caixa", "Visualização completa de entradas, saídas e saldo")
    if not df_financeiro.empty and 'Tipo' in df_financeiro.columns:
        total_ent = df_financeiro[df_financeiro['Tipo'] == 'Entrada']['Valor'].sum()
        total_sai = df_financeiro[df_financeiro['Tipo'] == 'Saída']['Valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Entradas", moeda(total_ent))
        c2.metric("Saídas", moeda(total_sai))
        c3.metric("Saldo Líquido", moeda(total_ent - total_sai))
        
        st.markdown("---")
        st.dataframe(df_financeiro[['id', 'Data', 'Tipo', 'Categoria', 'Descrição', 'Valor']].style.format({'Valor': 'R$ {:.2f}'}), hide_index=True, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🗑️ Gerenciar / Excluir Registros Financeiros")
        
        try:
            res_fin = supabase.table("financeiro").select("id, data, descricao, valor, tipo").order("id", desc=True).execute()
            dados_financeiros = res_fin.data
            
            if dados_financeiros:
                opcoes_fin = {
                    f"ID: {item['id']} | Data: {item['data']} | Desc: {item['descricao']} | R$ {item['valor']} ({item['tipo']})": item['id']
                    for item in dados_financeiros
                }
                
                selecao_fin_str = st.selectbox("Selecione o registro para excluir:", list(opcoes_fin.keys()), key="select_del_financeiro")
                
                if st.button("Excluir Registro Financeiro", use_container_width=True, type="primary"):
                    id_para_deletar = opcoes_fin[selecao_fin_str]
                    try:
                        supabase.table("financeiro").delete().eq("id", id_para_deletar).execute()
                        st.success(f"Registro ID {id_para_deletar} excluído com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")
            else:
                st.info("Nenhum registro disponível para exclusão.")
        except Exception as e:
            st.warning(f"Não foi possível carregar registros: {e}")
    else:
        empty_state("💰", "Nenhum registro financeiro", "Lance vendas ou despesas para começar")

# ==========================================
# 7. GESTÃO DE CLIENTES
# ==========================================
with tab_clientes:
    secao("👥 Gestão de Clientes", "Cadastro completo com dados de contato e endereço")
    sub_c_cad, sub_c_ger = st.tabs(["➕ Cadastrar Cliente", "✏️ Editar / Excluir Clientes"])
    
    with sub_c_cad:
        with st.form("form_cliente"):
            c1, c2 = st.columns(2)
            with c1:
                nome_cli = st.text_input("Nome Completo / Razão Social *")
                cpf_cnpj = st.text_input("CPF ou CNPJ")
                tel_cli = st.text_input("Telefone / WhatsApp")
            with c2:
                email_cli = st.text_input("E-mail")
                end_cli = st.text_input("Endereço Completo")
                obs_cli = st.text_area("Observações / Histórico")
                
            if st.form_submit_button("Salvar Cliente", use_container_width=True) and nome_cli:
                try:
                    supabase.table("clientes").insert({
                        "nome": nome_cli.strip(), "cpf_cnpj": cpf_cnpj.strip(), "telefone": tel_cli.strip(),
                        "email": email_cli.strip(), "endereco": end_cli.strip(), "observacoes": obs_cli.strip()
                    }).execute()
                    st.success(f"✅ Cliente '{nome_cli}' cadastrado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
                    
    with sub_c_ger:
        if not df_clientes.empty and 'nome' in df_clientes.columns:
            cli_sel_ed = st.selectbox("Selecione o cliente:", df_clientes['nome'].tolist(), key="sel_ed_cli")
            c_item = df_clientes[df_clientes['nome'] == cli_sel_ed].iloc[0]
            
            with st.form("form_edit_cli"):
                ec_nome = st.text_input("Nome Completo", value=str(c_item['nome']))
                ec_doc = st.text_input("CPF / CNPJ", value=str(c_item['cpf_cnpj']) if c_item['cpf_cnpj'] else "")
                ec_tel = st.text_input("Telefone", value=str(c_item['telefone']) if c_item['telefone'] else "")
                ec_email = st.text_input("E-mail", value=str(c_item['email']) if c_item['email'] else "")
                ec_end = st.text_input("Endereço", value=str(c_item['endereco']) if c_item['endereco'] else "")
                ec_obs = st.text_area("Observações", value=str(c_item['observacoes']) if c_item['observacoes'] else "")
                
                col_cb1, col_cb2 = st.columns(2)
                salvar_cli_ed = col_cb1.form_submit_button("💾 Salvar Alterações", use_container_width=True)
                excluir_cli = col_cb2.form_submit_button("🗑 Excluir Cliente", use_container_width=True)
                
                if salvar_cli_ed:
                    supabase.table("clientes").update({
                        "nome": ec_nome, "cpf_cnpj": ec_doc, "telefone": ec_tel,
                        "email": ec_email, "endereco": ec_end, "observacoes": ec_obs
                    }).eq("id", int(c_item['id'])).execute()
                    st.success("Cliente atualizado!")
                    st.rerun()
                    
                if excluir_cli:
                    supabase.table("clientes").delete().eq("id", int(c_item['id'])).execute()
                    st.success("Cliente excluído!")
                    st.rerun()
                    
            st.markdown("---")
            st.dataframe(df_clientes[['nome', 'cpf_cnpj', 'telefone', 'email', 'endereco', 'observacoes']], hide_index=True, use_container_width=True)
        else:
            empty_state("👥", "Nenhum cliente cadastrado", "Comece cadastrando seu primeiro cliente")

# ==========================================
# 8. DASHBOARD GERAL
# ==========================================
with tab_dashboard:
    secao("📈 Painel Gerencial", "Visão consolidada do negócio em tempo real")
    st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
    
    # ---- KPIs principais ----
    ent = df_financeiro[df_financeiro['Tipo'] == 'Entrada']['Valor'].sum() if not df_financeiro.empty and 'Tipo' in df_financeiro.columns else 0
    sai = df_financeiro[df_financeiro['Tipo'] == 'Saída']['Valor'].sum() if not df_financeiro.empty and 'Tipo' in df_financeiro.columns else 0
    lucro_vendas = df_vendas['Lucro'].sum() if not df_vendas.empty and 'Lucro' in df_vendas.columns else 0
    capital = (df_estoque['Quantidade'] * df_estoque['Preço de Custo']).sum() if not df_estoque.empty and 'Preço de Custo' in df_estoque.columns else 0
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💵 Entradas", moeda(ent))
    k2.metric("📉 Saídas", moeda(sai))
    k3.metric("💰 Saldo Líquido", moeda(ent - sai))
    k4.metric("📦 Capital em Estoque", moeda(capital))
    
    st.markdown("---")
    
    # ---- Linha 1 de gráficos ----
    col_a, col_b = st.columns(2)
    with col_a:
        if not df_vendas.empty and 'Data' in df_vendas.columns:
            df_v_temp = df_vendas.copy()
            df_v_temp['Data'] = pd.to_datetime(df_v_temp['Data'], errors='coerce')
            evolucao = df_v_temp.dropna(subset=['Data']).groupby(df_v_temp['Data'].dt.date)['Valor Total'].sum().reset_index()
            evolucao.columns = ['Data', 'Faturamento']
            if not evolucao.empty:
                chart = alt.Chart(evolucao).mark_area(
                    line={'color': '#4f46e5', 'strokeWidth': 3},
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[alt.GradientStop(color='#4f46e5', offset=0),
                               alt.GradientStop(color='rgba(79,70,229,0.05)', offset=1)],
                        x1=1, x2=1, y1=1, y2=0
                    )
                ).encode(
                    x=alt.X('Data:T', title=''),
                    y=alt.Y('Faturamento:Q', title='R$'),
                    tooltip=[alt.Tooltip('Faturamento:Q', format=',.2f')]
                ).properties(height=280, title='📈 Evolução de Vendas')
                st.altair_chart(tema_altair(chart), use_container_width=True)
            else:
                st.info("Sem dados de vendas por data.")
        else:
            st.info("Sem vendas registradas.")
    
    with col_b:
        if not df_vendas.empty and 'Produto' in df_vendas.columns:
            top = df_vendas.groupby('Produto')['Valor Total'].sum().nlargest(5).reset_index()
            if not top.empty:
                chart = alt.Chart(top).mark_bar(
                    cornerRadiusTopLeft=6, cornerRadiusTopRight=6
                ).encode(
                    x=alt.X('Valor Total:Q', title='R$'),
                    y=alt.Y('Produto:N', sort='-x', title=''),
                    color=alt.Color('Valor Total:Q', scale=alt.Scale(scheme='blues'), legend=None),
                    tooltip=['Produto', alt.Tooltip('Valor Total:Q', format=',.2f')]
                ).properties(height=280, title='🏆 Top 5 Produtos')
                st.altair_chart(tema_altair(chart), use_container_width=True)
            else:
                st.info("Sem dados de produtos.")
    
    # ---- Linha 2 de gráficos ----
    col_c, col_d = st.columns(2)
    with col_c:
        if not df_vendas.empty and 'Produto' in df_vendas.columns and 'Valor Total' in df_vendas.columns:
            curva_resumo = df_vendas.groupby('Produto')['Valor Total'].sum().reset_index()
            curva_resumo = curva_resumo.sort_values('Valor Total', ascending=False)
            total = curva_resumo['Valor Total'].sum()
            if total > 0:
                curva_resumo['Acum'] = (curva_resumo['Valor Total'].cumsum() / total) * 100
                curva_resumo['Classe'] = curva_resumo['Acum'].apply(
                    lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C')
                )
                resumo_classe = curva_resumo.groupby('Classe')['Valor Total'].sum().reset_index()
                chart = alt.Chart(resumo_classe).mark_arc(innerRadius=55, outerRadius=100).encode(
                    theta=alt.Theta('Valor Total:Q'),
                    color=alt.Color('Classe:N', scale=alt.Scale(
                        domain=['A', 'B', 'C'],
                        range=['#10b981', '#f59e0b', '#ef4444']),
                        legend=alt.Legend(title='Classe ABC')
                    ),
                    tooltip=['Classe', alt.Tooltip('Valor Total:Q', format=',.2f')]
                ).properties(height=280, title='📊 Curva ABC')
                st.altair_chart(tema_altair(chart), use_container_width=True)
            else:
                st.info("Sem dados para Curva ABC.")
        else:
            st.info("Registre vendas para ver a Curva ABC.")
    
    with col_d:
        if not df_financeiro.empty and 'Tipo' in df_financeiro.columns:
            desp = df_financeiro[df_financeiro['Tipo'] == 'Saída'].groupby('Categoria')['Valor'].sum().reset_index()
            if not desp.empty:
                chart = alt.Chart(desp).mark_bar(
                    cornerRadiusTopLeft=6, cornerRadiusTopRight=6
                ).encode(
                    x=alt.X('Valor:Q', title='R$'),
                    y=alt.Y('Categoria:N', sort='-x', title=''),
                    color=alt.Color('Valor:Q', scale=alt.Scale(scheme='reds'), legend=None),
                    tooltip=['Categoria', alt.Tooltip('Valor:Q', format=',.2f')]
                ).properties(height=280, title='💡 Despesas por Categoria')
                st.altair_chart(tema_altair(chart), use_container_width=True)
            else:
                st.info("Sem despesas registradas.")
        else:
            st.info("Sem dados financeiros.")

# ==========================================
# 9. RELATÓRIO PDF INTEGRADO
# ==========================================
with tab_relatorio:
    secao("📄 Relatório Geral em PDF", "Documento completo extraído em tempo real do Supabase")
    st.write(
        "Gere um relatório completo com **todas as informações do sistema** "
        "(Estoque, Vendas, Financeiro e Clientes)."
    )

    st.info(
        "📊 **O relatório inclui:**\n"
        "- **Valor de Custo Total por produto** (Quantidade × Preço de Custo)\n"
        "- **Valor de Venda Total por produto** (Quantidade × Valor Unitário)\n"
        "- **Linha de Totais Gerais** ao final da tabela de estoque"
    )

    st.markdown("---")

    col_r1, col_r2 = st.columns([1, 1])
    with col_r1:
        gerar = st.button("🔄 Gerar Relatório PDF", type="primary", use_container_width=True)

    if gerar:
        with st.spinner("Gerando relatório e conectando ao Supabase..."):
            try:
                df_estoque = carregar_dados_tabela("estoque")
                df_vendas = carregar_dados_tabela("vendas")
                df_financeiro = carregar_dados_tabela("financeiro")
                df_clientes = carregar_dados_tabela("clientes")

                if df_estoque.empty:
                    df_estoque = pd.DataFrame(columns=['id', 'Produto', 'Categoria', 'Quantidade', 'Preço de Custo', 'Valor Unitário'])
                else:
                    col_map_est = {}
                    for col in df_estoque.columns:
                        c_lower = col.lower().strip()
                        if c_lower in ['produto', 'nome']: col_map_est[col] = 'Produto'
                        elif c_lower in ['categoria']: col_map_est[col] = 'Categoria'
                        elif c_lower in ['quantidade', 'qtd']: col_map_est[col] = 'Quantidade'
                        elif c_lower in ['valor_unitario', 'valorunitario', 'preco', 'valor']: col_map_est[col] = 'Valor Unitário'
                        elif c_lower in ['preco_custo', 'precocusto', 'custo']: col_map_est[col] = 'Preço de Custo'
                    df_estoque = df_estoque.rename(columns=col_map_est)
                    if 'Preço de Custo' not in df_estoque.columns: df_estoque['Preço de Custo'] = 0.00
                    if 'Valor Unitário' not in df_estoque.columns: df_estoque['Valor Unitário'] = 0.00
                    if 'Categoria' not in df_estoque.columns: df_estoque['Categoria'] = 'Geral'

                if df_vendas.empty:
                    df_vendas = pd.DataFrame(columns=['id', 'Data', 'Produto', 'Quantidade', 'Valor Total', 'Lucro'])
                else:
                    col_map_vendas = {}
                    for col in df_vendas.columns:
                        c_lower = col.lower().strip()
                        if c_lower == 'data': col_map_vendas[col] = 'Data'
                        elif c_lower == 'produto': col_map_vendas[col] = 'Produto'
                        elif c_lower == 'quantidade': col_map_vendas[col] = 'Quantidade'
                        elif c_lower in ['valor_total', 'valortotal']: col_map_vendas[col] = 'Valor Total'
                        elif c_lower == 'lucro': col_map_vendas[col] = 'Lucro'
                    df_vendas = df_vendas.rename(columns=col_map_vendas)

                if df_financeiro.empty:
                    df_financeiro = pd.DataFrame(columns=['id', 'Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])
                else:
                    col_map_fin = {}
                    for col in df_financeiro.columns:
                        c_lower = col.lower().strip()
                        if c_lower == 'data': col_map_fin[col] = 'Data'
                        elif c_lower in ['descricao', 'descrição']: col_map_fin[col] = 'Descrição'
                        elif c_lower == 'tipo': col_map_fin[col] = 'Tipo'
                        elif c_lower == 'categoria': col_map_fin[col] = 'Categoria'
                        elif c_lower == 'valor': col_map_fin[col] = 'Valor'
                    df_financeiro = df_financeiro.rename(columns=col_map_fin)

                pdf_bytes = gerar_relatorio_pdf()

                st.success("✅ Relatório gerado com sucesso!")
                st.download_button(
                    label="⬇️ Baixar Relatório PDF",
                    data=pdf_bytes,
                    file_name=f"relatorio_erp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            except Exception as e:
                st.error(f"❌ Erro ao gerar o relatório PDF: {e}")
                st.exception(e)

    st.markdown("---")
    st.markdown("### 📋 Pré-visualização dos Totais")
    if not df_estoque.empty and 'Quantidade' in df_estoque.columns:
        q = pd.to_numeric(df_estoque['Quantidade'], errors='coerce').fillna(0)
        pc = pd.to_numeric(df_estoque.get('Preço de Custo', 0), errors='coerce').fillna(0)
        pv = pd.to_numeric(df_estoque.get('Valor Unitário', 0), errors='coerce').fillna(0)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 Itens em Estoque", f"{int(q.sum())} un")
        c2.metric("💰 Capital Investido", moeda((q * pc).sum()))
        c3.metric("🏷 Potencial de Venda", moeda((q * pv).sum()))
        c4.metric("📈 Lucro Potencial", moeda((q * pv).sum() - (q * pc).sum()))
    else:
        st.info("Sem produtos em estoque para pré-visualizar totais.")

# ==========================================
# RODAPÉ
# ==========================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.85rem; padding: 1rem 0;">
    📦 Sistema ERP Integrado • Desenvolvido com Streamlit + Supabase<br>
    Última sessão: {}
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)
