import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame


# ---------------------------------------------------------------
#  Estructura de datos: lista doblemente enlazada circular
# ---------------------------------------------------------------
class Nodocancion:
    def __init__(self, ruta):
        self.ruta = ruta
        self.titulo = os.path.splitext(os.path.basename(ruta))[0]
        self.anterior = None
        self.siguente = None


class listadoblecircilar:
    def __init__(self):
        self.primero = None
        self.actual = None
        self.tamaño = 0

    def esta_vacia(self):
        return self.primero is None

    def agregar(self, ruta):
        nuevo = Nodocancion(ruta)
        if self.esta_vacia():
            nuevo.siguente = nuevo
            nuevo.anterior = nuevo
            self.primero = nuevo
            self.actual = nuevo
        else:
            ultimo = self.primero.anterior

            ultimo.siguente = nuevo
            nuevo.anterior = ultimo

            nuevo.siguente = self.primero
            self.primero.anterior = nuevo
        self.tamaño += 1
        return nuevo

    def recorrer(self):
        nodos = []
        if self.esta_vacia():
            return nodos

        nodo = self.primero
        while True:
            nodos.append(nodo)
            nodo = nodo.siguente
            if nodo == self.primero:
                break
        return nodos

    def siguente(self):
        if self.actual is not None:
            self.actual = self.actual.siguente
            return self.actual
        return None

    def anterior(self):
        if self.actual is not None:
            self.actual = self.actual.anterior
            return self.actual
        return None

    def buscar_por_indice(self, indice):
        nodos = self.recorrer()
        if 0 <= indice < len(nodos):
            return nodos[indice]
        return None

    def selecccionar(self, nodo):
        if nodo in self.recorrer():
            self.actual = nodo
            return True
        return False

    def eliminar(self, nodo):
        if nodo is None or self.esta_vacia():
            return False

        # Unico nodo: la lista queda vacia
        if self.tamaño == 1:
            self.primero = None
            self.actual = None
        else:
            # Si se borra el primero o el actual, mover los punteros antes de desenlazar
            if nodo == self.primero:
                self.primero = nodo.siguente
            if nodo == self.actual:
                self.actual = nodo.siguente

            nodo.anterior.siguente = nodo.siguente
            nodo.siguente.anterior = nodo.anterior

        nodo.anterior = None
        nodo.siguente = None
        self.tamaño -= 1
        return True


# ---------------------------------------------------------------
#  Interfaz grafica
# ---------------------------------------------------------------
class reproductorMUsica:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("reproductor de musica")
        self.ventana.geometry("950x620")
        self.ventana.minsize(760, 500)
        self.ventana.configure(bg="#101827")

        self.lista = listadoblecircilar()
        self.pausado = False
        self.reproduciendo = False
        self.nodos_por_item = {}  # id del Treeview -> nodo
        self.volumen = tk.DoubleVar(value=0.65)
        self.mensaje = tk.StringVar(value="agregar archivos MP3 para reproducir")
        self.cacion_actual = tk.StringVar(value="ninguna canciion selecionada")

        try:
            pygame.mixer.init()
            self.audio_disponible = True
            pygame.mixer.music.set_volume(self.volumen.get())
        except pygame.error as error:
            self.audio_disponible = False
            messagebox.showerror(
                "erro de audio",
                "no se puede iniciar el audio \n"
                "compruebe la salida de sonido de su computadora \n\n"
                f"detalle: {error}"
            )

        self.crear_interfaz()
        self.revisar_fin_cancion()

    # ----------------------- construccion de la interfaz -----------------------
    def crear_interfaz(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "Treeview",
            background="#17243a",
            foreground="#f1f6f9",
            fieldbackground="#17243a",
            rowheight=30,
            borderwidth=0,
        )
        estilo.configure(
            "Treeview.Heading",
            background="#253650",
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold")
        )
        estilo.map(
            "Treeview",
            background=[("selected", "#6554d9")],
            foreground=[("selected", "#ffffff")],
        )

        # Encabezado
        encabezado = tk.Frame(self.ventana, bg="#101827")
        encabezado.pack(fill="x", padx=24, pady=(20, 10))

        tk.Label(
            encabezado,
            text="Reproductor de Música",
            font=("Segoe UI", 21, "bold"),
            fg="#ffffff",
            bg="#101827",
        ).pack(anchor="w")

        tk.Label(
            encabezado,
            text="lista doblemente enlazada circular",
            font=("Segoe UI", 10),
            fg="#aab8d0",
            bg="#101827"
        ).pack(anchor="w", pady=(4, 0))

        # Contenido: lista a la izquierda, panel a la derecha
        contenido = tk.Frame(self.ventana, bg="#101827")
        contenido.pack(fill="both", expand=True, padx=24, pady=8)

        # --- Lista de canciones ---
        marco_lista = tk.Frame(contenido, bg="#101827")
        marco_lista.pack(side="left", fill="both", expand=True)

        self.tabla = ttk.Treeview(
            marco_lista,
            columns=("num", "titulo"),
            show="headings",
            selectmode="browse",
        )
        self.tabla.heading("num", text="#")
        self.tabla.heading("titulo", text="Canción")
        self.tabla.column("num", width=50, anchor="center", stretch=False)
        self.tabla.column("titulo", anchor="w")
        self.tabla.pack(side="left", fill="both", expand=True)
        self.tabla.bind("<Double-1>", self.doble_clic)

        barra = ttk.Scrollbar(marco_lista, orient="vertical", command=self.tabla.yview)
        barra.pack(side="right", fill="y")
        self.tabla.configure(yscrollcommand=barra.set)

        # --- Panel derecho ---
        panel = tk.Frame(contenido, bg="#17243a", width=280)
        panel.pack(side="right", fill="y", padx=(16, 0))
        panel.pack_propagate(False)

        tk.Label(
            panel,
            text="Reproduciendo",
            font=("Segoe UI", 10),
            fg="#aab8d0",
            bg="#17243a",
        ).pack(anchor="w", padx=16, pady=(18, 4))

        tk.Label(
            panel,
            textvariable=self.cacion_actual,
            font=("Segoe UI", 14, "bold"),
            fg="#ffffff",
            bg="#17243a",
            wraplength=240,
            justify="left",
        ).pack(anchor="w", padx=16)

        tk.Label(
            panel,
            textvariable=self.mensaje,
            font=("Segoe UI", 9),
            fg="#aab8d0",
            bg="#17243a",
            wraplength=240,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(10, 0))

        self.boton(panel, "Agregar canciones", self.agregar_canciones, "#6554d9").pack(
            fill="x", padx=16, pady=(24, 6))
        self.boton(panel, "Agregar carpeta", self.agregar_carpeta, "#253650").pack(
            fill="x", padx=16, pady=6)
        self.boton(panel, "Eliminar seleccionada", self.eliminar_seleccionada, "#b8434f").pack(
            fill="x", padx=16, pady=6)

        # Volumen
        tk.Label(
            panel,
            text="Volumen",
            font=("Segoe UI", 10),
            fg="#aab8d0",
            bg="#17243a",
        ).pack(anchor="w", padx=16, pady=(20, 0))

        ttk.Scale(
            panel,
            from_=0.0,
            to=1.0,
            orient="horizontal",
            variable=self.volumen,
            command=self.cambiar_volumen,
        ).pack(fill="x", padx=16, pady=(4, 0))

        # Controles inferiores
        controles = tk.Frame(self.ventana, bg="#101827")
        controles.pack(fill="x", padx=24, pady=(8, 22))

        centro = tk.Frame(controles, bg="#101827")
        centro.pack()

        self.boton(centro, "⏮ Anterior", self.cancion_anterior, "#253650").pack(side="left", padx=6)
        self.boton_play = self.boton(centro, "▶ Reproducir", self.reproducir_pausar, "#6554d9")
        self.boton_play.pack(side="left", padx=6)
        self.boton(centro, "⏹ Detener", self.detener, "#253650").pack(side="left", padx=6)
        self.boton(centro, "Siguiente ⏭", self.cancion_siguiente, "#253650").pack(side="left", padx=6)

    def boton(self, padre, texto, comando, color):
        return tk.Button(
            padre,
            text=texto,
            command=comando,
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg=color,
            activebackground=color,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
        )

    # ----------------------- manejo de la lista -----------------------
    def agregar_canciones(self):
        rutas = filedialog.askopenfilenames(
            title="Seleccione canciones",
            filetypes=[("Audio", "*.mp3 *.wav *.ogg"), ("Todos los archivos", "*.*")],
        )
        self.agregar_rutas(rutas)

    def agregar_carpeta(self):
        carpeta = filedialog.askdirectory(title="Seleccione una carpeta")
        if not carpeta:
            return
        rutas = [
            os.path.join(carpeta, f)
            for f in sorted(os.listdir(carpeta))
            if f.lower().endswith((".mp3", ".wav", ".ogg"))
        ]
        if not rutas:
            self.mensaje.set("la carpeta no tiene archivos de audio")
            return
        self.agregar_rutas(rutas)

    def agregar_rutas(self, rutas):
        if not rutas:
            return
        for ruta in rutas:
            self.lista.agregar(ruta)
        self.refrescar_tabla()
        self.mensaje.set(f"{len(rutas)} canción(es) agregada(s). Total: {self.lista.tamaño}")

    def refrescar_tabla(self):
        """Reconstruye la tabla recorriendo la lista circular desde el primero."""
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        self.nodos_por_item.clear()

        for i, nodo in enumerate(self.lista.recorrer(), start=1):
            item = self.tabla.insert("", "end", values=(i, nodo.titulo))
            self.nodos_por_item[item] = nodo

        self.marcar_actual()

    def marcar_actual(self):
        """Resalta en la tabla la canción que está apuntada por 'actual'."""
        for item, nodo in self.nodos_por_item.items():
            if nodo == self.lista.actual:
                self.tabla.selection_set(item)
                self.tabla.see(item)
                return

    def eliminar_seleccionada(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            self.mensaje.set("seleccione una canción para eliminar")
            return

        nodo = self.nodos_por_item.get(seleccion[0])
        era_actual = nodo == self.lista.actual

        if era_actual and self.reproduciendo:
            self.detener()

        self.lista.eliminar(nodo)
        self.refrescar_tabla()

        if self.lista.esta_vacia():
            self.cacion_actual.set("ninguna canciion selecionada")
            self.mensaje.set("la lista está vacía")
        else:
            self.mensaje.set("canción eliminada")

    # ----------------------- reproduccion -----------------------
    def doble_clic(self, _evento):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        nodo = self.nodos_por_item.get(seleccion[0])
        if nodo and self.lista.selecccionar(nodo):
            self.reproducir_nodo(nodo)

    def reproducir_nodo(self, nodo):
        if not self.audio_disponible or nodo is None:
            return
        try:
            pygame.mixer.music.load(nodo.ruta)
            pygame.mixer.music.set_volume(self.volumen.get())
            pygame.mixer.music.play()
        except pygame.error as error:
            messagebox.showerror("error al reproducir", f"no se pudo reproducir:\n{nodo.titulo}\n\n{error}")
            return

        self.pausado = False
        self.reproduciendo = True
        self.cacion_actual.set(nodo.titulo)
        self.mensaje.set("reproduciendo")
        self.boton_play.config(text="⏸ Pausar")
        self.marcar_actual()

    def reproducir_pausar(self):
        if self.lista.esta_vacia():
            self.mensaje.set("agregue canciones primero")
            return

        if not self.reproduciendo:
            # Si hay una seleccionada en la tabla, empezar por ella
            seleccion = self.tabla.selection()
            if seleccion:
                self.lista.selecccionar(self.nodos_por_item[seleccion[0]])
            self.reproducir_nodo(self.lista.actual)
        elif self.pausado:
            pygame.mixer.music.unpause()
            self.pausado = False
            self.mensaje.set("reproduciendo")
            self.boton_play.config(text="⏸ Pausar")
        else:
            pygame.mixer.music.pause()
            self.pausado = True
            self.mensaje.set("en pausa")
            self.boton_play.config(text="▶ Reanudar")

    def detener(self):
        if self.audio_disponible:
            pygame.mixer.music.stop()
        self.reproduciendo = False
        self.pausado = False
        self.boton_play.config(text="▶ Reproducir")
        self.mensaje.set("detenido")

    def cancion_siguiente(self):
        if self.lista.esta_vacia():
            return
        nodo = self.lista.siguente()
        self.reproducir_nodo(nodo)

    def cancion_anterior(self):
        if self.lista.esta_vacia():
            return
        nodo = self.lista.anterior()
        self.reproducir_nodo(nodo)

    def cambiar_volumen(self, valor):
        if self.audio_disponible:
            pygame.mixer.music.set_volume(float(valor))

    def revisar_fin_cancion(self):
        """Cada medio segundo revisa si la canción terminó y pasa a la siguiente."""
        if (
            self.audio_disponible
            and self.reproduciendo
            and not self.pausado
            and not pygame.mixer.music.get_busy()
        ):
            self.cancion_siguiente()
        self.ventana.after(500, self.revisar_fin_cancion)


if __name__ == "__main__":
    ventana = tk.Tk()
    app = reproductorMUsica(ventana)
    ventana.mainloop()
