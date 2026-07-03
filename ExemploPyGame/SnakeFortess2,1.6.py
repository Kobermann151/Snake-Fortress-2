import pygame, random
pygame.init()
pygame.mixer.init()

# ── Constantes ────────────────────────────────────────────────────────────────
LARGURA, ALTURA, GRID = 1000, 700, 28
HUD_ALTURA  = 55
Y_MIN_CELLS = HUD_ALTURA // GRID + 1

FUNDO, FUNDO_FLASH = (12, 12, 18), (35, 35, 55)
HUD, BRANCO        = (25, 25, 35), (240, 240, 240)
VERDE, AMARELO     = (0, 255, 120), (255, 220, 80)
COR_AZUL_CPU       = (60, 120, 220)
CORES_P            = [(255, 255, 0), (255, 70, 70), (80, 150, 255)]
MENU, JOGANDO, FIM = "menu", "jogando", "fim"

# ── Tipos de comida e seus efeitos ────────────────────────────────────────────
# índice → (nome,       cor_fallback,    duração_ticks)
#   0 = Bife       → invencibilidade (mata quem encostar)  por 8 ticks
#   1 = Fishcake   → +1 vida extra
#   2 = Dalokohs   → +1 vida extra
#   3 = Banana     → +velocidade                           por 15 ticks
#   4 = Sandvich   → pontos em dobro                       por 12 ticks
TIPO_BIFE, TIPO_FISHCAKE, TIPO_DALOKOHS, TIPO_BANANA, TIPO_SANDVICH = 0, 1, 2, 3, 4
N_TIPOS = 5

COR_COMIDA = [
    (200,  50,  50),   # bife
    (255, 140,  60),   # fishcake
    (100,  60,  30),   # dalokohs
    (255, 220,  30),   # banana
    (240, 220, 160),   # sandvich
]
NOME_COMIDA = ["Bife", "Fishcake", "Dalokohs", "Banana", "Sandvich"]

# ── Velocidade base = 60 % da original (8 + nível) ───────────────────────────
VELOCIDADE_BASE_FATOR = 0.60     # multiplicador sobre (8+nivel) FPS
TICKS_INVENC   = 8               # ticks com invencibilidade (bife)
TICKS_BANANA   = 15              # ticks de bônus de velocidade
TICKS_SANDVICH = 12              # ticks de pontuação dobrada
BONUS_VEL      = 4               # FPS extras durante efeito banana

# ── Dados das CPUs ────────────────────────────────────────────────────────────
CPU_DADOS = [
    ("Scout",    (255,  80,  80)),
    ("Pyro",     (255, 120,  40)),
    ("Demoman",  (140,  60, 200)),
    ("Engineer", (255, 200,  50)),
    ("Medic",    ( 60, 220, 140)),
    ("Sniper",   ( 80, 200, 255)),
    ("Spy",      (200,  80, 180)),
    ("Soldier",  (220, 220,  60)),
]

tela  = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("SNAKE FORTRESS 2")
clock = pygame.time.Clock()

fonte   = pygame.font.SysFont("Arial", 22, True)
fonte_g = pygame.font.SysFont("Arial", 56, True)
fonte_m = pygame.font.SysFont("Arial", 30, True)
fonte_p = pygame.font.SysFont("Arial", 18, True)
fonte_fx = pygame.font.SysFont("Arial", 14, True)

# ── Carregamento de recursos ──────────────────────────────────────────────────
# Imagens (imagens/):
#   HeavyFace2.png, Soldier2.png, cabeca_p1_morte.png, cabeca_p2_morte.png
#   scout_viva.png…soldier_viva.png / scout_morta.png…soldier_morta.png
#   fruta1.png=Bife  fruta2.png=Fishcake  fruta3.png=Dalokohs
#   fruta4.png=Banana  fruta5.png=Sandvich
#   bomba.png, menu_fundo.jpg
# Sons (sons/):
#   {nome}_morte.wav/.ogg  {nome}_vitoria.wav/.ogg  {nome}_comemora.wav/.ogg

def _img(path, sz=GRID):
    try:
        return pygame.transform.smoothscale(
            pygame.image.load(path).convert_alpha(), (sz, sz))
    except Exception: return None

def _som(base):
    for ext in (".wav", ".ogg"):
        try: return pygame.mixer.Sound(base + ext)
        except: pass
    return None

def _fundo(path):
    try: img = pygame.image.load(path).convert()
    except: return None
    w, h = img.get_size()
    s = max(LARGURA/w, ALTURA/h)
    nw, nh = int(w*s)+1, int(h*s)+1
    img = pygame.transform.smoothscale(img, (nw, nh))
    sup = pygame.Surface((LARGURA, ALTURA))
    sup.blit(img, (0,0), ((nw-LARGURA)//2, (nh-ALTURA)//2, LARGURA, ALTURA))
    return sup

IMG_P1_VIVA  = _img("imagens/HeavyFace2.png")
IMG_P1_MORTA = _img("imagens/cabeca_p1_morte.png")
IMG_P2_VIVA  = _img("imagens/Soldier2.png")
IMG_P2_MORTA = _img("imagens/cabeca_p2_morte.png")
IMG_BOMBA    = _img("imagens/Pumpkinbomb.png")
IMG_MENU     = _fundo("imagens/menu_fundo.jpg")

# fruta1‥5 → índice 0‥4 (um por tipo de comida)
IMGS_FRUTA = [_img(f"imagens/fruta{i}.png") for i in range(1, N_TIPOS+1)]

_NOMES_LOW    = [n.lower() for n, _ in CPU_DADOS]
IMG_CPU_VIVA  = [_img(f"imagens/{n}_viva.png")  for n in _NOMES_LOW]
IMG_CPU_MORTA = [_img(f"imagens/{n}_morta.png") for n in _NOMES_LOW]
SOM_MORTE     = [_som(f"sons/{n}_morte")    for n in _NOMES_LOW]
SOM_VITORIA   = [_som(f"sons/{n}_vitoria")  for n in _NOMES_LOW]
SOM_COMEMORA  = [_som(f"sons/{n}_comemora") for n in _NOMES_LOW]

def tocar(s):
    if s: s.play()

# ── Notificações flutuantes (feedback visual de power-up) ─────────────────────
_notifs = []   # lista de [texto, cor, x, y, ttl]

def add_notif(texto, cor, x, y, ttl=90):
    _notifs.append([texto, cor, x, y, ttl])

def draw_notifs():
    for n in _notifs[:]:
        n[4] -= 1
        alpha = min(255, n[4] * 4)
        surf  = fonte_fx.render(n[0], True, n[1])
        surf.set_alpha(alpha)
        tela.blit(surf, (n[2] - surf.get_width()//2, n[3] - (90-n[4])//2))
        if n[4] <= 0: _notifs.remove(n)

# ── Classe Snake ──────────────────────────────────────────────────────────────
class Snake:
    def __init__(self, x, y, cor, iv=None, im=None, nome="?"):
        self.body, self.dir, self.size = [(x, y)], (1, 0), 5
        self.score, self.cor           = 0, cor
        self.img_viva, self.img_morta  = iv, im
        self.nome, self.morta          = nome, False
        # Power-up counters (em ticks)
        self.vidas       = 1     # morre quando chega a 0
        self.t_invenc    = 0     # ticks restantes de invencibilidade (bife)
        self.t_banana    = 0     # ticks restantes de velocidade extra
        self.t_sandvich  = 0     # ticks restantes de pontos dobrados

    @property
    def invencivel(self):  return self.t_invenc   > 0
    @property
    def acelerado(self):   return self.t_banana   > 0
    @property
    def dobro_pts(self):   return self.t_sandvich > 0

    def tick_powerups(self):
        """Decrementa contadores a cada tick do jogo."""
        if self.t_invenc   > 0: self.t_invenc   -= 1
        if self.t_banana   > 0: self.t_banana   -= 1
        if self.t_sandvich > 0: self.t_sandvich -= 1

    def move(self):
        x, y = self.body[0]
        nx = ((x + self.dir[0]*GRID) // GRID) * GRID
        ny = ((y + self.dir[1]*GRID) // GRID) * GRID
        self.body.insert(0, (nx, ny))
        while len(self.body) > self.size:
            self.body.pop()

    def draw(self, morte=False):
        for i, p in enumerate(self.body):
            if i == 0:
                img = (self.img_morta if morte and self.img_morta else self.img_viva)
                if img: tela.blit(img, p); continue
            b   = max(100, 255 - i*5)
            cor = tuple(min(c, b) for c in self.cor)
            # Anel dourado quando invencível
            if i == 0 and self.invencivel:
                pygame.draw.rect(tela, AMARELO, (p[0]-2, p[1]-2, GRID+2, GRID+2), 2, border_radius=5)
            pygame.draw.rect(tela, cor, (*p, GRID-2, GRID-2), border_radius=4)
        # Anel dourado na cabeça geométrica
        if self.invencivel and self.body:
            pygame.draw.rect(tela, AMARELO,
                             (self.body[0][0]-2, self.body[0][1]-2, GRID+2, GRID+2), 2, border_radius=5)

    @property
    def cabeca(self): return self.body[0]


# ── Classe SnakeCPU ───────────────────────────────────────────────────────────
class SnakeCPU(Snake):
    def __init__(self, x, y, idx):
        nome, dot_cor = CPU_DADOS[idx]
        super().__init__(x, y, COR_AZUL_CPU, IMG_CPU_VIVA[idx], IMG_CPU_MORTA[idx], nome)
        self.idx          = idx
        self.dot_cor      = dot_cor
        self.som_morte    = SOM_MORTE[idx]
        self.som_vitoria  = SOM_VITORIA[idx]
        self.som_comemora = SOM_COMEMORA[idx]
        self._eliminado   = False

    @staticmethod
    def _prox(pos, d):
        return (((pos[0]+d[0]*GRID)//GRID)*GRID, ((pos[1]+d[1]*GRID)//GRID)*GRID)

    @staticmethod
    def _perigoso(pos, corpos, bombas):
        x, y = pos
        if x < 0 or x >= LARGURA or y < HUD_ALTURA or y >= ALTURA: return True
        if pos in bombas: return True
        return any(pos in c for c in corpos)

    def _espaco(self, pos, d, corpos, bombas, n=4):
        for k in range(n):
            pos = self._prox(pos, d)
            if self._perigoso(pos, corpos, bombas): return k
        return n

    def ia(self, comidas, corpos, bombas):
        DIRS   = [(1,0),(-1,0),(0,1),(0,-1)]
        oposto = (-self.dir[0], -self.dir[1])
        cab    = self.cabeca
        cx, cy = cab
        alvo, md = None, float("inf")
        for c in comidas:
            d = abs(c[0]-cx)+abs(c[1]-cy)
            if d < md: md, alvo = d, c
        best_s, best_d = -float("inf"), self.dir
        for d in DIRS:
            if d == oposto: continue
            prox = self._prox(cab, d)
            if self._perigoso(prox, corpos, bombas): continue
            s  = self._espaco(prox, d, corpos, bombas)*2
            if alvo: s += (md - abs(prox[0]-alvo[0]) - abs(prox[1]-alvo[1]))*3
            s += random.uniform(-0.5, 0.5)
            if s > best_s: best_s, best_d = s, d
        self.dir = best_d

# ── Funções auxiliares ────────────────────────────────────────────────────────
def pos_livre(cobras, bombas, comidas_set):
    while True:
        p = (random.randint(0,(LARGURA//GRID)-1)*GRID,
             random.randint(Y_MIN_CELLS,(ALTURA//GRID)-1)*GRID)
        if p not in bombas and p not in comidas_set \
           and not any(p in c.body for c in cobras):
            return p

def add_comida(cobras, bombas, cset):
    """Retorna (pos, tipo, img)."""
    p    = pos_livre(cobras, bombas, cset)
    tipo = random.randint(0, N_TIPOS-1)
    img  = IMGS_FRUTA[tipo]
    return p, tipo, img

def update_bombas(nivel, cobras, bombas, cset):
    qtd = min(max(0, nivel-1), 10)
    while len(bombas) < qtd:
        bombas.append(pos_livre(cobras, bombas, cset))
    return bombas

def fora(cab):
    x, y = cab
    return x < 0 or x >= LARGURA or y < HUD_ALTURA or y >= ALTURA

def colide_com(cab, cobras, self_cobra=None):
    for c in cobras:
        seg = c.body[1:] if c is self_cobra else c.body
        if cab in seg: return True
    return False

def morreu_jogador(cobra, todas, bombas):
    cab = cobra.cabeca
    return (fora(cab) or cab in bombas
            or cab in cobra.body[1:]
            or colide_com(cab, [c for c in todas if c is not cobra]))

# ── Aplicar efeito de comida ──────────────────────────────────────────────────
def aplicar_powerup(cobra, tipo):
    """Aplica o efeito do tipo de comida à cobra e exibe notificação."""
    cx, cy = cobra.cabeca
    if tipo == TIPO_BIFE:
        cobra.t_invenc = TICKS_INVENC
        add_notif("⚔ INVENCÍVEL!", (255, 80, 80), cx, cy)
    elif tipo in (TIPO_FISHCAKE, TIPO_DALOKOHS):
        cobra.vidas += 1
        add_notif(f"+1 VIDA ({cobra.vidas})", (60, 255, 120), cx, cy)
    elif tipo == TIPO_BANANA:
        cobra.t_banana = TICKS_BANANA
        add_notif("⚡ RÁPIDO!", (255, 220, 30), cx, cy)
    elif tipo == TIPO_SANDVICH:
        cobra.t_sandvich = TICKS_SANDVICH
        add_notif("✦ 2× PONTOS!", (200, 160, 255), cx, cy)

# ── Posições iniciais das CPUs ────────────────────────────────────────────────
def inicio_cpus(n, p1, p2):
    usadas = {p1.cabeca} | ({p2.cabeca} if p2 else set())
    zonas  = []
    for col in range(4):
        for row in range(2):
            cx = (int(LARGURA*(col+0.5)/4)//GRID)*GRID
            cy = max((int(ALTURA*(row+0.5)/2)//GRID)*GRID, Y_MIN_CELLS*GRID)
            zonas.append((cx, cy))
    random.shuffle(zonas)
    res = [p for p in zonas if p not in usadas][:n]
    while len(res) < n:
        p = (random.randint(0,(LARGURA//GRID)-1)*GRID,
             random.randint(Y_MIN_CELLS,(ALTURA//GRID)-1)*GRID)
        if p not in usadas: usadas.add(p); res.append(p)
    return res

# ── Novo jogo ─────────────────────────────────────────────────────────────────
def novo_jogo(modo):
    _notifs.clear()
    p1 = Snake(200, 360, CORES_P[0], IMG_P1_VIVA, IMG_P1_MORTA, "P1")
    p2 = None
    if modo == 2:
        p2 = Snake(800, 360, CORES_P[2], IMG_P2_VIVA, IMG_P2_MORTA, "P2")
        p2.dir = (-1, 0)
    n   = 7 if modo == 2 else 8
    pos = inicio_cpus(n, p1, p2)
    cpus = []
    for i in range(n):
        c = SnakeCPU(*pos[i], i)
        c.dir = random.choice([(1,0),(-1,0),(0,1),(0,-1)])
        cpus.append(c)
    todas  = [p1]+([p2] if p2 else [])+cpus
    bombas = []
    comidas, ctipos, cimgs, cset = [], [], [], set()
    for _ in range(max(3, (1+n)//2)):
        p, t, img = add_comida(todas, bombas, cset)
        comidas.append(p); ctipos.append(t); cimgs.append(img); cset.add(p)
    return p1, p2, cpus, comidas, ctipos, cimgs, bombas

# ── HUD ───────────────────────────────────────────────────────────────────────
def draw_hud(p1, p2, cpus, nivel):
    pygame.draw.rect(tela, HUD, (0, 0, LARGURA, HUD_ALTURA))

    def icones(cobra):
        """Retorna string com ícones dos power-ups ativos."""
        s = ""
        if cobra.invencivel:  s += "⚔"
        if cobra.acelerado:   s += "⚡"
        if cobra.dobro_pts:   s += "✦"
        if cobra.vidas > 1:   s += f"❤×{cobra.vidas}"
        return (" " + s) if s else ""

    if p2:
        label = f"P1:{p1.score}{icones(p1)}   P2:{p2.score}{icones(p2)}   Nível:{nivel}"
    else:
        label = f"SCORE:{p1.score}{icones(p1)}   Nível:{nivel}"
    tela.blit(fonte.render(label, True, BRANCO), (10, 8))

    # Dots de CPU com mini-nome
    for i, cpu in enumerate(cpus):
        xd  = LARGURA - 20 - i*22
        cor = cpu.dot_cor if not cpu._eliminado else (60, 60, 60)
        pygame.draw.circle(tela, cor, (xd, 20), 7)
        if cpu._eliminado:
            pygame.draw.line(tela,(200,60,60),(xd-5,15),(xd+5,25),2)
        mini = fonte_p.render(cpu.nome[:2], True, BRANCO)
        tela.blit(mini, (xd - mini.get_width()//2, 30))

def centralizar(surf, y):
    tela.blit(surf, (LARGURA//2 - surf.get_width()//2, y))

# ── Estado global ─────────────────────────────────────────────────────────────
estado, modo_jogadores             = MENU, 1
p1 = p2 = None
cobras_cpu                         = []
comidas, ctipos, cimgs, bombas     = [], [], [], []
vencedor, msg_fim                  = "", ""
tick_global                        = 0   # contador de ticks para power-ups

# ── Loop principal ────────────────────────────────────────────────────────────
while True:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit(); raise SystemExit

        if ev.type == pygame.KEYDOWN:
            k = ev.key
            if estado == MENU:
                if k in (pygame.K_1, pygame.K_KP1):
                    modo_jogadores = 1
                    p1,p2,cobras_cpu,comidas,ctipos,cimgs,bombas = novo_jogo(1)
                    vencedor=msg_fim=""; tick_global=0; estado=JOGANDO
                if k in (pygame.K_2, pygame.K_KP2):
                    modo_jogadores = 2
                    p1,p2,cobras_cpu,comidas,ctipos,cimgs,bombas = novo_jogo(2)
                    vencedor=msg_fim=""; tick_global=0; estado=JOGANDO

            elif estado == JOGANDO:
                if k==pygame.K_w and p1.dir!=(0, 1):  p1.dir=(0,-1)
                if k==pygame.K_s and p1.dir!=(0,-1):  p1.dir=(0, 1)
                if k==pygame.K_a and p1.dir!=(1, 0):  p1.dir=(-1,0)
                if k==pygame.K_d and p1.dir!=(-1,0):  p1.dir=(1, 0)
                if p2:
                    if k==pygame.K_UP    and p2.dir!=(0, 1):  p2.dir=(0,-1)
                    if k==pygame.K_DOWN  and p2.dir!=(0,-1):  p2.dir=(0, 1)
                    if k==pygame.K_LEFT  and p2.dir!=(1, 0):  p2.dir=(-1,0)
                    if k==pygame.K_RIGHT and p2.dir!=(-1,0):  p2.dir=(1, 0)

            elif estado == FIM:
                if k == pygame.K_r:
                    p1,p2,cobras_cpu,comidas,ctipos,cimgs,bombas = novo_jogo(modo_jogadores)
                    vencedor=msg_fim=""; tick_global=0; estado=JOGANDO
                if k == pygame.K_m:
                    p1=p2=None; cobras_cpu=comidas=ctipos=cimgs=bombas=[]
                    vencedor=msg_fim=""; estado=MENU

    # ── MENU ──────────────────────────────────────────────────────────────────
    if estado == MENU:
        if IMG_MENU:
            tela.blit(IMG_MENU,(0,0))
            ov = pygame.Surface((LARGURA,ALTURA),pygame.SRCALPHA)
            ov.fill((0,0,0,140)); tela.blit(ov,(0,0))
        else:
            tela.fill(FUNDO)
        centralizar(fonte_g.render("SNAKE DUEL – TF2 EDITION", True, AMARELO), 130)
        centralizar(fonte_m.render("Sobreviva contra os personagens do TF2!", True, BRANCO), 220)
        centralizar(fonte_m.render("1 – Um jogador  (vs 8 CPUs)", True, BRANCO), 310)
        centralizar(fonte_m.render("2 – Dois jogadores  (vs 7 CPUs)", True, BRANCO), 355)
        # Legenda dos power-ups
        legenda = [
            ("Bife",     "⚔ Invencibilidade – mata quem encostar", (255, 80,  80)),
            ("Fishcake", "+1 Vida extra",                          (255,140,  60)),
            ("Dalokohs", "+1 Vida extra",                          (100, 60,  30)),
            ("Banana",   "⚡ Velocidade aumentada",                (255,220,  30)),
            ("Sandvich", "✦ Pontos em dobro",                      (200,160, 255)),
        ]
        y0 = 415
        for nome, desc, cor in legenda:
            img = IMGS_FRUTA[["Bife","Fishcake","Dalokohs","Banana","Sandvich"].index(nome)]
            if img: tela.blit(img, (LARGURA//2 - 200, y0-2))
            s = fonte_p.render(f"  {nome}: {desc}", True, cor)
            tela.blit(s, (LARGURA//2 - 180, y0))
            y0 += 22
        pygame.display.flip(); clock.tick(30); continue

    # ── LÓGICA ────────────────────────────────────────────────────────────────
    if estado == JOGANDO:
        tick_global += 1
        vivas_cpu   = [c for c in cobras_cpu if not c._eliminado]
        todas_vivas = [p1]+([p2] if p2 else [])+vivas_cpu
        cset        = set(comidas)

        # Tick dos power-ups de cada cobra
        for cobra in todas_vivas:
            cobra.tick_powerups()

        # Velocidade base (60% de 8+nivel) + bônus banana individual
        sc_total = p1.score+(p2.score if p2 else 0)+sum(c.score for c in vivas_cpu)
        nivel    = sc_total//100+1
        fps_base = max(3, int((8+nivel) * VELOCIDADE_BASE_FATOR))

        # IA das CPUs
        corpos_obs = [c.body for c in todas_vivas]
        for cpu in vivas_cpu:
            cpu.ia(comidas, corpos_obs, bombas)

        # Movimentação – cobra acelerada move 2× por tick
        cobras_para_mover = todas_vivas[:]
        for cobra in cobras_para_mover:
            cobra.move()
            if cobra.acelerado:
                cobra.move()   # segundo passo no mesmo tick

        # Coleta de comida
        def checar_comer(cobra):
            cab = cobra.cabeca
            if cab in cset:
                idx_c  = comidas.index(cab)
                tipo_c = ctipos[idx_c]
                pts    = 20 if cobra.dobro_pts else 10
                cobra.score += pts; cobra.size += 1
                cset.discard(cab)
                comidas.pop(idx_c); ctipos.pop(idx_c); cimgs.pop(idx_c)
                aplicar_powerup(cobra, tipo_c)
                np_, nt_, ni_ = add_comida(todas_vivas, bombas, cset)
                comidas.append(np_); ctipos.append(nt_); cimgs.append(ni_); cset.add(np_)

        checar_comer(p1)
        if p2: checar_comer(p2)
        for cpu in vivas_cpu: checar_comer(cpu)

        # Bombas
        bombas = update_bombas(nivel, todas_vivas, bombas, cset)

        # ── Morte das CPUs ────────────────────────────────────────────────────
        for cpu in vivas_cpu:
            cab = cpu.cabeca
            # Cobra invencível não morre ao bater em outros corpos,
            # mas ainda morre ao bater em paredes e bombas
            morreu_parede = fora(cab) or cab in bombas
            morreu_corpo  = (not cpu.invencivel) and colide_com(cab, todas_vivas, cpu)
            if morreu_parede or morreu_corpo:
                # Se estava invencível e colidiu com jogador: jogador perde vida
                if cpu.invencivel and not morreu_parede:
                    for v in todas_vivas:
                        if v is not cpu and cab in v.body:
                            v.vidas -= 1
                tocar(cpu.som_morte)
                for o in vivas_cpu:
                    if o is not cpu: tocar(o.som_comemora)
                cpu._eliminado = True; cpu.body = []

        # ── Morte dos jogadores ───────────────────────────────────────────────
        vivas_cpu_agora = [c for c in cobras_cpu if not c._eliminado]
        todas_agora     = [p1]+([p2] if p2 else [])+vivas_cpu_agora

        def checar_morte_jogador(cobra, todas):
            cab = cobra.cabeca
            if fora(cab) or cab in bombas or cab in cobra.body[1:]:
                return True
            for outra in todas:
                if outra is cobra: continue
                if cab in outra.body:
                    # Se a outra cobra está invencível, ela mata; caso contrário
                    # o jogador invencível sobrevive e a outra perde uma vida
                    if outra.invencivel:
                        return True
                    elif cobra.invencivel:
                        outra.vidas -= 1
                        return False
                    else:
                        return True
            return False

        p1_m = checar_morte_jogador(p1, todas_agora)
        p2_m = p2 and checar_morte_jogador(p2, todas_agora)

        # Vidas extras absorvem a morte
        def consumir_vida(cobra, flag):
            if flag and cobra.vidas > 1:
                cobra.vidas -= 1
                cx, cy = cobra.cabeca
                add_notif(f"❤ VIDA PERDIDA! ({cobra.vidas} restante(s))",
                          (255,60,60), cx, cy, ttl=80)
                return False   # não morreu, só perdeu vida
            return flag

        p1_m = consumir_vida(p1, p1_m)
        if p2: p2_m = consumir_vida(p2, p2_m)

        for jogador, flag in ((p1,p1_m),(p2,p2_m)):
            if jogador and flag:
                jogador.morta = True
                for cpu in vivas_cpu_agora:
                    if jogador.cabeca in cpu.body:
                        tocar(cpu.som_vitoria); break

        # ── Fim de jogo ───────────────────────────────────────────────────────
        def nomes_restantes(n=3):
            r = [c for c in cobras_cpu if not c._eliminado]
            v = " & ".join(c.nome for c in r[:n])
            return (v+(f" +{len(r)-n}" if len(r)>n else "")) if r else "?"

        j_mortos   = p1_m and (p2 is None or p2_m)
        cpu_acabou = all(c._eliminado for c in cobras_cpu)

        if j_mortos:
            vencedor = nomes_restantes()
            msg_fim  = f"{vencedor} venceu!" if vencedor!="?" else "EMPATE – todos morreram!"
            if vencedor=="?": vencedor="EMPATE"
            estado=FIM
        elif cpu_acabou:
            if p2 and not p1_m and not p2_m: vencedor,msg_fim="P1 & P2","P1 e P2 sobreviveram!"
            elif not p1_m:                   vencedor,msg_fim="PLAYER 1","P1 é o último sobrevivente!"
            elif p2 and not p2_m:            vencedor,msg_fim="PLAYER 2","P2 é o último sobrevivente!"
            estado=FIM
        elif p1_m and not (p2 and not p2_m):
            vencedor=nomes_restantes(2); msg_fim=f"{vencedor} eliminou P1!"; estado=FIM
        elif p2_m and not p1_m:
            vencedor=nomes_restantes(2); msg_fim=f"{vencedor} eliminou P2!"; estado=FIM

    # ── DESENHO ───────────────────────────────────────────────────────────────
    sc_draw = (p1.score if p1 else 0)+(p2.score if p2 else 0)
    nv_draw = sc_draw//50+1
    tela.fill(FUNDO_FLASH if sc_draw>=200 and pygame.time.get_ticks()//150%2 else FUNDO)

    draw_hud(p1, p2, cobras_cpu, nv_draw)

    # Comidas com cor de fundo por tipo (quando sem PNG)
    for pos_c, tipo_c, img_c in zip(comidas, ctipos, cimgs):
        if img_c:
            tela.blit(img_c, pos_c)
        else:
            pygame.draw.rect(tela, COR_COMIDA[tipo_c], (*pos_c, GRID, GRID), border_radius=4)
            label = fonte_fx.render(NOME_COMIDA[tipo_c][0], True, BRANCO)
            tela.blit(label, (pos_c[0]+2, pos_c[1]+2))

    for bx, by in bombas:
        if IMG_BOMBA:
            tela.blit(IMG_BOMBA,(bx,by))
        else:
            ct=(bx+GRID//2,by+GRID//2)
            pygame.draw.circle(tela,(30,30,30),ct,GRID//2)
            pygame.draw.circle(tela,(255,90,30),ct,GRID//2,2)
            pygame.draw.line(tela,(255,180,60),(ct[0]+1,by),(ct[0]+5,by-5),2)

    for cpu in cobras_cpu:
        if not cpu._eliminado: cpu.draw()
    if p1: p1.draw(morte=(estado==FIM and p1.morta))
    if p2: p2.draw(morte=(estado==FIM and p2.morta))

    draw_notifs()

    if estado==FIM:
        pan=pygame.Surface((720,180),pygame.SRCALPHA)
        pan.fill((10,10,20,210))
        tela.blit(pan,(LARGURA//2-360,ALTURA//2-100))
        centralizar(fonte_g.render(vencedor,True,AMARELO),  ALTURA//2-90)
        centralizar(fonte_m.render(msg_fim, True,BRANCO),   ALTURA//2-20)
        centralizar(fonte_p.render("R – Reiniciar     M – Menu",True,(180,180,180)),ALTURA//2+40)

    pygame.display.flip()
    clock.tick(fps_base if estado==JOGANDO else 30)