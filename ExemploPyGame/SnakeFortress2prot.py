import pygame, random, glob, os
pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(16)
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

# ── Modos e Classes ───────────────────────────────────────────────────────────────
MODO_CLASSICO, MODO_VERSUS, MODO_GUERRA, MODO_GUERRA_COOP = "classico", "versus", "guerra", "guerra_coop"
DOIS_JOGADORES_MODOS = (MODO_VERSUS, MODO_GUERRA_COOP)
COM_CPUS_MODOS       = (MODO_GUERRA, MODO_GUERRA_COOP)

# DADOS: [Vida, Vel, Cor, [Desc1, Desc2]]
DADOS_CLASSES = {
    "Scout":    [125, 1.33, (255, 80, 80), ["HP: 125 | Velocidade: 133%", "Ágil e difícil de atingir."]],
    "Soldier":  [200, 0.90, (220, 220, 60), ["HP: 200 | Velocidade: 90%",  "Habilidade: Foguete (100 de dano)."]],
    "Pyro":     [175, 1.00, (255, 120, 40), ["HP: 175 | Velocidade: 100%", "Habilidade: Fogo (40 de dano / 6s)."]],
    "Demoman":  [175, 0.95, (140, 60, 200), ["HP: 175 | Velocidade: 95%",  "Bombas e 25% Res. Explosiva."]],
    "Heavy":    [300, 0.80, (200, 80, 80), ["HP: 300 | Velocidade: 80%",  "Vida alta, mas lento."]],
    "Engineer": [150, 1.00, (255, 200, 50), ["HP: 150 | Velocidade: 100%", "Equilibrado: Atributos padrão."]],
    "Medic":    [150, 1.08, (60, 220, 140), ["HP: 150 | Velocidade: 108%", "Regeneração e Ubercarga (Invencível)."]],
    "Sniper":   [125, 1.04, (80, 200, 255), ["HP: 125 | Velocidade: 104%", "Flechas: 360 cabeça / 120 corpo."]],
    "Spy":      [125, 1.04, (200, 80, 180), ["HP: 125 | Velocidade: 104%", "Backstab (10s CD): Mata ao atingir o rabo."]],
}
NOME_CLASSES = list(DADOS_CLASSES.keys())
N_CLASSES    = len(NOME_CLASSES)
_NOMES_LOW   = [n.lower() for n in NOME_CLASSES]
DOT_COR_CLASSES = [d[2] for d in DADOS_CLASSES.values()]

# ── Combate e Itens ─────────────────────────────────────────────────────────────
DANO_ATAQUE_BASE, DANO_ATAQUE_BIFE, CARGAS_BIFE_MAX, COOLDOWN_ATAQUE_MS = 50, 80, 3, 1000
DANO_BOMBA, DANO_BOMBA_CRIT, CHANCE_BOMBA_CRIT = 100, 190, 0.2
TIPO_BIFE, TIPO_FISHCAKE, TIPO_DALOKOHS, TIPO_BANANA, TIPO_SANDVICH = range(5)
N_TIPOS, VELOCIDADE_BASE_FATOR, TICKS_BANANA, TICKS_DALOKOHS = 5, 0.60, 15, 64
COR_COMIDA  = [(200,50,50),(255,140,60),(100,60,30),(255,220,30),(240,220,160)]
NOME_COMIDA = ["Bife", "Fishcake", "Dalokohs", "Banana", "Sandvich"]
PESOS_COMIDA = [1.0, 2.0, 1.0, 0.5, 1.0]
# ── Setup Pygame ────────────────────────────────────────────────────────────────
tela  = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("SNAKE FORTRESS 2")
clock = pygame.time.Clock()
fs = [pygame.font.SysFont("Arial", s, True) for s in [22, 56, 30, 18, 14, 20, 120]]
fonte, fonte_g, fonte_m, fonte_p, fonte_fx, fonte_sel, fonte_cont = fs
DURACAO_CONTAGEM_MS = 3000

def _img(path, sz=GRID):
    try: return pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), (sz, sz))
    except: return None
def _som(b, vol=1.0):
    for e in (".wav", ".ogg"):
        try:
            s = pygame.mixer.Sound(b + e); s.set_volume(vol); return s
        except: pass
    return None
def _fundo(p):
    try: img = pygame.image.load(p).convert()
    except: return None
    w, h = img.get_size(); s = max(LARGURA/w, ALTURA/h)
    nw, nh = int(w*s)+1, int(h*s)+1
    img = pygame.transform.smoothscale(img, (nw, nh))
    sup = pygame.Surface((LARGURA, ALTURA))
    sup.blit(img, (0, 0), ((nw-LARGURA)//2, (nh-ALTURA)//2, LARGURA, ALTURA))
    return sup

IMG_BOMBA_NORMAL = _img("imagens/bomb.png")
IMG_BOMBA_CRIT   = _img("imagens/critbomb.png") or _img("imagens/critbombs.png")
IMG_ROCKET       = _img("imagens/rocket.png")
SOM_EXPLODE, SOM_CRIT_EXPLODE, SOM_ROCKET = [_som(f"sons/{s}") for s in ["explode1", "crit_explode1", "rocket_shoot"]]
MAPAS_NOMES      = ["2fort", "badlands", "barnblitz", "gorge", "hoodoo", "steel", "upward", "snakewater"]
IMGS_FUNDOS      = [i for i in [_fundo(f"imagens/{m}.jpg") or _fundo(f"imagens/{m}.jpeg") for m in MAPAS_NOMES] if i]
IMG_MENU         = random.choice(IMGS_FUNDOS) if IMGS_FUNDOS else _fundo("imagens/menu_fundo.jpg")
IMGS_FRUTA       = [_img(f"imagens/fruta{i}.png") for i in range(1, 6)]
_FB_VIVA, _FB_MORTA = {"heavy": "imagens/HeavyFace2.png", "soldier": "imagens/Soldier2.png"}, {"heavy": "imagens/Heavyded.png", "soldier": "imagens/cabeca_p2_morte.png"}
def _ld(n, s, sz=GRID):
    return _img(f"imagens/{n}_{s}.png", sz) or _img(_FB_VIVA.get(n) if s=="viva" else _FB_MORTA.get(n), sz)
IMG_CLASSE_VIVA  = [_ld(n, "viva") for n in _NOMES_LOW]
IMG_CLASSE_MORTA = [_ld(n, "morta") for n in _NOMES_LOW]
IMG_CLASSE_SEL   = [_ld(n, "viva", 80) for n in _NOMES_LOW]
SOM_MORTE, SOM_VITORIA, SOM_COMEMORA = ([_som(f"sons/{n}_{s}", 0.8) for n in _NOMES_LOW] for s in ("morte","vitoria","comemora"))
SOM_MELEE = [_som(f"sons/melee _frying_pan_0{i}") for i in range(1, 5)]
def tocar(s):
    if s: s.play()

def _listar_falas(cl, oc):
    m = {"Demoman":"Demolines","Engineer":"Engielines"}
    d = f"sons/{m.get(cl, cl.capitalize()+'lines' if cl not in ['Scout','Sniper','Spy'] else cl.lower()+'lines')}"
    if not os.path.exists(d): return []
    sin = {"dor":["dor","pain"],"vitoria":["vitoria","win"],"morte":["morte","die"],"matou":["matou","kill"],"atacar":["atacar","attack","battlecry"]}
    ts, ss = sin.get(oc, [oc]), []
    for f in os.listdir(d):
        if any(t in f.lower() for t in ts) and f.lower().endswith((".mp3", ".wav", ".ogg")):
            s = pygame.mixer.Sound(f"{d}/{f}"); s.set_volume(0.8); ss.append(s)
    return ss

def tocar_fala(cobra, ocasiao):
    # Excessão para sons de morte: tocam sempre (interrompendo outros) e apenas uma vez.
    if ocasiao == "morte":
        if getattr(cobra, "falou_morte", False):
            return
        if hasattr(cobra, "canal_fala") and cobra.canal_fala:
            cobra.canal_fala.stop()
        sons = getattr(cobra, "falas", {}).get("morte", [])
        if sons:
            cobra.canal_fala = random.choice(sons).play()
            cobra.falou_morte = True
        return

    if hasattr(cobra, "canal_fala") and cobra.canal_fala and cobra.canal_fala.get_busy():
        return
    sons = getattr(cobra, "falas", {}).get(ocasiao, [])
    if sons:
        cobra.canal_fala = random.choice(sons).play()

def todas_reagem_matou(v, ts, m=None):
    if getattr(v, "falou_matou", False): return
    cs = [c for c in ts if c not in ({v}|(m or set())) and not c.morta and not getattr(c, "_eliminado", False)]
    if cs: cs.sort(key=lambda c: abs(c.cabeca[0]-v.cabeca[0]) + abs(c.cabeca[1]-v.cabeca[1])); tocar_fala(cs[0], "matou")
def tocar_administrator(oc):
    d = "sons/administrator"
    if os.path.exists(d):
        fs = [f"{d}/{f}" for f in os.listdir(d) if f.lower().startswith(oc)]
        if fs: tocar(pygame.mixer.Sound(random.choice(fs)))
_musica_atual = None
_notifs = []
def tocar_musica(oc, vol=0.5):
    global _musica_atual
    if oc == _musica_atual: return
    fs = glob.glob(f"sons/musicas/{oc}*.*")
    if fs:
        try:
            pygame.mixer.music.load(random.choice(fs))
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.play(-1)
        except: pass
    else: pygame.mixer.music.stop()
    _musica_atual = oc
def add_notif(txt, cor, x, y, ttl=90): _notifs.append([fonte_fx.render(txt, True, cor), x, y, ttl])
def draw_notifs():
    for n in _notifs[:]:
        n[3] -= 1; s, x, y, t = n; s.set_alpha(min(255, t*4)); tela.blit(s, (x-s.get_width()//2, y-(90-t)//2))
        if t <= 0: _notifs.remove(n)
class Snake:
    def __init__(self, x, y, cor, iv=None, im=None, nome="?"):
        self.body, self.dir, self.size, self.score, self.cor, self.nome, self.morta = [(x, y)], (1, 0), 5, 0, cor, nome, False
        self.ultimo_dir, self.mudou_dir = (1, 0), False
        self.img_viva, self.img_morta, self.vidas, self.t_banana, self.t_dalokohs = iv, im, 1, 0, 0
        info = DADOS_CLASSES.get(nome, [150, 1.0])
        self.vida = self.vida_max = info[0]
        self.fator_vel, self.mov_acc, self.cargas_bife, self.ultimo_ataque = info[1], 0.0, 0, -1000
        self.falas = {o: _listar_falas(nome, o) for o in ["dor","vitoria","morte","matou","atacar"]}
        self.falou_vitoria = self.falou_matou = self.falou_morte = False
        self.canal_fala = None
        self.uber_timer = self.queimando_timer = self.cooldown_especial = self.cooldown_backstab = 0
        self.burn_source = None
    @property
    def acelerado(self): return self.t_banana > 0
    def tick_powerups(self):
        if self.t_banana > 0: self.t_banana -= 1
        if self.t_dalokohs > 0:
            self.t_dalokohs -= 1
            if self.t_dalokohs == 0: self.vida_max -= 50; self.vida = min(self.vida, self.vida_max)
        if self.nome == "Medic": self.vida = min(self.vida_max, self.vida + 10 / max(1, fps_base))
        if self.uber_timer > 0: self.uber_timer -= 1
        if self.queimando_timer > 0:
            self.queimando_timer -= 1
            self.vida -= 40 / (6 * max(1, fps_base))
            if self.vida <= 0 and not self.morta: self.vida = 0; aplicar_dano(self, 0, self.burn_source)
        if self.cooldown_especial > 0: self.cooldown_especial -= 1
        if self.cooldown_backstab > 0: self.cooldown_backstab -= 1
    def move(self):
        self.ultimo_dir, self.mudou_dir = self.dir, False
        x, y = self.body[0]; nx, ny = ((x + self.dir[0]*GRID)//GRID)*GRID, ((y + self.dir[1]*GRID)//GRID)*GRID
        self.body.insert(0, (nx, ny))
        if len(self.body) > self.size: self.body.pop()
    def draw(self, morte=False):
        if not self.body: return
        r, off = GRID//2-2, (GRID-(GRID//2-2)*2)//2
        for i in range(len(self.body)-1, -1, -1):
            p, b = self.body[i], max(100, 255-i*5); c = tuple(min(x, b) for x in self.cor)
            if i == 0: continue
            pygame.draw.circle(tela, c, (p[0]+GRID//2, p[1]+GRID//2), r)
            prev = self.body[i-1]
            if p[0] == prev[0]: pygame.draw.rect(tela, c, (p[0]+off, min(p[1], prev[1])+GRID//2, r*2, GRID))
            else: pygame.draw.rect(tela, c, (min(p[0], prev[0])+GRID//2, p[1]+off, GRID, r*2))
        p0, img = self.body[0], (self.img_morta if morte else self.img_viva)
        if img: tela.blit(img, p0)
        else: pygame.draw.circle(tela, self.cor, (p0[0]+GRID//2, p0[1]+GRID//2), r)
        if self.cargas_bife > 0: pygame.draw.rect(tela, (255,140,40), (p0[0]-2, p0[1]-2, GRID+2, GRID+2), 2, 5)
        if not morte and self.uber_timer > 0: pygame.draw.rect(tela, (0, 255, 255), (p0[0]-4, p0[1]-4, GRID+8, GRID+8), 3, 10)
        if not morte:
            f = max(0.0, min(1.0, self.vida/self.vida_max)); bx, by = p0[0], max(HUD_ALTURA, p0[1]-6)
            pygame.draw.rect(tela, (50,15,15), (bx, by, GRID, 4))
            chp = (255,100,0) if self.queimando_timer > 0 else ((60,220,90) if f>0.5 else ((230,200,40) if f>0.25 else (220,60,60)))
            pygame.draw.rect(tela, chp, (bx, by, int(GRID*f), 4))
    @property
    def cabeca(self): return self.body[0] if self.body else (0, 0)

class SnakeCPU(Snake):
    def __init__(self, x, y, idx):
        super().__init__(x, y, COR_AZUL_CPU, IMG_CLASSE_VIVA[idx], IMG_CLASSE_MORTA[idx], NOME_CLASSES[idx])
        self.classe_idx, self.dot_cor, self._eliminado = idx, DOT_COR_CLASSES[idx], False
        self.som_morte, self.som_vitoria, self.som_comemora = SOM_MORTE[idx], SOM_VITORIA[idx], SOM_COMEMORA[idx]
    def ia(self, comidas, corpos, bomb_pos, todas_vivas, bombas, foguetes, flechas):
        if self.mudou_dir: return
        DIRS, oposto, cab, agora = [(1,0),(-1,0),(0,1),(0,-1)], (-self.ultimo_dir[0], -self.ultimo_dir[1]), self.cabeca, pygame.time.get_ticks()
        can_atk, alvo, md = pode_atacar(self, agora), None, float("inf")
        for c in comidas:
            d = abs(c[0]-cab[0]) + abs(c[1]-cab[1])
            if d < md: md, alvo = d, c
        inimigo_alvo, d_inimigo = None, float("inf")
        for c in todas_vivas:
            if c is self or c.morta or getattr(c, "_eliminado", False): continue
            t_pos = c.body[-1] if self.nome == "Spy" and c.body else (c.body[0] if c.body else None)
            if t_pos:
                d = abs(t_pos[0]-cab[0]) + abs(t_pos[1]-cab[1])
                if d < d_inimigo: d_inimigo, inimigo_alvo = d, t_pos
        dist_p = 6*GRID if self.nome in ["Pyro", "Spy", "Scout"] else 4*GRID
        if (can_atk or self.nome in ["Pyro", "Spy"]) and inimigo_alvo and d_inimigo < dist_p: alvo, md = inimigo_alvo, d_inimigo
        best_s, best_d = -float("inf"), self.dir
        for d in DIRS:
            if d == oposto: continue
            px, py = cab[0]+d[0]*GRID, cab[1]+d[1]*GRID; p = (px, py)
            if fora(p) or p in bomb_pos or p in self.body: continue
            if any(p in c for c in corpos if c is not self.body):
                if can_atk: s = 2000
                else: continue
            else:
                s = 0; tp = p
                for _ in range(10):
                    tp = (tp[0]+d[0]*GRID, tp[1]+d[1]*GRID)
                    if fora(tp) or tp in bomb_pos or any(tp in c for c in corpos): break
                    s += 50
                if alvo: s += (md - abs(p[0]-alvo[0]) - abs(p[1]-alvo[1])) * 3
                s += random.uniform(-0.5, 0.5)
            if s > best_s: best_s, best_d = s, d
        self.dir, self.mudou_dir = best_d, True
        if self.cooldown_especial <= 0:
            if self.nome in ["Soldier", "Sniper"]:
                dx, dy = self.dir
                for dist in range(2, 11):
                    px, py = cab[0]+dx*dist*GRID, cab[1]+dy*dist*GRID
                    if any(p[0]==px and p[1]==py for c in todas_vivas if c is not self for p in c.body):
                        executar_habilidade(self, todas_vivas, bombs, foguetes, flechas); break
            elif self.nome == "Medic" and self.vida < self.vida_max*0.6 or (self.nome == "Demoman" and any(any(abs(p[0]-cab[0])<=3*GRID and abs(p[1]-cab[1])<=3*GRID for p in c.body) for c in todas_vivas if c is not self)):
                executar_habilidade(self, todas_vivas, bombas, foguetes, flechas)
def pos_livre(cobras, bombas, cset):
    occ = cset | {(x,y) for x,y,_ in bombas}
    for c in cobras: occ.update(c.body)
    while True:
        p = (random.randint(0, LARGURA//GRID-1)*GRID, random.randint(Y_MIN_CELLS, ALTURA//GRID-1)*GRID)
        if p not in occ: return p
def add_comida(cobras, bombas, cset):
    p, ps = pos_livre(cobras, bombas, cset), list(PESOS_COMIDA)
    if modo_jogo == MODO_CLASSICO: ps[TIPO_BIFE] = 0.0
    t = random.choices(range(N_TIPOS), weights=ps)[0]
    return p, t, IMGS_FRUTA[t]
def update_bombas(nv, cobras, bombas, cset):
    while len(bombas) < min(max(0, (nv-1)*2), 20):
        p = pos_livre(cobras, bombas, cset)
        bombas.append((p[0], p[1], random.random() < CHANCE_BOMBA_CRIT))
    return bombas
def bomba_em(pos, bombas):
    for x, y, c in bombas:
        if (x, y) == pos: return c
def remover_bomba(pos, bombas):
    for i, (x, y, c) in enumerate(bombas):
        if (x, y) == pos: bombas.pop(i); return
def fora(p): return p[0] < 0 or p[0] >= LARGURA or p[1] < HUD_ALTURA or p[1] >= ALTURA
def aplicar_powerup(c, t):
    cx, cy = c.cabeca
    if t == TIPO_BIFE:
        c.cargas_bife = min(CARGAS_BIFE_MAX, c.cargas_bife + 1)
        add_notif(f"⚔ ATAQUE+ ({c.cargas_bife}/{CARGAS_BIFE_MAX})", (255,80,80), cx, cy)
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
            c.vida = min(c.vida_max, c.vida + v); add_notif(txt, cor, cx, cy)
def novo_jogo(modo, idx1, idx2=None):
    _notifs.clear(); p1 = Snake(196, 364, COR_P1, IMG_CLASSE_VIVA[idx1], IMG_CLASSE_MORTA[idx1], NOME_CLASSES[idx1])
    p2 = Snake(784, 364, COR_P2, IMG_CLASSE_VIVA[idx2], IMG_CLASSE_MORTA[idx2], NOME_CLASSES[idx2]) if modo in DOIS_JOGADORES_MODOS and idx2 is not None else None
    if p2: p2.dir = p2.ultimo_dir = (-1, 0)
    cpus = []
    if modo in COM_CPUS_MODOS:
        ids = [i for i in range(N_CLASSES) if i not in ({idx1} | ({idx2} if idx2 is not None else set()))]
        for i, cidx in enumerate(ids):
            p = pos_livre([p1]+([p2] if p2 else [])+cpus, [], set())
            c = SnakeCPU(*p, cidx); d = random.choice([(1,0),(-1,0),(0,1),(0,-1)]); c.dir = c.ultimo_dir = d; cpus.append(c)
    todas, cset, coms, ctps, cims = [p1]+([p2] if p2 else [])+cpus, set(), [], [], []
    for _ in range(max(3, (1+len(cpus))//2)):
        p, t, im = add_comida(todas, [], cset); coms.append(p); ctps.append(t); cims.append(im); cset.add(p)
    return p1, p2, cpus, coms, ctps, cims, [], [], []

class Projetil:
    def __init__(self, x, y, dx, dy, dano=100, dono=None): self.x, self.y, self.dx, self.dy, self.dano, self.dono = x, y, dx, dy, dano, dono
    def move(self): self.x += self.dx*GRID; self.y += self.dy*GRID
    def fora(self): return self.x < -GRID or self.x > LARGURA or self.y < HUD_ALTURA-GRID or self.y > ALTURA

def update_foguetes(nv, cobras, foguetes):
    if random.random() < 0.02 + nv*0.01:
        for _ in range(10):
            l = random.randint(0, 3)
            fx, fy, fdx, fdy = [(-GRID, random.randint(Y_MIN_CELLS, ALTURA//GRID-1)*GRID, 1, 0), (LARGURA, random.randint(Y_MIN_CELLS, ALTURA//GRID-1)*GRID, -1, 0), (random.randint(0, LARGURA//GRID-1)*GRID, HUD_ALTURA, 0, 1), (random.randint(0, LARGURA//GRID-1)*GRID, ALTURA-GRID, 0, -1)][l]
            if all(all(abs(s[0]-fx) >= 4*GRID or abs(s[1]-fy) >= 4*GRID for s in c.body) for c in cobras):
                foguetes.append(Projetil(fx, fy, fdx, fdy)); tocar(SOM_ROCKET); break
    for f in foguetes[:]:
        f.move()
        if f.fora(): foguetes.remove(f)
    return foguetes

def checar_comer(c, coms, ctps, cims, cset, vivas, bombs):
    if c.cabeca in cset:
        i = coms.index(c.cabeca); t = ctps[i]; c.score += 10; c.size += 1; cset.discard(c.cabeca)
        coms.pop(i); ctps.pop(i); cims.pop(i); aplicar_powerup(c, t)
        np, nt, ni = add_comida(vivas, bombs, cset); coms.append(np); ctps.append(nt); cims.append(ni); cset.add(np)

def pode_atacar(c, ms): return ms - c.ultimo_ataque >= COOLDOWN_ATAQUE_MS
def aplicar_dano(c, dano, atk=None):
    if c.uber_timer > 0: return
    s_motivo = atk if isinstance(atk, str) else (atk.nome if hasattr(atk, "nome") else str(atk))
    if c.nome == "Demoman" and "explosivo" in s_motivo.lower(): dano = int(dano*0.75)
    c.vida -= dano; cx, cy = c.cabeca; add_notif(f"-{int(dano)} HP" + (f" ({s_motivo})" if s_motivo else ""), (255,70,70), cx, cy, 60)
    if c.vida > 0: tocar_fala(c, "dor")
    elif not c.morta: tocar_fala(c, "morte"); tocar_fala(atk, "matou")

def aplicar_explosao(px, py, dano, mot, vivas):
    for c in vivas:
        if any(abs(s[0]-px) <= 2*GRID and abs(s[1]-py) <= 2*GRID for s in c.body): aplicar_dano(c, dano, mot)

def executar_habilidade(c, vivas, bombs, roks, flas):
    if c.cooldown_especial > 0 or c.morta: return
    cx, cy, dx, dy = c.cabeca[0], c.cabeca[1], c.dir[0], c.dir[1]
    if c.nome == "Soldier": roks.append(Projetil(cx+dx*2*GRID, cy+dy*2*GRID, dx, dy)); tocar(SOM_ROCKET); c.cooldown_especial = 40
    elif c.nome == "Sniper": flas.append(Projetil(cx+dx*2*GRID, cy+dy*2*GRID, dx, dy, dono=c)); c.cooldown_especial = 50
    elif c.nome == "Medic": c.uber_timer, c.cooldown_especial = 5*fps_base, 20*fps_base
    elif c.nome == "Demoman":
        for d in [(dy, -dx), (-dy, dx)]:
            px, py = cx+d[0]*GRID, cy+d[1]*GRID
            if not fora((px, py)): bombs.append((px, py, False))
        c.cooldown_especial = 60

def processar_colisoes(vivas, bombs, roks, flas, ms):
    mortas = set()
    for c in vivas:
        cab = c.cabeca
        if fora(cab) or cab in c.body[1:] or c.vida <= 0: mortas.add(c); continue
        if c.nome == "Spy" and c.cooldown_backstab <= 0:
            for o in vivas:
                if o is not c and o not in mortas and len(o.body) > 1 and cab == o.body[-1]: aplicar_dano(o, o.vida_max, c); c.cooldown_backstab = 10*fps_base
        if c.nome == "Pyro":
            for o in vivas:
                if o is not c and o not in mortas and (o.cabeca in c.body or cab in o.body): o.queimando_timer, o.burn_source = 6*fps_base, c
        crit = bomba_em(cab, bombs)
        if crit is not None:
            remover_bomba(cab, bombs); tocar(SOM_CRIT_EXPLODE if crit else SOM_EXPLODE)
            aplicar_explosao(cab[0], cab[1], DANO_BOMBA_CRIT if crit else DANO_BOMBA, "explosivo crítico" if crit else "explosivo", vivas)
        for f in roks[:]:
            if any(abs(p[0]-f.x) < GRID and abs(p[1]-f.y) < GRID for p in c.body):
                tocar(SOM_EXPLODE); aplicar_explosao(f.x, f.y, f.dano, "explosivo", vivas); roks.remove(f)
        for f in flas[:]:
            if f.x == cab[0] and f.y == cab[1]: aplicar_dano(c, 360, f.dono); flas.remove(f)
            elif any(p[0]==f.x and p[1]==f.y for p in c.body[1:]): aplicar_dano(c, 120, f.dono); flas.remove(f)
        if c in mortas: continue
        for o in vivas:
            if o is not c and o not in mortas and cab in o.body and pode_atacar(c, ms):
                aplicar_dano(o, DANO_ATAQUE_BIFE if c.cargas_bife > 0 else (25 if c.nome=="Spy" else DANO_ATAQUE_BASE), c)
                if c.cargas_bife > 0: c.cargas_bife -= 1
                tocar(random.choice(SOM_MELEE)); c.ultimo_ataque = ms
    for c in vivas:
        if c.vida <= 0: mortas.add(c)
    return mortas
def nomes_restantes(cobras_cpu, n=3):
    r = [c for c in cobras_cpu if not c._eliminado]
    v = " & ".join(c.nome for c in r[:n])
    return (v + (f" +{len(r)-n}" if len(r) > n else "")) if r else "?"
def draw_grade():
    for x in range(0, LARGURA+1, GRID): pygame.draw.line(tela, (25,25,35), (x, HUD_ALTURA), (x, ALTURA))
    for y in range(Y_MIN_CELLS*GRID, ALTURA+1, GRID): pygame.draw.line(tela, (25,25,35), (0, y), (LARGURA, y))
    pygame.draw.rect(tela, (80,80,100), (0, HUD_ALTURA, LARGURA, ALTURA-HUD_ALTURA), 3)

def draw_hud(p1, p2, cpus, nv):
    pygame.draw.rect(tela, HUD, (0, 0, LARGURA, HUD_ALTURA))
    def _ic(c):
        s = (f" ⚔×{c.cargas_bife}" if c.cargas_bife > 0 else "") + (" ⚡" if c.acelerado else "") + (f" ❤×{c.vidas}" if c.vidas > 1 else "")
        if c.uber_timer > 0: s += f" 🛡️UBER:{c.uber_timer/fps_base:.1f}s"
        elif c.cooldown_especial > 0: s += f" ⏱️CD:{c.cooldown_especial/fps_base:.1f}s"
        if c.nome == "Spy" and c.cooldown_backstab > 0: s += f" 🔪BS:{c.cooldown_backstab/fps_base:.1f}s"
        return s
    lbl = f"P1‑{p1.nome}: {p1.score} HP {int(p1.vida)}/{p1.vida_max}{_ic(p1)}"
    if p2: lbl += f"  P2‑{p2.nome}: {p2.score} HP {int(p2.vida)}/{p2.vida_max}{_ic(p2)}"
    tela.blit(fonte.render(lbl + f"  Nível: {nv}", True, BRANCO), (10, 8))
    for i, cpu in enumerate(cpus):
        xd = LARGURA - 20 - i*22
        pygame.draw.circle(tela, cpu.dot_cor if not cpu._eliminado else (60,60,60), (xd, 20), 7)
        if cpu._eliminado: pygame.draw.line(tela, (200,60,60), (xd-5,15), (xd+5,25), 2)
        m = fonte_p.render(cpu.nome[:2], True, BRANCO); tela.blit(m, (xd - m.get_width()//2, 30))
def centralizar(s, y): tela.blit(s, (LARGURA//2 - s.get_width()//2, y))
CARD_W, CARD_H, CARD_GAP_X, CARD_GAP_Y = 298, 163, 18, 14
SEL_X0, SEL_Y0 = (LARGURA-3*CARD_W-2*CARD_GAP_X)//2, 112
def _card_rect(i): col, row = i%3, i//3; return pygame.Rect(SEL_X0+col*(CARD_W+CARD_GAP_X), SEL_Y0+row*(CARD_H+CARD_GAP_Y), CARD_W, CARD_H)
def _card_at(mx, my):
    for i in range(N_CLASSES):
        if _card_rect(i).collidepoint(mx, my): return i
    return -1
def draw_selecao(passo, p1_idx, p2_idx, hover):
    if IMG_MENU: tela.blit(IMG_MENU,(0,0)); ov = pygame.Surface((LARGURA,ALTURA), pygame.SRCALPHA); ov.fill((0,0,0,178)); tela.blit(ov,(0,0))
    else: tela.fill(FUNDO)
    ct, msg, sub = ((235,70,70), "JOGADOR 1 – ESCOLHA SUA CLASSE", "WASD para jogar | 1-9 ou clique | ESC = Menu") if passo==1 else ((120,190,55), "JOGADOR 2 – ESCOLHA SUA CLASSE", "Setas para jogar | 1-9 ou clique | ESC = P1 reescolhe")
    centralizar(fonte_m.render(msg, True, ct), 18); centralizar(fonte_p.render(sub, True, (155,155,155)), 58)
    bloq = {p1_idx, p2_idx} - {-1}
    for i in range(N_CLASSES):
        r, dc, b = _card_rect(i), DOT_COR_CLASSES[i], (i in bloq)
        hov, p1, p2 = (i == hover and not b), (i == p1_idx), (i == p2_idx)
        bg = (32,32,42) if b else tuple(min(255, c//2+60) if hov else max(8, c//5+10) for c in dc)
        borda = (235,70,70) if p1 else ((120,190,55) if p2 else ((60,60,70) if b else (BRANCO if hov else dc)))
        pygame.draw.rect(tela, bg, r, border_radius=10); pygame.draw.rect(tela, borda, r, 3, 10)
        tela.blit(fonte_p.render(str(i+1), True, AMARELO if not b else (65,65,65)), (r.x+8, r.y+8))
        img, ix, iy = IMG_CLASSE_SEL[i], r.x+(CARD_W-80)//2, r.y+16
        if img:
            tela.blit(img, (ix, iy))
            if b: d = pygame.Surface((80,80), pygame.SRCALPHA); d.fill((0,0,0,145)); tela.blit(d, (ix,iy))
        else:
            pygame.draw.circle(tela, (45,45,55) if b else dc, (r.x+CARD_W//2, r.y+56), 36); pygame.draw.circle(tela, borda, (r.x+CARD_W//2, r.y+56), 36, 2)
            ini = fonte_g.render(NOME_CLASSES[i][0], True, BRANCO if not b else (75,75,75)); tela.blit(ini, (r.x+CARD_W//2-ini.get_width()//2, r.y+56-ini.get_height()//2))
        ns = fonte_sel.render(NOME_CLASSES[i], True, BRANCO if not b else (70,70,70)); tela.blit(ns, (r.x+CARD_W//2-ns.get_width()//2, r.y+96))
        d1, d2 = [fonte_fx.render(d, True, (200,200,200) if not b else (60,60,60)) for d in DADOS_CLASSES[NOME_CLASSES[i]][3]]
        tela.blit(d1, (r.x+CARD_W//2-d1.get_width()//2, r.y+122)); tela.blit(d2, (r.x+CARD_W//2-d2.get_width()//2, r.y+140))
        if p1 or p2: tag = fonte_p.render("P1 ✓" if p1 else "P2 ✓", True, (235,80,80) if p1 else (120,190,55)); tela.blit(tag, (r.right-tag.get_width()-8, r.y+8))
        elif b:
            pygame.draw.line(tela, (110,40,40), (r.x+12,r.y+12), (r.right-12,r.bottom-12), 3); pygame.draw.line(tela, (110,40,40), (r.right-12,r.y+12), (r.x+12,r.bottom-12), 3)
            tag = fonte_p.render("TOMADO", True, (100,100,100)); tela.blit(tag, (r.right-tag.get_width()-8, r.y+8))
    centralizar(fonte_p.render("ESC – Voltar", True, (110,110,110)), ALTURA-26)

estado, modo_jogo, selecao_passo, selecao_p1, selecao_p2, hover_sel = MENU, MODO_GUERRA, 1, -1, -1, -1
p1 = p2 = None; cobras_cpu, coms, ctps, cims, roks, flas, bombs, cset = [], [], [], [], [], [], [], set()
vencedor, msg_fim, tick_global, fps_base, contagem_inicio_ms = "", "", 0, 8, 0

def iniciar_rodada():
    global cset, vencedor, msg_fim, tick_global, estado, contagem_inicio_ms
    cset, vencedor, msg_fim, tick_global, contagem_inicio_ms, estado = set(coms), "", "", 0, pygame.time.get_ticks(), CONTAGEM
    tocar_musica("combate")
    if modo_jogo in COM_CPUS_MODOS: tocar_administrator("inicio")
    for c in random.sample([p1]+([p2] if p2 else [])+cobras_cpu, min(len(cobras_cpu)+1, 3)): tocar_fala(c, "atacar")

def processar_selecao(idx):
    global selecao_passo, selecao_p1, selecao_p2, p1, p2, cobras_cpu, coms, ctps, cims, bombs, roks, flas
    if idx in {selecao_p1, selecao_p2}: return
    if selecao_passo == 1:
        selecao_p1 = idx
        if modo_jogo in DOIS_JOGADORES_MODOS: selecao_passo = 2
        else: p1, p2, cobras_cpu, coms, ctps, cims, bombs, roks, flas = novo_jogo(modo_jogo, idx); iniciar_rodada()
    else: selecao_p2 = idx; p1, p2, cobras_cpu, coms, ctps, cims, bombs, roks, flas = novo_jogo(modo_jogo, selecao_p1, idx); iniciar_rodada()
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
                if k in d1:
                    nova = d1[k]
                    if not p1.mudou_dir and nova != (-p1.ultimo_dir[0], -p1.ultimo_dir[1]):
                        p1.dir, p1.mudou_dir = nova, True
                if k == pygame.K_SPACE: executar_habilidade(p1, vivas, bombs, roks, flas)
                if p2:
                    d2 = {pygame.K_UP:(0,-1), pygame.K_DOWN:(0,1), pygame.K_LEFT:(-1,0), pygame.K_RIGHT:(1,0)}
                    if k in d2:
                        nova = d2[k]
                        if not p2.mudou_dir and nova != (-p2.ultimo_dir[0], -p2.ultimo_dir[1]):
                            p2.dir, p2.mudou_dir = nova, True
                    if k in (pygame.K_RSHIFT, pygame.K_RETURN, pygame.K_KP_ENTER): executar_habilidade(p2, vivas, bombas, roks, flas)
                if k == pygame.K_m and (p1.morta and (p2 is None or p2.morta)):
                    # Força fim da partida (desiste de assistir)
                    v_atuais = [c for c in cobras_cpu if not c._eliminado]
                    if v_atuais:
                        vencedor = v_atuais[0].nome
                        msg_fim = f"{vencedor} estava vencendo!"
                    else:
                        vencedor = "EMPATE"
                        msg_fim = "Todos morreram!"
                    estado = FIM
                    tocar_administrator("fracasso")
            elif estado == FIM:
                if k == pygame.K_r: p1, p2, cobras_cpu, comidas, ctipos, cimgs, bombas, foguetes, flechas = novo_jogo(modo_jogo, selecao_p1, selecao_p2 if modo_jogo in DOIS_JOGADORES_MODOS else None); iniciar_rodada()
                if k == pygame.K_c:
                    if IMGS_FUNDOS: IMG_MENU = random.choice(IMGS_FUNDOS)
                    selecao_passo, selecao_p1, selecao_p2, hover_sel, estado = 1, -1, -1, -1, SELECAO
                if k == pygame.K_m:
                    if IMGS_FUNDOS: IMG_MENU = random.choice(IMGS_FUNDOS)
                    p1 = p2 = None; cobras_cpu, comidas, ctipos, cimgs, bombas, foguetes, flechas, cset, vencedor, msg_fim, estado = [], [], [], [], [], [], [], set(), "", "", MENU
    if estado == SELECAO:
        tocar_musica("menu")
        draw_selecao(selecao_passo, selecao_p1, selecao_p2, hover_sel)
        pygame.display.flip()
        clock.tick(30)
        continue
    if estado == MENU:
        tocar_musica("menu")
        if IMG_MENU: tela.blit(IMG_MENU, (0,0)); ov = pygame.Surface((LARGURA,ALTURA), pygame.SRCALPHA); ov.fill((0,0,0,140)); tela.blit(ov,(0,0))
        else: tela.fill(FUNDO)
        centralizar(fonte_g.render("SNAKE FORTRESS 2", True, AMARELO), 100); centralizar(fonte_m.render("LUTE ATÈ A MORTE!", True, BRANCO), 165)
        for i, t in enumerate(["1 – Clássico", "2 – Versus", "3 – Guerra", "4 – Guerra Coop"]): centralizar(fonte_m.render(f"{i+1} – {t}", True, BRANCO), 222 + i*34)
        y0, leg = ALTURA - 160, [("Bife","⚔ +Dano corpo a corpo",(255,80,80)),("Fishcake","Cura 25% HP máx",(255,140,60)),("Dalokohs","+50 vida máx (8s)",(150,100,40)),("Banana","⚡ Cura 50% HP+vel",(255,220,30)),("Sandvich","Cura 50% HP máx",(200,160,255))]
        for n, d, c in leg:
            im = IMGS_FRUTA[NOME_COMIDA.index(n)]
            if im: tela.blit(im, (20, y0-2))
            tela.blit(fonte.render(f"  {n}: {d}", True, c), (40, y0)); y0 += 26
        creditos = [
            "Assets: Valve Software Inc.",
            "Trilha Sonora: Valve Studio Orchestra",
            "Obrigado à Valve por criar Team Fortress 2!"
        ]
        for i, linha in enumerate(creditos):
            txt_c = fonte_fx.render(linha, True, (130, 130, 130))
            tela.blit(txt_c, (LARGURA - txt_c.get_width() - 20, ALTURA - 65 + i * 18))
        pygame.display.flip(); clock.tick(30); continue

    if estado == CONTAGEM:
        dt = pygame.time.get_ticks() - contagem_inicio_ms
        if dt >= DURACAO_CONTAGEM_MS: estado = JOGANDO

    if estado == JOGANDO:
        tick_global += 1; v_cpu = [c for c in cobras_cpu if not c._eliminado]
        vivas = [j for j in [p1, p2] if j and not j.morta] + v_cpu
        cset = set(coms)
        for c in vivas: c.tick_powerups()
        sc = (p1.score if p1 else 0) + (p2.score if p2 else 0) + sum(c.score for c in v_cpu)
        nv = sc // 100 + 1; fps_base = max(3, int((8+nv)*VELOCIDADE_BASE_FATOR))
        corps, bpos = [c.body for c in vivas], {(x,y) for x,y,_ in bombs}
        for c in v_cpu: c.ia(coms, corps, bpos, vivas, bombs, roks, flas)
        for c in vivas:
            c.mov_acc += c.fator_vel * (2 if c.acelerado else 1)
            while c.mov_acc >= 1.0: c.move(); c.mov_acc -= 1.0; checar_comer(c, coms, ctps, cims, cset, vivas, bombs)
        bombs = update_bombas(nv, vivas, bombs, cset); roks = update_foguetes(nv, vivas, roks)
        for f in flas[:]:
            f.move()
            if f.fora(): flas.remove(f)
        ms = pygame.time.get_ticks(); mortas = processar_colisoes(vivas, bombs, roks, flas, ms)
        for c in v_cpu:
            if c in mortas: todas_reagem_matou(c, vivas, mortas); c._eliminado, c.body = True, []
        for j in [p1, p2]:
            if j and j in mortas:
                todas_reagem_matou(j, vivas, mortas)
                j.morta, j.body = True, []
        v_fin = [j for j in [p1, p2] if j and not j.morta] + [c for c in cobras_cpu if not c._eliminado]
        if modo_jogo == MODO_CLASSICO and p1.morta: vencedor, msg_fim, estado = "FIM DE JOGO", f"Pontuação: {p1.score}", FIM
        elif modo_jogo != MODO_CLASSICO and len(v_fin) <= 1:
            estado = FIM
            if len(v_fin) == 1:
                v = v_fin[0]; vencedor = "PLAYER 1" if v==p1 else ("PLAYER 2" if v==p2 else v.nome)
                msg_fim = f"{vencedor} venceu!"; tocar_administrator("vitoria" if v in [p1,p2] else "fracasso"); tocar_musica("fimdejogo" if v in [p1,p2] else None)
            else: vencedor, msg_fim = "EMPATE", "Ninguém sobreviveu!"; tocar_administrator("fracasso")

    tela.fill(FUNDO_FLASH if (p1.score if p1 else 0) >= 200 and pygame.time.get_ticks()//150%2 else FUNDO); draw_grade()
    if p1: draw_hud(p1, p2, cobras_cpu, (p1.score+(p2.score if p2 else 0))//50+1)
    for p, t, im in zip(coms, ctps, cims):
        if im: tela.blit(im, p)
        else: pygame.draw.rect(tela, COR_COMIDA[t], (*p, GRID, GRID), border_radius=4)
    for x, y, crit in bombs:
        im = IMG_BOMBA_CRIT if crit else IMG_BOMBA_NORMAL
        if im: tela.blit(im, (x, y))
        else: pygame.draw.circle(tela, (255,30,30) if crit else (255,90,30), (x+GRID//2, y+GRID//2), GRID//2, 2)
    for f in roks:
        if IMG_ROCKET: tela.blit(IMG_ROCKET, (f.x, f.y))
        else: pygame.draw.rect(tela, (200,200,200), (f.x, f.y, GRID, GRID))
    for f in flas:
        e = (f.x+GRID//2+f.dx*GRID//2, f.y+GRID//2+f.dy*GRID//2)
        pygame.draw.line(tela, (255, 220, 100), (f.x+GRID//2-f.dx*GRID//2, f.y+GRID//2-f.dy*GRID//2), e, 4)
        pygame.draw.circle(tela, (255, 220, 100), e, 3)
    for c in cobras_cpu:
        if not c._eliminado: c.draw()
    if p1: p1.draw(p1.morta)
    if p2: p2.draw(p2.morta)
    draw_notifs()
    if estado == CONTAGEM:
        dt = pygame.time.get_ticks() - contagem_inicio_ms
        seg = 3 - (dt // 1000)
        if seg > 0:
            txt = fonte_cont.render(str(seg), True, AMARELO); cx, cy = LARGURA//2 - txt.get_width()//2, ALTURA//2 - txt.get_height()//2
            for dx, dy in ((-3,0),(3,0),(0,-3),(0,3)): tela.blit(fonte_cont.render(str(seg), True, (0,0,0)), (cx+dx, cy+dy))
            tela.blit(txt, (cx, cy)); centralizar(fonte_m.render("Prepare-se...", True, BRANCO), ALTURA//2 + 80)
    if estado == JOGANDO and (p1.morta and (p2 is None or p2.morta)): centralizar(fonte_p.render("VOCÊ MORREU! [M] Sair ou assista...", True, BRANCO), ALTURA - 30)
    if estado == FIM:
        for c in [p1, p2]+cobras_cpu:
            if c and not c.morta and not getattr(c, "_eliminado", False) and not c.falou_vitoria: tocar_fala(c, "vitoria"); c.falou_vitoria = True
        p = pygame.Surface((760, 205), pygame.SRCALPHA); p.fill((10,10,20,215)); tela.blit(p, (LARGURA//2-380, ALTURA//2-112))
        centralizar(fonte_g.render(vencedor, True, AMARELO), ALTURA//2-102); centralizar(fonte_m.render(msg_fim, True, BRANCO), ALTURA//2-35)
        centralizar(fonte_p.render("R – Reiniciar | C – Trocar Classe | M – Menu", True, (175,175,175)), ALTURA//2+35)
    pygame.display.flip(); clock.tick(fps_base if estado == JOGANDO else 30)