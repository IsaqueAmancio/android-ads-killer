import subprocess
import sys
import time
import re
from datetime import datetime

class AndroidExterminator:
    """
    Classe responsável por gerenciar a comunicação com o dispositivo Android via ADB.
    O objetivo é identificar e remover adwares sorrateiros.
    """

    # Palavras-chave de pacotes vitais do Android que NUNCA devem ser desinstalados
    PACOTES_PROTEGIDOS = (
        "com.android.systemui",
        "com.android.settings",
        "com.google.android.gms",
        "com.google.android.packageinstaller",
        "launcher",
        "miui.home",
    )

    def __init__(self, adb_path: str = "adb"):
        """
        Inicializa o nosso exterminador.
        
        :param adb_path: O caminho para o executável do ADB. 
                         Se estiver nas variáveis de ambiente do PC, apenas "adb" basta.
        """
        self.adb_path = adb_path
        self.target_device = None

    def _run_command(self, command: list) -> str:
        """
        Método interno e privado para rodar comandos no terminal e pegar a resposta.
        Seguindo boas práticas (DRY - Don't Repeat Yourself), tudo passa por aqui.
        
        :param command: Lista de strings contendo o comando (ex: ['adb', 'devices'])
        :return: A saída do terminal em formato de texto.
        """
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        
        except FileNotFoundError:
            print("🚨 ERRO CRÍTICO: O comando ADB não foi encontrado!")
            print("Verifique se o ADB está instalado e nas variáveis de ambiente.")
            sys.exit(1)
            
        except subprocess.CalledProcessError as e:
            erro_msg = e.stderr.strip() if e.stderr else e.stdout.strip()
            print(f"⚠️ Erro ao executar o comando {command}: {erro_msg}")
            return ""

    def check_connection(self) -> bool:
        """
        Verifica se há algum dispositivo conectado e com a depuração USB autorizada.
        """
        print("🔍 Procurando dispositivos conectados...")
        output = self._run_command([self.adb_path, "devices"])
        
        lines = output.splitlines()
        
        devices = []
        for line in lines[1:]:  # Pula a primeira linha "List of devices attached"
            if "device" in line and "unauthorized" not in line:
                devices.append(line.split("\t")[0])
                
        if not devices:
            print("❌ Nenhum celular conectado ou depuração USB não autorizada (olhe a tela do celular!).")
            return False
            
        self.target_device = devices[0]
        print(f"✅ Dispositivo encontrado! ID: {self.target_device}")
        return True

    def list_third_party_apps(self) -> list:
        """
        Lista apenas os pacotes instalados pelo usuário (terceiros).
        
        :return: Lista de strings em ordem alfabética com os nomes dos pacotes.
        """
        print("\n📦 Varrendo aplicativos instalados (apenas terceiros)...")
        output = self._run_command([
            self.adb_path, "-s", self.target_device, 
            "shell", "pm", "list", "packages", "-3"
        ])
        
        if not output:
            return []

        packages = []
        for line in output.splitlines():
            clean_name = line.replace("package:", "").strip()
            if clean_name:
                packages.append(clean_name)
        
        packages.sort()
        return packages

    def catch_suspect_in_action(self, silencioso: bool = False) -> str:
        """
        Inspeciona o gerenciador de janelas do Android para descobrir qual aplicativo
        está em primeiro plano (foco atual) na tela do celular.
        
        :param silencioso: Se True, não imprime a mensagem de busca (usado no loop do radar).
        :return: String contendo a linha de foco atual.
        """
        if not silencioso:
            print("\n🕵️‍♂️ Analisando o que está aberto na tela agora...")
            
        output = self._run_command([
            self.adb_path, "-s", self.target_device, 
            "shell", "dumpsys", "window", "displays"
        ])
        
        for line in output.splitlines():
            if "mCurrentFocus" in line or "mFocusedApp" in line:
                return line.strip()
                
        return "Tela bloqueada ou sem foco ativo"

    def extract_package_name(self, raw_focus_line: str) -> str:
        """
        Usa Expressão Regular (Regex) para extrair apenas o nome do pacote (ex: 'com.whatsapp')
        de dentro da linha bruta retornada pelo dumpsys.
        
        :param raw_focus_line: Linha bruta do ADB (ex: 'mCurrentFocus=Window{... com.app.teste/.MainActivity}')
        :return: Nome limpo do pacote ou a própria linha caso não haja pacote identificado.
        """
        # Procura o padrão 'com.alguma.coisa/' antes da barra da Activity
        match = re.search(r"([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)+)/", raw_focus_line)
        if match:
            return match.group(1)
        return raw_focus_line

    def is_protected_package(self, package_name: str) -> bool:
        """
        Verifica se o pacote faz parte da lista de proteção do sistema (Launcher, SystemUI, etc).
        """
        pacote_lower = package_name.lower()
        for protegido in self.PACOTES_PROTEGIDOS:
            if protegido in pacote_lower:
                return True
        return False

    def force_stop_app(self, package_name: str) -> bool:
        """
        Força a parada imediata de um aplicativo usando o Activity Manager (am).
        """
        print(f"\n🛑 Congelando o pacote '{package_name}'...")
        self._run_command([
            self.adb_path, "-s", self.target_device,
            "shell", "am", "force-stop", package_name
        ])
        print(f"❄️ '{package_name}' foi forçado a parar! Veja se a propaganda sumiu.")
        return True

    def uninstall_app(self, package_name: str) -> bool:
        """
        Desinstala um aplicativo do dispositivo.
        Bloqueia a ação caso o pacote esteja na lista de proteção do sistema.
        """
        if self.is_protected_package(package_name):
            print(f"\n🛡️ TRAVA DE SEGURANÇA ATIVADA: '{package_name}' é um componente vital do sistema/Launcher!")
            print("Desinstalar isso causaria tela preta no celular. Operação bloqueada pelo seu próprio bem.")
            return False

        print(f"\n💥 Tentando exterminar '{package_name}' (Método Padrão)...")
        output = self._run_command([
            self.adb_path, "-s", self.target_device,
            "uninstall", package_name
        ])

        if "Success" in output:
            print(f"💀 BOOM! '{package_name}' foi devidamente varrido da existência!")
            return True

        print("⚠️ O alvo resistiu ao tiro comum. Tentando remoção forçada do usuário (--user 0)...")
        output_user0 = self._run_command([
            self.adb_path, "-s", self.target_device,
            "shell", "pm", "uninstall", "--user", "0", package_name
        ])

        if "Success" in output_user0:
            print(f"💀 BOOM! '{package_name}' foi arrancado do usuário atual com sucesso!")
            return True

        print(f"❌ Falha ao remover '{package_name}'.")
        print("💡 Dica: Verifique se esse app não ativou permissão de 'Administrador do Dispositivo' nas Configurações de Segurança do Android.")
        return False


# =========================================================
# Funções de Interface no Terminal (Menu e Radar)
# =========================================================
def executar_ataque(ferramenta: AndroidExterminator, pacote_alvo: str):
    """
    Submenu reutilizável (DRY) para escolher entre Forçar Parada ou Desinstalar um pacote.
    """
    print(f"\n👉 Alvo na mira: [{pacote_alvo}]")
    if ferramenta.is_protected_package(pacote_alvo):
        print("   ⚠️ ATENÇÃO: Este pacote parece ser a tela inicial (Launcher) ou parte do Android!")

    print("  [1] 🛑 Forçar Parada (Seguro - Apenas fecha o app na hora)")
    print("  [2] 💀 Desinstalar (Irreversível - Apaga o app e seus dados)")
    print("  [0] 🔙 Cancelar")

    acao = input("Escolha a munição (1, 2 ou 0): ").strip()

    if acao == "1":
        ferramenta.force_stop_app(pacote_alvo)
    elif acao == "2":
        confirmacao = input(f"⚠️ TEM CERTEZA que deseja DESINSTALAR '{pacote_alvo}'? (s/n): ").strip().lower()
        if confirmacao == "s":
            ferramenta.uninstall_app(pacote_alvo)
        else:
            print("😅 Operação abortada. O pacote continua vivo por enquanto.")
    else:
        print("Ação cancelada.")


def gerenciar_alvos(ferramenta: AndroidExterminator):
    """
    Lista os aplicativos de terceiros numerados e permite escolher qual pacote atacar.
    """
    apps_instalados = ferramenta.list_third_party_apps()
    
    if not apps_instalados:
        print("Nenhum aplicativo de terceiro encontrado.")
        return

    print(f"\n📋 Total de apps de terceiros encontrados: {len(apps_instalados)}")
    for indice, app in enumerate(apps_instalados, start=1):
        print(f"  [{indice}] {app}")

    escolha = input("\n🎯 Digite o NÚMERO do app que deseja atacar (ou Enter para voltar): ").strip()
    if not escolha:
        return

    try:
        indice_escolhido = int(escolha)
        if indice_escolhido < 1 or indice_escolhido > len(apps_instalados):
            print("❌ Número fora da lista! Respira fundo e tenta de novo.")
            return
    except ValueError:
        print("❌ Isso não é um número válido!")
        return

    pacote_alvo = apps_instalados[indice_escolhido - 1]
    executar_ataque(ferramenta, pacote_alvo)


def modo_caca_fantasma(ferramenta: AndroidExterminator, intervalo: float = 2.0):
    """
    Vigia a tela do celular em loop contínuo e registra um histórico com data/hora
    sempre que um novo aplicativo assumir o foco da tela.
    
    :param ferramenta: Instância do AndroidExterminator.
    :param intervalo: Tempo em segundos entre cada checagem (mínimo de 0.5s).
    """
    # Trava de segurança contra sobrecarga do ADB
    if intervalo < 0.5:
        intervalo = 0.5

    print("\n" + "=" * 60)
    print("👻 MODO CAÇA-FANTASMA ATIVADO (Vigilância em Tempo Real)")
    print("=" * 60)
    print(f"⏱️  Radar checando a tela a cada {intervalo} segundos.")
    print("📱 Deixe o celular aberto e espere a propaganda pular na tela.")
    print("🛑 Pressione [Ctrl + C] a qualquer momento para parar o radar e atacar!\n")

    ultimo_pacote = None
    historico_suspeitos = []  # Guarda os pacotes únicos capturados na sessão

    try:
        while True:
            linha_bruta = ferramenta.catch_suspect_in_action(silencioso=True)
            pacote_atual = ferramenta.extract_package_name(linha_bruta)

            # Só registra no log se o app na tela mudou desde a última checagem
            if pacote_atual != ultimo_pacote:
                agora = datetime.now().strftime("%H:%M:%S")
                tag_sistema = " [🛡️ SISTEMA/LAUNCHER]" if ferramenta.is_protected_package(pacote_atual) else " [🎯 SUSPEITO/APP]"
                
                print(f"[{agora}] Mudança na tela -> {pacote_atual}{tag_sistema}")
                ultimo_pacote = pacote_atual

                # Salva na lista de suspeitos (se for um pacote válido com ponto no nome e ainda não estiver na lista)
                if "." in pacote_atual and pacote_atual not in historico_suspeitos:
                    historico_suspeitos.append(pacote_atual)

            time.sleep(intervalo)

    except KeyboardInterrupt:
        # Quando o usuário aperta Ctrl+C, caímos aqui sem quebrar o programa
        print("\n\n🛑 Radar pausado pelo usuário! Gerando dossiê da vigília...")

    if not historico_suspeitos:
        print("Nenhum pacote foi capturado durante a vigília.")
        return

    print("\n📋 Pacotes flagrados abrindo na tela durante a vigília:")
    for indice, app in enumerate(historico_suspeitos, start=1):
        aviso = " (Sistema/Protegido)" if ferramenta.is_protected_package(app) else ""
        print(f"  [{indice}] {app}{aviso}")

    escolha = input("\n🎯 Quer atacar algum desses flagrados agora? Digite o NÚMERO (ou Enter para voltar): ").strip()
    if not escolha:
        return

    try:
        indice_escolhido = int(escolha)
        if 1 <= indice_escolhido <= len(historico_suspeitos):
            pacote_alvo = historico_suspeitos[indice_escolhido - 1]
            executar_ataque(ferramenta, pacote_alvo)
        else:
            print("❌ Número fora da lista.")
    except ValueError:
        print("❌ Entrada inválida.")


def menu_principal(ferramenta: AndroidExterminator):
    """
    Mantém o programa rodando em um menu interativo até o usuário decidir sair.
    """
    while True:
        print("\n" + "=" * 55)
        print("🗡️  AD KILLER- PAINEL DE CONTROLE")
        print("=" * 55)
        print("  [1] 🕵️‍♂️ Dedo-Duro Instantâneo (Ver qual app está na tela agora)")
        print("  [2] 📦 Listar Apps de Terceiros e Atacar (Parar / Desinstalar)")
        print("  [3] 👻 Modo Caça-Fantasma (Vigilância em Loop com Histórico)")
        print("  [0] 🚪 Sair")
        print("=" * 55)

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            app_na_tela = ferramenta.catch_suspect_in_action()
            pacote_limpo = ferramenta.extract_package_name(app_na_tela)
            print(f"\n🎯 Alvo na tela agora:\n   Pacote: {pacote_limpo}\n   Bruto:  {app_na_tela}")
        elif opcao == "2":
            gerenciar_alvos(ferramenta)
        elif opcao == "3":
            modo_caca_fantasma(ferramenta, intervalo=2.0)
        elif opcao == "0":
            print("\n👋 Guardando as armas. Até a próxima caçada!")
            break
        else:
            print("\n❌ Opção inválida. Tente um dos números do menu.")


# =========================================================
# Bloco de Execução Principal (Ponto de Entrada)
# =========================================================
if __name__ == "__main__":
    # Instanciamos a nossa arma
    ferramenta = AndroidExterminator()
    
    # Testamos a conexão antes de sair atirando
    if ferramenta.check_connection():
        print("Tudo pronto para a caçada. Abrindo painel tático...")
        menu_principal(ferramenta)
    else:
        print("Conecte o cabo USB e tente novamente.")