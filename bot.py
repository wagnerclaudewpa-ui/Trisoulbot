"""
╔══════════════════════════════════════════════════════════════════╗
║              🐉  TRISOUL BOT  🔥🌑✨                              ║
║      O Filho dos Deuses Dragônicos — Três Consciências            ║
║        Ignis (Fogo) • Umbra (Sombra) • Luxor (Luz)                ║
║                         v1.1 — Online                             ║
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
"""

import discord
from discord.ext import commands
import asyncio
import os
import json
import random
import re
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
CHANCE_GATILHO_SEM_CHAMADO = 0.25   # chance de responder a um gatilho sem ser chamado
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
    "boa noite": {
        "ignis": ["boa noite!! descansa, amanhã tem mais fogo pra queimar!! 🔥", "boa noite!! nem à noite eu apago completamente, hehe!! 🔥🐉"],
        "umbra": ["...boa noite... a escuridão cuida de você enquanto dorme... 🌑", "...finalmente, a noite é minha hora... durma bem... 🌑🐉"],
        "luxor": ["boa noite!! que seus sonhos sejam leves e cheios de luz!! ✨", "descanse bem, viajante!! amanhã brilharemos juntos de novo!! ✨🐉"],
    },
    "tchau": {
        "ignis": ["tchau!! volta logo, tem muito chão pra queimar ainda!! 🔥", "beleza, vai!! mas eu tô de olho, hein!! 🔥🐉"],
        "umbra": ["...vá... eu vou continuar aqui, nas sombras, observando... 🌑", "...até logo... ou talvez eu já esteja te seguindo... 🌑🐉"],
        "luxor": ["até mais!! que a luz te acompanhe onde quer que você vá!! ✨", "tchau tchau!! cuide-se, viajante!! ✨🐉"],
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
        for gatilho in self.db["respostas"]:
            if gatilho in texto_lower:
                return gatilho
        return None

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
        embed.set_footer(text="🐉 Trisoul Bot v1.1")
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
        if not TOKEN:
            print("❌ ERRO: token não encontrado! Crie um .env com TRISOUL_TOKEN=seu_token")
            return
        await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio as _asyncio
    _asyncio.run(_main())
