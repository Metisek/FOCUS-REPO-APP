import tkinter as tk
from tkinter import messagebox
import webbrowser
import customtkinter
from lib.email_handler import send_email
from lib.sheet_handler import read_all_data, filter_data, update_event_status, delete_event_from_sheet
import json
import os

config_path = os.path.join('config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

THEME_PATH = config['theme_path']

# Ustawienie ciemnego motywu CustomTkinter
customtkinter.set_default_color_theme(THEME_PATH)
customtkinter.set_appearance_mode("dark")  # ciemny motyw

class EventApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Konfiguracja głównego okna
        self.title("Lista wydarzeń")
        self.geometry("1100x600")
        self.minsize(800, 600)

        # Przechowuje nagłówki i dane
        self.headers, self.data = read_all_data()

        # Konfiguracja layoutu siatki (2 kolumny)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure(0, weight=1)  # Dane wydarzeń rosną dynamicznie
        self.grid_rowconfigure(1, weight=0)  # Zablokowany panel przycisków

        # Tabview do przeglądania statusów wydarzeń
        self.tabview_events = customtkinter.CTkTabview(self, width=350, height=600)
        self.tabview_events.grid(row=0, column=0, rowspan=2, padx=(20, 0), pady=(10, 20), sticky="nsew")

        self.tabview_events.add("Nowe")
        self.tabview_events.add("Zaakceptowane")
        self.tabview_events.add("Odrzucone")

        # Konfiguracja zakładek
        self.tabview_events.tab("Nowe").grid_columnconfigure(0, weight=1)
        self.tabview_events.tab("Zaakceptowane").grid_columnconfigure(0, weight=1)
        self.tabview_events.tab("Odrzucone").grid_columnconfigure(0, weight=1)

        self.scrollable_events_new = customtkinter.CTkScrollableFrame(self.tabview_events.tab("Nowe"))
        self.scrollable_events_new.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.scrollable_events_accepted = customtkinter.CTkScrollableFrame(self.tabview_events.tab("Zaakceptowane"))
        self.scrollable_events_accepted.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.scrollable_events_rejected = customtkinter.CTkScrollableFrame(self.tabview_events.tab("Odrzucone"))
        self.scrollable_events_rejected.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tabview dla szczegółów wydarzeń
        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=1, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.tabview.add("Dane wydarzenia")
        self.tabview.add("Informacje współpracy")
        self.tabview.tab("Dane wydarzenia").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Informacje współpracy").grid_columnconfigure(0, weight=1)

        self.tabview_scrollable_data = customtkinter.CTkScrollableFrame(self.tabview.tab("Dane wydarzenia"))
        self.tabview_scrollable_data.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tabview_scrollable_info = customtkinter.CTkScrollableFrame(self.tabview.tab("Informacje współpracy"))
        self.tabview_scrollable_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frame na przyciski, zablokowany na dole
        self.buttons_frame = customtkinter.CTkFrame(self)
        self.buttons_frame.grid(row=1, column=1, padx=(20, 20), pady=(20, 20), sticky="sew")
        self.buttons_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Załaduj dane
        self.refresh_data()

    def refresh_all_events(self):
        self.add_events_to_scrollable_frame(self.scrollable_events_new, "Nowe")
        self.add_events_to_scrollable_frame(self.scrollable_events_accepted, "Zaakceptowane")
        self.add_events_to_scrollable_frame(self.scrollable_events_rejected, "Odrzucone")

    def add_events_to_scrollable_frame(self, frame, status):
        filtered_events = filter_data(status)
        for widget in frame.winfo_children():
            widget.destroy()
        for event in filtered_events:
            event_label = customtkinter.CTkLabel(frame, text=f"{event[self.headers.index('Nazwa wydarzenia')]}: "
                                    f"{event[self.headers.index('Data startu wydarzenia')]}", height=22)
            event_label.bind("<Button-1>", lambda e, label=event_label, event=event, status=status: self.label_click_event(label, event, status))
            event_label.pack(padx=10, pady=0)

    def label_click_event(self, label, event, status):
        # Determine the scrollable frame based on the status
        if status == "Nowe":
            frame = self.scrollable_events_new
        elif status == "Zaakceptowane":
            frame = self.scrollable_events_accepted
        elif status == "Odrzucone":
            frame = self.scrollable_events_rejected
        else:
            return

        # Reset background color of all labels
        for widget in frame.winfo_children():
            if isinstance(widget, customtkinter.CTkLabel):
                widget.configure(fg_color='#212121')  # Original background color

        # Highlight the clicked label
        label.configure(fg_color='#555555')  # Highlighted background color
        self.show_event_details(event)

        # Clear previous buttons and ensure only `grid()` is used for buttons
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()

        # Create action buttons and use only `grid()` for layout management
        accept_button = customtkinter.CTkButton(self.buttons_frame, text="Zaakceptuj", command=lambda: self.accept_event(event))
        accept_button.grid(column=0, row=0, padx=6, pady=5, sticky="ew")

        reject_button = customtkinter.CTkButton(self.buttons_frame, text="Odrzuć", command=lambda: self.reject_event(event))
        reject_button.grid(column=1, row=0, padx=6, pady=5, sticky="ew")

        ask_button = customtkinter.CTkButton(self.buttons_frame, text="Spytaj o szczegóły", command=lambda: self.ask_details(event))
        ask_button.grid(column=2, row=0, padx=6, pady=5, sticky="ew")

        delete_button = customtkinter.CTkButton(self.buttons_frame, text="Usuń", command=lambda: self.delete_event(event))
        delete_button.grid(column=3, row=0, padx=6, pady=5, sticky="ew")



    # Funkcja odświeżania danych
    def refresh_data(self):
        self.headers, self.data = read_all_data()
        self.refresh_all_events()

        # Funkcja wyświetlania szczegółów wydarzenia
    def show_event_details(self, event_data):
        # Słownik do zmiany nazw nagłówków w sekcji "Informacje współpracy"
        label_translations = {
            "Adres e-mail": "Adres e-mail osoby rejestrującej:",
            "Organizacja odpowiedzialna za wydarzenie": "Organizacja",
            "Przewidywana liczba potrzebnych fotografów": "Fotografowie"
        }

        # Czyszczenie poprzednich widgetów z zakładek
        for widget in self.tabview.tab("Dane wydarzenia").winfo_children():
            widget.destroy()
        for widget in self.tabview.tab("Informacje współpracy").winfo_children():
            widget.destroy()

        # Reinicjalizacja scrollowalnych ramek
        self.tabview_scrollable_data = customtkinter.CTkScrollableFrame(self.tabview.tab("Dane wydarzenia"))
        self.tabview_scrollable_data.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tabview_scrollable_info = customtkinter.CTkScrollableFrame(self.tabview.tab("Informacje współpracy"))
        self.tabview_scrollable_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Wypełnianie zakładki "Dane wydarzenia"
        # 1 kolumna, domyślna wysokość
        self._create_field(self.tabview_scrollable_data, "Nazwa wydarzenia", event_data, height=25)

        # Opis wydarzenia - 1 kolumna, większa wysokość
        self._create_field(self.tabview_scrollable_data, "Opis wydarzenia", event_data, height=100)

        # Miejsce wydarzenia - 1 kolumna, domyślna wysokość
        self._create_field(self.tabview_scrollable_data, "Miejsce wydarzenia", event_data, height=25)

        # Data startu i końca - 2 kolumny, mała wysokość
        self._create_two_column_fields(self.tabview_scrollable_data, ["Data startu wydarzenia", "Data końca wydarzenia"], event_data)

        # Godzina startu i końca - 2 kolumny, mała wysokość
        self._create_two_column_fields(self.tabview_scrollable_data, ["Godzina startu fotorelacji", "Godzina zakończenia fotorelacji"], event_data)

        # Link do wydarzenia - 1 kolumna, domyślna wysokość
        self._create_field(self.tabview_scrollable_data, "Link do wydarzenia/strony internetowej", event_data, height=25)

        # Uwagi - 1 kolumna, duża wysokość
        self._create_field(self.tabview_scrollable_data, "Uwagi", event_data, height=100)

        # Wypełnianie zakładki "Informacje współpracy"
        self._create_three_column_fields(
            self.tabview_scrollable_info,
            ["Adres e-mail", "Organizacja odpowiedzialna za wydarzenie", "Przewidywana liczba potrzebnych fotografów"],
            event_data,
            label_translations,
            col_weights=[3, 3, 1]
        )

        # Oczekiwania wobec nas i co możecie nam zaoferować - 2 kolumny, domyślna wysokość
        self._create_two_column_fields(self.tabview_scrollable_info, ["Oczekiwania wobec nas?", "Co możecie nam zaoferować?"], event_data)

        # Pozostałe pola - 1 kolumna, domyślna wysokość
        for field in ["Dokładniejszy opis wymagań (opcjonalnie)", "Dokładniejszy opis Waszej oferty (opcjonalnie)", "Dane kontaktowe osoby odpowiedzialnej za kontakt"]:
            self._create_field(self.tabview_scrollable_info, field, event_data, height=50)

    # Pomocnicze metody do tworzenia layoutu
    def _create_field(self, parent, field, event_data, height=50, label_translations=None):
        field_index = self.headers.index(field) if field in self.headers else None
        label_text = label_translations.get(field, field) if label_translations else field
        header_label = customtkinter.CTkLabel(parent, text=f"{label_text}:", font=("Arial", 14, "bold"), anchor='w')
        value_text = customtkinter.CTkTextbox(parent, height=height, wrap='word', font=("Arial", 12))
        value_text.insert("1.0", f"{event_data[field_index] if field_index is not None else 'Brak danych'}")
        value_text.configure(state="disabled")  # Wyłącz edycję
        header_label.pack(anchor='w', padx=10, pady=5)
        value_text.pack(fill='x', padx=10, pady=2)

    def _create_two_column_fields(self, parent, fields, event_data):
        frame = customtkinter.CTkFrame(parent)
        frame.pack(fill='x', padx=10, pady=5)
        for i, field in enumerate(fields):
            field_index = self.headers.index(field) if field in self.headers else None
            header_label = customtkinter.CTkLabel(frame, text=f"{field}:", font=("Arial", 14, "bold"), anchor='w')
            header_label.grid(row=0, column=i, padx=5, pady=5, sticky='w')
            value_text = customtkinter.CTkTextbox(frame, height=25, wrap='word', font=("Arial", 12))
            value_text.insert("1.0", f"{event_data[field_index] if field_index is not None else 'Brak danych'}")
            value_text.configure(state="disabled")  # Wyłącz edycję
            value_text.grid(row=1, column=i, padx=5, pady=2, sticky='ew')
            frame.grid_columnconfigure(i, weight=1)

    def _create_three_column_fields(self, parent, fields, event_data, label_translations, col_weights):
        frame = customtkinter.CTkFrame(parent)
        frame.pack(fill='x', padx=10, pady=5)
        for i, field in enumerate(fields):
            field_index = self.headers.index(field) if field in self.headers else None
            label_text = label_translations.get(field, field)
            header_label = customtkinter.CTkLabel(frame, text=f"{label_text}:", font=("Arial", 14, "bold"), anchor='w')
            header_label.grid(row=0, column=i, padx=5, pady=5, sticky='w')
            value_text = customtkinter.CTkTextbox(frame, height=25, wrap='word', font=("Arial", 12))
            value_text.insert("1.0", f"{event_data[field_index] if field_index is not None else 'Brak danych'}")
            value_text.configure(state="disabled")  # Wyłącz edycję
            value_text.grid(row=1, column=i, padx=5, pady=2, sticky='ew')
            frame.grid_columnconfigure(i, weight=col_weights[i])


    # Funkcja do wysyłania maila z zapytaniem
    def ask_details(self, event_data):
        webbrowser.open(f"mailto:{event_data[self.headers.index('Adres e-mail')]}")

    # Akceptowanie wydarzenia
    def accept_event(self, event_data):
        event_accepted_index = self.headers.index("event_accepted")
        confirmation = messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz zaakceptować wydarzenie?")
        if confirmation:
            row_number = self.data.index(event_data)
            update_event_status(event_data, row_number, event_accepted_index, True)
            send_email(event_data[self.headers.index('Adres e-mail')], "Wydarzenie zaakceptowane", "ACCEPT",  event_data[self.headers.index('Nazwa wydarzenia')])
            self.refresh_all_events()

    # Odrzucenie wydarzenia
    def reject_event(self, event_data):
        event_accepted_index = self.headers.index("event_accepted")
        confirmation = messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz odrzucić wydarzenie?")
        if confirmation:
            row_number = self.data.index(event_data)
            update_event_status(event_data, row_number, event_accepted_index, False)
            send_email(event_data[self.headers.index('Adres e-mail')], "Wydarzenie odrzucone", "REJECT", event_data[self.headers.index('Nazwa wydarzenia')])
            self.refresh_all_events()

    def delete_event(self, event_data):
        confirmation = messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz usunąć wydarzenie z bazy?")
        if confirmation:
            row_number = self.data.index(event_data)
            delete_event_from_sheet(row_number)
            self.refresh_all_events()
            messagebox.showinfo("Informacja", "Wydarzenie zostało usunięte")

if __name__ == "__main__":
    app = EventApp()
    app.mainloop()
