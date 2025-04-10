# Reed-Muller Decoder 
## Group Members: Adwita(2203303), Lakshay(2203312), Jash(2203308)

A user-friendly Python-based GUI application to decode Reed-Muller codes using majority logic. Built with `customtkinter`, the interface allows users to input parameters and a codeword, visualize decoding steps, simulate errors, and understand the decoding process interactively.

## Features

- **Interactive GUI** for decoding Reed-Muller codes.
- **Step-by-step decoding visualization** with majority logic.
- **Polynomial representation** of the decoded message.
- **Error simulation** to test error-correction capability.
- **Display generator matrix (PGM)** for any RM(t, v) code.
- **Custom font and theme support** for enhanced appearance.

## Dependencies

Ensure the following Python packages are installed:

```bash
pip install customtkinter numpy
```

## Decoding Process Explained

The decoding is done using **majority logic decoding**, a method well-suited for Reed-Muller codes.

### 1. **Monomial Basis Construction**
Given parameters RM(t, v), the decoder:
- Constructs all possible **monomials** (terms like `x1x2`, `x3`, or `1`) of degree up to `t`.
- Each monomial represents a column in the generator matrix.

### 2. **Evaluation Vector**
- Converts the input codeword into a **mapping** from all binary inputs of length `v` to output values (0 or 1).

### 3. **Majority Vote per Monomial**
- For each monomial:
  - Partially assign variables and evaluate the residual outputs.
  - Perform a **majority vote** to decide whether the monomial coefficient is `1` or `0`.

### 4. **Constant Term Decoding**
- After removing effects of higher-degree terms, the remaining mismatch helps determine the **constant term**.

### 5. **Reconstructing the Message**
- Coefficients (from step 3 and 4) are compiled into a binary string.
- This string is interpreted as the **message polynomial**.

### 6. **Error Detection**
- The decoded message is re-encoded using the generator matrix.
- The received codeword is compared against this to:
  - Identify error positions.
  - Check if the number of errors is within the correctable limit

### Output:
- **Decoded message**
- **Polynomial expression**
- **Detected errors (if any)**
- **Original codeword** (after correction)
- **Step-by-step log** of majority logic computation

---

