import os
import math
import random
import sys
import librosa
import numpy as np
from playsound import playsound

# =============================================================
# == FUNGSI BANTU (HELPER FUNCTIONS) ==
# =============================================================

def play_mp3(path_audio):
    """Memutar file audio menggunakan library playsound."""
    try:
        print(f"🎵 Memutar file: {path_audio}...")
        playsound(path_audio)
        print("✅ Selesai memutar audio.")
    except Exception as e:
        # Menangani error spesifik dari playsound, misal format tidak didukung
        print(f"❌ Gagal memutar audio: {e}")

def hitung_psnr_mp3(path_audio_asli, path_audio_stego):
    """
    Menghitung PSNR untuk file audio (termasuk MP3)
    berdasarkan formula MSE.

    Args:
        path_audio_asli (str): Path ke file audio asli (cover).
        path_audio_stego (str): Path ke file audio stego.

    Returns:
        float: Nilai PSNR dalam dB.
    """
    try:
        # 1. Membaca data audio menggunakan librosa. Ini akan mendekode audio
        #    ke dalam format PCM (sebagai float array yang dinormalisasi ke [-1, 1]).
        audio_asli, sr_asli = librosa.load(path_audio_asli, sr=None)
        audio_stego, sr_stego = librosa.load(path_audio_stego, sr=None)

        # Menyamakan panjang array audio untuk perhitungan
        min_len = min(len(audio_asli), len(audio_stego))
        audio_asli = audio_asli[:min_len]
        audio_stego = audio_stego[:min_len]

        # 2. Menghitung Mean Squared Error (MSE)
        # x[n] = audio_asli, y[n] = audio_stego
        mse = np.mean((audio_asli - audio_stego) ** 2)

        # Jika MSE adalah 0, file identik, PSNR tak terhingga.
        if mse == 0:
            return float('inf')

        # 3. Menghitung PSNR
        # MAX = 1.0 karena librosa menormalisasi audio ke rentang [-1, 1].
        MAX_SQUARE = 1.0**2
        psnr_value = 10 * np.log10(MAX_SQUARE / mse)
        
        return psnr_value

    except FileNotFoundError:
        print(f"Error: Salah satu file tidak ditemukan.")
        return None
    except Exception as e:
        print(f"Terjadi error saat menghitung PSNR: {e}")
        return None

def key_to_seed(key):
    """Converts a string key into a numerical seed."""
    seed = 0
    for char in key:
        seed = (seed * 31 + ord(char)) & 0xFFFFFFFF
    return seed

def calculate_random_start_index(message_size_in_bits, m, cover_data_length, seed):
    """
    Calculates a random starting index based on the cover data's byte length.
    Fungsi ini harus memberikan hasil yang sama persis saat menyisipkan dan mengekstrak.
    """
    print("\n--- Calculating Random Start Index for Extraction ---")
    r = cover_data_length
    header_spesial_size_in_bytes = 35
    bytes_needed_for_payload = math.ceil(message_size_in_bits / m)
    espace = r - bytes_needed_for_payload - header_spesial_size_in_bytes
    
    if espace <= 0:
        return None

    random.seed(seed)
    rand_offset = random.randint(0, espace)
    Irand = header_spesial_size_in_bytes + rand_offset
    
    print(f"Calculated random start index: {Irand}")
    return Irand

def bytes_ke_biner(data_bytes):
    """Mengubah data bytes menjadi string biner ('0101...')."""
    return ''.join(format(byte, '08b') for byte in data_bytes)

def biner_ke_bytes(biner_str):
    """Mengubah string biner ('0101...') kembali menjadi data bytes."""
    return bytes(int(biner_str[i:i+8], 2) for i in range(0, len(biner_str), 8))

# =============================================================
# == FUNGSI KRIPTOGRAFI (VIGENÈRE CIPHER FOR BYTES) ==
# =============================================================

def encrypt_key(data_bytes, key_bytes):
    """Mengulang kunci (bytes) agar panjangnya sama dengan data."""
    key_len = len(key_bytes)
    return bytes(key_bytes[i % key_len] for i in range(len(data_bytes)))

def encrypt(data_bytes, key):
    """Mengenkripsi bytes menggunakan Vigenère."""
    key_bytes = key.encode('utf-8')
    extended_key = encrypt_key(data_bytes, key_bytes)
    return bytes((data_byte + key_byte) % 256 for data_byte, key_byte in zip(data_bytes, extended_key))

def decrypt(cipher_bytes, key):
    """Mendekripsi bytes menggunakan Vigenère."""
    key_bytes = key.encode('utf-8')
    extended_key = encrypt_key(cipher_bytes, key_bytes)
    return bytes((cipher_byte - key_byte + 256) % 256 for cipher_byte, key_byte in zip(cipher_bytes, extended_key))

# =============================================================
# == FUNGSI STEGANOGRAFI (LSB) ==
# =============================================================

# Konstanta untuk metadata
HEADER_TYPE_BYTES = 10 # 10 bytes = 80 bits

def sisipkan_file(cover_data, message_data, isEncrypt, isRandom, m, key, tipe):
    """Menyembunyikan file (message_data) di dalam file cover (cover_data)."""
    if isEncrypt:
        message_data = encrypt(message_data, key)

    message_biner = bytes_ke_biner(message_data)
    panjang_pesan_biner = len(message_biner)

    tipe_bytes = tipe.encode('utf-8').ljust(HEADER_TYPE_BYTES, b'\0')
    header_type = bytes_ke_biner(tipe_bytes)
    
    header_Encrypt = format(isEncrypt, '01b')
    header_random = format(isRandom, '01b')
    header_m = format(m, '02b')
    header_panjang = format(panjang_pesan_biner, '032b')
    
    data_untuk_disisipkan = header_type + header_Encrypt + message_biner
    data_sisip_spesial = header_random + header_m + header_panjang

    bytes_needed_for_special = len(data_sisip_spesial)
    bytes_needed_for_main = math.ceil(len(data_untuk_disisipkan) / m)
    
    if (bytes_needed_for_special + bytes_needed_for_main) > len(cover_data):
        print("❌ Error: Kapasitas file cover tidak mencukupi.")
        return None

    listed_data = [list(format(byte, '08b')) for byte in cover_data]
    
    idx_bit_spesial = 0
    for i in range(bytes_needed_for_special):
        listed_data[i][7] = data_sisip_spesial[idx_bit_spesial]
        idx_bit_spesial += 1

    idx_bit_pesan = 0
    start_byte_index = bytes_needed_for_special
    if isRandom:
        start_byte_index = calculate_random_start_index(len(data_untuk_disisipkan), m, len(cover_data), key_to_seed(key))
        if start_byte_index is None:
            return None

    idx_byte_cover = start_byte_index
    
    while idx_bit_pesan < len(data_untuk_disisipkan) and idx_byte_cover < len(listed_data):
        for j in range(8 - m, 8):
            if idx_bit_pesan < len(data_untuk_disisipkan):
                listed_data[idx_byte_cover][j] = data_untuk_disisipkan[idx_bit_pesan]
                idx_bit_pesan += 1
        idx_byte_cover += 1

    stego_data = biner_ke_bytes("".join("".join(bits) for bits in listed_data))
    return stego_data


def ekstrak_file(stego_data, key):
    """Mengekstrak file tersembunyi dari data stego."""
    try:
        # 1. Ekstrak header spesial dari 35 byte pertama (selalu 1 LSB)
        stego_bytes = bytes(stego_data)
        header_spesial_biner = ""
        for i in range(35):
            header_spesial_biner += format(stego_bytes[i], '08b')[7]

        # 2. Parse header spesial untuk mendapatkan parameter
        isRandom = bool(int(header_spesial_biner[0]))
        m = int(header_spesial_biner[1:3], 2)
        panjang_pesan_biner = int(header_spesial_biner[3:35], 2)

        print(f"--- Extraction Info ---")
        print(f"Random Start: {isRandom}, LSB Count (m): {m}, Message Bits: {panjang_pesan_biner}")

        # 3. Tentukan di mana data utama dimulai
        total_bit_payload = (HEADER_TYPE_BYTES * 8) + 1 + panjang_pesan_biner
        start_byte_index = 35 # Default jika tidak acak

        if isRandom:
            start_byte_index = calculate_random_start_index(total_bit_payload, m, len(stego_data), key_to_seed(key))
            if start_byte_index is None:
                raise ValueError("Tidak dapat menghitung indeks awal. Kunci mungkin salah.")

        # 4. Ekstrak payload utama dari lokasi yang benar
        extracted_bits = ""
        idx_byte_cover = start_byte_index
        bits_to_extract = total_bit_payload

        while len(extracted_bits) < bits_to_extract and idx_byte_cover < len(stego_data):
            byte_biner = format(stego_bytes[idx_byte_cover], '08b')
            extracted_bits += byte_biner[8 - m:]
            idx_byte_cover += 1
        
        # Potong jika ada kelebihan bit akibat ekstraksi per byte
        extracted_bits = extracted_bits[:bits_to_extract]

        # 5. Parse payload utama
        header_type_len = HEADER_TYPE_BYTES * 8
        header_type_biner = extracted_bits[0:header_type_len]
        isEncrypt = bool(int(extracted_bits[header_type_len]))
        
        pesan_biner = extracted_bits[header_type_len + 1:]

        # 6. Konversi header tipe file dan pesan
        tipe_bytes = biner_ke_bytes(header_type_biner)
        # Hapus padding byte null di akhir
        tipe_file = tipe_bytes.replace(b'\0', b'').decode('utf-8')
        
        message_data = biner_ke_bytes(pesan_biner)

        # 7. Dekripsi jika perlu
        if isEncrypt:
            print("Message is encrypted. Decrypting...")
            message_data = decrypt(message_data, key)
        
        return message_data, tipe_file

    except (IndexError, ValueError) as e:
        print(f"❌ Error saat parsing data stego: {e}. File mungkin rusak atau kunci salah.")
        return None, None

# =============================================================
# == FUNGSI UI (USER INTERFACE) ==
# =============================================================

def handle_sisipkan():
    print("\n--- Menu Menyembunyikan File ---")
    try:
        file_cover = input("Masukkan nama file media cover (contoh: cover.mp3): ")
        if not os.path.exists(file_cover):
            print(f"❌ Error: File cover '{file_cover}' tidak ditemukan.")
            return

        file_pesan = input("Masukkan nama file yang ingin disembunyikan (contoh: secret.txt): ")
        if not os.path.exists(file_pesan):
            print(f"❌ Error: File pesan '{file_pesan}' tidak ditemukan.")
            return

        file_stego = input("Masukkan nama file output (contoh: stego.mp3): ")
        
        encrypt_choice = input("Enkripsi pesan? (Ya/Tidak): ").lower()
        isEncrypt = encrypt_choice.startswith('y')

        random_choice = input("Titik awal penyisipan acak? (Ya/Tidak): ").lower()
        isRandom = random_choice.startswith('y')
        
        m = int(input("Masukkan jumlah LSB yang ingin digunakan (1-4): "))
        if not 1 <= m <= 4:
            raise ValueError("Jumlah LSB harus antara 1 dan 4.")
            
        key = input("Masukkan kunci rahasia (wajib diisi): ")
        if not key:
            print("❌ Error: Kunci rahasia tidak boleh kosong.")
            return

        with open(file_cover, "rb") as f:
            cover_data = f.read()
        with open(file_pesan, "rb") as f:
            message_data = f.read()

        _, ekstensi = os.path.splitext(file_pesan)
        tipe = ekstensi.lstrip('.')

        print("🔄 Memproses penyisipan file...")
        stego_data = sisipkan_file(cover_data, message_data, isEncrypt, isRandom, m, key, tipe)

        if stego_data:
            with open(file_stego, "wb") as f:
                f.write(stego_data)
            print(f"✅ Berhasil! File '{file_pesan}' telah disembunyikan di dalam '{file_stego}'.")
            
    except ValueError as e:
        print(f"❌ Error: Masukkan angka yang valid. Detail: {e}")
    except Exception as e:
        print(f"❌ Terjadi error: {e}")

def handle_ekstrak():
    print("\n--- Menu Mengekstrak File ---")
    try:
        file_stego = input("Masukkan nama file yang berisi data tersembunyi (contoh: stego.mp3): ")
        if not os.path.exists(file_stego):
            print(f"❌ Error: File stego '{file_stego}' tidak ditemukan.")
            return

        output_basename = input("Masukkan nama dasar untuk file yang akan diekstrak (tanpa ekstensi): ")
        key = input("Masukkan kunci rahasia: ")
        if not key:
            print("❌ Error: Kunci rahasia tidak boleh kosong.")
            return

        with open(file_stego, "rb") as f:
            stego_data = f.read()
        
        print("🔄 Memproses ekstraksi...")
        pesan_ditemukan, tipe_file = ekstrak_file(stego_data, key)

        if pesan_ditemukan and tipe_file:
            output_filename = f"{output_basename}.{tipe_file}"
            with open(output_filename, 'wb') as f:
                f.write(pesan_ditemukan)
            print(f"✅ Berhasil! File tersembunyi telah diekstrak dan disimpan sebagai '{output_filename}'.")
        else:
            print("❌ Gagal mengekstrak file. Pastikan kunci rahasia sudah benar.")
            
    except Exception as e:
        print(f"❌ Terjadi error saat ekstraksi: {e}")

def handle_psnr():
    """Fungsi UI untuk menghitung dan menampilkan nilai PSNR."""
    print("\n--- Cek Kualitas Steganografi (PSNR) ---")
    try:
        # 1. Minta input dari pengguna
        path_asli = input("Masukkan nama file audio asli (cover): ")
        if not os.path.exists(path_asli):
            print(f"❌ Error: File '{path_asli}' tidak ditemukan.")
            return

        path_stego = input("Masukkan nama file audio stego: ")
        if not os.path.exists(path_stego):
            print(f"❌ Error: File '{path_stego}' tidak ditemukan.")
            return
        
        # 2. Panggil fungsi perhitungan
        print("🔄 Menghitung PSNR...")
        psnr_value = hitung_psnr_mp3(path_asli, path_stego)

        # 3. Tampilkan hasil
        if psnr_value is not None:
            if psnr_value == float('inf'):
                print("✅ Hasil: File audio asli dan stego identik secara sinyal. PSNR: Tak terhingga (infinity).")
            else:
                print(f"✅ Nilai PSNR adalah: {psnr_value:.2f} dB")
        else:
            # Pesan error spesifik sudah ditampilkan di dalam fungsi hitung_psnr_mp3
            print("❌ Gagal menghitung PSNR.")

    except Exception as e:
        print(f"❌ Terjadi error tak terduga: {e}")

def handle_mp3():
    """Fungsi UI untuk memutar file audio."""
    print("\n--- Putar File Audio ---")
    try:
        # 1. Minta input dari pengguna
        path_audio = input("Masukkan nama file audio yang ingin diputar (contoh: stego.mp3): ")

        # 2. Validasi apakah file ada
        if not os.path.exists(path_audio):
            print(f"❌ Error: File '{path_audio}' tidak ditemukan.")
            return

        # 3. Panggil fungsi pemutar audio
        play_mp3(path_audio)

    except Exception as e:
        # Menangani error umum jika terjadi masalah lain
        print(f"❌ Terjadi error tak terduga: {e}")

# =============================================================
# == BLOK EKSEKUSI UTAMA ==
# =============================================================
if __name__ == "__main__":
    while True:
        print("\n" + "="*40)
        print("      PROGRAM STEGANOGRAFI FILE LSB")
        print("="*40)
        print("1. Sembunyikan File")
        print("2. Ekstrak File")
        print("3. Cek PSNR")
        print("4. Mainkan mp3")
        print("5. Keluar")
        
        pilihan = input("Masukkan pilihan Anda (1/2/3/4/5): ")

        if pilihan == '1':
            handle_sisipkan()
        elif pilihan == '2':
            handle_ekstrak()
        elif pilihan == '3':
            handle_psnr()
        elif pilihan == '4':
            handle_mp3()
        elif pilihan == '5':
            print("Terima kasih telah menggunakan program ini!")
            break
        else:
            print("Pilihan tidak valid, silakan coba lagi.")
