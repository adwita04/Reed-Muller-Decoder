# Enhanced Reed-Muller Decoder GUI

import customtkinter as ctk
import os
import ctypes
import numpy as np
import random
from math import comb
from itertools import combinations, product
from tkinter import messagebox

# DPI Awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.title("Reed-Muller Decoder")
app.geometry("1000x1000")
app.configure(fg_color="white")

# Fonts
font_path_cafiloser = "Cafiloser.otf"
font_path_mont = "Montserrat-Regular.otf"
cafiloser = ("Cafiloser", 32, "bold") if os.path.exists(font_path_cafiloser) else ("Arial", 28, "bold")
cafiloser_small = ("Cafiloser", 20) if os.path.exists(font_path_cafiloser) else ("Arial", 14)
cafiloser_button = ("Cafiloser", 14) if os.path.exists(font_path_cafiloser) else ("Arial", 12)
mont_input = ("Montserrat", 14) if os.path.exists(font_path_mont) else ("Arial", 12)
mont_output = ("Montserrat", 18, "bold") if os.path.exists(font_path_mont) else ("Arial", 12)

# Functions

def dec_to_binary(n, v):
    return format(n, f'0{v}b')

# Find Coefficient using Majority Logic 
def find_coeff(mon, evals, var):
    coeff = {}
    ans = ''
    steps = []  

    for pol, m in enumerate(mon):
        if pol == len(mon)-1:
            continue

        part_ass, comp = [], []
        for idx, i in enumerate(m):
            (part_ass if i == 0 else comp).append(idx)

        bags, v = {}, {}
        count_1, count_0 = 0, 0

        for i in product(range(2), repeat=len(part_ass)):
            tot = 0
            for t, j in enumerate(part_ass):
                v[j] = i[t]
            for y in product(range(2), repeat=len(comp)):
                for t0, z in enumerate(comp):
                    v[z] = y[t0]
                to_eval = ''.join(str(v[s]) for s in range(var))
                tot ^= int(evals[to_eval])
            key = ''.join(str(i[t]) for t in range(len(part_ass)))
            bags[key] = tot
            if tot == 1:
                count_1 += 1
            else:
                count_0 += 1

        majority = 1 if count_1 > count_0 else 0
        coeff[pol] = majority
        ans += '1' if majority else '0'

        # Generate human-readable monomial like x1x3
        term = ''.join([f"x{idx+1}" for idx, val in enumerate(m) if val == 1]) or "1"

        steps.append(
            f"Monomial {pol + 1} ({term}):\n"
            f"Binary: {''.join(map(str, m))}\n"
            f"Assignments with 1s: {count_1}, 0s: {count_0}\n"
            f"Majority = {majority}\n"
        )


    # Constant term
    maj_bag = []
    for bits in product(range(2), repeat=var):
        r = int(evals[''.join(map(str, bits))])
        f_val = 0
        for i, monomial in enumerate(mon):
            if i == len(mon)-1:
                continue
            term_val = 1
            for j in range(var):
                if monomial[j] == 1:
                    term_val &= bits[j]
            f_val ^= (coeff[i] * term_val)
        maj_bag.append(r ^ f_val)

    count_1 = maj_bag.count(1)
    count_0 = maj_bag.count(0)
    a_0 = 1 if count_1 > count_0 else 0
    ans += '1' if a_0 else '0'
    ans = ans[::-1]

    steps.append(
        f"Constant Term (Final Majority Check):\n"
        f"Total 1s: {count_1}, 0s: {count_0}\n"
        f"a_0 = {a_0}"
    )

    return ans, coeff, steps

# Main Decoder function
def decoder(t, v, codeword):
    n = 1 << v
    evals = {format(i, f'0{v}b'): codeword[i] for i in range(n)}
    monomials = []
    for d in range(t + 1):
        for combo in combinations(range(v), d):
            monomial = [0] * v
            for i in combo:
                monomial[i] = 1
            monomials.append(monomial)
    monomials.reverse()
    return monomials, evals

# Generate Parity Generator Matrix
def generate_pgm(r, m):
    monomials = [mask for mask in product([0, 1], repeat=m) if sum(mask) <= r]
    inputs = list(product([0, 1], repeat=m))
    G = [[
        int(all(inp[i] if mono[i] else 1 for i in range(m))) for inp in inputs
    ] for mono in monomials]
    return np.array(G), monomials

# Encode message using PGM
def encode_message(message_str, generator_matrix):
    message_bits = np.array([int(b) for b in message_str])
    codeword = np.dot(message_bits, generator_matrix) % 2
    return ''.join(str(int(b)) for b in codeword)

# Find Errors
def find_error_positions(encoded_str, received_str):
    error_mask = ''.join('1' if a != b else '0' for a, b in zip(encoded_str, received_str))
    return error_mask, [i for i, bit in enumerate(error_mask) if bit == '1']

# Find Polynomial message
def polynomial_string(coeffs, monomials):
    terms = []
    for c, m in zip(coeffs, monomials[::-1]):
        if c:
            term = ''.join([f"x{i+1}" for i in range(len(m)) if m[i] == 1])
            terms.append(term if term else '1')
    return ' + '.join(terms)

# Function decode the message 
def decode_action():
    decoded_label.configure(text="")
    matrix_label.configure(text="")
    pgm_label.configure(text="")
    steps_label.configure(text="")

    try:
        t, v = int(entries[0].get()), int(entries[1].get())
        codeword = entries[2].get().strip()
        if len(codeword) != 2 ** v:
            decoded_label.configure(text="Codeword length must be 2^v")
            return

        mon, evals = decoder(t, v, codeword)
        decoded_str, coeff_dict, decoding_steps = find_coeff(mon, evals, v)
        G, monomials = generate_pgm(t, v)
        encoded = encode_message(decoded_str, G)
        error_mask, indices = find_error_positions(encoded, codeword)

        max_errors = (2 ** (v - t) - 1) // 2
        if len(indices) > max_errors:
            messagebox.showerror("Too Many Errors", 
                                 f"Maximum correctable errors for RM({t},{v}) is {max_errors}.\n"
                                 f"Detected {len(indices)} errors which exceeds this limit.")
            return
        decoded_frame.configure(border_color="#1D2450", fg_color='#CDC3DB', border_width=2)
        poly_expr = polynomial_string([int(b) for b in decoded_str], mon)
        decoded_label.configure(text=f"{decoded_str}")
        polynomial_label.configure(text=f"Polynomial: f(x) = {poly_expr}")
        process_steps_text = "\n\n".join(decoding_steps)
        steps_label.configure(text=f"{process_steps_text}")

        if not indices:
            error_label.configure(text="No error", text_color="#0B6B35")
            orig_label.configure(text="")
        else:
            error_label.configure(text=f"Error at Positions: {indices}", text_color="#8E0608")
            orig_label.configure(text=f"Original Codeword: {encoded}", text_color="#1D2450")

    except Exception as e:
        decoded_label.configure(text=f"Error: {e}")

# Function to display PGM
def display_generator_matrix():
    try:
        t, v = int(entries[0].get()), int(entries[1].get())
        G, monomials = generate_pgm(t, v)

        matrix_text = "Generator Matrix (PGM):\n"
        matrix_text += "Monomials: " + ", ".join(["".join(map(str, m)) for m in monomials]) + "\n\n"
        
        for row in G:
            matrix_text += " ".join(map(str, row)) + "\n"
        
        pgm_label.configure(text="Parity Generator Matrix: ")
        matrix_label.configure(text=matrix_text)
    except Exception as e:
        matrix_label.configure(text=f"Error displaying generator matrix: {e}")

# Function to reset inputs  
def reset_action():
    for entry in entries:
        entry.delete(0, "end")
    decoded_label.configure(text="")
    polynomial_label.configure(text="")
    error_label.configure(text="")
    orig_label.configure(text="")
    matrix_label.configure(text="")
    pgm_label.configure(text="")
    steps_label.configure(text="")

# Function to simulate error
def simulate_error():
    try:
        t = int(entries[0].get())
        v = int(entries[1].get())
        codeword = entries[2].get().strip()
        
        if not codeword:
            messagebox.showerror("Error", "Please enter a codeword first")
            return
            
        if len(codeword) != 2 ** v:
            messagebox.showerror("Error", f"Codeword length must be exactly {2**v} bits for v={v}")
            return

        max_errors = (2 ** (v - t) - 1) // 2
        if max_errors < 1:
            messagebox.showerror("Error", 
                               f"RM({t},{v}) cannot correct any errors (max correctable: {max_errors})")
            return

        num_errors = random.randint(1, max_errors)
        
        positions = list(range(len(codeword)))
        error_positions = random.sample(positions, num_errors)
        codeword_list = list(codeword)
        for pos in error_positions:
            codeword_list[pos] = '1' if codeword_list[pos] == '0' else '0'
        
        entries[2].delete(0, "end")
        entries[2].insert(0, ''.join(codeword_list))
        

    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid integers for t and v")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Function to load sample inputs
def load_sample():
    entries[0].delete(0, "end")
    entries[0].insert(0, "1")
    entries[1].delete(0, "end")
    entries[1].insert(0, "4")
    entries[2].delete(0, "end")
    entries[2].insert(0, "1100001111000011")


# GUI Layout

main_frame = ctk.CTkScrollableFrame(app, fg_color="#9f93aa", corner_radius=15)
main_frame.pack(padx=15, pady=15, expand=True, fill="both")

title = ctk.CTkLabel(main_frame, text="REED MULLER DECODER", font=cafiloser, text_color="#1D2450")
title.pack(pady=(30, 10))

input_label = ctk.CTkLabel(main_frame, text="INPUT", font=cafiloser_small, text_color="#495291")
input_label.pack(pady=5)

input_frame = ctk.CTkFrame(main_frame, fg_color="#9f93aa")
input_frame.pack(pady=2.5)

labels = ["t :", "v :", "Codeword :"]
entries = []

for i, label in enumerate(labels):
    ctk.CTkLabel(input_frame, text=label, font=mont_input, text_color="#1D2450", width=80, anchor="e").grid(row=i, column=0, pady=5, padx=10)
    entry = ctk.CTkEntry(input_frame, font=mont_input, width=220, fg_color="#d6d2d6", border_width=0)
    entry.grid(row=i, column=1, pady=5)
    entries.append(entry)

# Button Frame
button_frame = ctk.CTkFrame(main_frame, fg_color="#9f93aa")
button_frame.pack(pady=(10, 10))

buttons = [
    ("DECODE", decode_action),
    ("Simulate Error", simulate_error),
    ("Load Sample", load_sample),
    ("Display PGM", display_generator_matrix ),
    ("RESET", reset_action)
]

for i, (txt, cmd) in enumerate(buttons):
    ctk.CTkButton(button_frame, text=txt, font=cafiloser_button, 
                 fg_color="#1D2450", text_color="#9f93aa", 
                 hover_color="#495291", corner_radius=15, 
                 width=120, height=40, command=cmd).grid(row=0, column=i, padx=5)

# Label frame to hold both labels side-by-side
label_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
label_frame.pack(pady=(20, 0), padx=20, fill="x")

# Output Label
output_label = ctk.CTkLabel(label_frame, text="OUTPUT", font=cafiloser_small, text_color="#495291")
output_label.pack(side="left", padx=(0, 10), expand=True, fill="x", anchor="w")

# Process Label
process_label = ctk.CTkLabel(label_frame, text="Decoding Process", font=cafiloser_small, text_color="#495291")
process_label.pack(side="left", padx=(10, 0), expand=True, fill="x", anchor="w")

# Frame holding both areas side-by-side
side_by_side_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
side_by_side_frame.pack(pady=(5, 20), padx=20, fill="both", expand=True)

# Output Frame (50%)
output_scroll_frame = ctk.CTkFrame(side_by_side_frame, fg_color="#e4e0e4", corner_radius=10)
output_scroll_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

# Process Frame (50%)
process_scroll_frame = ctk.CTkFrame(side_by_side_frame, fg_color="#e4e0e4", corner_radius=10)
process_scroll_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))

# Decoded Message
decoded_ = ctk.CTkLabel(output_scroll_frame, text="Decoded Message: ", font=mont_output, text_color="#495291")
decoded_frame = ctk.CTkFrame(output_scroll_frame, fg_color='#e4e0e4', corner_radius=10)
decoded_label = ctk.CTkLabel(decoded_frame, text="", font=mont_output, text_color="#1D2450")

decoded_.pack(pady=2.5)
decoded_frame.pack(pady=5, padx=20)
decoded_label.pack(pady=10, padx=20)

# Polynomial
polynomial_label = ctk.CTkLabel(output_scroll_frame, text="", font=mont_input, text_color="#1d3557", wraplength=600, justify="left")
polynomial_label.pack(pady=5, padx=10)

# Error Info
error_label = ctk.CTkLabel(output_scroll_frame, text="", font=mont_output, wraplength=600, justify="left")
error_label.pack(pady=5, padx=10)

# Original Message
orig_label = ctk.CTkLabel(output_scroll_frame, text="", font=mont_output, wraplength=600, justify="left")
orig_label.pack(pady=2.5, padx=10)

# Generator Matrix
pgm_label = ctk.CTkLabel(output_scroll_frame, text="", font=mont_output, text_color="#495291")
pgm_label.pack(pady=2.5)
matrix_label = ctk.CTkLabel(output_scroll_frame, text="", font=("Courier New", 14), wraplength=800, justify="center")
matrix_label.pack(pady=10, padx=10)

# Steps 
steps_label = ctk.CTkLabel(process_scroll_frame, text="", font=mont_input, wraplength=850, justify="left", text_color="#1D2450")
steps_label.pack(padx=10, pady=10)

app.mainloop()