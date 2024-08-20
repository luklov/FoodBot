import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import datetime
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from tkinter import simpledialog

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.image as mpimg

from main import load_data, report, analyze_data, plot

current_date = datetime.date.today().isoformat()

fwat_label_font = ("Helvetica", 36, "italic")
label_font = ("Helvetica", 36)
entry_font = ("Helvetica", 24)

small_button_font = ("Helvetica", 24)
button_font = ("Helvetica", 36)

dropdown_font = ("Helvetica", 24)
calendar_font = ("Helvetica", 24)

choices = ['counters', 'buys', 'counter_avg', 'yeargroup', 'house', 'formclass'] # List of available plot categories

def setup_window(title, title_col=0):
    root = tk.Tk()
    root.title(title)

    # Calculate the window size as 1/3 of the screen's dimensions
    width = root.winfo_screenwidth() // 2
    height = root.winfo_screenheight() // 3
    root.geometry(f"{width}x{height}+0+0")  # Standardize the window size + position
    
    # Create a label with the app name "FWAT" in italic
    label_app_name = tk.Label(root, text="FWAT - Food Waste Analysis Tool", font=fwat_label_font, fg='purple')
    label_app_name.grid(row=0, column=title_col, sticky='nsew', columnspan=2)  # Use grid instead of pack and span across 2 columns

    # Create a line to separate the first row from the rest of the window
    separator = tk.Frame(root, height=2, bd=1, relief="sunken")
    separator.grid(row=1, column=0, sticky='ew', columnspan=1000)  # Span across 2 columns

    return root

def ask_credentials():
    # Create a new window
    popup = tk.Toplevel()
    popup.title("Email Plots")

    # Add email label and entry
    email_label = tk.Label(popup, text="Sender Email:", font=button_font, fg='purple')
    email_label.pack()
    email_entry = tk.Entry(popup)
    email_entry.pack()

    # Add password label and entry
    password_label = tk.Label(popup, text="Password:", font=button_font, fg='purple')
    password_label.pack()
    password_entry = tk.Entry(popup, show="*")
    password_entry.pack()

    # Add email label and entry
    send_to_label = tk.Label(popup, text="Recipient Email:", font=button_font, fg='purple')
    send_to_label.pack()
    send_to_entry = tk.Entry(popup)
    send_to_entry.pack()

    # Add submit button
    submit_button = tk.Button(popup, text="Submit", command=lambda: send_mail(email_entry.get(), password_entry.get(), send_to_entry.get()))
    submit_button.pack()

def send_mail(sender_email, sender_password, recipient_email):
    try:    
        # Set up the SMTP server
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()

        # Log in to the server
        server.login(sender_email, sender_password)

        # Create a multipart message
        msg = MIMEMultipart()

        # Set the email parameters
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "Plot"

        # Attach the file
        with open("plots/plot_app_output.png", "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="plot_app_output.png"')
        msg.attach(part)

        # Send the email
        server.send_message(msg)

        # Close the server
        server.quit()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while sending the email: {str(e)}")    

def launch():
    print("Launching app...")
    signin()
    #mode_choice() # Skip the login screen during dev
    print("App launched!")

def authenticate(entry_username, entry_password, root):
    username = entry_username.get()
    password = entry_password.get()

    # Simple authentication logic
    if username == "admin" and password == "pw":
        #messagebox.showinfo("Login Success", "Welcome, Admin!")
        root.destroy()  # Close the login window
        mode_choice()  # Transition to the next screen
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")

def signin():
    root = setup_window("Sign In")

    # Create the username label and entry with a larger font
    label_username = tk.Label(root, text="Username:", font=label_font)
    label_username.grid(row=1, column=0, sticky='ew')
    entry_username = tk.Entry(root, font=entry_font)
    entry_username.grid(row=1, column=1, sticky='ew')

    # Create the password label and entry with a larger font
    label_password = tk.Label(root, text="Password:", font=label_font)
    label_password.grid(row=2, column=0, sticky='ew')
    entry_password = tk.Entry(root, show="*", font=entry_font)
    entry_password.grid(row=2, column=1, sticky='ew')

    # Create the login button with a larger font
    button_login = tk.Button(root, text="Login", command=lambda: authenticate(entry_username, entry_password, root), font=button_font)
    button_login.grid(row=3, column=0, columnspan=2, sticky='ew')

    # Configure the grid to expand properly when the window is resized
    for i in range(2):
        root.columnconfigure(i, weight=1)
    for i in range(4):
        root.rowconfigure(i, weight=1)

    root.mainloop()

def mode_choice():
    root = setup_window("Mode Choice", 1)

    # Create two buttons for mode choice
    button_mode1 = tk.Button(root, text="Real Time", command=lambda: [root.destroy(), realtime_menu()], font=button_font)
    button_mode1.grid(row=2, column=0, sticky='ew')
    button_mode2 = tk.Button(root, text="Recap", command=lambda: [root.destroy(), recap_menu()], font=button_font)
    button_mode2.grid(row=2, column=1, sticky='ew')

    # Create a signout button
    button_signout = tk.Button(root, text="Sign Out", width=10, command=lambda: [root.destroy(), signin()], font=small_button_font)
    button_signout.grid(row=0, column=0, sticky='ew')

    # Configure the grid to expand properly when the window is resized
    root.columnconfigure(0, weight=1)
    for i in range(3):
        root.rowconfigure(i, weight=1)

    root.mainloop()

def realtime_menu():
    print("Real-time menu selected.")
    root = setup_window("Real-time Menu", 1)

    # Add a back button
    button_back = tk.Button(root, text="Back", command=lambda: [root.destroy(), mode_choice()], font=small_button_font)
    button_back.grid(row=0, column=0, sticky='ew')

    # Configure the grid to expand properly when the window is resized
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    root.mainloop()

def select_date(root, date_var):
    def update_date():
        selected_date = cal.get_date()
        if selected_date <= datetime.date.today():
            date_var.set(selected_date.isoformat())  # Update the date variable with the selected date
            top.destroy()
        else:
            messagebox.showerror("Error", "The date cannot be in the future.")

    
    top = tk.Toplevel(root)
    top.title("Select Date")
    cal = DateEntry(top, width=12, background='light grey', foreground='purple', borderwidth=2, font=calendar_font)
    cal.pack(padx=10, pady=10)

    button_ok = tk.Button(top, text="OK", command=update_date)
    button_ok.pack(pady=10)

def regenerate_data():
    start_date = "2024-05-13"
    end_date = current_date
    all_data = report(start_date, end_date)
    if all_data:
        messagebox.showinfo("Success", "Data regenerated successfully.")
    else:
        messagebox.showerror("Error", "Failed to regenerate data.")
    return all_data

def add_plot(startDate, endDate, preset, continous, all_data, customs = None):
    startDate = datetime.datetime.strptime(startDate.get(), "%Y-%m-%d").date() # Convert the strings to a date object
    endDate = datetime.datetime.strptime(endDate.get(), "%Y-%m-%d").date()

    year_groups = None

    if startDate > endDate:
        messagebox.showerror("Error", "Start date cannot be greater than end date.")
        return

    metadata = analyze_data(all_data, startDate, endDate) # only analyze selected days data

    if preset == "Student":
        plots = ['yeargroup', 'house', 'formclass']
    elif preset == "Sodexo":
        plots = ['counters', 'buys', 'counter_avg']
    elif preset == "All":
        plots = choices
    elif preset == "Custom":
        if customs is None or len(customs) == 0:
            messagebox.showerror("Error", "No custom options selected.")
            return
        plots = customs

    if "formclass" in plots:
        # Prompt the user to enter a list of year groups
        year_groups_input = simpledialog.askstring("Formclass Input", "Enter year groups to show formclasses, separated by commas:")

        # Split the input string into a list of year groups
        year_groups = [year_group.strip() for year_group in year_groups_input.split(',')]
    
    plot(startDate, endDate, plots, metadata, continous, "app_output", year_groups)
    '''
    # Create a new Tkinter window
    window = tk.Tk()

    # Create a new figure and a new axes
    fig = Figure(figsize=(5, 5))
    ax = fig.add_subplot(111)

    # Load the image file
    img = mpimg.imread('plots/plot_app_output.png')

    # Display the image in the axes
    ax.imshow(img)

    # Create a canvas and add it to the window
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()
    canvas.get_tk_widget().pack()

    # Start the Tkinter event loop
    window.mainloop()
    '''

def recap_menu():
    all_data = load_data()

    def call_regenerate_data():
        global all_data
        all_data = regenerate_data()

    print("Recap menu selected.")
    root = setup_window("Recap Menu", 1)

    startDate = tk.StringVar(root, value="2024-05-13")
    endDate = tk.StringVar(root, value=current_date)

    # Add a back button
    button_back = tk.Button(root, text="Back", width=10, command=lambda: [root.destroy(), mode_choice()], font=small_button_font)
    button_back.grid(row=0, column=0, sticky='ew')

    listbox = None # Initialize the listbox variable
    custom_window = None #

    presets = ["Student", "Sodexo", "All", "Custom"]
    
    def get_selected_options(preset_var):
        nonlocal listbox  # Use the outer variable
        # Check if the selected preset is "Custom"
        if preset_var.get() == "Custom" and listbox is not None:
            # Get the selected options from the listbox
            return [listbox.get(i) for i in listbox.curselection()]
        else:
            return None
    
    def on_preset_change(preset_var):
        nonlocal root, custom_window, listbox  # Use the outer variable
        # Check if the selected preset is "Custom"
        if preset_var.get() == "Custom":    
            # Open the custom window
            custom_window, listbox = open_custom_window(root)
        else:
            # Close the listbox if it exists
            if custom_window is not None:
                custom_window.destroy()
                listbox = None

    def open_custom_window(root):
        global choices
        # Create a new window
        custom_window = tk.Toplevel(root)
        custom_window.title("Custom Preset")

        # Add a label to the window
        label = tk.Label(custom_window, text="Pick and order multiple choices:", font=button_font, fg='purple')
        label.pack()

        # Add a listbox to the window
        listbox = tk.Listbox(custom_window, selectmode=tk.MULTIPLE, font=button_font)
        for choice in choices:
            listbox.insert(tk.END, choice)
        listbox.pack()

        return custom_window, listbox
    
    preset_var = tk.StringVar(root)
    preset_var.set(presets[0])  # default value
    preset_var.trace_add("write", lambda *args: on_preset_change(preset_var))
    dropdown_presets = tk.OptionMenu(root, preset_var, *presets)
    dropdown_presets.grid(row=2, column=0, sticky='ew')
    dropdown_presets.configure(font=dropdown_font)  # Change the font and size

    # Create a variable to hold the state of the switch
    continuous_var = tk.BooleanVar()
    continuous_var.set(False)  # Default value

    def update_color():
        # Update the color of the text based on the state of the switch
        switch_continuous.config(fg='green' if continuous_var.get() else 'red')

    # Create a checkbutton that acts as a switch
    switch_continuous = tk.Checkbutton(root, text="Continuous Timeline", variable=continuous_var, command=update_color, font=button_font)
    switch_continuous.grid(row=3, column=1, sticky='ew')

    # Update the color of the text initially
    update_color()

    # Add date buttons
    button_start_date = tk.Button(root, textvariable=startDate, command=lambda: select_date(root, startDate), font=button_font)
    button_start_date.grid(row=4, column=0, sticky='ew')

    button_end_date = tk.Button(root, textvariable=endDate, command=lambda: select_date(root, endDate), font=button_font) # End date select
    button_end_date.grid(row=4, column=1, sticky='ew')

    button_regenerate = tk.Button(root, text="Regenerate Data", command=call_regenerate_data, font=button_font) # Regenerate merged data file
    button_regenerate.grid(row=3, column=0, sticky='ew')

    # Add plot and mail buttons
    button_add_plot = tk.Button(root, text="Preview", command=lambda: add_plot(startDate, endDate, preset_var.get(), continuous_var.get(), all_data, get_selected_options(preset_var)), font=button_font) # Add plot
    button_add_plot.grid(row=5, column=0, sticky='ew')

    button_send_mail = tk.Button(root, text="Send Mail", command=ask_credentials, font=button_font) # sender, recipient
    button_send_mail.grid(row=5, column=1, sticky='ew')

    # Configure the grid to expand properly when the window is resized
    for i in range(3):
        root.columnconfigure(i, weight=1)
    for i in range(7):
        root.rowconfigure(i, weight=1)

    root.mainloop()

if __name__ == "__main__":
    launch()