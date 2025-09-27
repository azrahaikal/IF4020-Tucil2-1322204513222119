import math
import random
import os
import sys
from pydub import AudioSegment
import numpy as np

# --- Encryption Functions (Unchanged) ---

def encrypt_key(message, key):
    """Mengulang kunci enkripsi agar panjangnya sama dengan panjang teks."""
    if len(message) >= len(key):
        return "".join(key[i % len(key)] for i in range(len(message)))
    return "".join(key)

def encrypt(message, key):
    """Mengenkripsi teks menggunakan sandi Vigenère."""
    cipher = []
    key = encrypt_key(message, key)
    for i in range(len(message)):
        kode_karakter = ord(message[i])
        kode_kunci = ord(key[i])
        karakter_terenkripsi = chr((kode_karakter + kode_kunci) % 256)
        cipher.append(karakter_terenkripsi)
    return "".join(cipher)

def decrypt(cipher, key):
    """Mendekripsi teks menggunakan sandi Vigenère."""
    message = []
    key = encrypt_key(cipher, key)
    for i in range(len(cipher)):
        kode_karakter_enkripsi = ord(cipher[i])
        kode_kunci = ord(key[i])
        karakter_asli = chr((kode_karakter_enkripsi - kode_kunci + 256) % 256)
        message.append(karakter_asli)
    return "".join(message)

# --- Core Steganography Functions (MODIFIED) ---

def calculate_random_start_index(message_size_in_bits, m, audio_samples, seed):
    """
    Calculates a random starting index, ensuring it doesn't overwrite the header.
    """
    print("\n--- Calculating Random Start Index ---")
    
    r = len(audio_samples)
    header_size = 41
    buffer = 200 # A safe buffer
    samples_needed_for_payload = math.ceil(message_size_in_bits / m)
    
    # Espace is the number of available slots to start the embedding
    espace = r - samples_needed_for_payload - header_size - buffer
    
    if espace <= 0:
        print("\n[ERROR] The secret file is likely too large for this MP3 or 'm' is too small.")
        return None

    random.seed(seed)
    
    # Pick a random offset within the available space
    rand_offset = random.randint(0, int(espace))
    
    # The final index is after the header, the buffer, and the random offset
    Irand = header_size + buffer + rand_offset
    
    print(f"Calculated random start index: {Irand}")
    return Irand

def key_to_seed(key):
    """Converts a string key into a numerical seed."""
    seed = 0
    for char in key:
        seed = (seed * 31 + ord(char)) & 0xFFFFFFFF
    return seed

def convert_file_to_bits(file_path):
    """
    Reads any file in binary mode and converts its content to a list of bits.
    """
    print(f"--- [Step 2] Converting '{os.path.basename(file_path)}' to a bit stream ---")
    try:
        with open(file_path, 'rb') as f:
            content_bytes = f.read()
        bits = [int(bit) for byte in content_bytes for bit in format(byte, '08b')]
        print(f"File converted to {len(bits)} bits.")
        return bits
    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
        return None
    except Exception as e:
        print(f"[ERROR] Could not read file: {e}")
        return None

def embed_file(mp3_path, secret_file_path, output_path, m, isEncrypt, isRandom, key):
    """
    Embeds any secret file into an MP3 file. Returns True on success, False on failure.
    """
    try:
        audio = AudioSegment.from_mp3(mp3_path)
        samples = np.array(audio.get_array_of_samples())
    except Exception as e:
        print(f"[ERROR] Failed to load MP3 file. Ensure it's a valid MP3 and FFmpeg is installed.")
        print(f"Details: {e}")
        return False

    # --- Step 1: Encrypt file content if requested ---
    try:
        with open(secret_file_path, 'rb') as f:
            secret_content = f.read()
        
        if isEncrypt:
            print("--- [Step 1] Encrypting secret file content ---")
            secret_content_str = secret_content.decode('latin-1')
            encrypted_str = encrypt(secret_content_str, key)
            secret_content = encrypted_str.encode('latin-1')

    except FileNotFoundError:
        print(f"[ERROR] File not found: {secret_file_path}")
        return False
    except Exception as e:
        print(f"[ERROR] Could not read or encrypt file: {e}")
        return None

    # --- Step 2: Create the main payload (type, flag, secret) ---
    print(f"--- [Step 2] Converting secret data and creating payload ---")
    secret_bits = [int(bit) for byte in secret_content for bit in format(byte, '08b')]
    
    filename_without_extension, extension = os.path.splitext(os.path.basename(secret_file_path))
    secret_type = extension[1:] if extension else "bin"

    type_bits = [int(b) for char in secret_type for b in format(ord(char), '08b')]
    encrypt_flag_bits = [1] if isEncrypt else [0] 

    main_payload_bits = type_bits + encrypt_flag_bits + secret_bits
    main_payload_size_bits = len(main_payload_bits)
    print(f"Created main payload. Total bits to hide in main block: {main_payload_size_bits}")
    
    # --- Step 3: Embed the unencrypted header (isRandom, m, size) ---
    print("--- [Step 3] Embedding unencrypted header ---")
    
    if len(samples) < 41:
        print("[ERROR] Audio file is too short to hold the header.")
        return False
        
    def embed_header_bits(bit_list, start_offset):
        for i, bit in enumerate(bit_list):
            sample_index = start_offset + i
            sample_val = samples[sample_index].item()
            sample_binary = list(format(sample_val & 0xFFFF, '016b'))
            sample_binary[-1] = str(bit)
            new_val_str = "".join(sample_binary)
            new_val = int(new_val_str, 2)
            if new_val > 32767: new_val -= 65536
            samples[sample_index] = new_val

    embed_header_bits(['1' if isRandom else '0'], 0)
    print(f"isRandom flag set to {'1' if isRandom else '0'}")
    
    m_bits = [int(b) for b in format(m, '02b')]
    embed_header_bits(m_bits, 1)
    print(f"m value ({m}) embedded.")
    
    size_bits = [int(b) for b in format(main_payload_size_bits, '032b')]
    embed_header_bits(size_bits, 3)
    print(f"Main payload size ({main_payload_size_bits}) embedded.")

    # --- Step 4: Determine the starting index for the main payload ---
    start_index = 35
    if isRandom:
        seed = key_to_seed(key)
        start_index = calculate_random_start_index(main_payload_size_bits, m, samples, seed)
        if start_index is None:
            return False

    # --- Step 5: Check if the payload will fit ---
    required_samples = math.ceil(main_payload_size_bits / m)
    if start_index + required_samples >= len(samples):
        print("[ERROR] Embedding failed: The secret file is too large to fit in the cover from the chosen start index.")
        return False
    
    print(f"Size check passed. Payload requires {required_samples} audio samples.")
    print(f"--- [Step 6] Embedding main payload starting at index {start_index} ---")
    bit_index = 0
    for i in range(required_samples):
        sample_index = start_index + i
        sample_val = samples[sample_index].item()
        sample_binary = list(format(sample_val & 0xFFFF, '016b'))
        
        for j in range(m):
            if bit_index < main_payload_size_bits:
                sample_binary[-(j + 1)] = str(main_payload_bits[bit_index])
                bit_index += 1
        
        new_val_str = "".join(sample_binary)
        new_val = int(new_val_str, 2)
        if new_val > 32767: new_val -= 65536
        samples[sample_index] = new_val

    # --- Step 7: Save the new stego MP3 file ---
    print("--- [Step 7] Saving new stego MP3 file ---")
    new_audio = audio._spawn(samples.tobytes())
    new_audio.export(output_path, format="mp3")
    print(f"\n>>> SUCCESS! New file saved to '{output_path}'")
    
    if isRandom or isEncrypt:
        print(f"!!! IMPORTANT: Your secret key to extract the file is: '{key}' !!!")
    else:
        print(f"!!! SUCCESS: No key is needed for extraction. !!!")
        
    return True

def extract_file(stego_mp3_path, key, output_dir):
    """
    Extracts a hidden file from a stego MP3.
    """
    try:
        audio = AudioSegment.from_mp3(stego_mp3_path)
        samples = np.array(audio.get_array_of_samples())
    except Exception as e:
        print(f"[ERROR] Failed to load stego MP3. Ensure it's valid and FFmpeg is installed.")
        print(f"Details: {e}")
        return False

    # --- Step 1: Extract and parse the unencrypted header ---
    print("--- [Step 1] Reading unencrypted header ---")
    if len(samples) < 35:
        print("[ERROR] Stego file is too short to contain a valid header.")
        return False
        
    def extract_header_bits(start_offset, count):
        bits = []
        for i in range(count):
            sample_val = samples[start_offset + i].item()
            bits.append(format(sample_val & 0xFFFF, '016b')[-1])
        return "".join(bits)

    isRandom_flag = (extract_header_bits(0, 1) == '1')
    print(f"isRandom flag found: {isRandom_flag}")
    
    m = int(extract_header_bits(1, 2), 2)
    if not (1 <= m <= 16):
        print(f"[ERROR] Extracted an invalid 'm' value: {m}. File may be corrupt.")
        return False
    print(f"Found embedded 'm' value: {m}")
    
    main_payload_size_bits = int(extract_header_bits(3, 32), 2)
    print(f"Found main payload size: {main_payload_size_bits} bits")
    
    # --- Step 2: Determine the start index ---
    start_index = 35
    if isRandom_flag:
        if not key:
            print("[ERROR] This file was hidden with a random start index. A key is required.")
            return False
        print("Calculating random start index using the provided key...")
        seed = key_to_seed(key)
        start_index = calculate_random_start_index(main_payload_size_bits, m, samples, seed)
        if start_index is None:
            print("[ERROR] Could not calculate a valid start index. The key may be wrong.")
            return False
    else:
        print("Using default start index of 41.")
        
    # --- Step 3: Extract the main payload ---
    print(f"--- [Step 3] Extracting {main_payload_size_bits} bits of the main payload ---")
    total_samples_needed = math.ceil(main_payload_size_bits / m)
    
    if start_index + total_samples_needed > len(samples):
        print("[ERROR] File appears to be truncated or header is corrupt.")
        return False

    main_payload_bits = []
    for i in range(total_samples_needed):
        sample_binary = format(samples[start_index + i].item() & 0xFFFF, '016b')
        for j in range(m):
            main_payload_bits.append(sample_binary[-(j+1)])
    
    main_payload_bits = main_payload_bits[:main_payload_size_bits]
    
    # --- Step 4: Parse the main payload ---
    print("--- [Step 4] Parsing main payload metadata ---")
    main_payload_str = "".join(main_payload_bits)
    
    type_bits_str = main_payload_str[:8]
    secret_type = "".join([chr(int(type_bits_str[i:i+8], 2)) for i in range(0, len(type_bits_str), 8)])
    print(f"Found file type: .{secret_type}")

    encrypt_flag_start_index = 8
    encrypt_flag = (main_payload_str[encrypt_flag_start_index] == '1')
    print(f"Encryption flag found: {encrypt_flag}")

    secret_data_start_index = encrypt_flag_start_index + 1
    secret_data_bits_str = main_payload_str[secret_data_start_index:]
    
    # --- Step 5: Reconstruct the file ---
    print(f"--- [Step 5] Reconstructing file bytes ---")
    file_bytes = bytearray()
    for i in range(0, len(secret_data_bits_str), 8):
        byte_str = secret_data_bits_str[i:i+8]
        if len(byte_str) == 8:
            file_bytes.append(int(byte_str, 2))
    reconstructed_content = bytes(file_bytes)
    
    # --- Step 6: Decrypt if necessary ---
    if encrypt_flag:
        if not key:
            print("[ERROR] File is encrypted, but no key was provided.")
            return False
        print("--- [Step 6] Decrypting file content ---")
        reconstructed_content_str = reconstructed_content.decode('latin-1')
        decrypted_str = decrypt(reconstructed_content_str, key)
        reconstructed_content = decrypted_str.encode('latin-1')

    # --- Step 7: Save the final file ---
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_filename = f"extracted_file.{secret_type}"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"--- [Step 7] Saving reconstructed file to '{output_path}' ---")
    with open(output_path, 'wb') as f:
        f.write(reconstructed_content)
    
    print(f"\n>>> SUCCESS! File extracted and saved to '{output_path}'")
    return True

# --- Terminal GUI Functions (Unchanged) ---

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_header():
    print("===================================")
    print("      MP3 Steganography Tool")
    print("===================================")
    print(" Hides any file inside an MP3 audio file.\n")
    print(" NOTE: Requires 'pydub' and 'numpy'. FFmpeg must be installed.")

def handle_embedding():
    clear_screen()
    display_header()
    print("--- Hide a Secret File ---\n")
    try:
        mp3_in = input("Enter the path to the original MP3 file: ")
        secret_in = input("Enter the path to the secret file to hide: ")
        mp3_out = input("Enter the output path for the new stego MP3: ")
        m_val = int(input("Enter number of bits to use per sample (1-4): "))
        EncryptChoice = input("Apakah Anda ingin melakukan enkripsi sebelum penyisipan? (Ya/Tidak): ").lower()
        isEncrypt = True if EncryptChoice == 'ya' else False
        RandomChoice = input("Apakah Anda ingin menggunakan titik awal penyisipan acak? (Ya/Tidak): ").lower()
        isRandom = True if RandomChoice == 'ya' else False
        
        key = ""
        if isEncrypt or isRandom:
            key = input("Kunci rahasia (untuk enkripsi dan/atau posisi acak): ")
        
        if not os.path.exists(mp3_in) or not os.path.exists(secret_in):
            print("\n[ERROR] One of the input files was not found. Please check paths.")
            return

        print("\nStarting the embedding process...")
        embed_file(mp3_in, secret_in, mp3_out, m_val, isEncrypt, isRandom, key)

    except ValueError:
        print("\n[ERROR] Invalid input for insertion bits. Please enter an integer.")
    except Exception as e:
        print(f"\nAn unexpected error occurred during embedding: {e}")

def handle_extraction():
    clear_screen()
    display_header()
    print("--- Extract a Secret File ---\n")
    try:
        stego_file = input("Enter the path to the stego MP3 file: ")
        key = input("Enter the extraction key (leave blank if none): ")
        output_folder = input("Enter folder name to save the extracted file: ")

        if not os.path.exists(stego_file):
            print("\n[ERROR] Stego file not found. Please check the path.")
            return
        
        print("\nStarting the extraction process...")
        extract_file(stego_file, key, output_folder)

    except Exception as e:
         print(f"\nAn unexpected error occurred during extraction: {e}")

def main():
    while True:
        clear_screen()
        display_header()
        print("\nChoose an option:")
        print("  1. Hide Secret Data")
        print("  2. Extract Secret Data")
        print("  3. Exit")
        
        choice = input("\nEnter your choice (1, 2, or 3): ")

        if choice == '1':
            handle_embedding()
        elif choice == '2':
            handle_extraction()
        elif choice == '3':
            print("Exiting program.")
            sys.exit()
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to return to the main menu...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting.")
        sys.exit()

