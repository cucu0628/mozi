import sqlite3
import os
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel, Entry, Label, Button, IntVar, Spinbox

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
    (2, "Inception", 80),
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

    Label(foglalas_window, text="Keresztnév:").pack()
    keresztnev_entry = Entry(foglalas_window)
    keresztnev_entry.pack()

    Label(foglalas_window, text="Vezetéknév:").pack()
    vezeteknev_entry = Entry(foglalas_window)
    vezeteknev_entry.pack()

    Label(foglalas_window, text="Foglalni kívánt helyek száma:").pack()
    jegy_szam = IntVar(value=1)
    Spinbox(foglalas_window, from_=1, to=szabad_helyek, textvariable=jegy_szam).pack()

    def foglalas():
        keresztnev = keresztnev_entry.get()
        vezeteknev = vezeteknev_entry.get()
        helyek_szama = jegy_szam.get()
        if keresztnev and vezeteknev:
            c.execute("SELECT szek_szam FROM foglalasok WHERE terem_szam = ?", (terem_szam,))
            foglalt_helyek = {row[0] for row in c.fetchall()}
            sikeres = False
            for i in range(1, szabad_helyek + 1):
                if i not in foglalt_helyek and helyek_szama > 0:
                    if uj_foglalas(keresztnev, vezeteknev, terem_szam, i):
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

    Button(foglalas_window, text="Foglalás", command=foglalas).pack(pady=10)

def mutat_film_informacio(terem_szam, film_cim, kapacitas, foglalt_helyek, frissit_film_lista):
    info_window = Toplevel()
    info_window.title("Film Információ")
    info_window.geometry("300x200")
    szabad_helyek = kapacitas - foglalt_helyek
    Label(info_window, text=f"Film: {film_cim}", font=("Arial", 14)).pack(pady=5)
    Label(info_window, text=f"Összes férőhely: {kapacitas}").pack()
    Label(info_window, text=f"Foglalt helyek: {foglalt_helyek}").pack()
    Label(info_window, text=f"Szabad helyek: {szabad_helyek}").pack()
    if szabad_helyek != 0:
        Button(info_window, text="Foglalás", command=lambda: jegyfoglalas_ablak(terem_szam, film_cim, szabad_helyek, frissit_film_lista)).pack(pady=10)

def film_kivalasztas(event, film_lista, frissit_film_lista):
    selected_item = film_lista.selection()
    if selected_item:
        terem_szam, film_cim, szabad_helyek = film_lista.item(selected_item, "values")
        c.execute("SELECT COUNT(*) FROM foglalasok WHERE terem_szam = ?", (terem_szam,))
        foglalt_helyek = c.fetchone()[0]
        mutat_film_informacio(int(terem_szam), film_cim, int(szabad_helyek) + foglalt_helyek, foglalt_helyek, frissit_film_lista)

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
    root.mainloop()
    conn.close()
    
if __name__ == "__main__":
    main()
