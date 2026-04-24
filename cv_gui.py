"""
Interfaccia grafica (Tkinter) per compilare i dati del CV e generare il PDF.

Usa il layout/font definiti in ``generate_cv_template.py``: l'utente compila i
campi in una finestra a schede, sceglie foto/logo/output e preme "Genera PDF".

Avvio:
    python cv_gui.py
"""

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List

# Riutilizziamo strutture, palette e funzioni di layout dal template.
import generate_cv_template as tpl
from generate_cv_template import CVData, Education, Job


HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Helper UI
# ---------------------------------------------------------------------------
class LabeledEntry(ttk.Frame):
    """Etichetta + Entry monoriga con tooltip-like description."""

    def __init__(self, master, label: str, hint: str = "", width: int = 60):
        super().__init__(master)
        self.columnconfigure(1, weight=1)
        ttk.Label(self, text=label).grid(row=0, column=0, sticky="w",
                                         padx=(0, 8), pady=2)
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.grid(row=0, column=1, sticky="ew", pady=2)
        if hint:
            ttk.Label(self, text=hint, foreground="#666",
                      font=("Segoe UI", 8)).grid(row=1, column=1,
                                                  sticky="w")

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value: str) -> None:
        self.var.set(value)


class LabeledText(ttk.Frame):
    """Etichetta + Text multiriga."""

    def __init__(self, master, label: str, hint: str = "", height: int = 5):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text=label).grid(row=0, column=0, sticky="w")
        if hint:
            ttk.Label(self, text=hint, foreground="#666",
                      font=("Segoe UI", 8)).grid(row=1, column=0,
                                                  sticky="w")
        self.text = tk.Text(self, height=height, wrap="word")
        self.text.grid(row=2, column=0, sticky="nsew", pady=(2, 0))
        self.rowconfigure(2, weight=1)

    def get(self) -> str:
        return self.text.get("1.0", "end").strip()

    def set(self, value: str) -> None:
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value)


class ScrollableFrame(ttk.Frame):
    """Frame scrollabile verticalmente, pratico per liste dinamiche."""

    def __init__(self, master):
        super().__init__(master)
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        vbar = ttk.Scrollbar(self, orient="vertical",
                             command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")
        self.inner = ttk.Frame(canvas)
        self._win = canvas.create_window((0, 0), window=self.inner,
                                         anchor="nw")

        def _on_inner(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas(event):
            canvas.itemconfigure(self._win, width=event.width)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.inner.bind("<Configure>", _on_inner)
        canvas.bind("<Configure>", _on_canvas)
        canvas.bind_all("<MouseWheel>", _on_mousewheel)


# ---------------------------------------------------------------------------
# Sezioni "ripetibili" (Esperienze / Formazione)
# ---------------------------------------------------------------------------
class JobBlock(ttk.LabelFrame):
    def __init__(self, master, index: int, on_remove):
        super().__init__(master, text=f"Esperienza #{index}")
        self.columnconfigure(0, weight=1)
        self.role = LabeledEntry(self, "Ruolo",
                                 "Es. Software Developer")
        self.role.grid(row=0, column=0, sticky="ew", padx=8, pady=2)
        self.company = LabeledEntry(self, "Azienda + luogo",
                                    "Es. Azienda S.r.l. - Roma, Italia")
        self.company.grid(row=1, column=0, sticky="ew", padx=8, pady=2)
        self.period = LabeledEntry(self, "Periodo",
                                   "Es. 01/2024 - Present")
        self.period.grid(row=2, column=0, sticky="ew", padx=8, pady=2)
        self.bullets = LabeledText(self, "Bullet points (una per riga)",
                                   "Inizia con un verbo d'azione",
                                   height=4)
        self.bullets.grid(row=3, column=0, sticky="ew", padx=8, pady=2)
        ttk.Button(self, text="Rimuovi",
                   command=lambda: on_remove(self)).grid(row=4, column=0,
                                                          sticky="e",
                                                          padx=8, pady=4)

    def to_job(self) -> Job:
        bullets = [b.strip() for b in self.bullets.get().splitlines()
                   if b.strip()]
        return Job(self.role.get(), self.company.get(),
                   self.period.get(), bullets)


class EducationBlock(ttk.LabelFrame):
    def __init__(self, master, index: int, on_remove):
        super().__init__(master, text=f"Formazione #{index}")
        self.columnconfigure(0, weight=1)
        self.title_e = LabeledEntry(self, "Titolo / Diploma",
                                    "Es. Laurea in Informatica")
        self.title_e.grid(row=0, column=0, sticky="ew", padx=8, pady=2)
        self.school = LabeledEntry(self, "Scuola / Universita'",
                                   "Es. Universita' La Sapienza")
        self.school.grid(row=1, column=0, sticky="ew", padx=8, pady=2)
        self.period = LabeledEntry(self, "Periodo",
                                   "Es. 09/2018 - 07/2022")
        self.period.grid(row=2, column=0, sticky="ew", padx=8, pady=2)
        self.place = LabeledEntry(self, "Luogo",
                                  "Es. Roma, Italia (opzionale)")
        self.place.grid(row=3, column=0, sticky="ew", padx=8, pady=2)
        self.note = LabeledEntry(self, "Nota",
                                 "Voto, tesi, menzioni... (opzionale)")
        self.note.grid(row=4, column=0, sticky="ew", padx=8, pady=2)
        ttk.Button(self, text="Rimuovi",
                   command=lambda: on_remove(self)).grid(row=5, column=0,
                                                          sticky="e",
                                                          padx=8, pady=4)

    def to_education(self) -> Education:
        return Education(self.title_e.get(), self.school.get(),
                         self.period.get(), self.place.get(),
                         self.note.get())


# ---------------------------------------------------------------------------
# Finestra principale
# ---------------------------------------------------------------------------
class CVApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generatore CV - stile 42 Roma ELIS")
        self.geometry("820x720")
        self.minsize(720, 600)

        try:
            ttk.Style(self).theme_use("vista")
        except tk.TclError:
            pass

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(10, 4))

        self._build_personal_tab(nb)
        self._build_profile_tab(nb)
        self._build_skills_tab(nb)
        self._build_experience_tab(nb)
        self._build_education_tab(nb)
        self._build_assets_tab(nb)

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=10, pady=8)
        self.status = tk.StringVar(value="Compila i campi e premi Genera PDF.")
        ttk.Label(bar, textvariable=self.status,
                  foreground="#444").pack(side="left")
        ttk.Button(bar, text="Genera PDF",
                   command=self._on_generate).pack(side="right")
        ttk.Button(bar, text="Carica esempio",
                   command=self._load_example).pack(side="right",
                                                     padx=(0, 8))

    # ---- Tabs --------------------------------------------------------------
    def _build_personal_tab(self, nb: ttk.Notebook) -> None:
        tab = ttk.Frame(nb, padding=12)
        nb.add(tab, text="Anagrafica")
        tab.columnconfigure(0, weight=1)

        self.f_name = LabeledEntry(tab, "Nome",
                                   "In MAIUSCOLO. Es. MARIO")
        self.f_surname = LabeledEntry(tab, "Cognome",
                                      "In MAIUSCOLO. Es. ROSSI")
        self.f_title = LabeledEntry(tab, "Job title",
                                    "Es. SOFTWARE DEVELOPER")
        self.f_birthday = LabeledEntry(tab, "Data di nascita",
                                       "Es. 01/01/1990")
        self.f_nationality = LabeledEntry(tab, "Nazionalita'",
                                          "Es. Italian")
        self.f_address = LabeledEntry(tab, "Indirizzo",
                                      "Via, civico, CAP, citta', paese")
        self.f_email = LabeledEntry(tab, "Email")
        self.f_phone = LabeledEntry(tab, "Telefono",
                                    "Con prefisso. Es. (+39) 333 123 4567")
        self.f_website = LabeledEntry(tab, "Sito web",
                                      "URL completo (opzionale)")
        self.f_github = LabeledEntry(tab, "GitHub / GitLab",
                                     "URL completo (opzionale)")
        for i, w in enumerate([self.f_name, self.f_surname, self.f_title,
                                self.f_birthday, self.f_nationality,
                                self.f_address, self.f_email, self.f_phone,
                                self.f_website, self.f_github]):
            w.grid(row=i, column=0, sticky="ew", pady=4)

    def _build_profile_tab(self, nb: ttk.Notebook) -> None:
        tab = ttk.Frame(nb, padding=12)
        nb.add(tab, text="Profilo")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        self.f_profile = LabeledText(
            tab, "Profilo personale",
            "3-6 righe: chi sei, specializzazioni, obiettivi.",
            height=12)
        self.f_profile.grid(row=0, column=0, sticky="nsew")

    def _build_skills_tab(self, nb: ttk.Notebook) -> None:
        tab = ttk.Frame(nb, padding=12)
        nb.add(tab, text="Skills")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        self.f_skills = LabeledText(
            tab, "Competenze (una per riga)",
            "Tieni le voci brevi (~60 caratteri max).",
            height=14)
        self.f_skills.grid(row=0, column=0, sticky="nsew")

    def _build_experience_tab(self, nb: ttk.Notebook) -> None:
        tab = ttk.Frame(nb, padding=8)
        nb.add(tab, text="Esperienze")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        ttk.Button(tab, text="+ Aggiungi esperienza",
                   command=self._add_job).grid(row=0, column=0,
                                                sticky="w", pady=(0, 4))
        self.exp_scroll = ScrollableFrame(tab)
        self.exp_scroll.grid(row=1, column=0, sticky="nsew")
        self.exp_scroll.inner.columnconfigure(0, weight=1)
        self._jobs: List[JobBlock] = []
        self._add_job()

    def _build_education_tab(self, nb: ttk.Notebook) -> None:
        tab = ttk.Frame(nb, padding=8)
        nb.add(tab, text="Formazione")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        ttk.Button(tab, text="+ Aggiungi formazione",
                   command=self._add_edu).grid(row=0, column=0,
                                                sticky="w", pady=(0, 4))
        self.edu_scroll = ScrollableFrame(tab)
        self.edu_scroll.grid(row=1, column=0, sticky="nsew")
        self.edu_scroll.inner.columnconfigure(0, weight=1)
        self._edus: List[EducationBlock] = []
        self._add_edu()

    def _build_assets_tab(self, nb: ttk.Notebook) -> None:
        tab = ttk.Frame(nb, padding=12)
        nb.add(tab, text="File & Output")
        tab.columnconfigure(1, weight=1)

        # Foto
        ttk.Label(tab, text="Foto profilo (jpg/png):").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.photo_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.photo_var).grid(
            row=0, column=1, sticky="ew", pady=4)
        ttk.Button(tab, text="Sfoglia...",
                   command=lambda: self._pick_file(
                       self.photo_var,
                       [("Immagini", "*.jpg *.jpeg *.png")])).grid(
            row=0, column=2, padx=(8, 0))

        # Logo
        ttk.Label(tab, text="Logo (png):").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        self.logo_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.logo_var).grid(
            row=1, column=1, sticky="ew", pady=4)
        ttk.Button(tab, text="Sfoglia...",
                   command=lambda: self._pick_file(
                       self.logo_var, [("PNG", "*.png")])).grid(
            row=1, column=2, padx=(8, 0))

        # Output
        ttk.Label(tab, text="File di output (PDF):").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        self.output_var = tk.StringVar(
            value=os.path.join(HERE, "cv.pdf"))
        ttk.Entry(tab, textvariable=self.output_var).grid(
            row=2, column=1, sticky="ew", pady=4)
        ttk.Button(tab, text="Salva come...",
                   command=self._pick_output).grid(
            row=2, column=2, padx=(8, 0))

        ttk.Label(tab,
                  text=("Suggerimento: i file foto/logo possono restare "
                        "vuoti.\nVerranno auto-rilevati 'foto_profilo.jpg' "
                        "e 'logo.png' accanto allo script."),
                  foreground="#555", font=("Segoe UI", 9)).grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(12, 0))

    # ---- Dynamic blocks ----------------------------------------------------
    def _add_job(self) -> None:
        idx = len(self._jobs) + 1
        block = JobBlock(self.exp_scroll.inner, idx, self._remove_job)
        block.grid(row=idx - 1, column=0, sticky="ew", padx=4, pady=6)
        self._jobs.append(block)

    def _remove_job(self, block: JobBlock) -> None:
        if len(self._jobs) <= 1:
            messagebox.showinfo("Info",
                                "Mantieni almeno una esperienza.")
            return
        block.destroy()
        self._jobs.remove(block)
        for i, b in enumerate(self._jobs, 1):
            b.configure(text=f"Esperienza #{i}")

    def _add_edu(self) -> None:
        idx = len(self._edus) + 1
        block = EducationBlock(self.edu_scroll.inner, idx,
                               self._remove_edu)
        block.grid(row=idx - 1, column=0, sticky="ew", padx=4, pady=6)
        self._edus.append(block)

    def _remove_edu(self, block: EducationBlock) -> None:
        if len(self._edus) <= 1:
            messagebox.showinfo("Info",
                                "Mantieni almeno una voce di formazione.")
            return
        block.destroy()
        self._edus.remove(block)
        for i, b in enumerate(self._edus, 1):
            b.configure(text=f"Formazione #{i}")

    # ---- File pickers ------------------------------------------------------
    def _pick_file(self, var: tk.StringVar, types) -> None:
        path = filedialog.askopenfilename(filetypes=types,
                                          initialdir=HERE)
        if path:
            var.set(path)

    def _pick_output(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialdir=HERE,
            initialfile="cv.pdf")
        if path:
            self.output_var.set(path)

    # ---- Example -----------------------------------------------------------
    def _load_example(self) -> None:
        self.f_name.set("MARIO")
        self.f_surname.set("ROSSI")
        self.f_title.set("SOFTWARE DEVELOPER")
        self.f_birthday.set("01/01/1995")
        self.f_nationality.set("Italian")
        self.f_address.set("Via Roma 1, 00100 Roma, Italia")
        self.f_email.set("mario.rossi@example.com")
        self.f_phone.set("(+39) 333 123 4567")
        self.f_website.set("https://mariorossi.dev")
        self.f_github.set("https://github.com/mariorossi")
        self.f_profile.set(
            "Software developer con esperienza in sviluppo web full-stack "
            "e applicazioni desktop. Appassionato di architetture pulite, "
            "DevOps e automazione. In cerca di sfide tecniche stimolanti.")
        self.f_skills.set(
            "Python, TypeScript, Go\n"
            "React, Node.js, FastAPI\n"
            "Docker, Kubernetes, CI/CD\n"
            "PostgreSQL, Redis\n"
            "Problem solving & teamwork")
        # Sostituisce blocchi correnti
        for j in list(self._jobs):
            j.destroy()
        self._jobs.clear()
        self._add_job()
        self._jobs[0].role.set("Software Developer")
        self._jobs[0].company.set("Esempio S.r.l. - Roma, Italia")
        self._jobs[0].period.set("01/2023 - Present")
        self._jobs[0].bullets.set(
            "Sviluppo di microservizi in Python e Go.\n"
            "Migrazione dell'infrastruttura su Kubernetes.\n"
            "Mentorship di due junior developer.")
        for e in list(self._edus):
            e.destroy()
        self._edus.clear()
        self._add_edu()
        self._edus[0].title_e.set("Laurea in Informatica")
        self._edus[0].school.set("Universita' La Sapienza")
        self._edus[0].period.set("09/2014 - 07/2018")
        self._edus[0].place.set("Roma, Italia")
        self._edus[0].note.set("Voto: 110/110")

    # ---- Build CV ----------------------------------------------------------
    def _collect(self) -> CVData:
        skills = [s.strip() for s in self.f_skills.get().splitlines()
                  if s.strip()]
        jobs = [j.to_job() for j in self._jobs
                if j.role.get() or j.company.get()]
        edus = [e.to_education() for e in self._edus
                if e.title_e.get() or e.school.get()]
        return CVData(
            name=self.f_name.get() or "NOME",
            surname=self.f_surname.get() or "COGNOME",
            title=self.f_title.get() or "JOB TITLE",
            birthday=self.f_birthday.get(),
            nationality=self.f_nationality.get(),
            profile=self.f_profile.get(),
            address=self.f_address.get(),
            email=self.f_email.get(),
            phone=self.f_phone.get(),
            website=self.f_website.get(),
            github=self.f_github.get(),
            skills=skills,
            experience=jobs,
            education=edus,
        )

    def _on_generate(self) -> None:
        output = self.output_var.get().strip()
        if not output:
            messagebox.showerror("Errore",
                                 "Specifica il file di output.")
            return
        photo = self.photo_var.get().strip() or \
            tpl._default("foto_profilo.jpg") or \
            tpl._default("Foto_Profilo.jpeg")
        logo = self.logo_var.get().strip() or \
            tpl._default("logo.png") or \
            tpl._default("42_Elis.png")

        cv = self._collect()
        self.status.set("Generazione in corso...")
        self.update_idletasks()

        def worker():
            try:
                # Sostituisce CV nel modulo template e genera il PDF.
                tpl.CV = cv
                tpl.build_pdf(output, photo or None, logo or None)
                self.after(0, lambda: self._done(output))
            except Exception as exc:  # noqa: BLE001
                self.after(0, lambda: self._fail(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _done(self, output: str) -> None:
        self.status.set(f"PDF generato: {output}")
        if messagebox.askyesno("Fatto",
                               f"PDF generato in:\n{output}\n\n"
                               "Aprirlo ora?"):
            try:
                os.startfile(output)  # type: ignore[attr-defined]
            except Exception:
                pass

    def _fail(self, exc: Exception) -> None:
        self.status.set("Errore durante la generazione.")
        messagebox.showerror("Errore", str(exc))


def main() -> None:
    app = CVApp()
    app.mainloop()


if __name__ == "__main__":
    main()
