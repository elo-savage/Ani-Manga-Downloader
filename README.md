<div align="center">
  <h1>🛸 AniManga Downloader (Ani-Manga)</h1>
  <p><strong>Un'applicazione desktop neo-brutalista per scaricare i tuoi Anime e Manga preferiti!</strong></p>
  <p><i>Costruito interamente tramite <b>Vibecoding</b> 🎵✨</i></p>
</div>

---

## 📖 Cosa fa questo programma?

AniManga Downloader è un'applicazione desktop dal design moderno e accattivante (stile Neo-Brutalista) che ti permette di scaricare in massa capitoli di manga ed episodi di anime. Ti basta incollare il link, selezionare i capitoli o gli episodi che ti interessano e lasciare che il programma faccia il resto, organizzando tutto in comode cartelle.

Attualmente supporta nativamente il download dai seguenti portali italiani:
- 📚 **MangaWorld** (Manga)
- 📺 **AnimeSaturn** (Anime)

## ✨ Funzionalità

- **Interfaccia Neo-Brutalista:** Design pulito, moderno e responsivo.
- **Selezione Intelligente:** Puoi scegliere esattamente quali episodi o capitoli scaricare tramite un selettore di range (es: `1-10, 15`).
- **Download in Parallelo:** Puoi analizzare e scaricare più opere insieme (es. un anime e un manga), ognuna con la propria barra di avanzamento in tempo reale.
- **Multi-Piattaforma:** Il codice può essere compilato per creare eseguibili sia per macOS che per Windows.

## 🚀 Come si usa?

1. **Avvia l'app:** Lancia l'eseguibile scaricato oppure esegui il programma da terminale.
2. **Incolla il Link:** Devi usare il link della **pagina principale dell'anime o del manga** (quella dove c'è la trama e la lista di tutti gli episodi/capitoli).
   - Esempio AnimeSaturn: `https://www.animesaturn.net/anime/one-piece-PmTvj`
   - Esempio MangaWorld: `https://www.mangaworld.mx/manga/1708/one-piece`
   Incolla l'URL nella barra di ricerca dell'applicazione.
3. **Analizza:** Clicca sul pulsante per analizzare il link. L'app troverà in automatico tutti i capitoli o episodi disponibili.
4. **Seleziona e Scarica:** Inserisci il range (es. `1-5` per i primi 5 episodi) e clicca Scarica! Troverai i tuoi file scaricati e ordinati automaticamente sul tuo computer.

## 📥 Download (utenti finali)

Scarica il pacchetto per il tuo sistema dalla pagina [**Releases**](https://github.com/elo-savage/Ani-Manga-Downloader/releases/latest):
- 🍏 **macOS (Apple Silicon / M1–M4):** `AniManga_Downloader_macOS_AppleSilicon.zip`
- 🍏 **macOS (Intel):** `AniManga_Downloader_macOS_Intel.zip`
- 🪟 **Windows:** `AniManga_Downloader_Windows.zip`

Estrai lo zip e avvia l'app: **ffmpeg è già incluso**, non devi installare nulla.

### 🍏 Prima apertura su macOS (avviso "app non verificata")
L'app non è firmata con un account Apple a pagamento, quindi al primo avvio macOS mostra un avviso. Per aprirla:
1. **Tasto destro** (o Ctrl+clic) sull'app → **Apri** → poi di nuovo **Apri** nella finestra che compare.
2. In alternativa: **Impostazioni di Sistema → Privacy e sicurezza**, scorri fino al messaggio sull'app e clicca **Apri comunque**.

Se compare *"l'app è danneggiata e non può essere aperta"* è solo la quarantena di macOS: apri il Terminale ed esegui una volta (sostituisci il percorso con quello reale):
```bash
xattr -cr /percorso/di/AniManga_Downloader.app
```

### 🪟 Prima apertura su Windows (SmartScreen)
Windows può mostrare *"Windows ha protetto il PC"*. Clicca **Ulteriori informazioni → Esegui comunque**.

## 🛠️ Installazione (Per Sviluppatori)

Se vuoi smanettare con il codice, ecco come fare:

### 📋 Prerequisiti
- **Python 3.10+**
- **ffmpeg** installato e raggiungibile nel PATH — è necessario per assemblare gli stream degli anime (HLS):
  - macOS: `brew install ffmpeg`
  - Windows: `choco install ffmpeg` (oppure scaricalo da [gyan.dev](https://www.gyan.dev/ffmpeg/builds/))
  - Linux: `sudo apt install ffmpeg`
- `yt-dlp` viene installato automaticamente da `requirements.txt`.

```bash
# 1. Clona il repository
git clone https://github.com/elo-savage/Ani-Manga-Downloader.git
cd Ani-Manga-Downloader

# 2. Installa i pacchetti richiesti
pip install -r requirements.txt

# 3. Avvia l'applicazione
python3 app.py
```

### 📦 Compilare gli Eseguibili
Se vuoi creare un'app nativa `.app` o `.exe` da distribuire senza far usare il terminale:
- **Su macOS:** Lancia lo script `./build_mac.sh` dal tuo terminale. Troverai l'app macOS nella cartella `dist`.
- **Su Windows:** Fai doppio clic sul file `build_windows.bat` lavorando da un PC Windows. Troverai il tuo `.exe` nella cartella `dist`.

> **⚠️ Nota per la distribuzione:** l'app impacchettata include ffmpeg, ma per un bundle che funzioni **su altri computer** serve un **ffmpeg statico** (quello di Homebrew è collegato dinamicamente e non è portabile). Esporta `FFMPEG_BIN=/percorso/ffmpeg-statico` prima di lanciare lo script di build. L'app compilata non è firmata: su macOS apri con **tasto destro → Apri** la prima volta.

## 🎵 Vibecoding

Questo progetto è nato ed è stato sviluppato al 100% tramite **Vibecoding**! Nessuna tastiera è stata maltrattata durante la stesura del codice: solo interazioni vocali/chat con l'Intelligenza Artificiale (agenti autonomi), prompt curati e tanta buona musica di sottofondo. 🤖🎶

---

## ⚠️ Disclaimer Legale

Questo software è stato creato **esclusivamente per scopi educativi e di ricerca**. 
L'autore di questo software non ospita, carica, distribuisce o gestisce alcun contenuto coperto da copyright a cui questo strumento accede. Il software agisce semplicemente come un web scraper lato client, automatizzando interazioni con contenuti già disponibili pubblicamente su Internet.

L'utente è l'unico responsabile dell'uso di questo software ed è tenuto a rispettare le leggi locali e internazionali in materia di copyright e proprietà intellettuale. L'autore non si assume alcuna responsabilità per qualsiasi uso improprio, illegale, o per eventuali violazioni di copyright commesse da chi scarica e utilizza il programma. Sostieni sempre le release ufficiali e i creatori originali ogni volta che è possibile.
