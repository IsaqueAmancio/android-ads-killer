# 🗡️ Android Ads Killer (`android-ads-killer`)

O **Android Ads Killer** é uma ferramenta de linha de comando (CLI) escrita em Python puro que utiliza o **ADB (Android Debug Bridge)** para rastrear, congelar e desinstalar *adwares* (aplicativos maliciosos de propaganda) que se escondem no sistema ou exibem anúncios intrusivos em tela cheia sem deixar rastros no menu de aplicativos recentes.

## 🎯 Funcionalidades Principais

* **🕵️‍♂️ Dedo-Duro Instantâneo (`catch_suspect_in_action`):** Inspeciona o gerenciador de janelas do Android (`dumpsys window`) e usa Expressões Regulares (Regex) para revelar exatamente qual pacote está aberto na tela naquele segundo — mesmo que o app não tenha ícone nem nome no menu.

* **👻 Modo Caça-Fantasma (`modo_caca_fantasma`):** Um radar de vigilância em tempo real que monitora a tela em *loop* e registra um dossiê com horário exato (`[HH:MM:SS]`) sempre que uma janela diferente pula na frente da tela.

* **📦 Varredura Segura (`list_third_party_apps`):** Lista exclusivamente aplicativos instalados por terceiros (flag `-3`), mantendo pacotes nativos do sistema longe da mira por padrão.

* **🛑 Congelamento Tático (`force_stop_app`):** Força a parada imediata do processo suspeito via *Activity Manager* (`am force-stop`), permitindo testar se os anúncios somem antes de apagar qualquer dado.

* **💀 Extermínio em Dois Estágios (`uninstall_app`):** Tenta a desinstalação tradicional e, caso o adware resista, executa automaticamente um *fallback* de remoção forçada para o usuário atual (`pm uninstall --user 0`) sem exigir *Root*.

* **🛡️ Trava Anti-Tiro no Pé (`PACOTES_PROTEGIDOS`):** Sistema de segurança interno que bloqueia tentativas acidentais de desinstalar a tela inicial (*Launcher*) ou componentes vitais do Android (`systemui`, `settings`, `gms`).

  ## 

## 🛠️ Pré-requisitos

Não é necessário instalar nenhuma biblioteca externa com `pip` (o projeto utiliza 100% bibliotecas nativas do Python: `subprocess`, `sys`, `time`, `re` e `datetime`). Você só precisa de:

1. **Python 3.8 ou superior** instalado no computador.

2. **ADB (Android SDK Platform-Tools)** instalado e configurado nas variáveis de ambiente (`PATH`) do seu sistema operacional.

   * *Download oficial do Google:* [SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools)

3. **No celular Android:**

   * Vá em *Configurações > Sobre o telefone* e toque 7 vezes em **Número da versão** para ativar as *Opções do Desenvolvedor*.

   * Entre em *Opções do Desenvolvedor* e ative a chave **Depuração USB**.

## 🚀 Como Executar

1. Clone este repositório para a sua máquina:

   ```
   git clone https://github.com/SEU-USUARIO/android-ads-killer.git
   cd android-ads-killer
   
   ```

2. Conecte o celular ao computador via cabo USB e marque **"Permitir sempre a partir deste computador"** no aviso que aparecerá na tela do aparelho.

3. Execute o script principal:

   ```
   python main.py
   
   ```

## ⚙️ Parâmetros Ajustáveis no Código

Se precisar adaptar o comportamento do **Android Ads Killer** para cenários específicos, você pode ajustar os seguintes parâmetros diretamente no código:

| Parâmetro / Variável | Localização | Valor Padrão | Descrição | 
| ----- | ----- | ----- | ----- | 
| `adb_path` | `AndroidExterminator.__init__` | `"adb"` | Caminho do executável do ADB. Caso o ADB não esteja no `PATH` do Windows, passe o caminho completo (ex: `"C:\\platform-tools\\adb.exe"`). | 
| `PACOTES_PROTEGIDOS` | Topo da classe `AndroidExterminator` | `("com.android.systemui", ...)` | Tupla contendo palavras-chave de pacotes do sistema que são bloqueados contra desinstalação acidental. | 
| `intervalo` | `modo_caca_fantasma()` | `2.0` | Tempo (em segundos) entre cada varredura de tela no Modo Caça-Fantasma. Possui trava mínima de `0.5s` para não sobrecarregar o ADB. | 

## ⚠️ Aviso Legal (Disclaimer)

Esta ferramenta foi desenvolvida para fins de **manutenção técnica, diagnóstico e educação**. Embora o código conte com filtros para listar apenas pacotes de terceiros (`-3`) e travas contra a remoção de *Launchers* e pacotes essenciais, a decisão final de desinstalar um aplicativo é do usuário.

**Faça sempre backup dos dados importantes antes de remover pacotes desconhecidos.** O autor não se responsabiliza por perda de dados em aplicativos desinstalados pelo usuário.