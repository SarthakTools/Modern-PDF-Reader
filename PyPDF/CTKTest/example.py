from tkinter import font
from CTkScrollableDropdown import *
import customtkinter
from customtkinter import *

set_appearance_mode("dark")
set_default_color_theme("dark-blue")

root = customtkinter.CTk()

customtkinter.CTkLabel(root, text="Different Dropdown Styles").pack(pady=5)

def do_something(e):
    print(e)

# Some option list
values = ["python","tkinter","customtkinter","widgets",
          "options","menu","combobox","dropdown","search"]

# Attach to OptionMenu 
optionmenu = customtkinter.CTkOptionMenu(root, width=500)
optionmenu.pack(padx=10, pady=10)

CTkScrollableDropdown(optionmenu, values=values, justify="left", font=("Segoe UI", 17), command=do_something, height=800, width=400) # Using command to print the chosen option

# Attach to Combobox
combobox = customtkinter.CTkComboBox(root, width=240)
combobox.pack(fill="x", padx=10, pady=10)

CTkScrollableDropdown(combobox, values=values, justify="left", button_color="transparent")

# Attach to Entry
customtkinter.CTkLabel(root, text="Live Search Values").pack()

entry = customtkinter.CTkEntry(root, width=240)
entry.pack(fill="x", padx=10, pady=10)

# method to insert the chosen option from the autocomplete
def insert_method(e):
    entry.delete(0, 'end')
    entry.insert(0, e)

CTkScrollableDropdown(entry, values=values, command=lambda e: insert_method(e),
                      autocomplete=True) # Using autocomplete

button = customtkinter.CTkButton(root, text="choose options", width=240)
button.pack(padx=10, pady=10)

CTkScrollableDropdown(button, values=values, height=270, resize=False, button_height=30,
                      scrollbar=False, command=lambda e: button.configure(text=e))

root.mainloop() 
