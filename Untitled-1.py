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

c.execute('''CREATE TABLE IF NOT EXISTS foglalasok (
    foglalas_sorszam INTEGER PRIMARY KEY AUTOINCREMENT,
    keresztnev TEXT,
    vezeteknev TEXT,
    terem_szam INTEGER,
    szek_szam INTEGER,
    FOREIGN KEY (terem_szam) REFERENCES termek(terem_szam)
)''')
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

def uj_foglalas(keresztnev, vezeteknev, terem_szam, szek_szam):
    c.execute("SELECT kapacitas FROM termek WHERE terem_szam = ?", (terem_szam,))
    kapacitas = c.fetchone()
    if kapacitas:
        c.execute("SELECT COUNT(*) FROM foglalasok WHERE terem_szam = ?", (terem_szam,))
        foglalt_helyek = c.fetchone()[0]
        if foglalt_helyek < kapacitas[0]:
            c.execute("INSERT INTO foglalasok (keresztnev, vezeteknev, terem_szam, szek_szam) VALUES (?, ?, ?, ?)",
                      (keresztnev, vezeteknev, terem_szam, szek_szam))
            conn.commit()
            print(keresztnev, vezeteknev, terem_szam, szek_szam)
            return True
    return False

def jegyfoglalas_ablak(terem_szam, film_cim, szabad_helyek, frissit_film_lista):
    
    foglalas_window = Toplevel()
    foglalas_window.title("Jegyfoglalás")
    foglalas_window.geometry("400x300")

    Label(foglalas_window, text=f"Film: {film_cim}", font=("Arial", 14)).pack(pady=5)
    Label(foglalas_window, text=f"Szabad helyek: {szabad_helyek}", font=("Arial", 12)).pack(pady=5)

    Label(foglalas_window, text="Vezetéknév:").pack()
    keresztnev_entry = Entry(foglalas_window)
    keresztnev_entry.pack()

    Label(foglalas_window, text="Keresztnév:").pack()
    vezeteknev_entry = Entry(foglalas_window)
    vezeteknev_entry.pack()

    Label(foglalas_window, text="Foglalni kívánt helyek száma:").pack()
    jegy_szam = IntVar(value=1)
    Spinbox(foglalas_window, from_=1, to=szabad_helyek, textvariable=jegy_szam).pack()

    def foglalas():
        keresztnev = keresztnev_entry.get()
        vezeteknev = vezeteknev_entry.get()
        helyek_szama = jegy_szam.get()
        jegy = jegy_szam.get()
        if szabad_helyek+1 > jegy:
            if keresztnev and vezeteknev:
                c.execute("SELECT szek_szam FROM foglalasok WHERE terem_szam = ?", (terem_szam,))
                foglalt_helyek = {row[0] for row in c.fetchall()}
                sikeres = False
                for i in range(1, 121):
                    if i not in foglalt_helyek and helyek_szama > 0:
                        if uj_foglalas(keresztnev, vezeteknev, terem_szam, i):
                            if helyek_szama < 0:
                                messagebox.showerror("Hiba", "Nincs elegendő hely!")
                            else:
                                helyek_szama -= 1
                                sikeres = True
                if sikeres:
                    messagebox.showinfo("Siker", "Foglalás sikeres!")
                    foglalas_window.destroy()
                    frissit_film_lista()
                else:
                    messagebox.showerror("Hiba", "Nem sikerült a foglalás!")
            else:
                messagebox.showerror("Hiba", "Minden mezőt ki kell tölteni!")
        else:
            messagebox.showerror("Hiba","A foglalni kívánt jegyszám meghaladja a hátralévő helyek számát")

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
            keresztnev, vezeteknev, terem_szam, szekek = values
            szek_lista = szekek.split(", ")
            for szek_szam in szek_lista:
                c.execute("DELETE FROM foglalasok WHERE keresztnev = ? AND vezeteknev = ? AND terem_szam = ? AND szek_szam = ?", 
                          (keresztnev, vezeteknev, terem_szam, szek_szam))
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
            jegy_pdf_keszitese(values)
        else:
            messagebox.showerror("Hiba", "Nincs kijelölt jegy a PDF készítéshez!")

    jegyek_window = Toplevel()
    jegyek_window.title("Vásárolt Jegyek")
    jegyek_window.geometry("1000x400")

    Label(jegyek_window, text="Vásárolt Jegyek", font=("Arial", 14)).pack(pady=5)

    jegy_lista = tb.Treeview(jegyek_window, columns=("keresztnev", "vezeteknev", "terem", "szek"), show="headings")
    jegy_lista.heading("keresztnev", text="Vezetéknév")
    jegy_lista.heading("vezeteknev", text="Keresztnév")
    jegy_lista.heading("terem", text="Terem")
    jegy_lista.heading("szek", text="Székek")
    jegy_lista.pack(fill=BOTH, expand=True, padx=10, pady=10)

    c.execute("SELECT keresztnev, vezeteknev, terem_szam, GROUP_CONCAT(szek_szam) FROM foglalasok GROUP BY keresztnev, vezeteknev, terem_szam")
    for row in c.fetchall():
        jegy_lista.insert("", "end", values=row)

    torles_gomb = Button(jegyek_window, text="Kijelölt jegy törlése", command=torol_jegyet)
    torles_gomb.pack(pady=10)

    pdf_gomb = Button(jegyek_window, text="PDF generálása", command=pdf_keszitese)
    pdf_gomb.pack(pady=10)

def jegy_pdf_keszitese(values):
    keresztnev, vezeteknev, terem_szam, szekek = values
    
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
    pdf.cell(200, 10, f"Székek: {szekek}", ln=True)
    
    # Aláírás
    pdf.ln(20)
    pdf.set_font("Times", style='I', size=12)
    pdf.cell(200, 10, "______________________________", ln=True, align="C")
    pdf.cell(200, 10, "Aláírás", ln=True, align="C")

    # Díszítő grafika (pl. mozi filmtekercs ikona)
    # Itt hozzáadhatnál egy kis képet vagy grafikát, például egy filmtekercset
    #pdf.image("tekercs.png", 150, 250, 40)

    # PDF mentése
    pdf_path = os.path.join(f"{script_dir}\jegyek", f"{keresztnev}.pdf")
    pdf.output(f"{pdf_path}")
    messagebox.showinfo("Siker", "PDF jegy létrehozva!")


def main():
    root = tb.Window(themename="newtheme")
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
