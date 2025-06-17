import json
import os
import qrcode
import webbrowser

# --- Constantes de Caminhos ---
DADOS_DIR = 'dados'
SAIDA_DIR = 'saida'
TEMPLATES_DIR = 'templates'
CONFIG_FILE = os.path.join(DADOS_DIR, 'config.json')
ESTOQUE_FILE = os.path.join(DADOS_DIR, 'estoque.json')
TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, 'template_cardapio.html')
SAIDA_HTML_FILE = os.path.join(SAIDA_DIR, 'cardapio.html')
SAIDA_QRCODE_FILE = os.path.join(SAIDA_DIR, 'qr_code.png')

# --- Funções de Manipulação de Dados ---

def carregar_dados(caminho_arquivo, default_data):
    """Carrega dados de um arquivo JSON, criando-o se não existir."""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Se o arquivo não existe ou está vazio/corrompido, cria com dados padrão
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=4)
        return default_data

def salvar_dados(caminho_arquivo, dados):
    """Salva dados em um arquivo JSON."""
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# --- Funções do Administrador ---

def configurar_sistema():
    """Permite ao administrador alterar as configurações da loja."""
    config = carregar_dados(CONFIG_FILE, {})
    print("\n--- Configuração do Sistema ---")
    print("Deixe em branco para manter o valor atual.")

    novo_nome = input(f"Nome da loja [{config.get('nome_loja', 'N/A')}]: ")
    if novo_nome:
        config['nome_loja'] = novo_nome

    novo_whatsapp = input(f"Número de WhatsApp (ex: 55119...)[{config.get('whatsapp', 'N/A')}]: ")
    if novo_whatsapp:
        config['whatsapp'] = novo_whatsapp

    novo_email = input(f"E-mail para pedidos [{config.get('email', 'N/A')}]: ")
    if novo_email:
        config['email'] = novo_email

    while True:
        novo_metodo = input(f"Método de pedido (whatsapp/email) [{config.get('metodo_pedido', 'N/A')}]: ").lower()
        if novo_metodo in ['whatsapp', 'email', '']:
            if novo_metodo:
                config['metodo_pedido'] = novo_metodo
            break
        else:
            print("Opção inválida. Escolha 'whatsapp' ou 'email'.")

    salvar_dados(CONFIG_FILE, config)
    print("\n✅ Configurações salvas com sucesso!")

def adicionar_produto():
    """Adiciona um novo produto ao estoque."""
    estoque = carregar_dados(ESTOQUE_FILE, [])
    print("\n--- Adicionar Novo Produto ---")
    
    produto = {}
    produto['id'] = len(estoque) + 1 if estoque else 1
    produto['nome'] = input("Nome do produto: ")
    while True:
        try:
            produto['preco'] = float(input("Preço (ex: 15.50): "))
            break
        except ValueError:
            print("Por favor, insira um número válido para o preço.")
    produto['descricao'] = input("Descrição do produto: ")
    produto['imagem_url'] = input("URL da imagem do produto: ")

    estoque.append(produto)
    salvar_dados(ESTOQUE_FILE, estoque)
    print(f"\n✅ Produto '{produto['nome']}' adicionado com sucesso!")

def listar_produtos():
    """Lista todos os produtos cadastrados."""
    estoque = carregar_dados(ESTOQUE_FILE, [])
    print("\n--- Lista de Produtos Cadastrados ---")
    if not estoque:
        print("Nenhum produto cadastrado.")
        return

    for produto in estoque:
        print(f"ID: {produto['id']} | Nome: {produto['nome']} | Preço: R$ {produto['preco']:.2f}")

def remover_produto():
    """Remove um produto do estoque pelo ID."""
    listar_produtos()
    estoque = carregar_dados(ESTOQUE_FILE, [])
    if not estoque:
        return

    try:
        id_para_remover = int(input("\nDigite o ID do produto que deseja remover: "))
        novo_estoque = [p for p in estoque if p.get('id') != id_para_remover]

        if len(novo_estoque) < len(estoque):
            salvar_dados(ESTOQUE_FILE, novo_estoque)
            print(f"\n✅ Produto com ID {id_para_remover} removido com sucesso!")
        else:
            print("\n❌ Produto não encontrado.")
    except ValueError:
        print("\n❌ ID inválido. Por favor, digite um número.")


# --- Funções de Geração ---

def gerar_cardapio_html():
    """Gera o arquivo HTML do cardápio a partir do template e dos dados."""
    print("\nGerando o arquivo do cardápio...")
    try:
        # Carregar dados
        config = carregar_dados(CONFIG_FILE, {})
        estoque = carregar_dados(ESTOQUE_FILE, [])
        
        # Carregar template
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Substituir os marcadores pelos dados reais
        html_content = template_content.replace('{{NOME_DA_LOJA}}', config.get('nome_loja', 'Minha Loja'))
        # Convertemos os dados Python para strings JSON para injetar no <script>
        html_content = html_content.replace('{{DADOS_ESTOQUE}}', json.dumps(estoque, ensure_ascii=False))
        html_content = html_content.replace('{{DADOS_CONFIG}}', json.dumps(config, ensure_ascii=False))

        # Salvar o arquivo final
        with open(SAIDA_HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ Cardápio gerado com sucesso em: {SAIDA_HTML_FILE}")
        return True
    except FileNotFoundError:
        print(f"❌ Erro: O arquivo de template '{TEMPLATE_FILE}' não foi encontrado.")
        return False
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")
        return False

def gerar_qr_code():
    """Gera um QR Code que aponta para o arquivo HTML local."""
    if not os.path.exists(SAIDA_HTML_FILE):
        print("\n❌ O arquivo 'cardapio.html' não existe. Gere o cardápio primeiro (opção 5).")
        return
    
    # Cria um caminho absoluto para o arquivo HTML, para que o QR Code funcione localmente
    caminho_absoluto = os.path.abspath(SAIDA_HTML_FILE)
    url_local = f'file:///{caminho_absoluto.replace(os.path.sep, "/")}'

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url_local)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(SAIDA_QRCODE_FILE)
    print(f"✅ QR Code gerado e salvo em: {SAIDA_QRCODE_FILE}")
    print("Aponte a câmera do seu celular para este QR Code para testar o cardápio.")


# --- Menu Principal ---

def inicializar_pastas():
    """Cria as pastas necessárias se elas não existirem."""
    os.makedirs(DADOS_DIR, exist_ok=True)
    os.makedirs(SAIDA_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)

def menu_principal():
    """Exibe o menu principal e gerencia as ações do usuário."""
    inicializar_pastas()
    
    while True:
        print("\n" + "="*30)
        print("   SISTEMA DE GESTÃO DE ESTOQUE E CARDÁPIO   ")
        print("="*30)
        print("1. Adicionar Produto")
        print("2. Listar Produtos")
        print("3. Remover Produto")
        print("4. Configurar Loja (WhatsApp, E-mail, etc.)")
        print("5. Gerar/Atualizar Cardápio Interativo")
        print("6. Gerar QR Code do Cardápio")
        print("7. Abrir Cardápio para Teste")
        print("8. Sair")
        print("="*30)
        
        escolha = input("Escolha uma opção: ")

        if escolha == '1':
            adicionar_produto()
        elif escolha == '2':
            listar_produtos()
        elif escolha == '3':
            remover_produto()
        elif escolha == '4':
            configurar_sistema()
        elif escolha == '5':
            gerar_cardapio_html()
        elif escolha == '6':
            gerar_qr_code()
        elif escolha == '7':
            if os.path.exists(SAIDA_HTML_FILE):
                webbrowser.open(f'file:///{os.path.abspath(SAIDA_HTML_FILE)}')
            else:
                print("\n❌ Cardápio ainda não foi gerado. Use a opção 5 primeiro.")
        elif escolha == '8':
            print("Saindo do sistema. Até logo!")
            break
        else:
            print("\n❌ Opção inválida. Tente novamente.")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    menu_principal()