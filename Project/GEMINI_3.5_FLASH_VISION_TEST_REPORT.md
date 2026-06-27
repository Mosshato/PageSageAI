# Test: descriere figuri cu `gemini-3.5-flash` (vision)

**Scop:** testa `describe_figure()` (folosit în `Functionalities/PDFExtraction/textAndImageExtraction.py`) cu modelul `gemini-3.5-flash` în loc de `gemini-2.5-flash`, pe figuri reale extrase din cursul "Gradient Descent Course" (AICourse #9), cu timing explicit pe fiecare apel.

**Metodă:** script standalone (`test_vision_35.py`), folosește exact același prompt și retry logic (backoff exponențial, 3 încercări, 5s → 10s → 20s) ca în pipeline-ul real, dar apelează direct `client.models.generate_content(model="gemini-3.5-flash", ...)`. Cropurile sunt decupate din PNG-urile deja generate ale cursului 9, folosind bbox-urile normalizate (0-1000) salvate în `page_000N.json`.

**Timer:** `t0 = time.perf_counter()` înainte de fiecare `generate_content`, `elapsed = time.perf_counter() - t0` după (succes sau eroare finală a unui attempt) — exact ca un cronometru pornit/oprit per apel, cu retry-urile incluse în timpul total al item-ului.

---

## Rezultate

Run pornit: **2026-06-24T18:19:04**

| # | Pagină | Conținut figură | Încercări | Timp total | Rezultat |
|---|---|---|---|---|---|
| 1 | 1 | background/copertă full-page | 2 (1× `503`, apoi succes) | **96.00s** | ✅ |
| 2 | 1 | figură reală de conținut | 1 | **12.83s** | ✅ |
| 3 | 2 | iconiță mică repetată (footer, pe toate slide-urile) | 1 | **15.98s** | ✅ |
| 4 | 10 | figură mare de conținut | 2 (1× `503`, apoi succes) | **95.83s** | ✅ |

**Timp total test:** ~220.6s (**3 min 41s**) pentru 4 figuri → medie **~55s/figură** (cu retry-uri incluse).

### Descrierile generate (text complet)

**1. Pagina 1 — background/copertă:**
> "This diagram illustrates the process of gradient descent using a U-shaped curve that represents a cost function. A sequence of circular markers descen[ds]..."

**2. Pagina 1 — figură conținut:**
> "This illustration depicts the process of gradient descent optimization along a U-shaped cost function curve. A sequence of circular markers, accompani[ed]..."

**3. Pagina 2 — iconiță footer:**
> "The image shows a horizontal, light purple bar with rounded ends and a soft, slightly blurred outline. It functions as a decorative graphical divider..."

**4. Pagina 10 — figură conținut:**
> "This image shows a dark-themed text card titled 'RECAP IN THREE SENTENCES' summarizing the core concepts of the gradient descent optimization algorith[m]..."

---

## Concluzii

1. **Calitatea descrierilor e foarte bună** — toate cele 4 sunt specifice și ancorate în conținutul real (curba U de cost function, markeri circulari pentru pașii de descent, cardul de recap, iconița decorativă). Nimic generic.
2. **`gemini-3.5-flash` funcționează**, dar e instabil: 2 din 4 apeluri (50%) au primit `503 UNAVAILABLE` (overload pe server-ul Google) la prima încercare, recuperate abia la a doua. Cele 2 apeluri afectate au luat **~96s și ~96s** (vs. ~13-16s pentru apelurile fără retry) — de **6× mai lent** din cauza overload-ului + backoff.
3. **Comparativ cu `gemini-2.5-flash`** (folosit curent în producție): acesta a răspuns constant rapid și fără erori în testele anterioare din aceeași sesiune — `gemini-3.5-flash` introduce risc real de latență/timeout pe pipeline-ul de extracție dacă e folosit ca model implicit acum (fiind preview, cu capacitate redusă pe partea Google).
4. **Recomandare:** rămân pe `gemini-2.5-flash` ca model implicit pentru `describe_figure()` (stabil, rapid). `gemini-3.5-flash` poate fi reconsiderat când iese din faza de overload/preview, pentru calitate posibil mai bună la text generat — dar diferența de calitate observată aici e marginală față de costul de latență.

---

*Notă tehnică: scriptul de test a avut un bug minor la salvarea JSON-ului brut (path Windows/POSIX mixat în scratchpad), dar toate cele 4 apeluri au rulat și au reușit — datele de mai sus sunt din log-ul de execuție (stdout), nu afectate de acel bug.*
