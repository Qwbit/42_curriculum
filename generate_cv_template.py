"""
Curriculum Vitae — TEMPLATE in stile 42 Roma ELIS.

Questo file e' una versione "clean" di generate_cv.py: tutti i dati
personali sono stati rimossi e sostituiti da segnaposto e commenti che
spiegano cosa va inserito in ciascun campo. Modifica solo la sezione
``CV = CVData(...)`` e (opzionalmente) la palette nella parte in alto.

Caratteristiche
---------------
* Sidebar nera con logo (es. ``42_Elis.png``) e foto profilo.
* Font:
    - Source Sans 3       -> titoli/sezioni (TITLE_FONT)
    - Assistant           -> corpo testo (BODY_FONT)
    - Glacial Indifference-> testo sidebar / contatti (SIDEBAR_FONT)
  I file TTF vengono scaricati automaticamente in ./fonts/ alla prima
  esecuzione (con fallback a Helvetica se la rete non e' disponibile).

Dipendenze: pip install reportlab
Uso:        python generate_cv_template.py [-o cv.pdf]
                                            [-p foto_profilo.jpg]
                                            [-l logo.png]
"""

from __future__ import annotations

import argparse
import os
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


# ---------------------------------------------------------------------------
# Palette template
# ---------------------------------------------------------------------------
SIDEBAR_BG          = HexColor("#000000")  # nero pieno come da demo
ACCENT              = HexColor("#1FB6B0")
TEXT_DARK           = HexColor("#1F1F1F")
TEXT_MUTED          = HexColor("#5A5A5A")
SIDEBAR_TEXT        = HexColor("#FFFFFF")
SIDEBAR_TEXT_MUTED  = HexColor("#B8BEC4")


# ---------------------------------------------------------------------------
# Font setup (download automatico con fallback Helvetica)
# ---------------------------------------------------------------------------
HERE      = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(HERE, "fonts")

# (nome reportlab, file locale, lista URL alternativi)
FONT_SOURCES: List[Tuple[str, str, List[str]]] = [
    # Google Fonts distribuisce solo il variable font; ReportLab ne usa
    # l'istanza di default. Lo registriamo sia come Regular che Bold.
    ("Assistant", "Assistant-VF.ttf", [
        "https://raw.githubusercontent.com/google/fonts/main/ofl/assistant/Assistant%5Bwght%5D.ttf",
        "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/assistant/Assistant%5Bwght%5D.ttf",
    ]),
    ("Assistant-Bold", "Assistant-VF.ttf", []),  # stesso file, registrato sotto altro nome
    ("SourceSans", "SourceSans3-Regular.ttf", [
        "https://cdn.jsdelivr.net/gh/adobe-fonts/source-sans@release/TTF/SourceSans3-Regular.ttf",
        "https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-Regular.ttf",
    ]),
    ("SourceSans-Bold", "SourceSans3-Bold.ttf", [
        "https://cdn.jsdelivr.net/gh/adobe-fonts/source-sans@release/TTF/SourceSans3-Bold.ttf",
        "https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-Bold.ttf",
    ]),
    ("GlacialIndifference", "GlacialIndifference-Regular.ttf", [
        "https://raw.githubusercontent.com/TechGamerExpert/Glacial-Indifference-Clone/main/GlacialIndifference-Regular.ttf",
        "https://cdn.jsdelivr.net/gh/TechGamerExpert/Glacial-Indifference-Clone@main/GlacialIndifference-Regular.ttf",
    ]),
    ("GlacialIndifference-Bold", "GlacialIndifference-Bold.ttf", [
        "https://raw.githubusercontent.com/TechGamerExpert/Glacial-Indifference-Clone/main/GlacialIndifference-Bold.ttf",
        "https://cdn.jsdelivr.net/gh/TechGamerExpert/Glacial-Indifference-Clone@main/GlacialIndifference-Bold.ttf",
    ]),
]


def _download(url: str, dest: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r, open(dest, "wb") as f:
            f.write(r.read())
        return os.path.getsize(dest) > 1024
    except Exception:
        if os.path.exists(dest):
            try:
                os.remove(dest)
            except OSError:
                pass
        return False


def setup_fonts() -> dict:
    os.makedirs(FONTS_DIR, exist_ok=True)
    registered: set = set()

    for ps_name, fname, urls in FONT_SOURCES:
        path = os.path.join(FONTS_DIR, fname)
        if not os.path.isfile(path) and urls:
            for u in urls:
                if _download(u, path):
                    break
        if os.path.isfile(path):
            try:
                pdfmetrics.registerFont(TTFont(ps_name, path))
                registered.add(ps_name)
            except Exception as e:
                print(f"[font] errore registrando {ps_name}: {e}")

    def pick(*names: str, fallback: str) -> str:
        for n in names:
            if n in registered:
                return n
        return fallback

    mapping = {
        "TITLE":         pick("SourceSans-Bold", "Assistant-Bold",
                              fallback="Helvetica-Bold"),
        "TITLE_REG":     pick("SourceSans", "Assistant",
                              fallback="Helvetica"),
        "BODY":          pick("Assistant", "SourceSans",
                              fallback="Helvetica"),
        "BODY_BOLD":     pick("Assistant-Bold", "SourceSans-Bold",
                              fallback="Helvetica-Bold"),
        "SIDEBAR":       pick("GlacialIndifference", "Assistant",
                              "SourceSans", fallback="Helvetica"),
        "SIDEBAR_BOLD":  pick("GlacialIndifference-Bold", "Assistant-Bold",
                              "SourceSans-Bold",
                              fallback="Helvetica-Bold"),
    }

    missing = {n for n, _, _ in FONT_SOURCES} - registered
    if missing:
        print("[font] non scaricati (fallback Helvetica): " +
              ", ".join(sorted(missing)))
    return mapping


# ---------------------------------------------------------------------------
# Modelli dati
# ---------------------------------------------------------------------------
@dataclass
class Job:
    role: str
    company: str
    period: str
    bullets: List[str] = field(default_factory=list)


@dataclass
class Education:
    title: str
    school: str
    period: str
    place: str = ""
    note: str = ""


@dataclass
class CVData:
    name: str
    surname: str
    title: str
    birthday: str
    nationality: str
    profile: str
    address: str
    email: str
    phone: str
    website: str
    github: str
    skills: List[str]
    experience: List[Job]
    education: List[Education]


# ---------------------------------------------------------------------------
# Contenuto del CV
# ---------------------------------------------------------------------------
# >>> COMPILA QUI I TUOI DATI. Tutti i campi sono stringhe (oppure liste di
# >>> stringhe / oggetti Job ed Education). Lascia un campo vuoto ("") se
# >>> non vuoi mostrarlo, ma evita di rimuoverne la chiave.
CV = CVData(
    # NOME proprio in MAIUSCOLO (es. "MARIO"). Compare grande in alto a destra.
    name="NOME",
    # COGNOME in MAIUSCOLO (es. "ROSSI"). Compare sotto al nome.
    surname="COGNOME",
    # Ruolo professionale / job title sotto il nome (es. "SOFTWARE DEVELOPER").
    title="JOB TITLE",
    # Data di nascita in formato libero (es. "01/01/1990").
    birthday="GG/MM/AAAA",
    # Nazionalita' (es. "Italian", "Italiana").
    nationality="Nazionalita'",
    # Profilo personale: 3-6 righe che riassumono chi sei, cosa sai fare e
    # quali sono i tuoi obiettivi professionali. Tono professionale, in
    # prima persona o impersonale.
    profile=(
        "Breve descrizione professionale di te stesso: ambito di "
        "specializzazione, tecnologie principali, esperienze chiave e "
        "obiettivi. Mantieni il testo conciso (max ~6 righe) e in tono "
        "professionale."
    ),
    # Indirizzo completo (via, civico, CAP, citta', paese).
    address="Via Esempio 1, 00100 Citta', Paese",
    # Indirizzo email professionale.
    email="nome.cognome@email.com",
    # Numero di telefono con prefisso internazionale (es. "(+39) 333 123 4567").
    phone="(+39) 000 000 0000",
    # Sito web personale / portfolio (URL completo). Lascia "" se non ne hai.
    website="https://miosito.example.com/",
    # Profilo GitHub / GitLab (URL completo). Lascia "" se non lo vuoi mostrare.
    github="https://github.com/tuo-utente",
    # Elenco di competenze chiave: ogni stringa appare come una riga nella
    # sezione "Skills summary" della sidebar. Tieni le voci brevi (max ~60
    # caratteri) per evitare a-capo poco eleganti.
    skills=[
        "Competenza 1 (es. linguaggi / framework)",
        "Competenza 2 (es. strumenti / DevOps)",
        "Competenza 3 (es. metodologie / soft skill)",
        # Aggiungi o rimuovi voci a piacere.
    ],
    # Esperienze lavorative in ordine cronologico inverso (la piu' recente
    # in cima). Ciascuna voce e' un oggetto Job(role, company, period,
    # bullets) dove ``bullets`` e' una lista di descrizioni puntate.
    experience=[
        Job(
            # Ruolo ricoperto (es. "Software Developer").
            "Ruolo / Job Title",
            # Azienda + citta'/paese (es. "Azienda S.r.l. - Roma, Italia").
            "Azienda - Citta', Paese",
            # Periodo (es. "01/2024 - Present" oppure "06/2020 - 12/2022").
            "MM/AAAA - MM/AAAA",
            # Bullet points: ogni stringa diventa un punto elenco. Inizia
            # con un verbo d'azione e descrivi risultati misurabili.
            [
                "Descrivi una responsabilita' o un risultato chiave.",
                "Aggiungi un secondo bullet con tecnologie usate o impatto.",
                # "Altro bullet opzionale...",
            ],
        ),
        # Job(
        #     "Ruolo precedente",
        #     "Altra azienda - Citta', Paese",
        #     "MM/AAAA - MM/AAAA",
        #     ["Bullet 1", "Bullet 2"],
        # ),
        # Aggiungi tutte le esperienze che vuoi.
    ],
    # Formazione in ordine cronologico inverso. Ciascuna voce e' un oggetto
    # Education(title, school, period, place="", note="").
    education=[
        Education(
            # Titolo conseguito (es. "Laurea in Informatica", "Diploma 42").
            "Titolo / Diploma",
            # Scuola o universita' + eventuale dettaglio del corso.
            "Istituto o universita'",
            # Periodo (es. "09/2018 - 07/2022" oppure "2020 - Present").
            "MM/AAAA - MM/AAAA",
            # Localita' (opzionale, es. "Roma, Italia").
            "Citta', Paese",
            # Nota opzionale: voto finale, tesi, menzioni speciali, ecc.
            "Voto / nota opzionale",
        ),
        # Education(
        #     "Diploma di scuola superiore",
        #     "Nome dell'istituto",
        #     "09/2013 - 07/2018",
        #     "Citta', Paese",
        # ),
    ],
)


# ---------------------------------------------------------------------------
# Utility di layout
# ---------------------------------------------------------------------------
def wrap_text(text: str, max_width: float, font_name: str,
              font_size: float, c: canvas.Canvas) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current = ""
    for w in words:
        candidate = w if not current else current + " " + w
        if c.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def draw_paragraph(c: canvas.Canvas, text: str, x: float, y: float,
                   max_width: float, font_name: str, font_size: float,
                   leading: float, color: Color) -> float:
    c.setFont(font_name, font_size)
    c.setFillColor(color)
    for line in wrap_text(text, max_width, font_name, font_size, c):
        c.drawString(x, y, line)
        y -= leading
    return y


def draw_section_header(c: canvas.Canvas, text: str, x: float, y: float,
                        accent: Color, text_color: Color,
                        font_name: str, font_size: float = 11,
                        center_x: Optional[float] = None,
                        underline_w: float = 28) -> float:
    """Disegna un'intestazione di sezione in maiuscolo con tratto teal sotto.

    Se center_x è valorizzato, testo e tratto vengono centrati attorno
    a quella coordinata (usato nella sidebar come nel template demo).
    """
    label = text.upper()
    c.setFont(font_name, font_size)
    c.setFillColor(text_color)
    if center_x is not None:
        tw = c.stringWidth(label, font_name, font_size)
        c.drawString(center_x - tw / 2, y, label)
        c.setStrokeColor(accent)
        c.setLineWidth(1.2)
        c.line(center_x - underline_w / 2, y - 4,
               center_x + underline_w / 2, y - 4)
    else:
        c.drawString(x, y, label)
        c.setStrokeColor(accent)
        c.setLineWidth(1.2)
        c.line(x, y - 4, x + underline_w, y - 4)
    return y - 14


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def draw_sidebar(c: canvas.Canvas, data: CVData,
                 photo_path: Optional[str], logo_path: Optional[str],
                 fonts: dict, page_w: float, page_h: float) -> None:
    sw = 70 * mm
    c.setFillColor(SIDEBAR_BG)
    c.rect(0, 0, sw, page_h, fill=1, stroke=0)

    pad = 10 * mm
    x = pad
    inner_w = sw - 2 * pad
    y = page_h - 12 * mm

    # --- Foto profilo (cerchio) ---
    photo_diam = 40 * mm
    photo_cx = sw / 2
    photo_cy = y - photo_diam / 2

    if photo_path and os.path.isfile(photo_path):
        c.saveState()
        p = c.beginPath()
        p.circle(photo_cx, photo_cy, photo_diam / 2)
        c.clipPath(p, stroke=0, fill=0)
        c.drawImage(photo_path,
                    photo_cx - photo_diam / 2,
                    photo_cy - photo_diam / 2,
                    width=photo_diam, height=photo_diam,
                    preserveAspectRatio=True, mask='auto')
        c.restoreState()
        # bordo bianco sottile
        c.setStrokeColor(SIDEBAR_TEXT)
        c.setLineWidth(0.6)
        c.circle(photo_cx, photo_cy, photo_diam / 2, stroke=1, fill=0)
    else:
        c.setFillColor(HexColor("#2A2F36"))
        c.circle(photo_cx, photo_cy, photo_diam / 2, fill=1, stroke=0)
        c.setFillColor(SIDEBAR_TEXT)
        c.setFont(fonts["TITLE"], 24)
        initials = (data.name[:1] + data.surname[:1]).upper()
        tw = c.stringWidth(initials, fonts["TITLE"], 24)
        c.drawString(photo_cx - tw / 2, photo_cy - 8, initials)

    y = photo_cy - photo_diam / 2 - 6 * mm

    # --- Logo 42 Roma ELIS ---
    if logo_path and os.path.isfile(logo_path):
        logo_h = 22 * mm
        logo_w = 28 * mm
        c.drawImage(logo_path,
                    photo_cx - logo_w / 2, y - logo_h,
                    width=logo_w, height=logo_h,
                    preserveAspectRatio=True, mask='auto')
        y -= logo_h + 6 * mm
    else:
        c.setFillColor(SIDEBAR_TEXT)
        c.setFont(fonts["TITLE"], 22)
        badge = "42"
        tw = c.stringWidth(badge, fonts["TITLE"], 22)
        c.drawString(photo_cx - tw / 2, y - 6 * mm, badge)
        y -= 10 * mm
        c.setFont(fonts["SIDEBAR"], 9)
        c.setFillColor(SIDEBAR_TEXT_MUTED)
        sub = "ROMA ELIS"
        tw = c.stringWidth(sub, fonts["SIDEBAR"], 9)
        c.drawString(photo_cx - tw / 2, y, sub)
        y -= 8 * mm

    # --- Contact me at (centrato come da demo) ---
    y = draw_section_header(c, "Contact me at", x, y, ACCENT,
                            SIDEBAR_TEXT, fonts["TITLE"], 10.5,
                            center_x=photo_cx, underline_w=22)
    y -= 4
    contact_values = [
        data.address,
        data.email,
        data.phone,
        data.website,
        data.github,
    ]
    for value in contact_values:
        c.setFont(fonts["SIDEBAR"], 8)
        c.setFillColor(SIDEBAR_TEXT)
        for line in wrap_text(value, inner_w, fonts["SIDEBAR"], 8, c):
            tw = c.stringWidth(line, fonts["SIDEBAR"], 8)
            c.drawString(photo_cx - tw / 2, y, line)
            y -= 10
        y -= 2

    y -= 6

    # --- Skills summary (centrato, senza pallini come da demo) ---
    y = draw_section_header(c, "Skills summary", x, y, ACCENT,
                            SIDEBAR_TEXT, fonts["TITLE"], 10.5,
                            center_x=photo_cx, underline_w=22)
    y -= 4
    for s in data.skills:
        c.setFont(fonts["SIDEBAR"], 8)
        c.setFillColor(SIDEBAR_TEXT)
        for line in wrap_text(s, inner_w, fonts["SIDEBAR"], 8, c):
            tw = c.stringWidth(line, fonts["SIDEBAR"], 8)
            c.drawString(photo_cx - tw / 2, y, line)
            y -= 10
        y -= 2


# ---------------------------------------------------------------------------
# Colonna principale
# ---------------------------------------------------------------------------
def ensure_space(c: canvas.Canvas, y: float, needed: float,
                 page_h: float, draw_sidebar_fn) -> float:
    if y - needed < 18 * mm:
        c.showPage()
        draw_sidebar_fn()
        return page_h - 20 * mm
    return y


def draw_main(c: canvas.Canvas, data: CVData, fonts: dict,
              page_w: float, page_h: float, draw_sidebar_fn) -> None:
    left = 78 * mm
    right_margin = 12 * mm
    main_w = page_w - left - right_margin
    y = page_h - 18 * mm

    # Nome
    c.setFillColor(TEXT_DARK)
    c.setFont(fonts["TITLE"], 26)
    c.drawString(left, y, data.name)
    y -= 9 * mm
    c.drawString(left, y, data.surname)
    y -= 8 * mm

    # Titolo
    c.setFont(fonts["TITLE"], 11)
    c.setFillColor(ACCENT)
    c.drawString(left, y, data.title)
    y -= 9 * mm

    # Personal data (come da demo, in alto a destra)
    y = draw_section_header(c, "Personal data", left, y,
                            ACCENT, TEXT_DARK, fonts["TITLE"], 11,
                            underline_w=32)
    y -= 4
    for label, value in (("Birthday", data.birthday),
                         ("Nationality", data.nationality)):
        c.setFont(fonts["BODY_BOLD"], 9)
        c.setFillColor(TEXT_DARK)
        c.drawString(left, y, label)
        c.setFont(fonts["BODY"], 9)
        c.setFillColor(TEXT_MUTED)
        c.drawString(left + 28 * mm, y, value)
        y -= 12
    y -= 6

    # Personal profile
    y = draw_section_header(c, "Personal profile", left, y,
                            ACCENT, TEXT_DARK, fonts["TITLE"], 11,
                            underline_w=32)
    y -= 4
    y = draw_paragraph(c, data.profile, left, y, main_w,
                       fonts["BODY"], 9.2, 12, TEXT_DARK)
    y -= 6

    # Work experience
    y = ensure_space(c, y, 30, page_h, draw_sidebar_fn)
    y = draw_section_header(c, "Work experience", left, y,
                            ACCENT, TEXT_DARK, fonts["TITLE"], 11,
                            underline_w=32)
    y -= 6

    for job in data.experience:
        block_h = 14 + 12 + sum(
            12 * max(1, len(wrap_text(b, main_w - 8,
                                       fonts["BODY"], 8.8, c)))
            for b in job.bullets) + 6
        y = ensure_space(c, y, block_h, page_h, draw_sidebar_fn)

        c.setFont(fonts["BODY_BOLD"], 10)
        c.setFillColor(TEXT_DARK)
        c.drawString(left, y, job.role)
        y -= 12
        c.setFont(fonts["BODY"], 8.6)
        c.setFillColor(TEXT_MUTED)
        c.drawString(left, y, f"{job.company}  |  {job.period}")
        y -= 11
        for b in job.bullets:
            c.setFillColor(ACCENT)
            c.circle(left + 2, y + 3, 1.1, fill=1, stroke=0)
            y = draw_paragraph(c, b, left + 8, y, main_w - 8,
                               fonts["BODY"], 8.8, 11, TEXT_DARK) - 1
        y -= 4

    # Educational history
    y = ensure_space(c, y, 30, page_h, draw_sidebar_fn)
    y = draw_section_header(c, "Educational history", left, y,
                            ACCENT, TEXT_DARK, fonts["TITLE"], 11,
                            underline_w=32)
    y -= 6

    for ed in data.education:
        block_h = 14 + 12 + (12 if ed.note else 0) + 6
        y = ensure_space(c, y, block_h, page_h, draw_sidebar_fn)

        c.setFont(fonts["BODY_BOLD"], 10)
        c.setFillColor(TEXT_DARK)
        c.drawString(left, y, ed.title)
        y -= 12
        c.setFont(fonts["BODY"], 8.6)
        c.setFillColor(TEXT_MUTED)
        meta = f"{ed.school}  |  {ed.period}"
        if ed.place:
            meta += f"  |  {ed.place}"
        y = draw_paragraph(c, meta, left, y, main_w,
                           fonts["BODY"], 8.6, 11, TEXT_MUTED)
        if ed.note:
            y = draw_paragraph(c, ed.note, left, y, main_w,
                               fonts["BODY"], 8.8, 11, TEXT_DARK)
        y -= 4


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def build_pdf(output: str, photo: Optional[str],
              logo: Optional[str]) -> None:
    fonts = setup_fonts()
    page_w, page_h = A4
    c = canvas.Canvas(output, pagesize=A4)
    # Imposta titolo e autore del PDF combinando nome e cognome dell'utente.
    full_name = f"{CV.name.title()} {CV.surname.title()}".strip()
    c.setTitle(f"Curriculum Vitae - {full_name}")
    c.setAuthor(full_name)

    def sidebar_fn():
        draw_sidebar(c, CV, photo, logo, fonts, page_w, page_h)

    sidebar_fn()
    draw_main(c, CV, fonts, page_w, page_h, sidebar_fn)
    c.save()
    print(f"PDF generato: {os.path.abspath(output)}")


def _default(name: str) -> Optional[str]:
    """Restituisce il percorso assoluto se ``name`` esiste accanto allo script.

    Comodo per auto-rilevare la foto profilo e il logo: basta posizionarli
    nella stessa cartella di questo file con i nomi attesi (vedi ``main``).
    """
    full = os.path.join(HERE, name)
    return full if os.path.isfile(full) else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Generatore CV stile 42")
    # Nome del PDF di output. Cambialo o passa -o sulla riga di comando.
    parser.add_argument("--output", "-o",
                        default="cv.pdf",
                        help="Nome del file PDF generato")
    # Foto profilo: di default cerca un file 'foto_profilo.jpg' nella stessa
    # cartella dello script. Sostituisci con il tuo file (jpg/png).
    parser.add_argument("--photo", "-p",
                        default=_default("foto_profilo.jpg"),
                        help="Foto profilo per la sidebar (jpg/png)")
    # Logo: di default cerca 'logo.png' accanto allo script. Sostituisci con
    # il logo della tua scuola/azienda o lascialo assente.
    parser.add_argument("--logo", "-l",
                        default=_default("logo.png"),
                        help="Logo per la sidebar (png)")
    args = parser.parse_args()
    build_pdf(args.output, args.photo, args.logo)


if __name__ == "__main__":
    main()
