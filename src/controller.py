import tkinter as tk
import tkinter.ttk as ttk
from pandas import DataFrame
from PIL import ImageTk, Image
import heartpy as hp
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import socket
import csv
import time
import matplotlib.animation as animation
import concurrent.futures
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA = os.path.join(BASE_DIR, 'media')
CLIENT_THREAD_FINISHED = False
PROGRESSBAR_THREAD_FINISHED = False


class Controller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry('1200x830')
        self.title('ECG Tool')
        self.protocol("WM_DELETE_WINDOW", self.__on_exit)

        self.__model = DataOperator()
        self.__frames = {}

        for F in (StartPage, MeasurePage, ResultPage):
            page_name = F.__name__
            frame = F(self)
            self.__frames[page_name] = frame
            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame('StartPage')

    def __on_exit(self):
        """When you click to exit, this function is called"""
        if tk.messagebox.askyesno("Exit", "Do you want to quit the application?"):
            plt.close('all')
            self.destroy()

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        self.__frame = self.__frames[page_name]
        self.__frame.tkraise()

    def start_measure(self):
        self.lock = threading.Lock()
        t1 = threading.Thread(target=self.__model.start_client)
        t1.daemon = True
        t1.start()
        t2 = threading.Thread(target=self.__frame.progress_bar_func)
        t2.daemon = True
        t2.start()
        self.after(500, self.__check_status)  # Start polling.

    def __progress_data(self):
        if not self.__model.client_state_pointer:
            self.__frame.unlock_btn()
            tk.messagebox.showerror(
                title='Server problem', message='Brak połączenia z serwerem')
        else:
            data, working_data, measures = self.__model.analyse_data()
            if data is not None:
                self.show_frame('ResultPage')
                self.__frame.display_result(data, working_data, measures)
            else:
                self.__frame.unlock_btn()
                tk.messagebox.showerror(
                    title='Niepoprawny pomiar', message='Niepoprawny pomiar.')

    def __check_status(self):
        global PROGRESSBAR_THREAD_FINISHED
        global CLIENT_THREAD_FINISHED

        with self.lock:
            if not (PROGRESSBAR_THREAD_FINISHED and CLIENT_THREAD_FINISHED):
                self.after(500, self.__check_status)  # Keep polling.
            else:
                self.__progress_data()


class StartPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.__parent = parent
        self.__set_background_photo()
        self.__set_buttons_labels()

    def __set_background_photo(self):
        self.__background_photo = ImageTk.PhotoImage(
            Image.open(os.path.join(MEDIA, 'test.png')))
        background_label = tk.Label(self, image=self.__background_photo)
        background_label.grid(
            row=0, column=0, columnspan=10, rowspan=10, sticky="nsew")

    def __set_buttons_labels(self):
        self.__button_photo = ImageTk.PhotoImage(
            Image.open(os.path.join(MEDIA, 'start.png')))
        start_btn = tk.Button(self, image=self.__button_photo, borderwidth=0.1,
                              command=lambda: self.__parent.show_frame('MeasurePage'))
        start_btn.grid(row=5, column=6, columnspan=1, rowspan=2)
        start_label = tk.Label(self, text='NACIŚNIJ SERCE BY ROZPOCZĄĆ!',
                               bg='#FEEBE7', fg='#660033', font=('italic', 30))
        start_label.grid(row=0, column=0, columnspan=10)


class MeasurePage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.__parent = parent

        self.__tutorial_frame = tk.Frame(
            self, width=1200, height=400, bg='#4C0000')
        self.__tutorial_frame.grid(row=0, column=0)

        self.__tutorial_description_frame = tk.Frame(
            self, width=1200, height=200, bg='#FDAA0E')
        self.__tutorial_description_frame.grid(row=1, column=0)

        self.__button_frame = tk.Frame(
            self, width=1200, height=150, bg='#FDAA0E')
        self.__button_frame.grid(row=2, column=0)

        self.__loading_frame = tk.Frame(
            self, width=1200, height=80, bg='#FDAA0E')
        self.__loading_frame.grid(row=3, column=0)

        self.__tutorial_frame.grid_columnconfigure(0, weight=1)
        self.__tutorial_frame.grid_columnconfigure(1, weight=1)
        self.__tutorial_frame.grid_columnconfigure(2, weight=1)
        self.__tutorial_frame.grid_rowconfigure(0, weight=1)
        self.__tutorial_frame.grid_propagate(0)

        self.__tutorial_description_frame.grid_columnconfigure(0, weight=1)
        self.__tutorial_description_frame.grid_columnconfigure(1, weight=1)
        self.__tutorial_description_frame.grid_columnconfigure(2, weight=1)
        self.__tutorial_description_frame.grid_rowconfigure(0, weight=1)
        self.__tutorial_description_frame.grid_propagate(0)

        self.__button_frame.grid_columnconfigure(0, weight=1)
        self.__button_frame.grid_rowconfigure(0, weight=1)
        self.__button_frame.grid_propagate(0)

        self.__loading_frame.grid_columnconfigure(0, weight=1)
        self.__loading_frame.grid_rowconfigure(0, weight=1)
        self.__loading_frame.grid_propagate(0)

        self.__set_buttons_labels()

    def __set_buttons_labels(self):
        self.__tutorial_photo_1 = ImageTk.PhotoImage(
            Image.open(os.path.join(MEDIA, 'tuto1.png')))
        tutorial_photo_1 = tk.Label(
            self.__tutorial_frame, image=self.__tutorial_photo_1)
        tutorial_photo_1.grid(row=0, column=0)
        tutorial_label_1 = tk.Label(self.__tutorial_description_frame, text='Upewnij się że elektrody są przytwierdzone w sposób zgodny z obrazkiem.', font=(
            'italic', 15), wraplength=300, bg='#FDAA0E')
        tutorial_label_1.grid(row=0, column=0, sticky="nsew")

        self.__tutorial_photo_2 = ImageTk.PhotoImage(
            Image.open(os.path.join(MEDIA, 'tuto2.jpg')))
        tutorial_photo_2 = tk.Label(
            self.__tutorial_frame, image=self.__tutorial_photo_2)
        tutorial_photo_2.grid(row=0, column=1)
        tutorial_label_2 = tk.Label(self.__tutorial_description_frame, text='Aby ustabilizować tętno i oddech wymagane jest przyjęcie pozycji siedzącej lub leżącej.', font=(
            'italic', 15), wraplength=300, bg='#FDAA0E')
        tutorial_label_2.grid(row=0, column=1, sticky="nsew")

        self.__tutorial_photo_3 = ImageTk.PhotoImage(
            Image.open(os.path.join(MEDIA, 'tuto3.jpg')))
        tutorial_photo_3 = tk.Label(
            self.__tutorial_frame, image=self.__tutorial_photo_3)
        tutorial_photo_3.grid(row=0, column=2)
        tutorial_label_3 = tk.Label(self.__tutorial_description_frame, text='Pomiar potrwa około 30 sekund. W tym czasie wskazane jest wykonywanie głębokich oddechów. Proszę pozostać w bezruchu.', font=(
            'italic', 15), wraplength=300, bg='#FDAA0E')
        tutorial_label_3.grid(row=0, column=2, sticky="nsew")

        def btn_func():
            self.__start_btn.config(state=tk.DISABLED)
            self.__parent.start_measure()

        self.__start_btn = tk.Button(
            self.__button_frame,
            text='Rozpocznij pomiar',
            bd=0,
            relief="groove",
            compound=tk.CENTER,
            bg='#4C0000',
            fg="orange",
            # activeforeground="pink",
            # activebackground="white",
            font="arial 30",
            pady=10,
            borderwidth=3,
            command=lambda: btn_func()
        )

        self.__start_btn.grid(row=0, column=0)

        self.__prog_bar_var = tk.IntVar()
        self.__prog_bar_var.set(0)
        self.__progress_bar = ttk.Progressbar(
            self.__loading_frame, length=100, variable=self.__prog_bar_var, style="black.Horizontal.TProgressbar", mode="determinate")
        self.__progress_bar.grid(row=0, column=0, sticky="nsew")

    def unlock_btn(self):
        self.__start_btn.config(state=tk.ACTIVE)

    def progress_bar_func(self):
        global PROGRESSBAR_THREAD_FINISHED

        for i in range(1, 101):
            time.sleep(0.320)
            self.__prog_bar_var.set(i)

        PROGRESSBAR_THREAD_FINISHED = True


class ResultPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.__parent = parent

        self.__description_frame = tk.Frame(self, width=1200, height=200)
        self.__description_frame.grid(row=0, column=0, sticky="nsew")
        self.__description_frame.grid_columnconfigure(0, weight=1)
        self.__description_frame.grid_columnconfigure(1, weight=1)
        self.__description_frame.grid_rowconfigure(0, weight=1)
        self.__description_frame.grid_rowconfigure(1, weight=1)
        self.__description_frame.grid_propagate(0)

        self.__graph_frame = tk.Frame(
            self, width=1200, height=630, highlightthickness=20)
        self.__graph_frame.grid(row=1, column=0, sticky="nsew")
        self.__graph_frame.grid_columnconfigure(0, weight=1)
        self.__graph_frame.grid_rowconfigure(0, weight=1)
        self.__graph_frame.grid_propagate(0)

        self.__set_buttons_labels()

    def __set_buttons_labels(self):
        description_label = tk.Label(
            self.__description_frame, bg='#FEEBE7', text='Wyniki badań', font=('italic', 30))
        description_label.grid(row=0, column=0, columnspan=2, sticky="nsew")

    def display_result(self, data, working_data, measures):
        bpm = int(measures["bpm"])
        if bpm >= 60 and bpm <= 100:
            bpm_color = '#33FF42'
        else:
            bpm_color = '#FF3333'
        # rmssd = float(measures["rmssd"])
        # if rmssd >=12 and rmssd<=27:
        #     rmssd_color = '#33FF42'
        # else:
        #     rmssd_color = '#FF3333'
        breathing_rate = float(measures["breathingrate"]) * 60
        breathing_rate = int(breathing_rate)
        if breathing_rate >= 12 and breathing_rate <= 16:
            breathing_rate_color = '#33FF42'
        else:
            breathing_rate_color = '#FF3333'
        bpm_label = tk.Label(self.__description_frame, bg='#FEEBE7',
                             text=f'Tętno: {bpm}, norma 60~100', foreground=bpm_color, font=('italic', 20))
        # rmssd_label = tk.Label(self.__description_frame, text = f'RMSSD: {rmssd}, norma 12~27', foreground=rmssd_color, font=('italic', 15), wraplength=300)
        breathingrate_label = tk.Label(self.__description_frame, bg='#FEEBE7',
                                       text=f'Współczynnik oddechu: {breathing_rate}, norma 12~16', foreground=breathing_rate_color, font=('italic', 20))

        bpm_label.grid(row=1, column=0, sticky="nsew")
        breathingrate_label.grid(row=1, column=1, sticky="nsew")
        plt.plot(data[1500:3000])
        plt.title('Wykaz EKG pacjenta')
        fig = plt.gcf()
        ax = plt.gca()
        ax.set_facecolor('#FEEBE7')
        fig.patch.set_facecolor('xkcd:mint green')
        fig.set_size_inches(15, 5.8, forward=True)
        chart_type = FigureCanvasTkAgg(fig, self.__graph_frame)
        chart_type.get_tk_widget().grid(row=0, column=0, sticky="nsew")


class DataOperator:
    def start_client(self):
        global CLIENT_THREAD_FINISHED
        self.__ekg_content = list()
        # Client code
        HOST = '192.168.0.31'  # The server's hostname or IP address
        PORT = 8083        # The port used by the server
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                start = time.time()
                while len(self.__ekg_content) < 8000:
                    data = s.recv(4)
                    # print(data.decode())
                    if len(data) > 0:
                        self.__ekg_content.append(int(data.decode())-1000)

                    else:
                        break
            end = time.time()
            print(end-start)
            # plt.plot(self.__ekg_content)
            # plt.show()

            self.__save_to_csv()
            self.client_state_pointer = True
            CLIENT_THREAD_FINISHED = True

        except TimeoutError as err:
            print(err)
            CLIENT_THREAD_FINISHED = True
            self.client_state_pointer = False

    def __save_to_csv(self):
        with open('najnowszy2.csv', 'w+', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.__ekg_content)

    def analyse_data(self):
        try:
            sample_rate = 250
            data = hp.get_data('najnowszy2.csv')
            filtered = hp.filter_signal(
                data, cutoff=0.05, sample_rate=sample_rate, filtertype='notch')
            working_data, measures = hp.process(filtered, sample_rate)
            return data, working_data, measures
        except hp.exceptions.BadSignalWarning as err:
            print(err)
            return None, None, None
