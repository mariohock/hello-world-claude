#!/usr/bin/env python3

import tkinter as tk


def main():
    root = tk.Tk()
    root.title("Hello World")
    root.geometry("600x400")

    label = tk.Label(root, text="Hello, World!", font=("Arial", 24))
    label.pack(expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
