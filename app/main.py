"""Diem khoi chay ung dung.

Chay tu thu muc goc du an: python -m app.main
"""

from app.views.main_window import MainWindow


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()