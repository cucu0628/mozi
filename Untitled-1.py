import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel, StringVar, IntVar
from fpdf import FPDF
import plotly.graph_objects as go
from tkinter import ttk

# Memória-alapú "adatbázis"
termek = {}
foglalasok = {}

# Terem és foglalások kezelése
def uj_terem(terem_szam, film_cim, ev, mufaj, jatekido, kapacitas):
    termek[terem_szam] = {
        "film_cim": film_cim,
        "ev": ev,
        "mufaj": mufaj,
        "jatekido": jatekido,
        "kapacitas": kapacitas,
        "foglalt_helyek": set()
    }

def uj_foglalas(keresztnev, vezeteknev, terem_szam, jegyek):
    if terem_szam in termek:
        szabad_helyek = termek[terem_szam]["kapacitas"] - len(termek[terem_szam]["foglalt_helyek"])
        if jegyek <= szabad_helyek:
            foglalas_sorszam = len(foglalasok) + 1
            for _ in range(jegyek):
                szek_szam = len(termek[terem_szam]["foglalt_helyek"]) + 1
                termek[terem_szam]["foglalt_helyek"].add(szek_szam)
                foglalasok[foglalas_sorszam] = {
                    "keresztnev": keresztnev,
                    "vezeteknev": vezeteknev,
                    "terem_szam": terem_szam,
                    "szek_szam": szek_szam
                }
            return True
    return False

def jegyfoglalas_ablak(terem_szam):
    ablak = Toplevel()
    ablak.title("Jegyfoglalás")
    ablak.geometry("400x300")
    
    keresztnev_var = StringVar()
    vezeteknev_var = StringVar()
    jegyek_var = IntVar()
    
    ttk.Label(ablak, text="Keresztnév:").pack()
    ttk.Entry(ablak, textvariable=keresztnev_var).pack()
    
    ttk.Label(ablak, text="Vezetéknév:").pack()
    ttk.Entry(ablak, textvariable=vezeteknev_var).pack()
    
    ttk.Label(ablak, text="Jegyek száma:").pack()
    ttk.Entry(ablak, textvariable=jegyek_var).pack()
    
    def foglalas():
        sikeres = uj_foglalas(keresztnev_var.get(), vezeteknev_var.get(), terem_szam, jegyek_var.get())
        if sikeres:
            messagebox.showinfo("Siker", "Foglalás sikeres!")
            ablak.destroy()
        else:
            messagebox.showerror("Hiba", "Nincs elég szabad hely!")
    
    ttk.Button(ablak, text="Foglalás", command=foglalas).pack()

def terem_foglaltsag():
    ablak = Toplevel()
    ablak.title("Statisztika")
    ablak.geometry("600x400")
    
    termek_szamok = list(termek.keys())
    foglaltsagok = [len(termek[t]["foglalt_helyek"]) / termek[t]["kapacitas"] * 100 for t in termek_szamok]
    
    fig = go.Figure([go.Bar(x=termek_szamok, y=foglaltsagok)])
    fig.update_layout(title="Termek foglaltsága (%)", xaxis_title="Terem", yaxis_title="Foglaltság (%)")
    fig.show()

def main():
    root = tb.Window(themename="superhero")
    root.title("Mozi Jegyfoglaló Rendszer")
    root.geometry("800x600")
    
    label = tb.Label(root, text="Válassz filmet:", font=("Arial", 16))
    label.pack(pady=10)
    
    film_lista = ttk.Treeview(root, columns=("terem", "cim", "helyek"), show="headings")
    film_lista.heading("terem", text="Terem")
    film_lista.heading("cim", text="Film címe")
    film_lista.heading("helyek", text="Szabad helyek")
    film_lista.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    for terem_szam, adat in termek.items():
        film_lista.insert("", "end", values=(terem_szam, adat["film_cim"], adat["kapacitas"] - len(adat["foglalt_helyek"])))
    
    def film_kivalasztas(event):
        selected = film_lista.selection()
        if selected:
            terem_szam = int(film_lista.item(selected[0], "values")[0])
            jegyfoglalas_ablak(terem_szam)
    
    film_lista.bind("<Double-1>", film_kivalasztas)
    
    stat_btn = tb.Button(root, text="Statisztika", bootstyle=SUCCESS, command=terem_foglaltsag)
    stat_btn.pack(pady=10)
    
    root.mainloop()
    
if __name__ == "__main__":
    uj_terem(1, "Avatar 2", 2022, "Sci-Fi", 180, 100)
    uj_terem(2, "Oppenheimer", 2023, "Dráma", 180, 80)
    main()
