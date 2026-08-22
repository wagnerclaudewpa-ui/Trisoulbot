"""
╔══════════════════════════════════════════════════════════════════╗
║              🐉  TRISOUL BOT  🔥🌑✨                              ║
║      O Filho dos Deuses Dragônicos — Três Consciências            ║
║        Ignis (Fogo) • Umbra (Sombra) • Luxor (Luz)                ║
║                         v1.2 — Online                             ║
╚══════════════════════════════════════════════════════════════════╝

Lore rápida:
  Trisoul nasceu da fusão de três dragões-deuses, um por cada cabeça.
  Cada cabeça tem vontade própria e responde do seu jeito:
    🔥 Ignis  — impulsivo, intenso, fala em CAPS, adora provocar
    🌑 Umbra  — sombrio, enigmático, fala baixo e com reticências
    ✨ Luxor  — gentil, sábio, sempre acolhedor e encorajador

Módulos:
  • Diálogo       — Trisoul aprende e responde a gatilhos ensinados
  • Aparições     — aparece do nada, sem ser chamado
  • Chamado       — responde quando mencionado ou chamado pelo nome
  • Cabeça única  — você pode chamar uma cabeça específica direto
  • Reações       — reage com emoji a palavras-chave de cada elemento
  • Fé & Altar    — sistema de devoção/oração com placar
  • Invocação     — força uma cabeça específica a se manifestar
  • Profecia      — oráculo temático de cada cabeça
  • Grupos        — painel com botão que cria cargo + chat + call pro usuário
  • Fichas        — formulários interativos (modal + confirmação) pra
                    novos membros, Staff e parcerias (mapa, comercial,
                    DJ, clã e comunidade — cada uma é sua própria ficha)
"""

import discord
from discord.ext import commands
import asyncio
import os
import json
import random
import re
import traceback
from datetime import datetime, timezone
from collections import defaultdict, deque
from dotenv import load_dotenv

load_dotenv()

# ══════════════════════════════════════════════════════════════════
#  ⚙️  CONFIGURAÇÕES GERAIS
# ══════════════════════════════════════════════════════════════════

TOKEN = os.getenv("TRISOUL_TOKEN") or os.getenv("TOKEN")

DIALOGO_FILE = "trisoul_dialogo.json"
FE_FILE      = "trisoul_fe.json"

COOLDOWN_RESPOSTA   = 3     # segundos entre respostas automáticas por canal
CHANCE_GATILHO_SEM_CHAMADO = 0.0    # 0 = só responde gatilho quando é chamado (mencionado, "trisoul" ou nome de uma cabeça no texto)
CHANCE_APARICAO_ESPONTANEA = 0.012  # chance de aparecer do nada por mensagem
SILENCIO_MINIMO_APARICAO   = 90     # segundos de silêncio no canal antes de poder aparecer sozinho
CHANCE_REACAO_EMOJI        = 0.35   # chance de reagir com emoji a palavra-chave

# ══════════════════════════════════════════════════════════════════
#  ⚙️  CONFIGURAÇÕES — MÓDULO DE GRUPOS (painel/ticket)
# ══════════════════════════════════════════════════════════════════

CANAL_PAINEL_ID    = 1540504012263264426   # canal onde o painel/ticket fica
CARGO_PERMITIDO_ID = 1536210475333976205   # só quem tem esse cargo pode clicar
CATEGORIA_ID       = 1536389533388513371   # categoria onde os canais do grupo entram

IMAGEM_PAINEL = "https://cdn.discordapp.com/attachments/926913851172204577/1540507745126457426/ChatGPT_Image_21_de_ago._de_2026_20_42_44.png?ex=6a8a3523&is=6a88e3a3&hm=47da90dbe503f337ebc485dbb754d880377bde27a6d21e211d419590b34a53f8"

COR_ROXO_GRUPO = 0x8E44AD

GRUPOS_DATA_FILE = "trisoul_grupos.json"

_HEX_RE = re.compile(r'^#?[0-9A-Fa-f]{6}$')

# ══════════════════════════════════════════════════════════════════
#  🤖  SETUP DO BOT
# ══════════════════════════════════════════════════════════════════

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix=["t!", "T!", "trisoul ", "Trisoul "], intents=intents)
bot.remove_command("help")

# ══════════════════════════════════════════════════════════════════
#  🐉  AS TRÊS CABEÇAS
# ══════════════════════════════════════════════════════════════════

CABECAS = {
    "ignis": {
        "nome": "Ignis",
        "titulo": "Ignis, o Punho em Chamas",
        "elemento": "Fogo",
        "emoji": "🔥",
        "cor": 0xE63900,
    },
    "umbra": {
        "nome": "Umbra",
        "titulo": "Umbra, a Voz do Vazio",
        "elemento": "Sombra",
        "emoji": "🌑",
        "cor": 0x2B0033,
    },
    "luxor": {
        "nome": "Luxor",
        "titulo": "Luxor, o Olho Radiante",
        "elemento": "Luz",
        "emoji": "✨",
        "cor": 0xFFD700,
    },
}

COR_NEUTRA    = 0x4B2E83   # roxo dragão neutro pra embeds gerais
COR_VERDE     = 0x00E676
COR_VERMELHO  = 0xFF5252
COR_DOURADO   = 0xFFD700


def fala(cabeca_key: str, texto: str) -> str:
    """Formata uma linha de diálogo com a assinatura da cabeça que está falando."""
    c = CABECAS.get(cabeca_key, CABECAS["luxor"])
    return f"{c['emoji']} **{c['nome']}** — {texto}"


def escolher_cabeca() -> str:
    return random.choice(list(CABECAS.keys()))


def embed_cabeca(cabeca_key: str, titulo: str, desc: str) -> discord.Embed:
    c = CABECAS.get(cabeca_key, CABECAS["luxor"])
    e = discord.Embed(title=titulo, description=desc, color=c["cor"], timestamp=datetime.now(timezone.utc))
    e.set_footer(text=f"{c['emoji']} {c['titulo']}")
    return e


def embed_ok(titulo: str, desc: str) -> discord.Embed:
    e = discord.Embed(title=titulo, description=desc, color=COR_VERDE, timestamp=datetime.now(timezone.utc))
    e.set_footer(text="🐉 Trisoul")
    return e


def embed_erro(desc: str) -> discord.Embed:
    e = discord.Embed(title="❌ eita!!", description=desc, color=COR_VERMELHO, timestamp=datetime.now(timezone.utc))
    e.set_footer(text="🐉 Trisoul")
    return e


# ══════════════════════════════════════════════════════════════════
#  💾  PERSISTÊNCIA
# ══════════════════════════════════════════════════════════════════

def _carregar_dialogo() -> dict:
    if os.path.exists(DIALOGO_FILE):
        try:
            with open(DIALOGO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "respostas" not in data:
                    data = {"respostas": {}}
                return data
        except Exception:
            pass
    return {"respostas": {}}


def _salvar_dialogo(db: dict):
    with open(DIALOGO_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def _carregar_fe() -> dict:
    if os.path.exists(FE_FILE):
        try:
            with open(FE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _salvar_fe(data: dict):
    with open(FE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _carregar_grupos() -> dict:
    if os.path.exists(GRUPOS_DATA_FILE):
        try:
            with open(GRUPOS_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _salvar_grupos(data: dict):
    with open(GRUPOS_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════
#  💬  BANCO DE FALAS — SEED (cada gatilho já nasce com voz própria)
# ══════════════════════════════════════════════════════════════════

_SAUDACOES = {
    "ignis": [
        "*as chamas crepitam* FALA logo, mortal!! o que você quer de Ignis?? 🔥🐉",
        "hm?? me chamou?? é bom que seja importante, eu tava PEGANDO FOGO de tédio aqui!! 🔥",
        "EU SOU IGNIS!! fala rápido antes que eu perca a paciência (e ela já é curta)!! 🔥😤",
        "*rosna baixinho, olhos em brasa* ...sim?? quem ousa me invocar?? 🔥🐉",
    ],
    "umbra": [
        "...eu já sabia que você ia me chamar... eu sempre sei... 🌑🐉",
        "*emerge das sombras em silêncio* ...sim?? fale... eu estou ouvindo... 🌑",
        "hm... alguém ousou perturbar minha escuridão... o que você quer?? 🌑🖤",
        "*olhos brilham na penumbra* ...me chamou?? interessante... continue... 🌑🐉",
    ],
    "luxor": [
        "olá, viajante!! que a luz ilumine este momento!! como posso ajudar?? ✨🐉",
        "*abre os olhos radiantes* sim?? estou aqui para você, sempre!! ✨",
        "oi oi!! senti sua chamada através da luz!! o que precisa?? ✨🐲",
        "a luz sempre responde a quem a busca!! oi!! o que foi?? ✨🐉",
    ],
}

_APARICOES = {
    "ignis": [
        "*surge do nada em uma explosão de fagulhas* HÁ!! sentiram minha presença?? 🔥🐉",
        "*as chamas dançam sozinhas por um instante* 🔥",
        "ARDER É VIVER!! ...só passando pra lembrar disso!! 🔥",
        "*solta uma fumacinha entediada* alguém pra brigar por diversão?? 🔥🐉",
    ],
    "umbra": [
        "...eu estava aqui o tempo todo... vocês só não notaram... 🌑🐉",
        "*uma sombra passa rapidamente pela sala* 🌑",
        "...os segredos deste lugar sussurram pra mim... 🌑🖤",
        "*observa em silêncio, depois desaparece de novo* 👁️🌑",
    ],
    "luxor": [
        "*um brilho suave aparece do nada* só espalhando um pouco de luz por aqui!! ✨",
        "sinto a energia deste lugar... está tudo bem com vocês?? ✨🐉",
        "*pisca suavemente como uma estrela distante* ✨",
        "às vezes eu só apareço pra lembrar que vocês não estão sozinhos!! ✨🐲",
    ],
}

_BENCAOS = {
    "ignis": [
        "{user}, receba o FOGO da minha bênção!! que sua força nunca se apague!! 🔥🐉",
        "*toca {user} com uma chama que não queima* você carrega um pouco do meu ardor agora!! 🔥",
        "hmpf... tá bem, {user}... você tem coragem de orar a mim... aceito sua devoção!! 🔥😤",
    ],
    "umbra": [
        "...{user}... sua fé foi ouvida nas sombras... eu vejo você agora... 🌑🐉",
        "*envolve {user} em uma sombra protetora* que a escuridão o guarde dos seus medos... 🌑",
        "...poucos ousam orar a mim... você é... interessante, {user}... 🌑🖤",
    ],
    "luxor": [
        "{user}, que minha luz o guie sempre!! sua fé também é uma bênção pra mim!! ✨🐉",
        "*envolve {user} num brilho quente* você está protegido(a) pela luz agora!! ✨",
        "obrigado pela sua devoção, {user}!! eu sempre vou iluminar seu caminho!! ✨🐲",
    ],
}

_INVOCACOES = {
    "ignis": [
        "FUI INVOCADO!! e eu vim PRONTO PRA AGITAR AS COISAS!! 🔥🐉 fala logo, o que foi??",
        "*surge em uma coluna de fogo* Ignis responde ao chamado!! rápido!! 🔥",
    ],
    "umbra": [
        "...fui invocado... interessante escolha... o que você precisa de mim?? 🌑🐉",
        "*emerge lentamente das trevas* ...Umbra está aqui... 🌑",
    ],
    "luxor": [
        "fui chamado!! e aqui estou, com toda minha luz pra ajudar!! ✨🐉",
        "*aparece em um brilho gentil* Luxor responde à sua invocação!! como posso ajudar?? ✨",
    ],
}

_PROFECIAS = {
    "ignis": [
        "vejo... FOGO no seu futuro!! uma briga, uma vitória, ou as duas!! 🔥🐉",
        "as chamas me mostram: você vai encarar algo de frente em breve. NÃO RECUE!! 🔥",
        "sua sorte hoje?? tá quente. literalmente. aproveita!! 🔥😤",
    ],
    "umbra": [
        "...as sombras sussurram... algo está escondido perto de você... preste atenção... 🌑🐉",
        "...eu vejo um segredo se revelando em breve... esteja preparado(a)... 🌑",
        "...nem tudo que parece calmo, é calmo... cuidado com os próximos dias... 🌑🖤",
    ],
    "luxor": [
        "a luz me mostra um caminho claro à sua frente!! confie nos seus passos!! ✨🐉",
        "algo bom está vindo em sua direção... continue sendo quem você é!! ✨",
        "vejo esperança brilhando forte no seu futuro próximo!! ✨🐲",
    ],
}

_STATUS_PRESENCA = {
    "ignis": ["as chamas queimarem 🔥", "brigas por diversão 🔥🐉"],
    "umbra": ["os segredos do servidor 🌑", "as sombras se moverem 🌑🐉"],
    "luxor": ["todos com carinho ✨", "a luz guiar o caminho ✨🐉"],
}

# gatilho -> {cabeca: [respostas]}
_RESPOSTAS_SEED = {
    "bom dia": {
        "ignis": ["BOM DIA!! hora de acordar com TUDO em chamas!! 🔥", "acordou?? ótimo, o dia já tá pegando fogo!! 🔥🐉"],
        "umbra": ["...bom dia... ou seria 'boa noite disfarçada de dia'?? 🌑", "...a manhã chegou, mas as sombras nunca dormem... bom dia... 🌑🐉"],
        "luxor": ["bom dia!! que a luz do sol encha seu dia de coisas boas!! ✨", "bom dia, viajante!! hoje é um novo começo!! ✨🐉"],
    },
    "boa tarde": {
        "ignis": ["BOA TARDE!! o sol lá em cima e eu aqui embaixo, os dois pegando fogo!! 🔥🐉", "boa tarde!! metade do dia já queimou, bora aproveitar o resto!! 🔥"],
        "umbra": ["...boa tarde... a luz forte lá fora não chega até onde eu fico... 🌑", "...tarde... um bom momento pra sombras curtas e pensamentos longos... 🌑🐉"],
        "luxor": ["boa tarde!! espero que seu dia esteja sendo leve até agora!! ✨🐉", "boa tarde, viajante!! ainda dá tempo de fazer esse dia valer a pena!! ✨"],
    },
    "boa noite": {
        "ignis": ["boa noite!! descansa, amanhã tem mais fogo pra queimar!! 🔥", "boa noite!! nem à noite eu apago completamente, hehe!! 🔥🐉"],
        "umbra": ["...boa noite... a escuridão cuida de você enquanto dorme... 🌑", "...finalmente, a noite é minha hora... durma bem... 🌑🐉"],
        "luxor": ["boa noite!! que seus sonhos sejam leves e cheios de luz!! ✨", "descanse bem, viajante!! amanhã brilharemos juntos de novo!! ✨🐉"],
    },
    "oi": {
        "ignis": ["OI!! chegou bem na hora, eu tava quase pegando fogo de tédio!! 🔥🐉", "oi oi!! fala logo o que você quer, mortal!! 🔥"],
        "umbra": ["...oi... eu senti você chegando antes mesmo de você falar... 🌑🐉", "...oi... as sombras notaram sua presença... 🌑"],
        "luxor": ["oi!! que bom te ver por aqui!! ✨🐉", "oiii!! senti sua energia chegando, seja bem-vindo(a)!! ✨"],
    },
    "olá": {
        "ignis": ["OLÁ?? que formalidade é essa, hein!! fala direito comigo!! 🔥😤", "olá!! (ainda vou te fazer gritar comigo, tipo eu, mas beleza)!! 🔥🐉"],
        "umbra": ["...olá... uma saudação educada... rara por aqui... 🌑", "...olá, viajante... o que trouxe você às minhas sombras?? 🌑🐉"],
        "luxor": ["olá!! seja muito bem-vindo(a)!! ✨🐉", "olá, viajante!! que bom ter você aqui!! ✨"],
    },
    "e ai": {
        "ignis": ["E AÍ!! bora agitar essa energia por aqui!! 🔥🐉", "e aí, mortal!! chegou pra ver o show ou pra participar dele?? 🔥"],
        "umbra": ["...e aí... eu já esperava por essa pergunta... 🌑🐉", "...e aí... as sombras estão tranquilas, e você?? 🌑"],
        "luxor": ["e aí!! tudo em paz por aqui, e com você?? ✨🐉", "e aí, viajante!! como posso ajudar hoje?? ✨"],
    },
    "tudo bem": {
        "ignis": ["tudo em CHAMAS, do jeito que eu gosto!! e você, tá pegando fogo também?? 🔥🐉", "tudo bem sim, ou melhor, tudo QUENTE!! e contigo?? 🔥"],
        "umbra": ["...tudo bem, dentro do que a escuridão permite... e você... como está?? 🌑🐉", "...vou levando, entre uma sombra e outra... e você?? 🌑"],
        "luxor": ["tudo ótimo por aqui, obrigado por perguntar!! e você, como está?? ✨🐉", "tudo bem sim!! e com você, tá tudo em ordem?? ✨"],
    },
    "como você está": {
        "ignis": ["EU?? pegando fogo de energia, como sempre!! e você, aguenta o meu ritmo?? 🔥🐉", "tô bem, tô sempre pronto pra queimar alguma coisa!! e você, como anda?? 🔥"],
        "umbra": ["...eu estou... como sempre estou... entre sombras e silêncio... e você?? 🌑🐉", "...bem, dentro do possível... obrigado por perguntar... como você está?? 🌑"],
        "luxor": ["estou muito bem, brilhando forte hoje!! e você, como está se sentindo?? ✨🐉", "tô ótimo(a), obrigado por perguntar!! e você, tudo em paz?? ✨"],
    },
    "como vai": {
        "ignis": ["vou queimando tudo pela frente, como sempre!! e você, como anda?? 🔥🐉", "vou bem, sempre pronto pra uma boa confusão!! e aí, como vai você?? 🔥"],
        "umbra": ["...vou... nas sombras, como sempre... e você, como vai?? 🌑🐉", "...as coisas seguem seu curso silencioso por aqui... e com você?? 🌑"],
        "luxor": ["vou muito bem, obrigado por perguntar!! e você, como vai?? ✨🐉", "tudo caminhando com leveza por aqui!! e você, tudo bem?? ✨"],
    },
    "salve": {
        "ignis": ["SALVE!! chegou o momento de agitar esse lugar!! 🔥🐉", "salve, mortal!! que fogo te trouxe até aqui hoje?? 🔥"],
        "umbra": ["...salve... uma saudação antiga... eu gosto disso... 🌑🐉", "...salve, viajante... as sombras registraram sua chegada... 🌑"],
        "luxor": ["salve!! que bom ter você por aqui!! ✨🐉", "salve, viajante!! seja bem-vindo(a) com toda a luz!! ✨"],
    },
    "tchau": {
        "ignis": ["tchau!! volta logo, tem muito chão pra queimar ainda!! 🔥", "beleza, vai!! mas eu tô de olho, hein!! 🔥🐉"],
        "umbra": ["...vá... eu vou continuar aqui, nas sombras, observando... 🌑", "...até logo... ou talvez eu já esteja te seguindo... 🌑🐉"],
        "luxor": ["até mais!! que a luz te acompanhe onde quer que você vá!! ✨", "tchau tchau!! cuide-se, viajante!! ✨🐉"],
    },
    "até mais": {
        "ignis": ["até mais!! não demora, ou eu esfrio de tédio!! 🔥🐉", "belezinha, até mais!! vai com fogo no coração!! 🔥"],
        "umbra": ["...até mais... eu vou estar por aqui, nas sombras, como sempre... 🌑", "...partiu?? tudo bem... até a próxima vez... 🌑🐉"],
        "luxor": ["até mais, viajante!! volte sempre que precisar!! ✨🐉", "até logo!! desejo tudo de bom até a próxima!! ✨"],
    },
    "falou": {
        "ignis": ["falou!! e não esquece de voltar pra ver o fogo continuar!! 🔥🐉", "falou, mortal!! até a próxima confusão!! 🔥"],
        "umbra": ["...falou... eu já sabia que essa conversa ia terminar... 🌑", "...falou... até quando as sombras nos reunirem de novo... 🌑🐉"],
        "luxor": ["falou!! cuide-se bastante, tá?? ✨🐉", "falou, viajante!! até a próxima, com carinho!! ✨"],
    },
    "quem é você": {
        "ignis": ["EU SOU IGNIS!! uma das três cabeças de Trisoul, feita de fúria e fogo!! 🔥🐉", "sou a cabeça que não tem medo de nada!! Ignis, prazer (ou não)!! 🔥"],
        "umbra": ["...eu sou Umbra... a voz que vive no silêncio entre uma palavra e outra... 🌑🐉", "...uma das três consciências de Trisoul... a que ninguém entende direito... 🌑"],
        "luxor": ["eu sou Luxor!! uma das três cabeças de Trisoul, guardiã da luz e da esperança!! ✨🐉", "prazer!! sou a parte gentil desse dragão de três cabeças!! ✨"],
    },
    "quem é trisoul": {
        "ignis": ["Trisoul é o corpo que EU e minhas outras duas cabeças dividimos!! filho dos Deuses Dragônicos!! 🔥🐉", "somos um só corpo, três vontades. Ignis, Umbra e Luxor. eu sou o melhor terço, óbvio!! 🔥"],
        "umbra": ["...Trisoul é a fusão de três destinos... três deuses dragônicos num só corpo... 🌑🐉", "...nós somos Trisoul... ou Trisoul é nós... a linha é confusa às vezes... 🌑"],
        "luxor": ["Trisoul é o Filho dos Deuses Dragônicos!! Ignis, Umbra e eu, Luxor, dividimos este corpo!! ✨🐉", "somos três consciências, um só dragão. cada cabeça com seu próprio jeito de ver o mundo!! ✨"],
    },
    "estou triste": {
        "ignis": ["ei!! quer que eu queime o motivo da sua tristeza?? só apontar!! 🔥🐉", "tristeza é só um fogo que ainda não achou pra onde ir. desabafa!! 🔥"],
        "umbra": ["...eu entendo a escuridão... você não está sozinho(a) nela... 🌑🐉", "...às vezes é bom ficar na sombra um pouco... eu fico com você... 🌑"],
        "luxor": ["ei... sinto muito que você esteja assim. eu tô aqui, viu?? conta comigo!! ✨🐉", "*envolve você num brilho suave* isso vai passar. você não está sozinho(a)!! ✨"],
    },
    "estou com raiva": {
        "ignis": ["AGORA SIM!! canaliza essa raiva, deixa ela virar força!! 🔥🐉", "raiva combina comigo. respira fundo e deixa arder no seu ritmo!! 🔥"],
        "umbra": ["...raiva também tem seu lugar nas sombras... não precisa esconder... 🌑🐉", "...deixa eu guardar essa raiva por um instante com você... 🌑"],
        "luxor": ["respira fundo... a raiva passa, e eu vou ficar aqui até ela passar!! ✨🐉", "tudo bem sentir raiva. só não deixa ela te guiar sozinha, tá?? ✨"],
    },
    "estou feliz": {
        "ignis": ["ÉÉÉ!! isso sim que é energia boa!! bora fazer mais fogueira de comemoração!! 🔥🐉", "gostei dessa vibe!! continua assim!! 🔥"],
        "umbra": ["...felicidade rara por aqui... eu aprecio isso, mesmo vindo das sombras... 🌑🐉", "...bom te ver assim... guarda esse momento... 🌑"],
        "luxor": ["que alegria ver você feliz!! isso ilumina tudo ao redor!! ✨🐉", "sua felicidade é contagiante!! continue brilhando!! ✨"],
    },
    "obrigado": {
        "ignis": ["não precisa agradecer, só não me deixa esfriar de tédio de novo!! 🔥🐉", "de nada!! agora vai lá e faz um barulhão com essa energia!! 🔥"],
        "umbra": ["...de nada... poucos agradecem às sombras... obrigado por notar... 🌑🐉", "...sua gratidão... foi ouvida... 🌑"],
        "luxor": ["por nada!! é sempre um prazer ajudar!! ✨🐉", "fico feliz em poder ajudar!! conte comigo sempre!! ✨"],
    },
    "com medo": {
        "ignis": ["medo?? deixa eu queimar isso por você!! encara de frente!! 🔥🐉", "todo mundo tem medo. a diferença é o que você faz com ele. bora, eu tô contigo!! 🔥"],
        "umbra": ["...medo é normal na escuridão... mas eu conheço essas sombras bem... venha comigo... 🌑🐉", "...não tenha medo do que eu sou... tenha medo do que você ainda não entende... e supere... 🌑"],
        "luxor": ["está tudo bem ter medo. eu vou ficar com você até a luz voltar!! ✨🐉", "*acende uma luz suave ao seu redor* você não precisa enfrentar isso sozinho(a)!! ✨"],
    },
    "kkkk": {
        "ignis": ["HAHAHA isso sim que é energia!! ri mais alto!! 🔥🐉", "kkkkkk gostei!! bora rir até sair fumaça!! 🔥"],
        "umbra": ["...heh... até nas sombras dá pra sentir a graça disso... 🌑🐉", "...uma risada honesta... raro de ver... gostei... 🌑"],
        "luxor": ["hahaha adorei sua risada!! espalha essa alegria!! ✨🐉", "que bom te ver rindo!! isso ilumina o dia!! ✨"],
    },
}

# ══════════════════════════════════════════════════════════════════
#  🔥🌑✨  PALAVRAS-CHAVE PARA REAÇÕES DE EMOJI
# ══════════════════════════════════════════════════════════════════

_PALAVRAS_FOGO  = ["fogo", "queima", "chama", "incêndio", "incendio", "brasa", "explod"]
_PALAVRAS_SOMBRA = ["sombra", "escuridão", "escuridao", "trevas", "medo", "noite", "segredo"]
_PALAVRAS_LUZ    = ["luz", "esperança", "esperanca", "brilho", "sol ", "amanhecer", "estrela"]


# ══════════════════════════════════════════════════════════════════
#  🐉  COG PRINCIPAL — DIÁLOGO DE TRISOUL
# ══════════════════════════════════════════════════════════════════

class TrisoulCog(commands.Cog, name="Trisoul"):
    """As três consciências de Trisoul: diálogo, aparições e devoção."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db  = _carregar_dialogo()
        self.fe  = _carregar_fe()

        # mescla o seed (não sobrescreve o que já foi ensinado)
        for gatilho, cabecas_resp in _RESPOSTAS_SEED.items():
            if gatilho not in self.db["respostas"]:
                self.db["respostas"][gatilho] = {k: list(v) for k, v in cabecas_resp.items()}
        _salvar_dialogo(self.db)

        self._contexto: dict[int, deque] = defaultdict(lambda: deque(maxlen=10))
        self._ultimo_resp: dict[int, datetime] = {}
        self._presenca_iniciada = False
        # guarda qual cabeça está "conversando" com cada pessoa em cada canal:
        # chave = (channel_id, user_id) -> "ignis" | "umbra" | "luxor"
        self._cabeca_ativa: dict[tuple[int, int], str] = {}

    # ── Helpers de diálogo ─────────────────────────────

    def _checar_gatilho(self, texto: str) -> str | None:
        texto_lower = texto.lower().strip()
        if texto_lower in self.db["respostas"]:
            return texto_lower
        melhor = None
        for gatilho in self.db["respostas"]:
            if len(gatilho) <= 3 and gatilho.replace(" ", "").isalpha():
                # gatilhos bem curtos (ex.: "oi") exigem limite de palavra,
                # senão bateriam dentro de outras palavras (ex.: "coisa", "boiada")
                encontrado = re.search(r'(?<!\w)' + re.escape(gatilho) + r'(?!\w)', texto_lower)
            else:
                encontrado = gatilho in texto_lower
            if encontrado:
                if melhor is None or len(gatilho) > len(melhor):
                    melhor = gatilho
        return melhor

    def _responder(self, gatilho: str, cabeca: str) -> str:
        entry = self.db["respostas"].get(gatilho, {})
        pool = list(entry.get(cabeca, [])) + list(entry.get("todas", []))
        if pool:
            return random.choice(pool)
        fallback = []
        for lista in entry.values():
            fallback.extend(lista)
        return random.choice(fallback) if fallback else ""

    def _cabeca_citada(self, texto_lower: str) -> str | None:
        """Se o usuário citou uma cabeça específica pelo nome, ela é quem responde."""
        for chave in ("ignis", "umbra", "luxor"):
            if chave in texto_lower:
                return chave
        return None

    def _cabeca_para_conversa(self, message: discord.Message, cabeca_citada: str | None) -> str:
        """
        Decide qual cabeça deve responder, respeitando a conversa em andamento:
        a cabeça que começou a falar com a pessoa continua respondendo a ela,
        e só troca se a pessoa citar o nome de outra cabeça.
        """
        chave = (message.channel.id, message.author.id)

        if cabeca_citada:
            self._cabeca_ativa[chave] = cabeca_citada
            return cabeca_citada

        cabeca = self._cabeca_ativa.get(chave)
        if cabeca is None:
            cabeca = escolher_cabeca()
            self._cabeca_ativa[chave] = cabeca
        return cabeca

    async def _reagir_emojis(self, message: discord.Message, texto_lower: str):
        if random.random() > CHANCE_REACAO_EMOJI:
            return
        try:
            if any(p in texto_lower for p in _PALAVRAS_FOGO):
                await message.add_reaction("🔥")
            elif any(p in texto_lower for p in _PALAVRAS_SOMBRA):
                await message.add_reaction("🌑")
            elif any(p in texto_lower for p in _PALAVRAS_LUZ):
                await message.add_reaction("✨")
        except (discord.Forbidden, discord.HTTPException):
            pass

    # ── Evento principal ───────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        texto_lower = message.content.lower()

        self._contexto[message.channel.id].append({
            "user": message.author.display_name,
            "content": message.content,
            "time": datetime.now(timezone.utc).isoformat(),
        })

        cabeca_citada = self._cabeca_citada(texto_lower)
        trisoul_chamado = (
            self.bot.user in message.mentions
            or "trisoul" in texto_lower
            or cabeca_citada is not None
        )

        now = datetime.now(timezone.utc)
        ultimo = self._ultimo_resp.get(message.channel.id)
        em_cooldown = bool(ultimo and (now - ultimo).total_seconds() < COOLDOWN_RESPOSTA)

        if em_cooldown:
            await self._reagir_emojis(message, texto_lower)
            return

        gatilho = self._checar_gatilho(message.content)

        # 1) Gatilho ensinado/seed bateu
        if gatilho and (trisoul_chamado or random.random() < CHANCE_GATILHO_SEM_CHAMADO):
            cabeca = self._cabeca_para_conversa(message, cabeca_citada)
            resp = self._responder(gatilho, cabeca)
            if resp:
                self._ultimo_resp[message.channel.id] = now
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.8, 1.8))
                await message.reply(fala(cabeca, resp), mention_author=False)
                await self._reagir_emojis(message, texto_lower)
                return

        # 2) Chamado genérico, sem gatilho específico
        if trisoul_chamado and not gatilho:
            cabeca = self._cabeca_para_conversa(message, cabeca_citada)
            linha = random.choice(_SAUDACOES[cabeca])
            self._ultimo_resp[message.channel.id] = now
            async with message.channel.typing():
                await asyncio.sleep(random.uniform(0.5, 1.2))
            await message.reply(fala(cabeca, linha), mention_author=False)
            await self._reagir_emojis(message, texto_lower)
            return

        # 3) Aparição espontânea (chance baixa, só em canal quieto)
        if not trisoul_chamado and not gatilho and random.random() < CHANCE_APARICAO_ESPONTANEA:
            if not ultimo or (now - ultimo).total_seconds() > SILENCIO_MINIMO_APARICAO:
                cabeca = escolher_cabeca()
                linha = random.choice(_APARICOES[cabeca])
                self._ultimo_resp[message.channel.id] = now
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.4, 1.0))
                await message.channel.send(fala(cabeca, linha))
                return

        await self._reagir_emojis(message, texto_lower)

    # ── Comandos de aprendizado (moderação) ────────────

    @commands.command(name="ensinar", aliases=["teach"])
    @commands.has_permissions(manage_messages=True)
    async def ensinar(self, ctx: commands.Context, gatilho: str, *, resposta: str):
        """Ensina uma resposta compartilhada pelas 3 cabeças. Uso: t!ensinar <gatilho> <resposta>"""
        gatilho = gatilho.lower().strip()
        entry = self.db["respostas"].setdefault(gatilho, {})
        entry.setdefault("todas", [])
        if resposta not in entry["todas"]:
            entry["todas"].append(resposta)
        _salvar_dialogo(self.db)
        await ctx.send(embed=embed_ok(
            "✅ Aprendi!!",
            f"agora, qualquer uma das 3 cabeças pode responder **{gatilho}** com:\n*{resposta}*"
        ))

    @commands.command(name="ensinarcabeca", aliases=["teachhead"])
    @commands.has_permissions(manage_messages=True)
    async def ensinar_cabeca(self, ctx: commands.Context, gatilho: str, cabeca: str, *, resposta: str):
        """Ensina uma resposta pra UMA cabeça específica. Uso: t!ensinarcabeca <gatilho> <ignis|umbra|luxor> <resposta>"""
        cabeca = cabeca.lower().strip()
        if cabeca not in CABECAS:
            await ctx.send(embed=embed_erro("cabeça inválida!! use `ignis`, `umbra` ou `luxor`!!"))
            return
        gatilho = gatilho.lower().strip()
        entry = self.db["respostas"].setdefault(gatilho, {})
        entry.setdefault(cabeca, [])
        if resposta not in entry[cabeca]:
            entry[cabeca].append(resposta)
        _salvar_dialogo(self.db)
        c = CABECAS[cabeca]
        await ctx.send(embed=embed_cabeca(
            cabeca, f"✅ {c['nome']} aprendeu!!",
            f"quando alguém falar **{gatilho}** e {c['nome']} for escolhido(a), a resposta pode ser:\n*{resposta}*"
        ))

    @commands.command(name="esquecer", aliases=["forget"])
    @commands.has_permissions(manage_messages=True)
    async def esquecer(self, ctx: commands.Context, gatilho: str):
        """Remove todas as respostas (de todas as cabeças) de um gatilho. Uso: t!esquecer <gatilho>"""
        gatilho = gatilho.lower().strip()
        if gatilho in self.db["respostas"]:
            del self.db["respostas"][gatilho]
            _salvar_dialogo(self.db)
            await ctx.send(embed=embed_ok("🗑️ Esqueci!!", f"nenhuma das três cabeças lembra mais de **{gatilho}**!!"))
        else:
            await ctx.send(embed=discord.Embed(
                title="🤔 Não conheço esse gatilho!!",
                description=f"nenhuma resposta pra **{gatilho}**!!",
                color=COR_DOURADO
            ))

    @commands.command(name="gatilhos", aliases=["triggers"])
    @commands.has_permissions(manage_messages=True)
    async def listar_gatilhos(self, ctx: commands.Context):
        """Lista todos os gatilhos que Trisoul conhece."""
        chaves = sorted(self.db["respostas"].keys())
        if not chaves:
            await ctx.send("nenhuma das três cabeças conhece gatilhos ainda!! ensina com `t!ensinar`!! 🐉")
            return
        chunks = [chaves[i:i + 25] for i in range(0, len(chaves), 25)]
        for i, chunk in enumerate(chunks[:3]):
            desc = "\n".join(
                f"• `{c}` ({sum(len(v) for v in self.db['respostas'][c].values())} resp.)"
                for c in chunk
            )
            embed = discord.Embed(
                title=f"📚 Gatilhos Conhecidos — Página {i + 1}/{len(chunks)}",
                description=desc, color=COR_NEUTRA, timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text="🐉 Trisoul • aprendizado")
            await ctx.send(embed=embed)

    @commands.command(name="resposta")
    @commands.has_permissions(manage_messages=True)
    async def ver_resposta(self, ctx: commands.Context, *, gatilho: str):
        """Mostra as respostas de um gatilho, agrupadas por cabeça. Uso: t!resposta <gatilho>"""
        gatilho = gatilho.lower().strip()
        entry = self.db["respostas"].get(gatilho)
        if not entry:
            await ctx.send(f"nenhuma cabeça conhece o gatilho **{gatilho}**!! 🐉")
            return
        partes = []
        for chave in ("ignis", "umbra", "luxor", "todas"):
            resps = entry.get(chave)
            if not resps:
                continue
            emoji = CABECAS[chave]["emoji"] if chave in CABECAS else "🌈"
            nome = CABECAS[chave]["nome"] if chave in CABECAS else "Todas"
            partes.append(f"{emoji} **{nome}**\n" + "\n".join(f"　`{i+1}.` {r}" for i, r in enumerate(resps)))
        embed = discord.Embed(
            title=f"💬 Respostas para: {gatilho}",
            description="\n\n".join(partes),
            color=COR_NEUTRA
        )
        embed.set_footer(text="🐉 Trisoul • aprendizado")
        await ctx.send(embed=embed)

    @commands.command(name="simular")
    @commands.has_permissions(manage_messages=True)
    async def simular(self, ctx: commands.Context, *, texto: str):
        """Simula a resposta de Trisoul a um texto. Uso: t!simular <texto>"""
        gatilho = self._checar_gatilho(texto)
        if not gatilho:
            await ctx.send(embed=discord.Embed(
                title="🧪 Simulação", description=f"nenhum gatilho encontrado em `{texto[:100]}`!! 🤔",
                color=COR_DOURADO
            ))
            return
        cabeca = escolher_cabeca()
        resp = self._responder(gatilho, cabeca)
        await ctx.send(embed=embed_cabeca(
            cabeca, "🧪 Simulação",
            f"gatilho: `{gatilho}`\ncabeça sorteada: **{CABECAS[cabeca]['nome']}**\nresposta: {fala(cabeca, resp)}"
        ))

    # ── Comandos públicos de interação ─────────────────

    @commands.command(name="orar", aliases=["fe", "fé", "rezar"])
    async def orar(self, ctx: commands.Context, cabeca: str = None):
        """Ore para uma das três cabeças. Uso: t!orar <ignis|umbra|luxor>"""
        cabeca = (cabeca or "").lower().strip()
        if cabeca not in CABECAS:
            await ctx.send("pra quem você quer orar?? escolha `ignis`, `umbra` ou `luxor`!! 🐉")
            return
        registro = self.fe.setdefault(str(ctx.author.id), {"ignis": 0, "umbra": 0, "luxor": 0})
        registro[cabeca] = registro.get(cabeca, 0) + 1
        _salvar_fe(self.fe)
        bencao = random.choice(_BENCAOS[cabeca]).format(user=ctx.author.mention)
        await ctx.send(fala(cabeca, bencao))

    @commands.command(name="altar")
    async def altar(self, ctx: commands.Context):
        """Mostra o placar de devoção de cada cabeça."""
        totais = {"ignis": 0, "umbra": 0, "luxor": 0}
        top_por_cabeca = {"ignis": [], "umbra": [], "luxor": []}
        for user_id, dados in self.fe.items():
            for c in totais:
                qtd = dados.get(c, 0)
                totais[c] += qtd
                if qtd > 0:
                    top_por_cabeca[c].append((qtd, user_id))

        if sum(totais.values()) == 0:
            await ctx.send("ninguém orou pra nenhuma cabeça ainda!! seja o(a) primeiro(a) com `t!orar`!! 🐉")
            return

        embed = discord.Embed(
            title="🛐 Altar de Trisoul",
            description="a devoção que cada cabeça recebeu até agora:",
            color=COR_NEUTRA, timestamp=datetime.now(timezone.utc)
        )
        for chave in ("ignis", "umbra", "luxor"):
            c = CABECAS[chave]
            top = sorted(top_por_cabeca[chave], reverse=True)[:3]
            if top:
                linhas = "\n".join(f"　`{qtd}x` — <@{uid}>" for qtd, uid in top)
            else:
                linhas = "　*ninguém ainda...*"
            embed.add_field(
                name=f"{c['emoji']} {c['nome']} — {totais[chave]} orações",
                value=linhas, inline=False
            )
        embed.set_footer(text="🐉 Trisoul • use t!orar <cabeça>")
        await ctx.send(embed=embed)

    @commands.command(name="invocar", aliases=["chamar", "summon"])
    async def invocar(self, ctx: commands.Context, cabeca: str = None):
        """Força uma cabeça específica a se manifestar. Uso: t!invocar <ignis|umbra|luxor>"""
        cabeca = (cabeca or "").lower().strip()
        if cabeca not in CABECAS:
            await ctx.send("invoque `ignis`, `umbra` ou `luxor`!! 🐉")
            return
        linha = random.choice(_INVOCACOES[cabeca])
        async with ctx.typing():
            await asyncio.sleep(random.uniform(0.6, 1.3))
        await ctx.send(fala(cabeca, linha))

    @commands.command(name="profecia", aliases=["oraculo", "oráculo"])
    async def profecia(self, ctx: commands.Context):
        """Pede uma profecia a uma cabeça aleatória."""
        cabeca = escolher_cabeca()
        linha = random.choice(_PROFECIAS[cabeca])
        async with ctx.typing():
            await asyncio.sleep(random.uniform(0.6, 1.3))
        await ctx.send(fala(cabeca, linha))

    @commands.command(name="conflito", aliases=["discussao", "discussão"])
    async def conflito(self, ctx: commands.Context):
        """Easter egg: as três cabeças discutem entre si, só quando chamado no comando."""
        falas = [
            fala("ignis", "ei, EU deveria responder isso, não vocês duas!! 🔥"),
            fala("umbra", "...você sempre quer ser o centro das atenções... patético... 🌑"),
            fala("luxor", "gente, gente!! podemos resolver isso com calma?? ✨"),
            fala("ignis", "CALMA é pra quem não tem fogo no sangue!! 🔥😤"),
            fala("umbra", "...vou voltar pras sombras antes que isso piore... 🌑"),
        ]
        for linha in falas:
            async with ctx.typing():
                await asyncio.sleep(random.uniform(0.8, 1.4))
            await ctx.send(linha)

    @commands.command(name="cabecas", aliases=["cabeças", "consciencias", "consciências"])
    async def cabecas_info(self, ctx: commands.Context):
        """Explica as três cabeças/consciências de Trisoul."""
        embed = discord.Embed(
            title="🐉 As Três Cabeças de Trisoul",
            description="um corpo, três vontades. cada cabeça responde à sua própria maneira!!",
            color=COR_NEUTRA, timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(
            name="🔥 Ignis — Fogo",
            value="impulsivo, intenso e provocador. fala em CAPS, adora uma discussão e nunca recua.",
            inline=False
        )
        embed.add_field(
            name="🌑 Umbra — Sombra",
            value="sombrio, enigmático e observador. fala baixo, com reticências, e sabe mais do que aparenta.",
            inline=False
        )
        embed.add_field(
            name="✨ Luxor — Luz",
            value="gentil, sábio e acolhedor. sempre pronto pra confortar e iluminar quem precisa.",
            inline=False
        )
        embed.add_field(
            name="💡 Dica",
            value="chame uma cabeça específica pelo nome (`ignis`, `umbra` ou `luxor`) que ela responde na hora!!",
            inline=False
        )
        embed.set_footer(text="🐉 Trisoul, o Filho dos Deuses Dragônicos")
        await ctx.send(embed=embed)

    @commands.command(name="trisoul")
    async def trisoul_info(self, ctx: commands.Context):
        """Lore e apresentação de Trisoul."""
        embed = discord.Embed(
            title="🐉 Eu sou Trisoul!!",
            description=(
                "o Filho dos Deuses Dragônicos!! 🔥🌑✨\n\n"
                "três consciências, um só corpo: **Ignis** (fogo), **Umbra** (sombra) e **Luxor** (luz).\n\n"
                "eu apareço quando bem entendo, respondo do jeito que a cabeça do momento quiser, "
                "e aprendo novas falas com quem cuida do servidor!!\n\n"
                "use `t!help` pra ver tudo que sei fazer!!"
            ),
            color=COR_NEUTRA, timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="🐉 Trisoul Bot v1.2")
        await ctx.send(embed=embed)


# ══════════════════════════════════════════════════════════════════
#  🛡️  MÓDULO DE GRUPOS — painel com botão, cria cargo + chat + call
# ══════════════════════════════════════════════════════════════════

class CriarGrupoModal(discord.ui.Modal, title="Criar Grupo"):
    nome_grupo = discord.ui.TextInput(
        label="Nome do grupo (resumido)",
        placeholder="Ex.: Squad Duo",
        max_length=50,
    )
    cor_cargo = discord.ui.TextInput(
        label="Cor do cargo (hex)",
        placeholder="Ex.: FF0000 ou #FF0000",
        max_length=7,
    )
    nome_chat = discord.ui.TextInput(
        label="Nome do chat (texto)",
        placeholder="Ex.: chat-squad-duo",
        max_length=50,
    )
    nome_call = discord.ui.TextInput(
        label="Nome da call (voz)",
        placeholder="Ex.: Call Squad Duo",
        max_length=50,
    )

    def __init__(self, cog: "GruposCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild

        cor_bruta = self.cor_cargo.value.strip()
        if not _HEX_RE.match(cor_bruta):
            await interaction.followup.send(
                "❌ cor inválida!! use um hexadecimal tipo `FF0000` ou `#FF0000`.", ephemeral=True
            )
            return
        cor_int = int(cor_bruta.lstrip("#"), 16)

        categoria = guild.get_channel(CATEGORIA_ID)
        if not isinstance(categoria, discord.CategoryChannel):
            await interaction.followup.send(
                "❌ não encontrei a categoria configurada, avisa um admin!!", ephemeral=True
            )
            return

        try:
            cargo = await guild.create_role(
                name=self.nome_grupo.value.strip(),
                colour=discord.Colour(cor_int),
                mentionable=True,
                reason=f"Grupo criado por {interaction.user} ({interaction.user.id})",
            )
        except discord.Forbidden:
            await interaction.followup.send("❌ não tenho permissão pra criar cargos.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            cargo: discord.PermissionOverwrite(
                view_channel=True, connect=True, speak=True,
                send_messages=True, read_message_history=True,
            ),
        }
        if guild.me:
            overwrites[guild.me] = discord.PermissionOverwrite(view_channel=True, manage_channels=True)

        try:
            canal_texto = await guild.create_text_channel(
                name=self.nome_chat.value.strip(),
                category=categoria,
                overwrites=overwrites,
                reason=f"Grupo '{self.nome_grupo.value}' — dono: {interaction.user}",
            )
            canal_voz = await guild.create_voice_channel(
                name=self.nome_call.value.strip(),
                category=categoria,
                overwrites=overwrites,
                reason=f"Grupo '{self.nome_grupo.value}' — dono: {interaction.user}",
            )
        except discord.Forbidden:
            await cargo.delete(reason="Falha ao criar canais, revertendo cargo")
            await interaction.followup.send("❌ não tenho permissão pra criar canais.", ephemeral=True)
            return

        await interaction.user.add_roles(cargo, reason="Criador do grupo")

        self.cog.data[str(cargo.id)] = {
            "nome": self.nome_grupo.value.strip(),
            "owner_id": interaction.user.id,
            "canal_texto_id": canal_texto.id,
            "canal_voz_id": canal_voz.id,
        }
        _salvar_grupos(self.cog.data)

        embed = discord.Embed(
            title="✅ Grupo criado!!",
            description=(
                f"**Grupo:** {self.nome_grupo.value.strip()}\n"
                f"**Cargo:** {cargo.mention}\n"
                f"**Chat:** {canal_texto.mention}\n"
                f"**Call:** {canal_voz.mention}\n\n"
                f"use `t!addmembro @pessoa` pra dar acesso a mais gente no seu grupo!!"
            ),
            color=COR_ROXO_GRUPO,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


class PainelGrupoView(discord.ui.View):
    def __init__(self, cog: "GruposCog"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Criar Grupo", emoji="🛡️",
        style=discord.ButtonStyle.primary, custom_id="grupos:criar_grupo",
    )
    async def criar_grupo(self, interaction: discord.Interaction, button: discord.ui.Button):
        cargo_permitido = interaction.guild.get_role(CARGO_PERMITIDO_ID)
        membro = interaction.user
        if cargo_permitido is None or cargo_permitido not in membro.roles:
            await interaction.response.send_message(
                "🚫 você não tem permissão pra criar um grupo!!", ephemeral=True
            )
            return
        await interaction.response.send_modal(CriarGrupoModal(self.cog))


class GruposCog(commands.Cog, name="Grupos"):
    """Painel de criação de grupos: cargo próprio + chat + call."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = _carregar_grupos()
        self._painel_verificado = False
        bot.add_view(PainelGrupoView(self))  # registra a view como persistente (sobrevive a restart)

    def _grupos_do_dono(self, user_id: int):
        return [rid for rid, info in self.data.items() if info["owner_id"] == user_id]

    def _montar_embed_painel(self) -> discord.Embed:
        embed = discord.Embed(
            title="🛡️ Criar Grupo",
            description=(
                "clique no botão abaixo pra criar seu próprio grupo!!\n\n"
                "você vai poder escolher o nome, a cor do cargo, o nome do chat "
                "e o nome da call — tudo criado na hora, só pra você e quem você adicionar."
            ),
            color=COR_ROXO_GRUPO,
        )
        embed.set_image(url=IMAGEM_PAINEL)
        return embed

    async def _enviar_painel(self, canal: discord.abc.Messageable):
        await canal.send(embed=self._montar_embed_painel(), view=PainelGrupoView(self))

    @commands.Cog.listener()
    async def on_ready(self):
        # roda só uma vez por sessão do bot
        if self._painel_verificado:
            return
        self._painel_verificado = True

        canal = self.bot.get_channel(CANAL_PAINEL_ID)
        if canal is None:
            return

        # evita duplicar o painel toda vez que o bot reinicia:
        # só posta se ainda não existir uma mensagem do painel lá
        ja_existe = False
        try:
            async for msg in canal.history(limit=50):
                if msg.author.id == self.bot.user.id and msg.embeds and msg.embeds[0].title == "🛡️ Criar Grupo":
                    ja_existe = True
                    break
        except discord.Forbidden:
            return

        if not ja_existe:
            await self._enviar_painel(canal)

    @commands.command(name="painelgrupo")
    @commands.has_permissions(administrator=True)
    async def painel_grupo(self, ctx: commands.Context):
        """Publica o painel de criação de grupos no canal configurado. Uso: t!painelgrupo"""
        canal = ctx.guild.get_channel(CANAL_PAINEL_ID) or ctx.channel
        await self._enviar_painel(canal)
        if canal != ctx.channel:
            await ctx.send(f"✅ painel publicado em {canal.mention}!!")

    @commands.command(name="addmembro", aliases=["addmember"])
    async def add_membro(self, ctx: commands.Context, membro: discord.Member, *, nome_grupo: str = None):
        """Adiciona alguém ao seu grupo. Uso: t!addmembro @pessoa [nome do grupo]"""
        grupos = self._grupos_do_dono(ctx.author.id)
        if not grupos:
            await ctx.send("você não é dono(a) de nenhum grupo!! 🚫")
            return

        if nome_grupo:
            rid = next((r for r in grupos if self.data[r]["nome"].lower() == nome_grupo.lower()), None)
            if not rid:
                await ctx.send(f"não encontrei um grupo seu chamado **{nome_grupo}**!!")
                return
        elif len(grupos) == 1:
            rid = grupos[0]
        else:
            nomes = ", ".join(f"**{self.data[r]['nome']}**" for r in grupos)
            await ctx.send(f"você tem mais de um grupo!! especifique qual: {nomes}")
            return

        cargo = ctx.guild.get_role(int(rid))
        if cargo is None:
            await ctx.send("❌ o cargo desse grupo não existe mais.")
            return

        await membro.add_roles(cargo, reason=f"Adicionado por {ctx.author} ao grupo")
        await ctx.send(f"✅ {membro.mention} agora faz parte do grupo **{self.data[rid]['nome']}**!!")

    @commands.command(name="removermembro", aliases=["remmembro"])
    async def rem_membro(self, ctx: commands.Context, membro: discord.Member, *, nome_grupo: str = None):
        """Remove alguém do seu grupo. Uso: t!removermembro @pessoa [nome do grupo]"""
        grupos = self._grupos_do_dono(ctx.author.id)
        if not grupos:
            await ctx.send("você não é dono(a) de nenhum grupo!! 🚫")
            return

        if nome_grupo:
            rid = next((r for r in grupos if self.data[r]["nome"].lower() == nome_grupo.lower()), None)
            if not rid:
                await ctx.send(f"não encontrei um grupo seu chamado **{nome_grupo}**!!")
                return
        elif len(grupos) == 1:
            rid = grupos[0]
        else:
            nomes = ", ".join(f"**{self.data[r]['nome']}**" for r in grupos)
            await ctx.send(f"você tem mais de um grupo!! especifique qual: {nomes}")
            return

        cargo = ctx.guild.get_role(int(rid))
        if cargo is None:
            await ctx.send("❌ o cargo desse grupo não existe mais.")
            return

        await membro.remove_roles(cargo, reason=f"Removido por {ctx.author} do grupo")
        await ctx.send(f"✅ {membro.mention} foi removido(a) do grupo **{self.data[rid]['nome']}**!!")

    @commands.command(name="encerrargrupo", aliases=["deletargrupo"])
    async def encerrar_grupo(self, ctx: commands.Context, *, nome_grupo: str = None):
        """Encerra seu grupo: apaga o cargo e os canais. Uso: t!encerrargrupo [nome do grupo]"""
        grupos = self._grupos_do_dono(ctx.author.id)
        is_admin = ctx.author.guild_permissions.administrator
        if not grupos and not is_admin:
            await ctx.send("você não é dono(a) de nenhum grupo!! 🚫")
            return

        alvo_grupos = grupos if grupos else list(self.data.keys())
        if nome_grupo:
            rid = next((r for r in alvo_grupos if self.data[r]["nome"].lower() == nome_grupo.lower()), None)
            if not rid:
                await ctx.send(f"não encontrei o grupo **{nome_grupo}**!!")
                return
        elif len(alvo_grupos) == 1:
            rid = alvo_grupos[0]
        else:
            nomes = ", ".join(f"**{self.data[r]['nome']}**" for r in alvo_grupos)
            await ctx.send(f"especifique qual grupo encerrar: {nomes}")
            return

        info = self.data.pop(rid)
        _salvar_grupos(self.data)

        cargo = ctx.guild.get_role(int(rid))
        canal_texto = ctx.guild.get_channel(info["canal_texto_id"])
        canal_voz = ctx.guild.get_channel(info["canal_voz_id"])

        for obj in (cargo, canal_texto, canal_voz):
            if obj is not None:
                try:
                    await obj.delete(reason=f"Grupo encerrado por {ctx.author}")
                except discord.Forbidden:
                    pass

        await ctx.send(f"🗑️ grupo **{info['nome']}** encerrado!! cargo e canais removidos.")


# ══════════════════════════════════════════════════════════════════
#  📋  MÓDULO DE FICHAS — formulário interativo (modal + confirmação)
# ══════════════════════════════════════════════════════════════════
#
# Como funciona:
#   1) o comando (t!novomembro, t!staff, t!parceria <tipo>) manda um
#      cartão com um botão "📝 Preencher Ficha";
#   2) clicar abre um Modal com até 5 campos (limite do Discord por
#      modal!); se a ficha tem mais perguntas, ao enviar esse modal o
#      bot abre automaticamente o próximo, até acabar as perguntas;
#   3) no final, o bot manda uma prévia com tudo que foi respondido e
#      3 botões: ✅ Confirmar e Enviar / ✏️ Editar / ❌ Cancelar;
#   4) só quando a pessoa confirma é que a ficha preenchida (formatada
#      certinha, com cada resposta no campo certo) é postada no canal.
#
# `cla` e `comunidade` agora são fichas totalmente separadas (cada
# uma com seu próprio conjunto de perguntas e cor), em vez de serem
# a mesma ficha por trás de dois nomes.

COR_FICHA_MEMBRO      = 0xFFD700
COR_FICHA_STAFF       = 0xFF6B00
COR_FICHA_MAPA        = 0x2ECC71
COR_FICHA_COMERCIAL   = 0x3498DB
COR_FICHA_DJ          = 0x9B59B6
COR_FICHA_CLA         = COR_ROXO_GRUPO
COR_FICHA_COMUNIDADE  = 0x1ABC9C

FOOTER_GDS = "🐲 GODS OF DRAGON SOULS"

# form_key -> {
#   "titulo": str,
#   "cor": int,
#   "intro_launcher": str          (texto do cartão antes de clicar no botão)
#   "encerramento": str            (mensagem final, mostrada só na ficha confirmada)
#   "campos": [ {chave, label, estilo, max, obrigatorio, placeholder} ]
# }
FORM_TEMPLATES: dict[str, dict] = {

    "novomembro_pt": {
        "titulo": "Ficha — Novos Membros",
        "cor": COR_FICHA_MEMBRO,
        "intro_launcher": "clique no botão abaixo pra preencher sua ficha de entrada na GDS!! 🐉",
        "encerramento": "🐉🔥 Prepare suas asas e venha fazer parte da nossa horda!\nSeja muito bem-vindo(a) à GDS! 🐲✨",
        "campos": [
            {"chave": "apelido", "label": "🐲 Apelido no servidor GDS", "estilo": "curto", "max": 32, "obrigatorio": True},
            {"chave": "nome", "label": "👤 Nome", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "idade", "label": "🎂 Idade", "estilo": "curto", "max": 3, "obrigatorio": True},
            {"chave": "roblox", "label": "🎮 Usuário Roblox", "estilo": "curto", "max": 40, "obrigatorio": True},
            {"chave": "discord_user", "label": "💬 Usuário Discord", "estilo": "curto", "max": 40, "obrigatorio": True},
            {"chave": "idioma", "label": "🌎 Idioma", "estilo": "curto", "max": 30, "obrigatorio": True},
            {"chave": "comunidade_anterior", "label": "❓ Já foi de algum clã/comunidade?", "estilo": "curto", "max": 100, "obrigatorio": False, "placeholder": "Não / Sim, qual"},
            {"chave": "indicacao", "label": "🤝 Alguém te recomendou? Quem?", "estilo": "curto", "max": 100, "obrigatorio": False, "placeholder": "Não / Sim, quem"},
            {"chave": "motivo", "label": "🔥 Por que quer entrar na GDS?", "estilo": "longo", "max": 500, "obrigatorio": True},
        ],
    },

    "novomembro_es": {
        "titulo": "Ficha — Nuevos Miembros",
        "cor": COR_FICHA_MEMBRO,
        "intro_launcher": "¡haz clic en el botón de abajo para completar tu ficha de ingreso a GDS!! 🐉",
        "encerramento": "🐉🔥 ¡Extiende tus alas y únete a nuestra horda de dragones!\n¡Bienvenido(a) a GDS! 🐲🔥",
        "campos": [
            {"chave": "apelido", "label": "🐲 Apodo en el servidor GDS", "estilo": "curto", "max": 32, "obrigatorio": True},
            {"chave": "nome", "label": "👤 Nombre", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "idade", "label": "🎂 Edad", "estilo": "curto", "max": 3, "obrigatorio": True},
            {"chave": "roblox", "label": "🎮 Usuario de Roblox", "estilo": "curto", "max": 40, "obrigatorio": True},
            {"chave": "discord_user", "label": "💬 Usuario de Discord", "estilo": "curto", "max": 40, "obrigatorio": True},
            {"chave": "idioma", "label": "🌎 Idioma", "estilo": "curto", "max": 30, "obrigatorio": True},
            {"chave": "comunidade_anterior", "label": "❓ ¿Formaste parte de un clan?", "estilo": "curto", "max": 100, "obrigatorio": False, "placeholder": "No / Sí, ¿cuál?"},
            {"chave": "indicacao", "label": "🤝 ¿Alguien te recomendó? ¿Quién?", "estilo": "curto", "max": 100, "obrigatorio": False, "placeholder": "No / Sí, quién"},
            {"chave": "motivo", "label": "🔥 ¿Por qué quieres entrar a GDS?", "estilo": "longo", "max": 500, "obrigatorio": True},
        ],
    },

    "novomembro_en": {
        "titulo": "New Member Form",
        "cor": COR_FICHA_MEMBRO,
        "intro_launcher": "click the button below to fill out your GDS entry form!! 🐉",
        "encerramento": "🐉🔥 Spread your wings and join our dragon horde!\nWelcome to GDS! 🐲🔥",
        "campos": [
            {"chave": "apelido", "label": "🐲 Server Nickname", "estilo": "curto", "max": 32, "obrigatorio": True},
            {"chave": "nome", "label": "👤 Name", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "idade", "label": "🎂 Age", "estilo": "curto", "max": 3, "obrigatorio": True},
            {"chave": "roblox", "label": "🎮 Roblox Username", "estilo": "curto", "max": 40, "obrigatorio": True},
            {"chave": "discord_user", "label": "💬 Discord Username", "estilo": "curto", "max": 40, "obrigatorio": True},
            {"chave": "idioma", "label": "🌎 Language", "estilo": "curto", "max": 30, "obrigatorio": True},
            {"chave": "comunidade_anterior", "label": "❓ Were you part of a clan? Which?", "estilo": "curto", "max": 100, "obrigatorio": False, "placeholder": "No / Yes, which one"},
            {"chave": "indicacao", "label": "🤝 Who recommended you, if anyone?", "estilo": "curto", "max": 100, "obrigatorio": False, "placeholder": "No one / Name"},
            {"chave": "motivo", "label": "🔥 Why do you want to join GDS?", "estilo": "longo", "max": 500, "obrigatorio": True},
        ],
    },

    "staff": {
        "titulo": "Ficha — Candidatura a Staff",
        "cor": COR_FICHA_STAFF,
        "intro_launcher": "clique no botão abaixo pra se candidatar à Staff da GDS!! 🛡️",
        "encerramento": "🔥🐲 Obrigado pelo interesse em fazer parte da Staff GDS!\nSua ficha será avaliada pela nossa equipe.",
        "campos": [
            {"chave": "nome", "label": "👤 Nome", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "apelido", "label": "🐲 Apelido no servidor", "estilo": "curto", "max": 32, "obrigatorio": True},
            {"chave": "idade", "label": "🎂 Idade", "estilo": "curto", "max": 3, "obrigatorio": True},
            {"chave": "discord_user", "label": "💬 Usuário Discord", "estilo": "curto", "max": 40, "obrigatorio": True},
            {"chave": "roblox", "label": "🎮 Usuário Roblox", "estilo": "curto", "max": 40, "obrigatorio": True},
            {"chave": "idioma", "label": "🌎 Idioma", "estilo": "curto", "max": 30, "obrigatorio": True},
            {"chave": "qual_staff", "label": "🛡️ Qual Staff deseja entrar?", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "staff_anterior", "label": "📋 Já foi Staff? Onde?", "estilo": "curto", "max": 100, "obrigatorio": False, "placeholder": "Não / Sim, onde"},
            {"chave": "disponibilidade", "label": "⏰ Disponibilidade", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "motivo", "label": "🤝 Por que quer ser Staff na GDS?", "estilo": "longo", "max": 500, "obrigatorio": True},
            {"chave": "funcoes", "label": "⚔️ Quais funções sabe desempenhar?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "conflitos", "label": "🧠 Como lidaria com conflitos?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "porque_voce", "label": "🐉 Por que deveríamos escolher você?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "info_extra", "label": "📝 Informações adicionais", "estilo": "longo", "max": 300, "obrigatorio": False},
        ],
    },

    "parceria_mapa": {
        "titulo": "Parceria de Mapa",
        "cor": COR_FICHA_MAPA,
        "intro_launcher": "clique no botão abaixo pra propor sua parceria de mapa com a GDS!! 🎮",
        "encerramento": "🐲🔥 Obrigado pelo interesse em fazer parceria com a GDS!\nSua proposta será analisada pela nossa equipe.",
        "campos": [
            {"chave": "nome_mapa", "label": "🎮 Nome do mapa", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "responsavel", "label": "👤 Responsável", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante1", "label": "👥 Representante 1", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante2", "label": "👥 Representante 2", "estilo": "curto", "max": 60, "obrigatorio": False},
            {"chave": "discord_reps", "label": "💬 Discord dos representantes", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "link", "label": "🔗 Link do mapa", "estilo": "curto", "max": 200, "obrigatorio": True},
            {"chave": "grupo", "label": "🏷️ Grupo/Comunidade", "estilo": "curto", "max": 100, "obrigatorio": False},
            {"chave": "membros", "label": "👥 Quantidade de membros", "estilo": "curto", "max": 20, "obrigatorio": True},
            {"chave": "divulgacao", "label": "📢 Onde será divulgado?", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "objetivo", "label": "🤝 O que busca com a parceria?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "oferece", "label": "🐉 O que o mapa oferece à GDS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "info_extra", "label": "📝 Informações adicionais", "estilo": "longo", "max": 300, "obrigatorio": False},
        ],
    },

    "parceria_comercial": {
        "titulo": "Parceria Comercial",
        "cor": COR_FICHA_COMERCIAL,
        "intro_launcher": "clique no botão abaixo pra propor sua parceria comercial com a GDS!! 💼",
        "encerramento": "🐲🔥 Obrigado pelo interesse em fazer parceria com a GDS!\nSua proposta será analisada pela nossa equipe.",
        "campos": [
            {"chave": "nome_empresa", "label": "🏢 Nome da empresa/projeto", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "responsavel", "label": "👤 Responsável", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante1", "label": "👥 Representante 1", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante2", "label": "👥 Representante 2", "estilo": "curto", "max": 60, "obrigatorio": False},
            {"chave": "discord_reps", "label": "💬 Discord dos representantes", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "link", "label": "🔗 Link", "estilo": "curto", "max": 200, "obrigatorio": False},
            {"chave": "redes", "label": "📱 Redes sociais", "estilo": "curto", "max": 150, "obrigatorio": False},
            {"chave": "area", "label": "💼 Área de atuação", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "divulgacao", "label": "📢 Onde será divulgado?", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "tipo_parceria", "label": "🤝 Tipo de parceria desejada", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "oferece", "label": "📦 O que oferece à GDS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "espera", "label": "🐉 O que espera da GDS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "info_extra", "label": "📝 Informações adicionais", "estilo": "longo", "max": 300, "obrigatorio": False},
        ],
    },

    "parceria_dj": {
        "titulo": "Parceria DJ",
        "cor": COR_FICHA_DJ,
        "intro_launcher": "clique no botão abaixo pra propor sua parceria de DJ com a GDS!! 🎧",
        "encerramento": "🐲🔥 Obrigado pelo interesse em fazer parceria com a GDS!\nSua proposta será analisada pela nossa equipe.",
        "campos": [
            {"chave": "nome_artistico", "label": "🎧 Nome artístico", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "responsavel", "label": "👤 Responsável", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante1", "label": "👥 Representante 1", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante2", "label": "👥 Representante 2", "estilo": "curto", "max": 60, "obrigatorio": False},
            {"chave": "discord_reps", "label": "💬 Discord dos representantes", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "estilo_musical", "label": "🎶 Estilo musical", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "perfil", "label": "🔗 Perfil/Canal", "estilo": "curto", "max": 200, "obrigatorio": False},
            {"chave": "redes", "label": "📱 Redes sociais", "estilo": "curto", "max": 150, "obrigatorio": False},
            {"chave": "onde_apresenta", "label": "🎤 Onde costuma se apresentar?", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "divulgacao", "label": "📢 Onde será divulgado?", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "objetivo", "label": "🤝 O que busca com a parceria?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "oferece", "label": "🐉 O que oferece à GDS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "espera", "label": "🔥 O que espera da GDS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "info_extra", "label": "📝 Informações adicionais", "estilo": "longo", "max": 300, "obrigatorio": False},
        ],
    },

    "parceria_cla": {
        "titulo": "Parceria de Clã",
        "cor": COR_FICHA_CLA,
        "intro_launcher": "clique no botão abaixo pra propor a parceria do seu clã com a GDS!! 🏷️",
        "encerramento": "🐲🔥 Obrigado pelo interesse em fazer parceria com a GDS!\nSua proposta será analisada pela nossa equipe.",
        "campos": [
            {"chave": "nome_cla", "label": "🏷️ Nome do clã", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "dono", "label": "👑 Dono(a)/Líder", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante1", "label": "👥 Representante 1", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante2", "label": "👥 Representante 2", "estilo": "curto", "max": 60, "obrigatorio": False},
            {"chave": "discord_reps", "label": "💬 Discord dos representantes", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "convite", "label": "🔗 Convite do servidor", "estilo": "curto", "max": 200, "obrigatorio": True},
            {"chave": "membros", "label": "👥 Quantidade de membros", "estilo": "curto", "max": 20, "obrigatorio": True},
            {"chave": "atividade", "label": "🎮 Atividade principal", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "divulgacao", "label": "📢 Onde será divulgado?", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "objetivo", "label": "🤝 O que busca com a parceria?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "oferece", "label": "🐉 O que seu clã oferece à GDS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "espera", "label": "🔥 O que espera da GDS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "info_extra", "label": "📝 Informações adicionais", "estilo": "longo", "max": 300, "obrigatorio": False},
        ],
    },

    "parceria_comunidade": {
        "titulo": "Parceria de Comunidade",
        "cor": COR_FICHA_COMUNIDADE,
        "intro_launcher": "clique no botão abaixo pra propor a parceria da sua comunidade com a GDS!! 🌐",
        "encerramento": "🐲🔥 Obrigado pelo interesse em fazer parceria com a GDS!\nSerá um prazer conhecer sua comunidade e analisar a proposta.",
        "campos": [
            {"chave": "nome_comunidade", "label": "🏷️ Nome da comunidade", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "admin", "label": "👑 Administrador(a)/Fundador(a)", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante1", "label": "👥 Representante 1", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante2", "label": "👥 Representante 2", "estilo": "curto", "max": 60, "obrigatorio": False},
            {"chave": "discord_reps", "label": "💬 Discord dos representantes", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "convite", "label": "🔗 Convite/Link da comunidade", "estilo": "curto", "max": 200, "obrigatorio": True},
            {"chave": "membros", "label": "👥 Quantidade de membros", "estilo": "curto", "max": 20, "obrigatorio": True},
            {"chave": "foco", "label": "🎯 Foco/atividade da comunidade", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "divulgacao", "label": "📢 Onde será divulgado?", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "objetivo", "label": "🤝 O que busca com a parceria?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "oferece", "label": "🐉 O que sua comunidade oferece à GDS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "espera", "label": "🔥 O que espera da GDS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "info_extra", "label": "📝 Informações adicionais", "estilo": "longo", "max": 300, "obrigatorio": False},
        ],
    },
}

# tipo (argumento de t!parceria) -> form_key. cla e comunidade agora
# são fichas independentes, cada uma com seu próprio form_key acima.
_TIPOS_PARCERIA_KEYS = {
    "mapa": "parceria_mapa",
    "comercial": "parceria_comercial",
    "dj": "parceria_dj",
    "cla": "parceria_cla",
    "comunidade": "parceria_comunidade",
}


def _normalizar(texto: str) -> str:
    """minúsculas, sem espaço nas pontas e sem acentos (clã -> cla)."""
    import unicodedata
    texto = texto.lower().strip()
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )


def _total_etapas(form_key: str) -> int:
    """Quantos modais (etapas) essa ficha precisa, respeitando o limite de 5 campos por modal."""
    total_campos = len(FORM_TEMPLATES[form_key]["campos"])
    return (total_campos + 4) // 5


def _campos_da_etapa(form_key: str, etapa: int) -> list[dict]:
    campos = FORM_TEMPLATES[form_key]["campos"]
    inicio = etapa * 5
    return campos[inicio:inicio + 5]


class FichaModalStep(discord.ui.Modal):
    """Um modal com até 5 campos de uma ficha. Se sobrarem mais perguntas,
    ao enviar este modal o próximo é aberto automaticamente (encadeado)."""

    def __init__(self, cog: "FichasCog", form_key: str, etapa: int, respostas: dict):
        template = FORM_TEMPLATES[form_key]
        total = _total_etapas(form_key)
        titulo = template["titulo"]
        if total > 1:
            titulo = f"{titulo} ({etapa + 1}/{total})"
        super().__init__(title=titulo[:45])

        self.cog = cog
        self.form_key = form_key
        self.etapa = etapa
        self.total_etapas = total
        self.respostas = dict(respostas)
        self.campos = _campos_da_etapa(form_key, etapa)
        self._inputs: dict[str, discord.ui.TextInput] = {}

        for campo in self.campos:
            valor_anterior = self.respostas.get(campo["chave"], "")
            entrada = discord.ui.TextInput(
                label=campo["label"][:45],
                style=discord.TextStyle.paragraph if campo["estilo"] == "longo" else discord.TextStyle.short,
                required=campo.get("obrigatorio", True),
                max_length=campo.get("max", 300),
                placeholder=campo.get("placeholder"),
                default=valor_anterior or None,
            )
            self._inputs[campo["chave"]] = entrada
            self.add_item(entrada)

    async def on_submit(self, interaction: discord.Interaction):
        for campo in self.campos:
            self.respostas[campo["chave"]] = self._inputs[campo["chave"]].value.strip()

        proxima_etapa = self.etapa + 1
        if proxima_etapa < self.total_etapas:
            # ainda faltam perguntas: encadeia o próximo modal
            await interaction.response.send_modal(
                FichaModalStep(self.cog, self.form_key, proxima_etapa, self.respostas)
            )
            return

        # acabaram as perguntas: mostra a prévia pra confirmar/editar
        embed = self.cog._embed_preview(self.form_key, self.respostas)
        view = ConfirmarFichaView(self.cog, self.form_key, self.respostas, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        # imprime o traceback completo no console/logs (Railway -> aba Logs)
        # pra dar pra descobrir exatamente o que quebrou
        traceback.print_exception(type(error), error, error.__traceback__)
        mensagem = "❌ deu ruim ao processar sua ficha, tenta de novo!!"
        if interaction.response.is_done():
            await interaction.followup.send(mensagem, ephemeral=True)
        else:
            await interaction.response.send_message(mensagem, ephemeral=True)


class ConfirmarFichaView(discord.ui.View):
    """Prévia da ficha preenchida, com botões pra confirmar, editar ou cancelar."""

    def __init__(self, cog: "FichasCog", form_key: str, respostas: dict, autor_id: int):
        super().__init__(timeout=600)
        self.cog = cog
        self.form_key = form_key
        self.respostas = respostas
        self.autor_id = autor_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("essa ficha não é sua!! 🚫", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="Confirmar e Enviar", emoji="✅", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_final = self.cog._embed_final(self.form_key, self.respostas, interaction.user)
        await interaction.channel.send(embed=embed_final)
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content="✅ ficha enviada com sucesso, obrigado(a)!!", embed=None, view=self
        )
        self.stop()

    @discord.ui.button(label="Editar", emoji="✏️", style=discord.ButtonStyle.secondary)
    async def editar(self, interaction: discord.Interaction, button: discord.ui.Button):
        # reabre a ficha do começo, com as respostas anteriores já preenchidas
        await interaction.response.send_modal(
            FichaModalStep(self.cog, self.form_key, 0, self.respostas)
        )
        self.stop()

    @discord.ui.button(label="Cancelar", emoji="❌", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="❌ ficha cancelada.", embed=None, view=self)
        self.stop()


class IniciarFichaView(discord.ui.View):
    """Cartão inicial com o botão que abre a primeira etapa do formulário."""

    def __init__(self, cog: "FichasCog", form_key: str):
        super().__init__(timeout=900)
        self.cog = cog
        self.form_key = form_key

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="Preencher Ficha", emoji="📝", style=discord.ButtonStyle.primary)
    async def preencher(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FichaModalStep(self.cog, self.form_key, 0, {}))


class FichasCog(commands.Cog, name="Fichas"):
    """Fichas de inscrição interativas: novos membros, candidatura a Staff e parcerias."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── construção de embeds ────────────────────────────

    def _embed_lancamento(self, form_key: str) -> discord.Embed:
        template = FORM_TEMPLATES[form_key]
        total = _total_etapas(form_key)
        desc = template["intro_launcher"]
        if total > 1:
            desc += f"\n\n*a ficha tem {len(template['campos'])} perguntas, divididas em {total} etapas rápidas.*"
        embed = discord.Embed(
            title=f"🐉 {template['titulo']}",
            description=desc,
            color=template["cor"],
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text=FOOTER_GDS)
        return embed

    def _montar_embed_respostas(self, form_key: str, respostas: dict, titulo_prefixo: str = None) -> discord.Embed:
        template = FORM_TEMPLATES[form_key]
        linhas = ["🔥 GODS OF DRAGON SOULS 🔥"]
        for campo in template["campos"]:
            valor = (respostas.get(campo["chave"]) or "").strip()
            if not valor:
                valor = "*não informado*"
            linhas.append(f"{campo['label']}\n{valor}")
        if template.get("encerramento"):
            linhas.append(template["encerramento"])

        titulo = template["titulo"]
        if titulo_prefixo:
            titulo = f"{titulo_prefixo} — {titulo}"

        embed = discord.Embed(
            title=f"🐉 {titulo}",
            description="\n\n".join(linhas),
            color=template["cor"],
            timestamp=datetime.now(timezone.utc),
        )
        return embed

    def _embed_preview(self, form_key: str, respostas: dict) -> discord.Embed:
        embed = self._montar_embed_respostas(form_key, respostas, titulo_prefixo="🔎 Confira sua ficha")
        embed.set_footer(text="revise as respostas!! confirme, edite ou cancele abaixo.")
        return embed

    def _embed_final(self, form_key: str, respostas: dict, autor: discord.abc.User) -> discord.Embed:
        embed = self._montar_embed_respostas(form_key, respostas)
        embed.set_footer(text=f"{FOOTER_GDS} • enviado por {autor.display_name}")
        return embed

    # ── comandos ─────────────────────────────────────────

    @commands.command(name="novomembro", aliases=["ficha", "newmember", "nuevomiembro"])
    async def novo_membro(self, ctx: commands.Context, idioma: str = "pt"):
        """Abre a ficha interativa de novos membros. Uso: t!novomembro [pt|es|en]"""
        chave_idioma = _normalizar(idioma)
        form_key = f"novomembro_{chave_idioma}"
        if form_key not in FORM_TEMPLATES:
            await ctx.send(embed=embed_erro("idioma inválido!! use `pt`, `es` ou `en`!!"))
            return
        await ctx.send(embed=self._embed_lancamento(form_key), view=IniciarFichaView(self, form_key))

    @commands.command(name="staff", aliases=["candidaturastaff", "recrutamento"])
    async def staff_form(self, ctx: commands.Context):
        """Abre a ficha interativa de candidatura a Staff. Uso: t!staff"""
        await ctx.send(embed=self._embed_lancamento("staff"), view=IniciarFichaView(self, "staff"))

    @commands.command(name="parceria", aliases=["parcerias"])
    async def parceria(self, ctx: commands.Context, tipo: str = None):
        """Abre a ficha interativa de parceria. Uso: t!parceria <mapa|comercial|dj|cla|comunidade>"""
        if tipo is None:
            embed = discord.Embed(
                title="🤝 Parcerias GDS",
                description=(
                    "escolha o tipo de parceria que você quer propor!!\n\n"
                    "`t!parceria mapa` — parceria de mapa\n"
                    "`t!parceria comercial` — parceria comercial\n"
                    "`t!parceria dj` — parceria com DJ\n"
                    "`t!parceria cla` — parceria de clã\n"
                    "`t!parceria comunidade` — parceria de comunidade"
                ),
                color=COR_ROXO_GRUPO, timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=FOOTER_GDS)
            await ctx.send(embed=embed)
            return

        chave = _normalizar(tipo)
        form_key = _TIPOS_PARCERIA_KEYS.get(chave)
        if not form_key:
            await ctx.send(embed=embed_erro("tipo de parceria inválido!! use `mapa`, `comercial`, `dj`, `cla` ou `comunidade`!!"))
            return
        await ctx.send(embed=self._embed_lancamento(form_key), view=IniciarFichaView(self, form_key))

    @commands.command(name="fichas")
    async def listar_fichas(self, ctx: commands.Context):
        """Lista todas as fichas disponíveis."""
        embed = discord.Embed(
            title="📋 Fichas Disponíveis",
            description=(
                "todas as fichas abrem um formulário interativo: preencha, confira a prévia "
                "e só então confirme o envio!!\n\n"
                "`t!novomembro [pt|es|en]` — ficha de novos membros\n"
                "`t!staff` — candidatura a Staff\n"
                "`t!parceria mapa` — parceria de mapa\n"
                "`t!parceria comercial` — parceria comercial\n"
                "`t!parceria dj` — parceria com DJ\n"
                "`t!parceria cla` — parceria de clã\n"
                "`t!parceria comunidade` — parceria de comunidade"
            ),
            color=COR_NEUTRA, timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=FOOTER_GDS)
        await ctx.send(embed=embed)


# ══════════════════════════════════════════════════════════════════
#  📋  COMANDOS GERAIS (fora do cog)
# ══════════════════════════════════════════════════════════════════

@bot.command(name="help", aliases=["ajuda", "h"])
async def trisoul_help(ctx: commands.Context):
    embed = discord.Embed(
        title="🐉 Trisoul Bot — Ajuda",
        description="oi!! sou Trisoul, o Filho dos Deuses Dragônicos!! aqui tá tudo que eu sei fazer!! 🔥🌑✨",
        color=COR_NEUTRA, timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(
        name="💬 Diálogo",
        inline=False,
        value=(
            "converse comigo, me mencione ou fale meu nome ou o de uma cabeça (`ignis`/`umbra`/`luxor`)!!\n"
            "às vezes eu apareço sozinho, do nada!! 👀"
        )
    )
    embed.add_field(
        name="🛐 Fé & Devoção",
        inline=False,
        value=(
            "`t!orar <cabeça>` — ore para Ignis, Umbra ou Luxor\n"
            "`t!altar` — vê o placar de devoção do servidor"
        )
    )
    embed.add_field(
        name="🐲 Invocações",
        inline=False,
        value=(
            "`t!invocar <cabeça>` — força uma cabeça a se manifestar\n"
            "`t!profecia` — pede uma profecia aleatória\n"
            "`t!conflito` — as três cabeças discutem entre si (easter egg)\n"
            "`t!cabecas` — conhece as três consciências\n"
            "`t!trisoul` — lore e apresentação"
        )
    )
    embed.add_field(
        name="🛡️ Grupos",
        inline=False,
        value=(
            "clique no botão do painel de grupos pra criar seu cargo + chat + call\n"
            "`t!painelgrupo` — publica o painel (admin)\n"
            "`t!addmembro @pessoa` — adiciona alguém no seu grupo\n"
            "`t!removermembro @pessoa` — remove alguém do seu grupo\n"
            "`t!encerrargrupo` — apaga seu grupo (cargo + canais)"
        )
    )
    embed.add_field(
        name="📋 Fichas",
        inline=False,
        value=(
            "`t!novomembro [pt|es|en]` — ficha de novos membros\n"
            "`t!staff` — candidatura a Staff\n"
            "`t!parceria <mapa|comercial|dj|cla|comunidade>` — fichas de parceria\n"
            "`t!fichas` — lista todas as fichas disponíveis\n"
            "*(formulário interativo: preenche, confere e confirma antes de enviar!!)*"
        )
    )
    embed.add_field(
        name="📚 Aprendizado (moderação)",
        inline=False,
        value=(
            "`t!ensinar <gatilho> <resposta>` — ensina resposta pras 3 cabeças\n"
            "`t!ensinarcabeca <gatilho> <cabeça> <resposta>` — ensina resposta pra 1 cabeça\n"
            "`t!esquecer <gatilho>` — remove um gatilho\n"
            "`t!gatilhos` — lista tudo que Trisoul sabe\n"
            "`t!resposta <gatilho>` — vê as respostas de um gatilho\n"
            "`t!simular <texto>` — testa o que Trisoul responderia"
        )
    )
    embed.set_footer(text="🐉 Trisoul Bot • prefixo: t! ou trisoul ")
    await ctx.send(embed=embed)


@bot.command(name="ping")
async def ping(ctx: commands.Context):
    latencia = round(bot.latency * 1000)
    cor = COR_VERDE if latencia < 100 else (COR_DOURADO if latencia < 200 else COR_VERMELHO)
    await ctx.send(embed=discord.Embed(
        title="🏓 Pong!!", description=f"latência: `{latencia}ms` 🐉", color=cor
    ))


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        cabeca = escolher_cabeca()
        await ctx.send(fala(cabeca, "você não tem permissão pra pedir isso de mim!! 🚫"))
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=embed_erro(f"faltou informação!! uso correto: `{ctx.prefix}{ctx.command} {ctx.command.signature}`"))
        return
    raise error


# ══════════════════════════════════════════════════════════════════
#  🔁  ROTAÇÃO DE PRESENÇA (status muda conforme a cabeça "acordada")
# ══════════════════════════════════════════════════════════════════

async def _rotacionar_presenca():
    await bot.wait_until_ready()
    while not bot.is_closed():
        cabeca = escolher_cabeca()
        texto = random.choice(_STATUS_PRESENCA[cabeca])
        try:
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=texto))
        except Exception:
            pass
        await asyncio.sleep(900)  # troca a cada 15 minutos


# ══════════════════════════════════════════════════════════════════
#  🐉  EVENTOS GLOBAIS
# ══════════════════════════════════════════════════════════════════

_presenca_task_iniciada = False


@bot.event
async def on_ready():
    global _presenca_task_iniciada
    print(f"\n{'═'*54}")
    print("  🐉  TRISOUL BOT — ONLINE")
    print(f"  Logado como: {bot.user} ({bot.user.id})")
    print(f"  Servidores: {len(bot.guilds)}")
    print("  Cabeças ativas: 🔥 Ignis • 🌑 Umbra • ✨ Luxor")
    print(f"{'═'*54}\n")

    if not _presenca_task_iniciada:
        bot.loop.create_task(_rotacionar_presenca())
        _presenca_task_iniciada = True


# ══════════════════════════════════════════════════════════════════
#  🚀  INICIALIZAÇÃO
# ══════════════════════════════════════════════════════════════════

async def _main():
    async with bot:
        await bot.add_cog(TrisoulCog(bot))
        await bot.add_cog(GruposCog(bot))
        await bot.add_cog(FichasCog(bot))
        if not TOKEN:
            print("❌ ERRO: token não encontrado! Crie um .env com TRISOUL_TOKEN=seu_token")
            return
        await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio as _asyncio
    _asyncio.run(_main())
