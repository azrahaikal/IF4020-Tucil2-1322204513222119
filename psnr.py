import numpy as np
import librosa # Ganti scipy.io.wavfile dengan librosa

def hitung_psnr_mp3(path_audio_asli, path_audio_stego):
    """
    Menghitung PSNR untuk file audio (termasuk MP3)
    berdasarkan formula dari gambar.

    Args:
        path_audio_asli (str): Path ke file audio asli (cover).
        path_audio_stego (str): Path ke file audio stego.

    Returns:
        float: Nilai PSNR dalam dB.
    """
    try:
        # 1. Membaca data audio menggunakan librosa
        # librosa.load mengembalikan data audio (sebagai float) dan sample rate
        # sr=None memastikan sample rate asli tetap dipertahankan
        audio_asli, sr_asli = librosa.load(path_audio_asli, sr=None)
        audio_stego, sr_stego = librosa.load(path_audio_stego, sr=None)

        # 2. Validasi
        # if sr_asli != sr_stego or len(audio_asli) != len(audio_stego):
        #     raise ValueError("File audio asli dan stego harus memiliki sample rate dan panjang yang sama.")

        # 3. Menghitung kekuatan sinyal (P0 dan P1)
        # Karena librosa sudah mengembalikan float, kita tidak perlu konversi tipe lagi
        
        # P0: Kekuatan sinyal audio asli
        P0 = np.mean(audio_asli**2)
        
        # P1: Kekuatan sinyal audio stego
        P1 = np.mean(audio_stego**2)

        if P0 == P1:
            return float('inf')

        # 4. Menerapkan formula PSNR
        numerator = P1**2
        denominator = (P1 - P0)**2
        
        if denominator == 0:
            return float('inf')

        psnr_value = 10 * np.log10(numerator / denominator)
        
        return psnr_value

    except FileNotFoundError:
        print(f"Error: Salah satu file tidak ditemukan.")
        return None
    except Exception as e:
        print(f"Terjadi error: {e}")
        return None

# --- Contoh Penggunaan ---

# Ganti dengan path file MP3 Anda
cover_audio_file_mp3 = "SpongebobGator.mp3"
stego_audio_file_mp3 = "SpongebobGator3.mp3"

psnr = hitung_psnr_mp3(cover_audio_file_mp3, stego_audio_file_mp3)

if psnr is not None:
    print(f"Nilai PSNR adalah: {psnr:.2f} dB")
    
    if psnr < 30:
        print("Peringatan: Kualitas audio mengalami kerusakan yang berarti (PSNR < 30 dB).")
    else:
        print("Kualitas audio cukup baik (PSNR >= 30 dB).")