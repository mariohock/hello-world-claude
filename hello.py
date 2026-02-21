#!/usr/bin/env python3

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class HelloWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Hello World")
        self.set_default_size(600, 400)

        label = Gtk.Label(label="Hello, World!")
        label.add_css_class("title-1")
        self.set_child(label)


def on_activate(app):
    window = HelloWindow(application=app)
    window.present()


def main():
    app = Gtk.Application(application_id="com.example.helloworld")
    app.connect("activate", on_activate)
    app.run()


if __name__ == "__main__":
    main()
