 Skeny dvojstran z Bookeye 3 do PDF
-------------------------------------------------------------------------------
 Verze:  1.2.2
 Datum:  2026-11-06

 Složí JPEG skeny dvojstran ze skeneru Bookeye 3 z jedné datumové složky
 do jednoho PDF. Každý sken je jedna stránka A4.
 Pořadí určuje číslo v názvu souboru (REFERENCE00001, REFERENCE00002, ...).

 Postup pro obsluhu skeneru: INFO_OBSLUHA.txt


-------------------------------------------------------------------------------
 STRUKTURA SLOŽEK
-------------------------------------------------------------------------------

 workspace\
   README.txt
   INFO_OBSLUHA.txt
   VYTVOŘIT PDF.bat     <- spouští se tímto (volá tool\jpg2pdf.bat)
   tool\
     jpg2pdf.bat        <- kontrola Pythonu a knihoven, spuštění
     jpg2pdf.py         <- vlastní logika
   log\
     runner_RRRR-MM-DD_HHMMSS.txt   <- záznam každého spuštění (vytvoří se samo)
   scans\
     2026-10-14\        <- skeny + výsledné 2026-10-14.pdf
     2026-10-15\

 - Datumové složky musí mít přesně tvar RRRR-MM-DD a ležet ve scans\.
 - Složka log\ a výsledná PDF se vytvoří automaticky.
 - Složka skeneru images\ses-started_RRRR-MM-DD_\ je mimo workspace;
   skript s ní nepracuje, skeny se z ní ručně kopírují do scans\.


-------------------------------------------------------------------------------
 INSTALACE (jednou na každém PC)
-------------------------------------------------------------------------------

 1. Nainstalovat Python 3 z https://www.python.org
    a při instalaci zaškrtnout "Add Python to PATH".
 2. Zkopírovat celou složku workspace (nebo aspoň tool\) na PC.
 3. Knihovny img2pdf a pillow si jpg2pdf.bat doinstaluje sám
    při prvním spuštění (potřebuje internet). pikepdf se nainstaluje
    automaticky spolu s img2pdf.
    Ručně:  py -m pip install img2pdf pillow

 PC bez internetu:
    Na jiném PC (se stejnou verzí Pythonu) stáhnout balíčky:
       py -m pip download img2pdf pillow -d balicky
    Složku "balicky" dát do tool\. .bat je pak nainstaluje odtud.


-------------------------------------------------------------------------------
 POSTUP PRÁCE
-------------------------------------------------------------------------------

 1. Ve workspace\scans\ vytvořit složku s dnešním datem, např. 2026-10-15.
 2. Zkopírovat do ní skeny z Bookeye 3 (.jpg / .jpeg).
    Soubory NEPŘEJMENOVÁVAT - pořadí v PDF se řídí číslem v názvu.
 3. Smazat špatné skeny, případně oříznout (uložit pod stejným názvem).
 4. Dvakrát kliknout na VYTVOŘIT PDF.bat (nebo tool\jpg2pdf.bat).
 5. Vybrat číslo složky ze seznamu
    (nejnovější je nahoře, [PDF uz existuje] = už zpracováno).
 6. Zkontrolovat vypsané pořadí skenů a chybějící čísla
    a potvrdit Y (nebo N = zrušit).
 7. Hotové PDF je v datumové složce: scans\2026-10-15\2026-10-15.pdf
 8. Volitelně zpracovat další složku, nebo ukončit.

 Alternativa: přetáhnout datumovou složku myší na VYTVOŘIT PDF.bat
              - zpracuje se rovnou ta.


-------------------------------------------------------------------------------
 JAK SKRIPT FUNGUJE
-------------------------------------------------------------------------------

 Výběr skenů     Všechny .jpg / .jpeg v dané složce (bez podsložek).
 Řazení          Podle názvu souboru, čísla se porovnávají jako čísla
                 (REF2 je před REF10).
 Mezery v řadě   Chybějící čísla (smazané skeny) nevadí. Vypíšou se
                 a zapíšou do logu jen pro kontrolu.
 Název bez čísla Zařadí se podle textu názvu, stav = OK S VAROVANIM.
 Stránky         1 sken = 1 stránka A4, okraj 1 mm.
                 Sken na šířku -> stránka na šířku.
 Kvalita         JPEGy se vkládají beze změny (bez ztráty kvality).
 Existující PDF  Upozorní a po potvrzení Y přepíše.
 Vadné soubory   Přeskočí a zapíše varování do logu.
 Kontrola        Po vytvoření ověří, že počet stran PDF = počet skenů.

 Nastavení (začátek jpg2pdf.py):
    PAGE_SIZE_MM = (210, 297)   # A4
    BORDER_MM = 1               # okraj stránky v mm
    SCANS_DIR = WORKSPACE / "scans"


-------------------------------------------------------------------------------
 AUDITNÍ LOG
-------------------------------------------------------------------------------

 Každé spuštění = nový soubor log\runner_RRRR-MM-DD_HHMMSS.txt.
 Log se jen připisuje, nikdy se nepřepisuje ani nemaže.

 Formát každého řádku:
   čas s časovou zónou | ID běhu | úroveň | událost

   2026-10-21 11:52:06 +02:00 | 20261021-115200 | INFO     | VSTUP str=1 | ...

 Úrovně:
   INFO      běžný průběh
   UZIVATEL  rozhodnutí uživatele (výběr složky, odpověď Y/N)
   VAROVANI  zpracováno, ale něco je potřeba zkontrolovat
   CHYBA     zpracování selhalo

 Události (v pořadí, jak jdou za sebou):
   START        verze skriptu, uživatel Windows, název PC, režim spuštění
   PROSTREDI    verze Pythonu a knihoven, operační systém
   NASTAVENI    cesty, velikost stránky, okraj, způsob řazení
   VYBER        kterou složku uživatel vybral
   SLOZKA       začátek zpracování složky
   VSTUP        každý sken: číslo stránky v PDF, název, velikost v B,
                SHA-256 otisk, datum souboru, rozměr v px, DPI
   PRESKOCENO   soubor, který nebude v PDF, a důvod
   NAZEV        soubor, jehož název nekončí číslem
   RADA         rozsah čísel a chybějící čísla v řadě
   EXISTUJICI   PDF, které bude přepsáno: velikost, SHA-256, datum
   ODPOVED      Y / N uživatele
   VYSTUP       cesta k PDF, počet stran, velikost, SHA-256
   KONTROLA     počet stran PDF = počet skenů
   VYSLEDEK     stav složky: OK / OK S VAROVANIM / ZRUSENO / CHYBA
   DALSI        zda uživatel chce zpracovat další složku
   KONEC        počet zpracovaných složek, jejich stavy, doba běhu


-------------------------------------------------------------------------------
 ŘEŠENÍ PROBLÉMŮ
-------------------------------------------------------------------------------

 "Python neni nainstalovany"
    -> Nainstalovat Python se zaškrtnutým "Add Python to PATH".

 "nelze zapsat - je otevrene v jinem programu?"
    -> Zavřít PDF v prohlížeči a spustit znovu.

 "VAROVANI: preskakuji ..."
    -> Soubor není platný JPEG (prázdný, nedokončený přenos, jiný formát).
       Sken zkopírovat znovu, případně naskenovat znovu.

 "VAROVANI: ... nekonci cislem"
    -> Soubor byl přejmenován. Vrátit mu původní název ze skeneru,
       jinak zkontrolovat, že je v PDF na správném místě.

 Sken je ve špatném pořadí
    -> Zkontrolovat název souboru - pořadí určuje jen číslo v názvu.
       Byl-li sken po úpravě uložen pod jiným názvem, přejmenovat zpět.

 V seznamu chybí datumová složka
    -> Zkontrolovat název (RRRR-MM-DD) a že leží ve scans\.


-------------------------------------------------------------------------------
 VERZOVÁNÍ
-------------------------------------------------------------------------------

 Verze ve tvaru HLAVNÍ.VEDLEJŠÍ.OPRAVA
   HLAVNÍ    - změna, po které se mění postup práce (struktura složek, ovládání)
   VEDLEJŠÍ  - nová funkce, postup zůstává stejný
   OPRAVA    - oprava chyby, úprava dokumentace

 Při každé změně skriptu: zvýšit verzi nahoře v tomto souboru
 a přidat záznam do historie změn.


-------------------------------------------------------------------------------
 HISTORIE ZMĚN
-------------------------------------------------------------------------------
 1.2.2  (2026-11-06)
   - Zástupce VYTVOŘIT PDF.lnk nahrazen souborem VYTVOŘIT PDF.bat
     (funguje v jakémkoli umístění složky workspace).

 1.2.1  (2026-10-21)
   - Zjednodušený kód, chování beze změny.
   - Výpis chybějících čísel prostým seznamem.
   - Dotaz před vytvořením PDF ukazuje počet stran.
   - Zrušena kontrola duplicitních čísel v názvech.
   - README: opraven údaj o okraji (1 mm), název jobu skeneru
     ses-started_RRRR-MM-DD_.

 1.2.0  (2026-10-21)
   - Řazení podle čísla v názvu souboru místo data z EXIF.
   - Výpis a log chybějících čísel v řadě (událost RADA).
   - Varování u souboru, jehož název nekončí číslem (událost NAZEV).
   - Z logu odstraněno datum z EXIF a údaj "razeno podle".

 1.1.0  (2026-10-15)
   - Log nahrazen podrobným auditním logem (viz AUDITNÍ LOG):
     ID běhu, čas s časovou zónou, úroveň, uživatel, PC, verze,
     SHA-256 otisky skenů i PDF, rozhodnutí uživatele, stav.
   - Kontrola, že počet stran PDF odpovídá počtu skenů.
   - Konkrétní důvod u každého přeskočeného souboru.

 1.0.1  (2026-10-15)
   - BORDER_MM = 5 se v jpg2pdf.py změnil na BORDER_MM = 1

 1.0.0  (2026-10-15)
   První verze workflow.
   - Výběr datumové složky ze scans\ v konzoli, potvrzení Y/N,
     nebo přetažení složky na .bat.
   - Řazení podle EXIF data pořízení, záloha datum souboru.
   - 1 dvojstrana = 1 stránka A4, automatická orientace stránky.
   - PDF pojmenované podle složky, uložené do ní.
   - Log každého spuštění do log\runner_RRRR-MM-DD_HHMMSS.txt.
   - .bat kontroluje Python a sám doinstaluje knihovny
     (i offline ze složky balicky).
