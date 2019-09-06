import tkinter as tk
from tkinter import filedialog

window = tk.Tk()
window.title("ChemCham Calibration")
window.geometry('500x350')

lbl = tk.Label(window, text="Input: ")

# radio button group
inputType = tk.IntVar()
fileBtn = tk.Radiobutton(window, text='File', value=1, variable=inputType)
listBtn = tk.Radiobutton(window, text='List Of Files', value=2, variable=inputType)
directoryBtn = tk.Radiobutton(window, text='Directory', value=3, variable=inputType)

fileName = tk.Entry(window, width=30)


def browse_clicked():
    file_type = inputType.get()
    if file_type == 1: # file
        print("file")
        file = filedialog.askopenfilename()
    elif file_type == 2: # list of files
        print("list of files")
        file = filedialog.askopenfilename()
    elif file_type == 3: # dir
        print("directory")
        file = filedialog.askdirectory()
    print(file)
    fileName.delete(0, "end")
    fileName.insert(0, file)


browseBtn = tk.Button(window, text='Browse', command=browse_clicked)

lbl.grid(column=0, row=0, sticky="w")
fileBtn.grid(column=0, row=1, sticky="w")
listBtn.grid(column=1, row=1, sticky="w")
directoryBtn.grid(column=2, row=1, sticky="w")
fileName.grid(column=0, row=2, columnspan=3, sticky="w")
browseBtn.grid(column=3, row=2, sticky="w")

window.mainloop()