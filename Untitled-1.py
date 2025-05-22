import sqlite3
import os
from PIL import Image
Image.CUBIC = Image.BICUBIC
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel, Entry, Label, Button, IntVar, Spinbox
from fpdf import FPDF


# Adatbázis inicializálása a script mappájában
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "mozi.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS termek (
    terem_szam INTEGER PRIMARY KEY,
    film_cim TEXT,
    kapacitas INTEGER
)''')

# Módosítjuk a foglalasok táblát, hogy tartalmazza a jegy_tipus oszlopot
c.execute('''CREATE TABLE IF NOT EXISTS foglalasok (
    foglalas_sorszam INTEGER PRIMARY KEY AUTOINCREMENT,
    keresztnev TEXT,
    vezeteknev TEXT,
    terem_szam INTEGER,
    szek_szam INTEGER,
    jegy_tipus TEXT, -- UJ OSZLOP: 'felnott' vagy 'gyerek'
    FOREIGN KEY (terem_szam) REFERENCES termek(terem_szam)
)''')

# Ha már létezik a tábla és nem tartalmazza a jegy_tipus oszlopot, hozzáadhatjuk ALTER TABLE-lel
# De a fenti CREATE TABLE IF NOT EXISTS már gondoskodik erről, ha még nincs tábla.
# Ha már van, és szeretnénk hozzáadni:
try:
    c.execute("ALTER TABLE foglalasok ADD COLUMN jegy_tipus TEXT")
except sqlite3.OperationalError as e:
    if "duplicate column name: jegy_tipus" not in str(e):
        raise e # Más hiba esetén dobjuk tovább

"""c.executemany("INSERT INTO termek (terem_szam, film_cim, kapacitas) VALUES (?, ?, ?)", [
    (1, "Titanic", 100),
    (2, "Inception", 3),
    (3, "Interstellar", 120)
])"""
conn.commit()

# Minden indításkor töröljük az összes foglalást
def reset_foglalasok():
    c.execute("DELETE FROM foglalasok")
    conn.commit()

reset_foglalasok()

def uj_terem(terem_szam, film_cim, kapacitas):
    c.execute("INSERT OR IGNORE INTO termek VALUES (?, ?, ?)",
              (terem_szam, film_cim, kapacitas))
    conn.commit()

# Módosítjuk az uj_foglalas függvényt, hogy fogadja a jegy_tipus-t
def uj_foglalas(keresztnev, vezeteknev, terem_szam, szek_szam, jegy_tipus):
    c.execute("SELECT kapacitas FROM termek WHERE terem_szam = ?", (terem_szam,))
    kapacitas = c.fetchone()
    if kapacitas:
        c.execute("SELECT COUNT(*) FROM foglalasok WHERE terem_szam = ?", (terem_szam,))
        foglalt_helyek = c.fetchone()[0]
        if foglalt_helyek < kapacitas[0]:
            # Beszúráskor már a jegy_tipus oszlopot is kitöltjük
            c.execute("INSERT INTO foglalasok (keresztnev, vezeteknev, terem_szam, szek_szam, jegy_tipus) VALUES (?, ?, ?, ?, ?)",
                      (keresztnev, vezeteknev, terem_szam, szek_szam, jegy_tipus))
            conn.commit()
            print(f"Foglalás sikeres: {keresztnev} {vezeteknev}, Terem: {terem_szam}, Szék: {szek_szam}, Típus: {jegy_tipus}")
            return True
    return False

def jegyfoglalas_ablak(terem_szam, film_cim, szabad_helyek, frissit_film_lista):

    foglalas_window = Toplevel()
    foglalas_window.title("Jegyfoglalás")
    foglalas_window.geometry("400x450") # Megnövelt méret az új mezők miatt

    Label(foglalas_window, text=f"Film: {film_cim}", font=("Arial", 14)).pack(pady=5)
    Label(foglalas_window, text=f"Szabad helyek: {szabad_helyek}", font=("Arial", 12)).pack(pady=5)

    Label(foglalas_window, text="Vezetéknév:").pack()
    vezeteknev_entry = Entry(foglalas_window)
    vezeteknev_entry.pack()

    Label(foglalas_window, text="Keresztnév:").pack()
    keresztnev_entry = Entry(foglalas_window)
    keresztnev_entry.pack()

    Label(foglalas_window, text="Felnőtt jegyek száma:").pack()
    felnott_jegy_szam = IntVar(value=0) # Kezdő érték 0
    Spinbox(foglalas_window, from_=0, to=szabad_helyek, textvariable=felnott_jegy_szam).pack()

    Label(foglalas_window, text="Gyerek jegyek száma:").pack()
    gyerek_jegy_szam = IntVar(value=0) # Kezdő érték 0
    Spinbox(foglalas_window, from_=0, to=szabad_helyek, textvariable=gyerek_jegy_szam).pack()


    def foglalas():
        keresztnev = keresztnev_entry.get()
        vezeteknev = vezeteknev_entry.get()
        felnott_jegyek = felnott_jegy_szam.get()
        gyerek_jegyek = gyerek_jegy_szam.get()
        osszes_jegy = felnott_jegyek + gyerek_jegyek

        if osszes_jegy == 0:
            messagebox.showerror("Hiba", "Válasszon legalább egy jegyet!")
            return

        if osszes_jegy > szabad_helyek:
            messagebox.showerror("Hiba", f"Nincs elegendő hely! Maximálisan foglalható: {szabad_helyek} jegy.")
            return

        if keresztnev and vezeteknev:
            c.execute("SELECT szek_szam FROM foglalasok WHERE terem_szam = ?", (terem_szam,))
            foglalt_helyek = {row[0] for row in c.fetchall()}
            sikeres = False
            foglalt_szekek_list = [] # Itt gyűjtjük a sikeresen foglalt székek sorszámát és típusát

            # Felnőtt jegyek foglalása
            for _ in range(felnott_jegyek):
                for i in range(1, 121): # Feltételezzük, hogy max 120 szék van egy teremben
                    if i not in foglalt_helyek:
                        if uj_foglalas(keresztnev, vezeteknev, terem_szam, i, 'felnott'):
                            foglalt_helyek.add(i)
                            foglalt_szekek_list.append(f"{i} (felnott)")
                            sikeres = True
                            break # Fontos: ha találtunk egy helyet, lépjünk ki a belső ciklusból

            # Gyerek jegyek foglalása
            for _ in range(gyerek_jegyek):
                for i in range(1, 121):
                    if i not in foglalt_helyek:
                        if uj_foglalas(keresztnev, vezeteknev, terem_szam, i, 'gyerek'):
                            foglalt_helyek.add(i)
                            foglalt_szekek_list.append(f"{i} (gyerek)")
                            sikeres = True
                            break

            if sikeres:
                messagebox.showinfo("Siker", f"Foglalás sikeres! Foglalt székek: {', '.join(foglalt_szekek_list)}")
                foglalas_window.destroy()
                frissit_film_lista()
            else:
                messagebox.showerror("Hiba", "Nem sikerült a foglalás!")
        else:
            messagebox.showerror("Hiba", "Minden mezőt ki kell tölteni!")

    Button(foglalas_window, text="Foglalás", command=foglalas).pack(pady=10)

def mutat_film_informacio(terem_szam, film_cim, kapacitas, foglalt_helyek, frissit_film_lista):
    info_window = Toplevel()
    info_window.title("Film Információ")
    info_window.geometry("350x400")
    szabad_helyek = kapacitas - foglalt_helyek
    Label(info_window, text=f"Film: {film_cim}", font=("Arial", 14)).pack(pady=5)
    Label(info_window, text=f"Összes férőhely: {kapacitas}").pack()
    Label(info_window, text=f"Foglalt helyek: {foglalt_helyek}").pack()
    Label(info_window, text=f"Szabad helyek: {szabad_helyek}").pack()
    foglaltsag_szazalek = (foglalt_helyek / kapacitas) * 100 if kapacitas else 0
    meter_szine = "success" if foglaltsag_szazalek < 40 else "warning" if foglaltsag_szazalek < 90 else "danger"
    meter = tb.Meter(info_window, bootstyle=meter_szine, subtext="Foglaltság", amountused=foglalt_helyek, amounttotal=kapacitas)
    meter.pack(pady=10)
    if szabad_helyek != 0:
        Button(info_window, text="Foglalás", command=lambda: [jegyfoglalas_ablak(terem_szam, film_cim, szabad_helyek, frissit_film_lista),info_window.destroy()]).pack(pady=10)
    else:
        Label(info_window, fg="red", text="ELFOGYOTT A HELY!").pack(pady=10)
    Label(info_window, text=f"Összes hátralévő hely: {szabad_helyek}").pack()


def film_kivalasztas(event, film_lista, frissit_film_lista):
    selected_item = film_lista.selection()
    if selected_item:
        terem_szam, film_cim, szabad_helyek = film_lista.item(selected_item, "values")
        c.execute("SELECT COUNT(*) FROM foglalasok WHERE terem_szam = ?", (terem_szam,))
        foglalt_helyek = c.fetchone()[0]
        mutat_film_informacio(int(terem_szam), film_cim, int(szabad_helyek) + foglalt_helyek, foglalt_helyek, frissit_film_lista)


def jegyek_listazasa(frissit_film_lista):
    def torol_jegyet():
        selected_item = jegy_lista.selection()
        if selected_item:
            values = jegy_lista.item(selected_item, "values")
            keresztnev, vezeteknev, terem_szam, felnott_db, gyerek_db, felnott_szekek_str, gyerek_szekek_str = values

            # Összegyűjtjük a törölendő székeket és típusokat
            tickets_to_delete = []
            if felnott_szekek_str:
                for szek_szam in felnott_szekek_str.split(','):
                    tickets_to_delete.append((int(szek_szam.strip()), 'felnott'))
            if gyerek_szekek_str:
                for szek_szam in gyerek_szekek_str.split(','):
                    tickets_to_delete.append((int(szek_szam.strip()), 'gyerek'))

            print(f"Törlés előtt: {keresztnev} {vezeteknev} {terem_szam}, Törölendő jegyek: {tickets_to_delete}")

            for szek_szam, jegy_tipus in tickets_to_delete:
                c.execute("DELETE FROM foglalasok WHERE keresztnev = ? AND vezeteknev = ? AND terem_szam = ? AND szek_szam = ? AND jegy_tipus = ?",
                        (keresztnev, vezeteknev, int(terem_szam), szek_szam, jegy_tipus))
                print(f"Törlés végrehajtva: {keresztnev} {vezeteknev} {terem_szam} szék: {szek_szam}, Típus: {jegy_tipus}")

            conn.commit()
            jegyek_window.destroy()
            jegyek_listazasa(frissit_film_lista)
            frissit_film_lista()
            messagebox.showinfo("Siker", "A jegy(ek) törölve lettek!")
        else:
            messagebox.showerror("Hiba", "Nincs kijelölt jegy törlésre!")

    def pdf_keszitese():
        selected_item = jegy_lista.selection()
        if selected_item:
            values = jegy_lista.item(selected_item, "values")
            # A values itt már a 7 elemű tuple lesz a Treeview-ból
            # (keresztnev, vezeteknev, terem_szam, felnott_db, gyerek_db, felnott_szekek, gyerek_szekek)
            jegy_pdf_keszitese(values)
        else:
            messagebox.showerror("Hiba", "Nincs kijelölt jegy a PDF készítéshez!")

    jegyek_window = Toplevel()
    jegyek_window.title("Vásárolt Jegyek")
    jegyek_window.geometry("1100x400") # Növeljük a szélességet az új oszlopok miatt

    Label(jegyek_window, text="Vásárolt Jegyek", font=("Arial", 14)).pack(pady=5)

    # Új oszlopok a Treeview-hoz: felnott_db, gyerek_db, felnott_szekek, gyerek_szekek
    jegy_lista = tb.Treeview(jegyek_window, columns=("keresztnev", "vezeteknev", "terem", "felnott_db", "gyerek_db", "felnott_szekek", "gyerek_szekek"), show="headings")
    jegy_lista.heading("keresztnev", text="Vezetéknév")
    jegy_lista.heading("vezeteknev", text="Keresztnév")
    jegy_lista.heading("terem", text="Terem")
    jegy_lista.heading("felnott_db", text="Felnőtt (db)")
    jegy_lista.heading("gyerek_db", text="Gyerek (db)")
    jegy_lista.heading("felnott_szekek", text="Felnőtt székek")
    jegy_lista.heading("gyerek_szekek", text="Gyerek székek")

    # Oszlopszélességek beállítása az olvashatóság érdekében
    jegy_lista.column("keresztnev", width=120, anchor='center')
    jegy_lista.column("vezeteknev", width=120, anchor='center')
    jegy_lista.column("terem", width=60, anchor='center')
    jegy_lista.column("felnott_db", width=80, anchor='center')
    jegy_lista.column("gyerek_db", width=80, anchor='center')
    jegy_lista.column("felnott_szekek", width=180, anchor='center')
    jegy_lista.column("gyerek_szekek", width=180, anchor='center')


    jegy_lista.pack(fill=BOTH, expand=True, padx=10, pady=10)

    # Módosítjuk a lekérdezést, hogy csoportosítva adja vissza az adatokat
    c.execute("""
        SELECT
            keresztnev,
            vezeteknev,
            terem_szam,
            SUM(CASE WHEN jegy_tipus = 'felnott' THEN 1 ELSE 0 END) AS felnott_darab,
            SUM(CASE WHEN jegy_tipus = 'gyerek' THEN 1 ELSE 0 END) AS gyerek_darab,
            GROUP_CONCAT(CASE WHEN jegy_tipus = 'felnott' THEN szek_szam ELSE NULL END) AS felnott_szekek,
            GROUP_CONCAT(CASE WHEN jegy_tipus = 'gyerek' THEN szek_szam ELSE NULL END) AS gyerek_szekek
        FROM
            foglalasok
        GROUP BY
            keresztnev, vezeteknev, terem_szam
    """)
    for row in c.fetchall():
        jegy_lista.insert("", "end", values=row)

    torles_gomb = Button(jegyek_window, text="Kijelölt jegy törlése", command=torol_jegyet)
    torles_gomb.pack(pady=10)

    pdf_gomb = Button(jegyek_window, text="PDF generálása", command=pdf_keszitese)
    pdf_gomb.pack(pady=10)

def jegy_pdf_keszitese(values):
    # Most már 7 értéket várunk a values-ban
    # Konvertáld a felnott_db és gyerek_db változókat integerré
    keresztnev, vezeteknev, terem_szam, felnott_db_str, gyerek_db_str, felnott_szekek_str, gyerek_szekek_str = values

    # Itt történik a konverzió stringből int-be
    felnott_db = int(felnott_db_str)
    gyerek_db = int(gyerek_db_str)


    pdf = FPDF()
    pdf.add_page()

    # Háttérszín (világos krémszín, hogy vintage hangulatot adjon)
    pdf.set_fill_color(255, 249, 212)  # Halvány krémszín
    pdf.rect(0, 0, 210, 297, 'F')  # Háttér színezése

    # Díszes szegélyek
    pdf.set_line_width(1.5)
    pdf.set_draw_color(205, 127, 50)  # Arany színű szegély
    pdf.rect(5, 5, 200, 287)  # Teli szegély

    # Díszes minták a szegélyekben
    pdf.set_draw_color(205, 127, 50)
    for i in range(5, 200, 30):  # Szegély mintázása
        pdf.line(i, 5, i + 20, 20)
        pdf.line(i, 287, i + 20, 267)

    # Cím díszítése
    pdf.set_font("Times", style='B', size=24)
    pdf.set_text_color(153, 101, 21)  # Sötét arany szín
    pdf.cell(200, 15, "MOZI JEGY", ln=True, align="C")
    pdf.ln(10)

    # Információk kiírása
    pdf.set_font("Times", size=14)
    pdf.set_text_color(0, 0, 0)  # Fekete szöveg
    pdf.cell(200, 10, f"Név: {keresztnev} {vezeteknev}", ln=True)
    pdf.cell(200, 10, f"Terem: {terem_szam}", ln=True)
    pdf.ln(5)

    if felnott_db > 0:
        pdf.cell(200, 10, f"Felnott jegyek száma: {felnott_db}", ln=True)
        if felnott_szekek_str:
            pdf.cell(200, 10, f"Felnott székek: {felnott_szekek_str}", ln=True)
        pdf.ln(2)

    if gyerek_db > 0:
        pdf.cell(200, 10, f"Gyerek jegyek száma: {gyerek_db}", ln=True)
        if gyerek_szekek_str:
            pdf.cell(200, 10, f"Gyerek székek: {gyerek_szekek_str}", ln=True)
        pdf.ln(2)


    # Aláírás
    pdf.ln(20)
    pdf.set_font("Times", style='I', size=12)
    pdf.cell(200, 10, "______________________________", ln=True, align="C")
    pdf.cell(200, 10, "Aláírás", ln=True, align="C")


    # PDF mentése
    # Győződjünk meg róla, hogy létezik a 'jegyek' mappa
    pdf_output_dir = os.path.join(script_dir, "jegyek")
    os.makedirs(pdf_output_dir, exist_ok=True) # Létrehozza a mappát, ha nem létezik

    pdf_path = os.path.join(pdf_output_dir, f"{vezeteknev}_{keresztnev}_terem_{terem_szam}_jegy.pdf")
    pdf.output(pdf_path)
    messagebox.showinfo("Siker", f"PDF jegy létrehozva: {pdf_path}")

# A main függvény marad változatlan
def main():
    root = tb.Window(themename="superhero")
    root.title("Mozi Jegyfoglaló Rendszer")
    root.geometry("800x600")

    label = tb.Label(root, text="Válassz filmet:", font=("Arial", 16))
    label.pack(pady=10)

    film_lista = tb.Treeview(root, columns=("terem", "cim", "helyek"), show="headings")
    film_lista.heading("terem", text="Terem")
    film_lista.heading("cim", text="Film címe")
    film_lista.heading("helyek", text="Szabad helyek")
    film_lista.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def frissit_film_lista():
        film_lista.delete(*film_lista.get_children())
        c.execute("SELECT * FROM termek")
        for row in c.fetchall():
            terem_szam, film_cim, kapacitas = row
            c.execute("SELECT COUNT(*) FROM foglalasok WHERE terem_szam = ?", (terem_szam,))
            foglalt = c.fetchone()[0]
            film_lista.insert("", "end", values=(terem_szam, film_cim, kapacitas - foglalt))

    frissit_film_lista()

    film_lista.bind("<Double-1>", lambda event: film_kivalasztas(event, film_lista, frissit_film_lista))

    jegyek_gomb = Button(root, text="Megvásárolt jegyek", command=lambda: jegyek_listazasa(frissit_film_lista))
    jegyek_gomb.pack(pady=10)

    root.mainloop()
    conn.close()

if __name__ == "__main__":
    main()