import pygame, random, glob, os
pygame.init()
pygame.mixer.init()
LARGURA, ALTURA, GRID = 1000, 700, 28
HUD_ALTURA  = 55
Y_MIN_CELLS = HUD_ALTURA // GRID + 1
FUNDO, FUNDO_FLASH = (12, 12, 18), (35, 35, 55)
HUD, BRANCO        = (25, 25, 35), (240, 240, 240)
VERDE, AMARELO     = (0, 255, 120), (255, 220, 80)
COR_AZUL_CPU = ( 60, 120, 220)
COR_P1       = (200,  40,  40)
COR_P2       = (107, 142,  35)
MENU, SELECAO, JOGANDO, FIM, CONTAGEM = "menu", "selecao", "jogando", "fim", "contagem"

# ── Modos de jogo ───────────────────────────────────────────────────────────────
MODO_CLASSICO    = "classico"      # só a cobra do jogador, sem CPUs
MODO_VERSUS      = "versus"        # 2 jogadores, sem CPUs, sobreviver mais tempo
MODO_GUERRA      = "guerra"        # 1 jogador vs 8 CPUs
MODO_GUERRA_COOP = "guerra_coop"   # 2 jogadores vs 7 CPUs (cooperativo)
DOIS_JOGADORES_MODOS = (MODO_VERSUS, MODO_GUERRA_COOP)
COM_CPUS_MODOS       = (MODO_GUERRA, MODO_GUERRA_COOP)
NOME_CLASSES = ["Scout", "Soldier", "Pyro", "Demoman", "Heavy",
                "Engineer", "Medic", "Sniper", "Spy"]
N_CLASSES    = len(NOME_CLASSES)
_NOMES_LOW   = [n.lower() for n in NOME_CLASSES]
DOT_COR_CLASSES = [
    (255,  80,  80),
    (220, 220,  60),
    (255, 120,  40),
    (140,  60, 200),
    (200,  80,  80),
    (255, 200,  50),
    ( 60, 220, 140),
    ( 80, 200, 255),
    (200,  80, 180),
]

# ── Sistema de saúde por classe ────────────────────────────────────────────────
VIDA_CLASSE = {
    "Scout": 125, "Spy": 125, "Sniper": 125,
    "Engineer": 150, "Medic": 150,
    "Demoman": 175, "Pyro": 175,
    "Soldier": 200,
    "Heavy": 300,
}

# ── Multiplicador de velocidade por classe (1.0 = velocidade normal) ──────────
FATOR_VEL_CLASSE = {
    "Scout": 1.33,     # 33% mais rápido
    "Medic": 1.08,     #  8% mais rápido
    "Sniper": 1.04,    #  4% mais rápido
    "Spy": 1.04,       #  4% mais rápido
    "Heavy": 0.80,     # 20% mais lento
    "Soldier": 0.90,   # 10% mais lento
    "Demoman": 0.95,   #  5% mais lento
    # Pyro e Engineer usam o padrão (1.0)
}

# ── Combate corpo-a-corpo ──────────────────────────────────────────────────────
DANO_ATAQUE_BASE   = 50
DANO_ATAQUE_BIFE   = 80
CARGAS_BIFE_MAX    = 3
COOLDOWN_ATAQUE_MS = 1000   # 1 ataque por segundo

# ── Bombas ──────────────────────────────────────────────────────────────────────
DANO_BOMBA       = 100
DANO_BOMBA_CRIT  = 190
CHANCE_BOMBA_CRIT = 0.2     # 20% das bombas geradas são críticas

TIPO_BIFE, TIPO_FISHCAKE, TIPO_DALOKOHS, TIPO_BANANA, TIPO_SANDVICH = 0, 1, 2, 3, 4
N_TIPOS = 5
COR_COMIDA  = [(200,50,50),(255,140,60),(100,60,30),(255,220,30),(240,220,160)]
NOME_COMIDA = ["Bife", "Fishcake", "Dalokohs", "Banana", "Sandvich"]
# Peso de sorteio de cada tipo de comida (relativo). Fishcake aparece mais,
# Banana aparece menos; os demais mantêm frequência padrão.
PESOS_COMIDA = [1.0, 2.0, 1.0, 0.5, 1.0]

VELOCIDADE_BASE_FATOR = 0.60
TICKS_BANANA   = 15
TICKS_DALOKOHS = 64
tela  = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("SNAKE FORTRESS 2")
clock = pygame.time.Clock()
fonte    = pygame.font.SysFont("Arial", 22, True)
fonte_g  = pygame.font.SysFont("Arial", 56, True)
fonte_m  = pygame.font.SysFont("Arial", 30, True)
fonte_p  = pygame.font.SysFont("Arial", 18, True)
fonte_fx = pygame.font.SysFont("Arial", 14, True)
fonte_sel = pygame.font.SysFont("Arial", 20, True)
fonte_cont = pygame.font.SysFont("Arial", 120, True)
DURACAO_CONTAGEM_MS = 3000
def _img(path, sz=GRID):
    try:
        return pygame.transform.smoothscale(
            pygame.image.load(path).convert_alpha(), (sz, sz))
    except Exception:
        return None
def _som(base):
    for ext in (".wav", ".ogg"):
        try: return pygame.mixer.Sound(base + ext)
        except: pass
    return None
def _fundo(path):
    try: img = pygame.image.load(path).convert()
    except: return None
    w, h = img.get_size()
    s = max(LARGURA / w, ALTURA / h)
    nw, nh = int(w * s) + 1, int(h * s) + 1
    img = pygame.transform.smoothscale(img, (nw, nh))
    sup = pygame.Surface((LARGURA, ALTURA))
    sup.blit(img, (0, 0), ((nw-LARGURA)//2, (nh-ALTURA)//2, LARGURA, ALTURA))
    return sup
IMG_BOMBA  = _img("imagens/Pumpkinbomb.png.png")
IMG_MENU   = _fundo("imagens/menu_fundo.jpg")
IMGS_FRUTA = [_img(f"imagens/fruta{i}.png") for i in range(1, N_TIPOS+1)]
_FB_VIVA  = {"heavy": "imagens/HeavyFace2.png",      "soldier": "imagens/Soldier2.png"}
_FB_MORTA = {"heavy": "imagens/Heavyded.png",  "soldier": "imagens/cabeca_p2_morte.png"}
def _ld(n, s, sz=GRID):
    i = _img(f"imagens/{n}_{s}.png", sz)
    if not i: i = _img(_FB_VIVA.get(n) if s=="viva" else _FB_MORTA.get(n), sz)
    return i
IMG_CLASSE_VIVA  = [_ld(n, "viva") for n in _NOMES_LOW]
IMG_CLASSE_MORTA = [_ld(n, "morta") for n in _NOMES_LOW]
IMG_CLASSE_SEL   = [_ld(n, "viva", 80) for n in _NOMES_LOW]
SOM_MORTE, SOM_VITORIA, SOM_COMEMORA = ([_som(f"sons/{n}_{s}") for n in _NOMES_LOW] for s in ("morte","vitoria","comemora"))
SOM_MELEE    = [_som(f"sons/melee_frying_pan_0{i}") for i in range(1, 5)]
def tocar(s):
    if s: s.play()


def _listar_falas(classe, ocasiao):
    mapa = {"Scout":"scoutlines","Soldier":"Soldierlines","Pyro":"Pyrolines","Demoman":"Demolines","Heavy":"Heavylines","Engineer":"Engielines","Medic":"Mediclines","Sniper":"sniperlines","Spy":"spylines"}
    dir_p = f"sons/{mapa.get(classe, classe.lower()+'lines')}"
    if not os.path.exists(dir_p): return []
    sin = {"dor":["dor","pain"],"vitoria":["vitoria","venceu","win"],"morte":["morte","morreu","die","death"],"matou":["matou","kill"],"atacar":["atacar","attack","battlecry"]}
    termos, sons = sin.get(ocasiao, [ocasiao]), []
    for f in os.listdir(dir_p):
        if any(t in f.lower() for t in termos) and f.lower().endswith((".mp3", ".wav", ".ogg")):
            sons.append(pygame.mixer.Sound(os.path.join(dir_p, f)))
    return sons

def tocar_fala(cobra, ocasiao):
    sons = getattr(cobra, "falas", {}).get(ocasiao, [])
    if sons: random.choice(sons).play()

def todas_reagem_matou(vitima, todas_cobras, mortas_frame=None):
    if getattr(vitima, "falou_matou", False): return
    excluir = {vitima} | (mortas_frame or set())
    cands = [c for c in todas_cobras if c not in excluir and not c.morta and not getattr(c, "_eliminado", False)]
    if cands:
        vx, vy = vitima.cabeca
        cands.sort(key=lambda c: abs(c.cabeca[0]-vx) + abs(c.cabeca[1]-vy))
        tocar_fala(cands[0], "matou")

def tocar_administrator(ocasiao):
    """Toca um efeito sonoro aleatório da pasta administrator para a ocasião pedida."""
    caminho_dir = "sons/administrator"
    if not os.path.exists(caminho_dir): return
    arquivos = []
    for f in os.listdir(caminho_dir):
        if f.lower().startswith(ocasiao) and f.lower().endswith((".mp3", ".wav", ".ogg")):
            arquivos.append(os.path.join(caminho_dir, f))
    if arquivos:
        s = pygame.mixer.Sound(random.choice(arquivos))
        s.play()

def _listar_musicas(ocasiao):
    arquivos = []
    for ext in ("ogg", "mp3", "wav"):
        arquivos += glob.glob(f"sons/musicas/{ocasiao}*.{ext}")
    return arquivos
MUSICAS = {
    "menu":    _listar_musicas("menu"),
    "combate": _listar_musicas("combate"),
    "fimdejogo": _listar_musicas("fimdejogo"),
}
_musica_atual = None
def tocar_musica(ocasiao, volume=0.5, loop=-1):
    global _musica_atual
    if ocasiao == _musica_atual:
        return
    faixas = MUSICAS.get(ocasiao, [])
    if not faixas:
        _musica_atual = ocasiao
        return
    try:
        pygame.mixer.music.load(random.choice(faixas))
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loop)
        _musica_atual = ocasiao
    except Exception:
        _musica_atual = ocasiao
def parar_musica():
    global _musica_atual
    pygame.mixer.music.stop()
    _musica_atual = None
_notifs = []
def add_notif(texto, cor, x, y, ttl=90):
    surf = fonte_fx.render(texto, True, cor)
    _notifs.append([surf, x, y, ttl])
def draw_notifs():
    for n in _notifs[:]:
        surf, x, y, ttl = n
        ttl -= 1
        n[3] = ttl
        alpha = min(255, ttl * 4)
        surf.set_alpha(alpha)
        tela.blit(surf, (x - surf.get_width()//2, y - (90-ttl)//2))
        if ttl <= 0:
            _notifs.remove(n)
class Snake:
    def __init__(self, x, y, cor, iv=None, im=None, nome="?"):
        self.body, self.dir, self.size = [(x, y)], (1, 0), 5
        self.score, self.cor, self.img_viva, self.img_morta, self.nome, self.morta = 0, cor, iv, im, nome, False
        self.vidas, self.t_banana, self.t_dalokohs = 1, 0, 0
        self.vida_max = VIDA_CLASSE.get(nome, 150)
        self.vida = self.vida_max
        self.fator_vel, self.mov_acc = FATOR_VEL_CLASSE.get(nome, 1.0), 0.0
        self.cargas_bife, self.ultimo_ataque = 0, -COOLDOWN_ATAQUE_MS
        self.falas = {o: _listar_falas(nome, o) for o in ["dor","vitoria","morte","matou","atacar"]}
        self.falou_vitoria = False
        self.falou_matou = False
    @property
    def acelerado(self): return self.t_banana > 0
    def tick_powerups(self):
        if self.t_banana > 0: self.t_banana -= 1
        if self.t_dalokohs > 0:
            self.t_dalokohs -= 1
            if self.t_dalokohs == 0:
                self.vida_max -= 50
                self.vida = min(self.vida, self.vida_max)
    def move(self):
        x, y = self.body[0]
        nx, ny = ((x + self.dir[0]*GRID)//GRID)*GRID, ((y + self.dir[1]*GRID)//GRID)*GRID
        self.body.insert(0, (nx, ny))
        if len(self.body) > self.size: self.body.pop()
    def draw(self, morte=False):
        for i, p in enumerate(self.body):
            if i == 0:
                img = self.img_morta if morte and self.img_morta else self.img_viva
                if img: tela.blit(img, p)
                if self.cargas_bife > 0:
                    pygame.draw.rect(tela, (255,140,40), (p[0]-2, p[1]-2, GRID+2, GRID+2), 2, border_radius=5)
                if img: continue
            b = max(100, 255 - i*5)
            pygame.draw.rect(tela, tuple(min(c, b) for c in self.cor), (*p, GRID-2, GRID-2), border_radius=4)
        if not morte and self.body:
            p, frac = self.body[0], max(0.0, min(1.0, self.vida / self.vida_max))
            bx, by = p[0], max(HUD_ALTURA, p[1]-6)
            pygame.draw.rect(tela, (50,15,15), (bx, by, GRID, 4))
            c_hp = (60,220,90) if frac > 0.5 else ((230,200,40) if frac > 0.25 else (220,60,60))
            pygame.draw.rect(tela, c_hp, (bx, by, int(GRID*frac), 4))
    @property
    def cabeca(self): return self.body[0]
class SnakeCPU(Snake):
    def __init__(self, x, y, idx):
        super().__init__(x, y, COR_AZUL_CPU, IMG_CLASSE_VIVA[idx], IMG_CLASSE_MORTA[idx], NOME_CLASSES[idx])
        self.classe_idx, self.dot_cor, self._eliminado = idx, DOT_COR_CLASSES[idx], False
        self.som_morte, self.som_vitoria, self.som_comemora = SOM_MORTE[idx], SOM_VITORIA[idx], SOM_COMEMORA[idx]
    @staticmethod
    def _prox(pos, d):
        return (((pos[0]+d[0]*GRID)//GRID)*GRID, ((pos[1]+d[1]*GRID)//GRID)*GRID)
    @staticmethod
    def _perigoso(pos, corpos, bomb_pos):
        x, y = pos
        if x < 0 or x >= LARGURA or y < HUD_ALTURA or y >= ALTURA: return True
        if pos in bomb_pos: return True
        return any(pos in c for c in corpos)
    def _espaco(self, pos, d, corpos, bomb_pos, n=4):
        for k in range(n):
            pos = self._prox(pos, d)
            if self._perigoso(pos, corpos, bomb_pos): return k
        return n
    def ia(self, comidas, corpos, bomb_pos):
        DIRS   = [(1,0),(-1,0),(0,1),(0,-1)]
        oposto = (-self.dir[0], -self.dir[1])
        cab    = self.cabeca
        cx, cy = cab
        agora  = pygame.time.get_ticks()
        can_atk = pode_atacar(self, agora)

        # 1. Alvo padrão: comida mais próxima
        alvo, md = None, float("inf")
        for c in comidas:
            d = abs(c[0]-cx) + abs(c[1]-cy)
            if d < md: md, alvo = d, c

        # 2. Se puder atacar, procurar inimigos muito perto (distância < 4 casas)
        inimigo_alvo, d_inimigo = None, float("inf")
        for c_body in corpos:
            if c_body is self.body: continue
            for p in c_body:
                d = abs(p[0]-cx) + abs(p[1]-cy)
                if d < d_inimigo:
                    d_inimigo = d
                    inimigo_alvo = p
        
        if can_atk and inimigo_alvo and d_inimigo < 4 * GRID:
            alvo, md = inimigo_alvo, d_inimigo

        best_s, best_d = -float("inf"), self.dir
        for d in DIRS:
            if d == oposto: continue
            prox = self._prox(cab, d)
            
            # Perigos fatais: parede, bombas ou o próprio corpo
            if fora(prox) or prox in bomb_pos or prox in self.body:
                continue
            
            # Checa se entra em corpo de outros
            em_outro = any(prox in c for c in corpos if c is not self.body)
            
            if em_outro:
                if can_atk:
                    s = 2000 # Prioridade total para ataque!
                else:
                    continue # Evita se não puder atacar
            else:
                # Pontuação normal de espaço e distância ao alvo
                s = self._espaco(prox, d, corpos, bomb_pos) * 2
                if alvo:
                    s += (md - abs(prox[0]-alvo[0]) - abs(prox[1]-alvo[1])) * 3
                s += random.uniform(-0.5, 0.5)
                
            if s > best_s:
                best_s, best_d = s, d
        self.dir = best_d
def pos_livre(cobras, bombas, comidas_set):
    ocupado = comidas_set | {(x, y) for x, y, _ in bombas}
    for c in cobras:
        ocupado.update(c.body)
    while True:
        p = (random.randint(0, (LARGURA//GRID)-1) * GRID,
             random.randint(Y_MIN_CELLS, (ALTURA//GRID)-1) * GRID)
        if p not in ocupado:
            return p
def add_comida(cobras, bombas, cset):
    p    = pos_livre(cobras, bombas, cset)
    pesos = list(PESOS_COMIDA)
    if modo_jogo == MODO_CLASSICO:
        pesos[TIPO_BIFE] = 0.0
    tipo = random.choices(range(N_TIPOS), weights=pesos, k=1)[0]
    return p, tipo, IMGS_FRUTA[tipo]
def update_bombas(nivel, cobras, bombas, cset):
    qtd = min(max(0, (nivel-1) * 2), 20)   # taxa de aparecimento dobrada
    while len(bombas) < qtd:
        p = pos_livre(cobras, bombas, cset)
        crit = random.random() < CHANCE_BOMBA_CRIT
        bombas.append((p[0], p[1], crit))
    return bombas
def bomba_em(pos, bombas):
    for x, y, crit in bombas:
        if (x, y) == pos:
            return crit
    return None
def remover_bomba(pos, bombas):
    for i, (x, y, crit) in enumerate(bombas):
        if (x, y) == pos:
            bombas.pop(i)
            return
def fora(cab):
    x, y = cab
    return x < 0 or x >= LARGURA or y < HUD_ALTURA or y >= ALTURA
def aplicar_powerup(c, t):
    cx, cy = c.cabeca
    if t == TIPO_BIFE:
        c.cargas_bife = min(CARGAS_BIFE_MAX, c.cargas_bife + 1)
        add_notif(f"⚔ ATAQUE+ ({c.cargas_bife}/{CARGAS_BIFE_MAX})", (255, 80, 80), cx, cy)
    else:
        d = {TIPO_FISHCAKE:(c.vida_max//4, f"+{c.vida_max//4} HP", (255,140,60)),
             TIPO_DALOKOHS:(50, "+50 VIDA MÁX (8s)", (150,100,40)),
             TIPO_BANANA:  (c.vida//2, f"⚡ +{c.vida//2} HP", (255,220,30)),
             TIPO_SANDVICH:(c.vida_max//2, f"+{c.vida_max//2} HP (SANDVICH)", (200,160,255))}.get(t)
        if d:
            v, txt, cor = d
            if t == TIPO_DALOKOHS:
                if c.t_dalokohs <= 0: c.vida_max += 50
                c.t_dalokohs = TICKS_DALOKOHS
            elif t == TIPO_BANANA: c.t_banana = TICKS_BANANA
            c.vida = min(c.vida_max, c.vida + v)
            add_notif(txt, cor, cx, cy)
def inicio_cpus(n, p1, p2):
    usadas = {p1.cabeca} | ({p2.cabeca} if p2 else set())
    zonas  = []
    for col in range(4):
        for row in range(2):
            cx = (int(LARGURA*(col+0.5)/4) // GRID) * GRID
            cy = max((int(ALTURA*(row+0.5)/2) // GRID) * GRID, Y_MIN_CELLS*GRID)
            zonas.append((cx, cy))
    random.shuffle(zonas)
    res = [p for p in zonas if p not in usadas][:n]
    while len(res) < n:
        p = (random.randint(0,(LARGURA//GRID)-1)*GRID,
             random.randint(Y_MIN_CELLS,(ALTURA//GRID)-1)*GRID)
        if p not in usadas: usadas.add(p); res.append(p)
    return res
def novo_jogo(modo, idx1, idx2=None):
    _notifs.clear()
    p1 = Snake(200, 360, COR_P1, IMG_CLASSE_VIVA[idx1], IMG_CLASSE_MORTA[idx1], NOME_CLASSES[idx1])
    p2 = Snake(800, 360, COR_P2, IMG_CLASSE_VIVA[idx2], IMG_CLASSE_MORTA[idx2], NOME_CLASSES[idx2]) if modo in DOIS_JOGADORES_MODOS and idx2 is not None else None
    if p2: p2.dir = (-1, 0)
    cpus = []
    if modo in COM_CPUS_MODOS:
        ids = [i for i in range(N_CLASSES) if i not in ({idx1} | ({idx2} if idx2 is not None else set()))]
        pos = inicio_cpus(len(ids), p1, p2)
        for i, cidx in enumerate(ids):
            c = SnakeCPU(*pos[i], cidx); c.dir = random.choice([(1,0),(-1,0),(0,1),(0,-1)]); cpus.append(c)
    todas, cset = [p1] + ([p2] if p2 else []) + cpus, set()
    comidas, ctipos, cimgs = [], [], []
    for _ in range(max(3, (1+len(cpus))//2)):
        p, t, im = add_comida(todas, [], cset)
        comidas.append(p); ctipos.append(t); cimgs.append(im); cset.add(p)
    return p1, p2, cpus, comidas, ctipos, cimgs, []
def checar_comer(cobra, comidas, ctipos, cimgs, cset, todas_vivas, bombas):
    cab = cobra.cabeca
    if cab in cset:
        idx_c  = comidas.index(cab)
        tipo_c = ctipos[idx_c]
        cobra.score += 10
        cobra.size  += 1
        cset.discard(cab)
        comidas.pop(idx_c); ctipos.pop(idx_c); cimgs.pop(idx_c)
        aplicar_powerup(cobra, tipo_c)
        np_, nt_, ni_ = add_comida(todas_vivas, bombas, cset)
        comidas.append(np_); ctipos.append(nt_); cimgs.append(ni_)
        cset.add(np_)

# ── Combate corpo-a-corpo e dano de bombas ─────────────────────────────────────
def pode_atacar(cobra, agora_ms):
    return agora_ms - cobra.ultimo_ataque >= COOLDOWN_ATAQUE_MS
def registrar_ataque(cobra, agora_ms):
    cobra.ultimo_ataque = agora_ms
def dano_ataque(cobra):
    if cobra.cargas_bife > 0:
        cobra.cargas_bife -= 1
        return DANO_ATAQUE_BIFE
    return DANO_ATAQUE_BASE
def aplicar_dano(cobra, dano, atacante=None):
    cobra.vida -= dano
    cx, cy = cobra.cabeca
    motivo = atacante.nome if hasattr(atacante, "nome") else str(atacante)
    add_notif(f"-{dano} HP" + (f" ({motivo})" if motivo else ""), (255, 70, 70), cx, cy, ttl=60)
    if cobra.vida > 0:
        tocar_fala(cobra, "dor")
    elif not cobra.morta:
        tocar_fala(cobra, "morte")
        if hasattr(atacante, "falas"):
            tocar_fala(atacante, "matou"); cobra.falou_matou = True
def processar_colisoes(todas_vivas, bombas, agora_ms):
    """
    Aplica dano de bombas e de ataques corpo-a-corpo (cabeça de uma cobra
    contra o corpo/cabeça de outra, respeitando o cooldown de 1 ataque por
    segundo por atacante) a todas as cobras vivas neste frame. Retorna o
    conjunto de cobras que devem morrer agora (parede, automordida ou HP<=0).
    """
    mortas = set()
    for cobra in todas_vivas:
        cab = cobra.cabeca
        if fora(cab) or cab in cobra.body[1:] or cobra.vida <= 0:
            if not cobra.morta:
                tocar_fala(cobra, "morte")
            mortas.add(cobra)
            continue
        crit = bomba_em(cab, bombas)
        if crit is not None:
            remover_bomba(cab, bombas)
            aplicar_dano(cobra, DANO_BOMBA_CRIT if crit else DANO_BOMBA,
                         "bomba crítica" if crit else "bomba")
            if cobra.vida <= 0:
                mortas.add(cobra)
                continue
        for outra in todas_vivas:
            if outra is cobra or outra in mortas:
                continue
            if cab in outra.body:
                if pode_atacar(cobra, agora_ms):
                    dano = dano_ataque(cobra)
                    aplicar_dano(outra, dano, cobra)
                    if SOM_MELEE:
                        tocar(random.choice(SOM_MELEE))
                    registrar_ataque(cobra, agora_ms)
    for cobra in todas_vivas:
        if cobra.vida <= 0:
            mortas.add(cobra)
    return mortas
def nomes_restantes(cobras_cpu, n=3):
    r = [c for c in cobras_cpu if not c._eliminado]
    v = " & ".join(c.nome for c in r[:n])
    return (v + (f" +{len(r)-n}" if len(r) > n else "")) if r else "?"
def draw_hud(p1, p2, cpus, nivel):
    pygame.draw.rect(tela, HUD, (0, 0, LARGURA, HUD_ALTURA))
    def _ic(c):
        s = f" ⚔×{c.cargas_bife}" if c.cargas_bife > 0 else ""
        if c.acelerado: s += " ⚡"
        if c.vidas > 1: s += f" ❤×{c.vidas}"
        return s
    lbl = f"P1‑{p1.nome}: {p1.score} HP {p1.vida}/{p1.vida_max}{_ic(p1)}"
    if p2: lbl += f"  P2‑{p2.nome}: {p2.score} HP {p2.vida}/{p2.vida_max}{_ic(p2)}"
    lbl += f"  Nível: {nivel}"
    tela.blit(fonte.render(lbl, True, BRANCO), (10, 8))
    for i, cpu in enumerate(cpus):
        xd = LARGURA - 20 - i*22
        pygame.draw.circle(tela, cpu.dot_cor if not cpu._eliminado else (60,60,60), (xd, 20), 7)
        if cpu._eliminado: pygame.draw.line(tela, (200,60,60), (xd-5,15), (xd+5,25), 2)
        m = fonte_p.render(cpu.nome[:2], True, BRANCO)
        tela.blit(m, (xd - m.get_width()//2, 30))
def centralizar(surf, y):
    tela.blit(surf, (LARGURA//2 - surf.get_width()//2, y))
CARD_W, CARD_H       = 298, 163
CARD_GAP_X, CARD_GAP_Y = 18, 14
SEL_X0 = (LARGURA - 3*CARD_W - 2*CARD_GAP_X) // 2
SEL_Y0 = 112
def _card_rect(idx):
    col, row = idx % 3, idx // 3
    x = SEL_X0 + col * (CARD_W + CARD_GAP_X)
    y = SEL_Y0 + row * (CARD_H + CARD_GAP_Y)
    return pygame.Rect(x, y, CARD_W, CARD_H)
def _card_at(mx, my):
    for i in range(N_CLASSES):
        if _card_rect(i).collidepoint(mx, my):
            return i
    return -1
def draw_selecao(passo, p1_idx, p2_idx, hover):
    if IMG_MENU:
        tela.blit(IMG_MENU,(0,0))
        ov = pygame.Surface((LARGURA,ALTURA), pygame.SRCALPHA); ov.fill((0,0,0,178)); tela.blit(ov,(0,0))
    else: tela.fill(FUNDO)
    ct, msg, sub = ((235,70,70), "JOGADOR 1 – ESCOLHA SUA CLASSE", "WASD para jogar | 1-9 ou clique | ESC = Menu") if passo==1 else \
                   ((120,190,55), "JOGADOR 2 – ESCOLHA SUA CLASSE", "Setas para jogar | 1-9 ou clique | ESC = P1 reescolhe")
    centralizar(fonte_m.render(msg, True, ct), 18)
    centralizar(fonte_p.render(sub, True, (155,155,155)), 58)
    bloq = {p1_idx, p2_idx} - {-1}
    for i in range(N_CLASSES):
        r, dc, b = _card_rect(i), DOT_COR_CLASSES[i], (i in bloq)
        hov, p1, p2 = (i == hover and not b), (i == p1_idx), (i == p2_idx)
        bg = (32,32,42) if b else tuple(min(255, c//2+60) if hov else max(8, c//5+10) for c in dc)
        borda = (235,70,70) if p1 else ((120,190,55) if p2 else ((60,60,70) if b else (BRANCO if hov else dc)))
        pygame.draw.rect(tela, bg, r, border_radius=10)
        pygame.draw.rect(tela, borda, r, 3, border_radius=10)
        tela.blit(fonte_p.render(str(i+1), True, AMARELO if not b else (65,65,65)), (r.x+8, r.y+8))
        img, ix, iy = IMG_CLASSE_SEL[i], r.x+(CARD_W-80)//2, r.y+16
        if img:
            tela.blit(img, (ix, iy))
            if b:
                dim = pygame.Surface((80,80), pygame.SRCALPHA); dim.fill((0,0,0,145)); tela.blit(dim, (ix,iy))
        else:
            pygame.draw.circle(tela, (45,45,55) if b else dc, (r.x+CARD_W//2, r.y+56), 36)
            pygame.draw.circle(tela, borda, (r.x+CARD_W//2, r.y+56), 36, 2)
            ini = fonte_g.render(NOME_CLASSES[i][0], True, BRANCO if not b else (75,75,75))
            tela.blit(ini, (r.x+CARD_W//2-ini.get_width()//2, r.y+56-ini.get_height()//2))
        ns = fonte_sel.render(NOME_CLASSES[i], True, BRANCO if not b else (70,70,70))
        tela.blit(ns, (r.x+CARD_W//2-ns.get_width()//2, r.y+CARD_H-32))
        if p1 or p2:
            tag = fonte_p.render("P1 ✓" if p1 else "P2 ✓", True, (235,80,80) if p1 else (120,190,55))
            tela.blit(tag, (r.right-tag.get_width()-8, r.y+8))
        elif b:
            pygame.draw.line(tela, (110,40,40), (r.x+12,r.y+12), (r.right-12,r.bottom-12), 3)
            pygame.draw.line(tela, (110,40,40), (r.right-12,r.y+12), (r.x+12,r.bottom-12), 3)
            tag = fonte_p.render("TOMADO", True, (100,100,100))
            tela.blit(tag, (r.right-tag.get_width()-8, r.y+8))
    centralizar(fonte_p.render("ESC – Voltar", True, (110,110,110)), ALTURA-26)
estado         = MENU
modo_jogo      = MODO_GUERRA
selecao_passo = 1
selecao_p1    = -1
selecao_p2    = -1
hover_sel     = -1
p1 = p2 = None
cobras_cpu                     = []
comidas, ctipos, cimgs, bombas = [], [], [], []
cset                           = set()
vencedor, msg_fim              = "", ""
tick_global                    = 0
fps_base                       = 8
contagem_inicio_ms             = 0
def iniciar_rodada():
    """Prepara o campo (já criado por novo_jogo) e entra em contagem
    regressiva de 3 segundos antes de liberar o controle das cobras."""
    global cset, vencedor, msg_fim, tick_global, estado, contagem_inicio_ms
    cset = set(comidas)
    vencedor = msg_fim = ""
    tick_global = 0
    contagem_inicio_ms = pygame.time.get_ticks()
    estado = CONTAGEM
    tocar_musica("combate")
    
    if modo_jogo in COM_CPUS_MODOS:
        tocar_administrator("inicio")
    
    # Efeito sonoro de ataque para as cobras participantes
    ps = [p1] + ([p2] if p2 else []) + cobras_cpu
    for c in random.sample(ps, min(len(ps), 3)): tocar_fala(c, "atacar")
def processar_selecao(idx):
    global selecao_passo, selecao_p1, selecao_p2
    global p1, p2, cobras_cpu, comidas, ctipos, cimgs, bombas
    bloq = set()
    if selecao_p1 >= 0: bloq.add(selecao_p1)
    if selecao_p2 >= 0: bloq.add(selecao_p2)
    if idx in bloq:
        return
    if selecao_passo == 1:
        selecao_p1 = idx
        if modo_jogo in DOIS_JOGADORES_MODOS:
            selecao_passo = 2
        else:
            p1, p2, cobras_cpu, comidas, ctipos, cimgs, bombas = \
                novo_jogo(modo_jogo, selecao_p1)
            iniciar_rodada()
    else:
        selecao_p2 = idx
        p1, p2, cobras_cpu, comidas, ctipos, cimgs, bombas = \
            novo_jogo(modo_jogo, selecao_p1, selecao_p2)
        iniciar_rodada()
while True:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit(); raise SystemExit
        if ev.type == pygame.MOUSEMOTION and estado == SELECAO:
            hover_sel = _card_at(*ev.pos)
        if ev.type == pygame.MOUSEBUTTONDOWN and estado == SELECAO:
            idx = _card_at(*ev.pos)
            if idx >= 0:
                processar_selecao(idx)
        if ev.type == pygame.KEYDOWN:
            k = ev.key
            if estado == MENU:
                ms = {pygame.K_1:MODO_CLASSICO, pygame.K_2:MODO_VERSUS, pygame.K_3:MODO_GUERRA, pygame.K_4:MODO_GUERRA_COOP}
                ms.update({pygame.K_KP1:MODO_CLASSICO, pygame.K_KP2:MODO_VERSUS, pygame.K_KP3:MODO_GUERRA, pygame.K_KP4:MODO_GUERRA_COOP})
                if k in ms: modo_jogo, selecao_passo, selecao_p1, selecao_p2, hover_sel, estado = ms[k], 1, -1, -1, -1, SELECAO
            elif estado == SELECAO:
                if k == pygame.K_ESCAPE:
                    if selecao_passo == 2: selecao_passo, selecao_p1 = 1, -1
                    else: estado, selecao_p1, selecao_p2, selecao_passo = MENU, -1, -1, 1
                num = k - pygame.K_1 if pygame.K_1 <= k <= pygame.K_9 else (k - pygame.K_KP1 if pygame.K_KP1 <= k <= pygame.K_KP9 else None)
                if num is not None and 0 <= num < N_CLASSES: processar_selecao(num)
            elif estado == JOGANDO:
                d1 = {pygame.K_w:(0,-1), pygame.K_s:(0,1), pygame.K_a:(-1,0), pygame.K_d:(1,0)}
                if k in d1 and p1.dir != (d1[k][0]*-1, d1[k][1]*-1): p1.dir = d1[k]
                if p2:
                    d2 = {pygame.K_UP:(0,-1), pygame.K_DOWN:(0,1), pygame.K_LEFT:(-1,0), pygame.K_RIGHT:(1,0)}
                    if k in d2 and p2.dir != (d2[k][0]*-1, d2[k][1]*-1): p2.dir = d2[k]
            elif estado == FIM:
                if k == pygame.K_r: p1, p2, cobras_cpu, comidas, ctipos, cimgs, bombas = novo_jogo(modo_jogo, selecao_p1, selecao_p2 if modo_jogo in DOIS_JOGADORES_MODOS else None); iniciar_rodada()
                if k == pygame.K_c: selecao_passo, selecao_p1, selecao_p2, hover_sel, estado = 1, -1, -1, -1, SELECAO
                if k == pygame.K_m: p1 = p2 = None; cobras_cpu, comidas, ctipos, cimgs, bombas, cset, vencedor, msg_fim, estado = [], [], [], [], [], set(), "", "", MENU
    if estado == SELECAO:
        draw_selecao(selecao_passo, selecao_p1, selecao_p2, hover_sel)
        pygame.display.flip()
        clock.tick(30)
        continue
    if estado == MENU:
        tocar_musica("menu")
        if IMG_MENU:
            tela.blit(IMG_MENU, (0,0))
            ov = pygame.Surface((LARGURA,ALTURA), pygame.SRCALPHA); ov.fill((0,0,0,140)); tela.blit(ov,(0,0))
        else: tela.fill(FUNDO)
        centralizar(fonte_g.render("SNAKE FORTRESS 2", True, AMARELO), 100)
        centralizar(fonte_m.render("LUTE ATÈ A MORTE!", True, BRANCO), 165)
        for i, t in enumerate(["1 – Clássico (só você)", "2 – Versus (2 jogadores)", "3 – Guerra (1 vs 8 CPUs)", "4 – Guerra Coop (2 vs 7 CPUs)"]):
            centralizar(fonte_m.render(t, True, BRANCO), 222 + i*34)
        y0, leg = 372, [("Bife","⚔ +Dano corpo a corpo",(255,80,80)),("Fishcake","Cura 25% HP máx",(255,140,60)),("Dalokohs","+50 vida máx temp (8s)",(150,100,40)),("Banana","⚡ Cura 50% HP atual+vel",(255,220,30)),("Sandvich","Cura 50% HP máx",(200,160,255))]
        for n, d, c in leg:
            img = IMGS_FRUTA[NOME_COMIDA.index(n)]
            if img: tela.blit(img, (LARGURA//2-200, y0-2))
            tela.blit(fonte_p.render(f"  {n}: {d}", True, c), (LARGURA//2-180, y0)); y0 += 22
        for t, y in [("Assets: Valve Software Inc.", 44), ("Trilha sonora: Valve Studio Orchestra", 24)]:
            s = fonte_fx.render(t, True, (150,150,150)); tela.blit(s, (LARGURA-s.get_width()-14, ALTURA-y))
        pygame.display.flip(); clock.tick(30); continue

    # ── Contagem regressiva antes da rodada começar ────────────────────────
    contagem_ativa = False
    contagem_decorrido = 0
    if estado == CONTAGEM:
        contagem_decorrido = pygame.time.get_ticks() - contagem_inicio_ms
        if contagem_decorrido >= DURACAO_CONTAGEM_MS:
            estado = JOGANDO
        else:
            contagem_ativa = True

    if estado == JOGANDO:
        tick_global += 1
        vivas_cpu   = [c for c in cobras_cpu if not c._eliminado]
        todas_vivas = [p1] + ([p2] if p2 else []) + vivas_cpu
        cset        = set(comidas)
        for cobra in todas_vivas:
            cobra.tick_powerups()
        sc_total = (p1.score if p1 else 0) + (p2.score if p2 else 0) \
                   + sum(c.score for c in vivas_cpu)
        nivel    = sc_total // 100 + 1
        fps_base = max(3, int((8+nivel) * VELOCIDADE_BASE_FATOR))
        corpos_obs = [c.body for c in todas_vivas]
        bomb_pos   = {(x, y) for x, y, _ in bombas}
        for cpu in vivas_cpu:
            cpu.ia(comidas, corpos_obs, bomb_pos)

        # Movimento com velocidade fracionária por classe. A comida é checada
        # a cada passo individual (não só no fim do frame) para não "pular"
        # comidas no caminho quando a cobra anda mais de uma vez no frame.
        for cobra in todas_vivas:
            fator = cobra.fator_vel * (2 if cobra.acelerado else 1)
            cobra.mov_acc += fator
            while cobra.mov_acc >= 1.0:
                cobra.move()
                cobra.mov_acc -= 1.0
                checar_comer(cobra, comidas, ctipos, cimgs, cset, todas_vivas, bombas)

        bombas = update_bombas(nivel, todas_vivas, bombas, cset)

        agora_ms = pygame.time.get_ticks()
        mortas   = processar_colisoes(todas_vivas, bombas, agora_ms)

        for cpu in vivas_cpu:
            if cpu in mortas:
                todas_reagem_matou(cpu, todas_vivas, mortas)
                cpu._eliminado = True
                cpu.body       = []

        vivas_cpu_agora = [c for c in cobras_cpu if not c._eliminado]

        p1_m = p1 in mortas
        p2_m = (p2 in mortas) if p2 else False

        for jogador, flag in ((p1,p1_m),(p2,p2_m)):
            if jogador and flag:
                jogador.morta = True
                todas_reagem_matou(jogador, todas_vivas, mortas)

        if modo_jogo == MODO_CLASSICO:
            # Só a cobra do jogador está em campo: fim de jogo ao morrer.
            if p1_m:
                vencedor = "FIM DE JOGO"
                msg_fim  = f"Pontuação final: {p1.score}"
                estado   = FIM
        elif modo_jogo == MODO_VERSUS:
            # 2 jogadores, sem CPUs: vence quem sobreviver mais tempo.
            if p1_m and p2_m:
                vencedor = "EMPATE"
                msg_fim  = "Os dois foram eliminados juntos!"
                estado   = FIM
            elif p1_m:
                vencedor = "PLAYER 2"
                msg_fim  = f"{p2.nome} sobreviveu mais tempo!"
                estado   = FIM
                tocar_musica("fimdejogo")
            elif p2_m:
                vencedor = "PLAYER 1"
                msg_fim  = f"{p1.nome} sobreviveu mais tempo!"
                estado   = FIM
                tocar_musica("fimdejogo")
        else:
            # MODO_GUERRA / MODO_GUERRA_COOP: jogador(es) vs CPUs.
            j_mortos   = p1_m and (p2 is None or p2_m)
            cpu_acabou = len(cobras_cpu) > 0 and all(c._eliminado for c in cobras_cpu)

            if j_mortos:
                vencedor = nomes_restantes(cobras_cpu)
                msg_fim  = f"{vencedor} venceu!" if vencedor != "?" else "EMPATE – todos morreram!"
                if vencedor == "?": vencedor = "EMPATE"
                estado = FIM
                tocar_administrator("fracasso")
            elif cpu_acabou:
                if   p2 and not p1_m and not p2_m: vencedor, msg_fim = "P1 & P2",   "P1 e P2 sobreviveram!"
                elif not p1_m:                      vencedor, msg_fim = "PLAYER 1",  "P1 é o último sobrevivente!"
                elif p2 and not p2_m:               vencedor, msg_fim = "PLAYER 2",  "P2 é o último sobrevivente!"
                estado = FIM
                tocar_administrator("vitoria")
                tocar_musica("fimdejogo")
            elif p1_m and not (p2 and not p2_m):
                vencedor = nomes_restantes(cobras_cpu, 2); msg_fim = f"{vencedor} eliminou P1!"; estado = FIM
                tocar_administrator("fracasso")
            elif p2_m and not p1_m:
                vencedor = nomes_restantes(cobras_cpu, 2); msg_fim = f"{vencedor} eliminou P2!"; estado = FIM
                tocar_administrator("fracasso")
    sc = (p1.score if p1 else 0) + (p2.score if p2 else 0)
    tela.fill(FUNDO_FLASH if sc >= 200 and pygame.time.get_ticks()//150%2 else FUNDO)
    if p1: draw_hud(p1, p2, cobras_cpu, sc//50+1)
    for pos, t, img in zip(comidas, ctipos, cimgs):
        if img: tela.blit(img, pos)
        else: pygame.draw.rect(tela, COR_COMIDA[t], (*pos, GRID, GRID), border_radius=4); tela.blit(fonte_fx.render(NOME_COMIDA[t][0], True, BRANCO), (pos[0]+2, pos[1]+2))
    for bx, by, crit in bombas:
        if IMG_BOMBA:
            tela.blit(IMG_BOMBA, (bx, by))
            if crit: pygame.draw.rect(tela, (255,40,40), (bx-2,by-2,GRID+4,GRID+4), 2, border_radius=6)
        else:
            ct = (bx+GRID//2, by+GRID//2)
            pygame.draw.circle(tela, (60,10,10) if crit else (30,30,30), ct, GRID//2)
            pygame.draw.circle(tela, (255,30,30) if crit else (255,90,30), ct, GRID//2, 2)
            pygame.draw.line(tela, (255,180,60), (ct[0]+1,by), (ct[0]+5,by-5), 2)
    for c in cobras_cpu:
        if not c._eliminado: c.draw()
    if p1: p1.draw(morte=(estado==FIM and p1.morta))
    if p2: p2.draw(morte=(estado==FIM and p2.morta))
    draw_notifs()
    if contagem_ativa:
        seg = 3 - (contagem_decorrido // 1000)
        txt = fonte_cont.render(str(seg), True, AMARELO)
        cx, cy = LARGURA//2 - txt.get_width()//2, ALTURA//2 - txt.get_height()//2
        for dx, dy in ((-3,0),(3,0),(0,-3),(0,3)): tela.blit(fonte_cont.render(str(seg), True, (0,0,0)), (cx+dx, cy+dy))
        tela.blit(txt, (cx, cy)); centralizar(fonte_m.render("Prepare-se...", True, BRANCO), ALTURA//2 + 80)
    if estado == FIM:
        for c in ([p1] + ([p2] if p2 else []) + cobras_cpu):
            if not c.morta and not getattr(c, "_eliminado", False) and not c.falou_vitoria: tocar_fala(c, "vitoria"); c.falou_vitoria = True
        pan = pygame.Surface((760, 205), pygame.SRCALPHA); pan.fill((10,10,20,215)); tela.blit(pan, (LARGURA//2-380, ALTURA//2-112))
        centralizar(fonte_g.render(vencedor, True, AMARELO), ALTURA//2-102)
        centralizar(fonte_m.render(msg_fim, True, BRANCO), ALTURA//2-35)
        centralizar(fonte_p.render("R – Reiniciar | C – Trocar Classe | M – Menu", True, (175,175,175)), ALTURA//2+35)
    pygame.display.flip()
    clock.tick(fps_base if estado == JOGANDO else 30)