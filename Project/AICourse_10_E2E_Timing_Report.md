# Raport End-to-End — AICourse #10 (Gradient Descent Course)

**Scop:** test complet, de la request HTTP până la `READY`, al pipeline-ului AI Teaching, cu două schimbări noi aplicate:
1. **Vision captioning pentru figuri** (`gemini-2.5-flash`, vezi raportul anterior `GEMINI_3.5_FLASH_VISION_TEST_REPORT.md`)
2. **Timp de narațiune adaptiv per pagină** (nu mai e fix 60s pe toate paginile — vezi `estimate_target_seconds()` în `tableExtraction.py`)

---

## Request

```
POST /api/teacher/classes/35/ai-courses/
file=Gradient_Descent_Course.pdf
title=Gradient Descent (full E2E timing test, dynamic narration)
```

**Pornit la:** `2026-06-24T15:35:45.368Z` (UTC) = **18:35:45.368** ora locală — acesta e momentul `created_at` returnat de API la creare (cronometrul "oficial" de start).

---

## Cronologie pe etape

| Etapă | Terminat la (local) | Durată etapă |
|---|---|---|
| Request → AICourse creat | 18:35:45.368 | — |
| **EXTRACTING** (rasterizare + LayoutLMv3 + vision figuri) | 18:40:04.641 | **4m 19.3s** |
| **NARRATING** (Groq, 10 pagini) | 18:41:52.356 | **1m 47.7s** |
| **TTS** (Deepgram, 10 pagini) | 18:50:01.469 | **8m 9.1s** |
| **CHROMA** (indexare RAG) | 18:50:10.247 | **8.8s** |
| **TOTAL (request → READY)** | | **14m 24.9s** |

TTS rămâne, ca și la cursurile anterioare, pasul cel mai costisitor (~57% din timpul total).

---

## Timp de narațiune adaptiv (schimbarea cerută)

Înainte: toate paginile primeau un target fix de **60s** (~130 cuvinte), indiferent de cât conținut aveau.

Acum: `estimate_target_seconds()` calculează un target din câte caractere de text relevant are pagina + bonus pentru formule/figuri, limitat la **20-110s**. Modelul Groq primește acest target ca *ghid*, nu ca o cotă strictă — i s-a spus explicit să vorbească mai puțin pe pagini sărace/de tranziție și mai mult pe pagini dense sau cu concepte importante, chiar dincolo de ghid dacă e nevoie.

| Pagină | Target calculat | Mod | Cuvinte generate | Durată estimată vorbire |
|---|---|---|---|---|
| 1 | 20s *(minim — pagină de titlu/copertă)* | auto | 76 | 35.1s |
| 2 | 67s | auto | 146 | 67.4s |
| 3 | 110s *(plafon — conținut dens)* | auto | 321 | 148.2s |
| 4 | 110s | auto | 320 | 147.7s |
| 5 | 110s | auto | 293 | 135.2s |
| 6 | 110s | auto | 312 | 144.0s |
| 7 | 107s | auto | 272 | 125.5s |
| 8 | 110s | auto | 299 | 138.0s |
| 9 | 110s | auto | 290 | 133.8s |
| 10 | 110s | auto | 292 | 134.8s |

**Observații:**
- Pagina 1 (titlu, foarte puțin text) a primit corect un target minim de 20s — în vechiul sistem ar fi fost forțată la 60s/~130 cuvinte, cu padding artificial.
- Paginile 3-10 (dense, cu formule și figuri) au atins plafonul de 110s, iar modelul a generat narațiuni **și mai lungi decât targetul** (125-148s vorbire estimată) — exact comportamentul dorit: pe conținut important, modelul "ia timpul de care are nevoie" în loc să se încadreze rigid într-un cuvânt-țintă.
- Diferența dintre pagina cea mai scurtă (20s target / 35s vorbire) și cea mai lungă (110s target / 148s vorbire) e de ~4×, față de uniformitatea de 60s/pagină de înainte.

---

## Vision captioning (figuri)

19 blocuri „figure" detectate pe cele 10 pagini, **0 descrise** de Gemini în acest run — cota gratuită zilnică (`gemini-2.5-flash`, limit 20 req/zi) era deja epuizată din testele anterioare din această sesiune (cursul #9 a consumat-o). Fallback-ul gol funcționează corect (nu a blocat pipeline-ul), dar pentru rezultate complete ar trebui rulat după reset de cotă sau cu o cheie API separată/plătită.

---

## Concluzie

Pipeline-ul complet (request → curs predat de AI, gata pentru elevi) a durat **~14m 25s** pentru acest PDF de 10 pagini. Timpul de narațiune e acum proporțional cu relevanța/densitatea fiecărei pagini, nu uniform — confirmat de variația 20s→110s din tabelul de mai sus.
