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

class ReedMullerDecoder:
    def __init__(self, r=2, m=4):
        self.r = r  # degree of polynomial
        self.m = m  # number of variables
        self.n = 2**m  # code length
        
        # Generate all monomials in order (degree r first, then r-1, ..., 0)
        self.monomials = []
        self.monomial_strings = []
        
        for degree in range(r, -1, -1):
            for vars in combinations(range(1, m+1), degree):
                self.monomials.append(vars)
                if len(vars) == 0:
                    self.monomial_strings.append("1")
                else:
                    self.monomial_strings.append("X" + "X".join(map(str, vars)))
        
        # Initialize steps storage
        self.calculation_steps = []
    
    def evaluate_monomial(self, monomial, x):
        """Evaluate a monomial at point x (x is a binary tuple of length m)"""
        result = 1
        for var in monomial:
            result *= x[var-1]
        return result
    
    def get_valuation(self, monomial):
        """Get the valuation vector for a monomial (all possible inputs)"""
        valuation = []
        for i in range(self.n):
            x = tuple((i >> (self.m - j - 1)) & 1 for j in range(self.m))
            valuation.append(self.evaluate_monomial(monomial, x))
        return valuation
    
    def decode(self, received_word):
        """Decode a received word using majority logic"""
        current_code = list(received_word.copy())
        polynomial = {}
        decoded_message = []
        self.calculation_steps = []  # Reset steps for each decode
        
        for monomial, monomial_str in zip(self.monomials, self.monomial_strings):
            step_info = {
                'monomial': monomial_str,
                'ones': 0,
                'zeros':0,
                'coefficient': None
            }
            
            # Determine fixed and varying variables
            all_vars = set(range(1, self.m+1))
            monomial_vars = set(monomial)
            fixed_vars = list(all_vars - monomial_vars)
            
            sums = []
            
            # Generate all possible fixed variable assignments
            for fixed_assignment in product([0, 1], repeat=len(fixed_vars)):
                assignment_info = {
                }
                
                total = 0
                # Generate all possible varying assignments
                for varying_assignment in product([0, 1], repeat=len(monomial)):
                    # Build complete assignment
                    assignment = [0] * self.m
                    # Set fixed variables
                    for var, val in zip(fixed_vars, fixed_assignment):
                        assignment[var-1] = val
                    # Set varying variables
                    for var, val in zip(monomial, varying_assignment):
                        assignment[var-1] = val
                    # Convert to index
                    index = 0
                    for j in range(self.m):
                        index = (index << 1) | assignment[j]
                    
                    total += current_code[index]
                
                sum_value = total % 2
                sums.append(sum_value)
            
            # Determine coefficient by majority vote
            ones = sum(sums)
            zeros = len(sums) - ones
            if ones > zeros:
                coefficient = 1
            elif zeros > ones:
                coefficient = 0
            else:
                coefficient = 0  # tie-breaker
            
            step_info['ones'] = ones
            step_info['zeros'] = zeros
            step_info['coefficient'] = coefficient
            self.calculation_steps.append(step_info)
            
            polynomial[monomial_str] = coefficient
            decoded_message.append(coefficient)
            
            # Update current code if coefficient is 1
            if coefficient == 1:
                valuation = self.get_valuation(monomial)
                for i in range(self.n):
                    current_code[i] = (current_code[i] - valuation[i]) % 2
        
        return polynomial, current_code, decoded_message
    
    def print_calculation_steps(self):
        steps = '\nDetailed Calculation Steps:\n'
        for step in self.calculation_steps:
            steps += f"\nMonomial: {step['monomial']}"
            steps+=f"\nMajority vote (1s: {step['ones']}, 0s: {step['zeros']})"
            steps+=f" → Coefficient: {step['coefficient']}\n"
            steps+="-"*50
        return steps


def arr_to_string(a):
    s =''
    for i in range(len(a)):
        s+= '0' if a[i] == 0 else '1'
    return s
# Generate Parity Generator Matrix
def generate_pgm(r, m):
    monomials = [mask for mask in product([0, 1], repeat=m) if sum(mask) <= r]
    inputs = list(product([0, 1], repeat=m))
    G = [[
        int(all(inp[i] if mono[i] else 1 for i in range(m))) for inp in inputs
    ] for mono in monomials]
    return np.array(G), monomials

# Function decode the message 
def decode_action():
    decoded_label.configure(text="")
    matrix_label.configure(text="")
    pgm_label.configure(text="")
    steps_label.configure(text="")

    try:
        t, v = int(entries[0].get()), int(entries[1].get())
        codeword = entries[2].get().strip()
        received_word = [int(bit) for bit in codeword]

        if len(codeword) != 2 ** v:
            decoded_label.configure(text="Codeword length must be 2^v")
            return
        
        rm = ReedMullerDecoder(t, v)
        polynomial,error_vec, decoded_str = rm.decode(received_word)

        G = generate_pgm(t, v)
        
        decoded_frame.configure(border_color="#1D2450", fg_color='#CDC3DB', border_width=2)
        poly_terms = []
        for monom, coeff in polynomial.items():
            if coeff == 1:
                poly_terms.append(monom)

        poly_expr = " + ".join(poly_terms) if poly_terms else "0"
        decoded_label.configure(text=f"{arr_to_string(decoded_str)}")
        polynomial_label.configure(text=f"Polynomial: f(x) = {poly_expr}")
        

        err =[]
        no_err = 0
        for i in range(len(error_vec)):
            if error_vec[i] == 1:
                err.append(i)
                no_err += 1
                
        corr_str = received_word

        for i in err:
            corr_str[i] = 1 if received_word[i] == 0 else 0


        max_errors = (2 ** (v - t) - 1) // 2
        if no_err == 0: 
            error_label.configure(text="No error", text_color="#0B6B35")
            orig_label.configure(text="")
        elif no_err > max_errors:
            messagebox.showerror("Too Many Errors", 
                                 f"Maximum correctable errors for RM({t},{v}) is {max_errors}.\n"
                                 f"Detected {no_err} errors which exceeds this limit.")
            return
        else:
            error_label.configure(text=f"Error at Positions: {err}", text_color="#8E0608")
            orig_label.configure(text=f"Original Codeword: {arr_to_string(corr_str)}", text_color="#1D2450")

        process_steps_text = rm.print_calculation_steps()
        steps_label.configure(text=f"{process_steps_text}")


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
    entries[0].insert(0, "2")
    entries[1].delete(0, "end")
    entries[1].insert(0, "4")
    entries[2].delete(0, "end")
    entries[2].insert(0, "0111100001001011")


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
