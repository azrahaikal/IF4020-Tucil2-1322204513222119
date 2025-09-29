import numpy as np
import librosa

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

# import numpy as np
# from pydub import AudioSegment

# def mp3_to_array(file_mp3):
#     # Baca MP3 pakai pydub
#     audio = AudioSegment.from_mp3(file_mp3)
    
#     # Ambil raw data (bytes) lalu ubah ke numpy array
#     samples = np.array(audio.get_array_of_samples())
    
#     if audio.channels == 2:
#         samples = samples.reshape((-1, 2))
    
#     # Normalisasi ke float64 (-1.0 s/d 1.0)
#     samples = samples.astype(np.float64) / (2**(8*audio.sample_width - 1))
    
#     return samples, audio.frame_rate

# def hitung_psnr_mp3(file_cover, file_stego):
#     # Konversi kedua file MP3 ke array numpy
#     cover, sr1 = mp3_to_array(file_cover)
#     stego, sr2 = mp3_to_array(file_stego)
    
#     if sr1 != sr2:
#         raise ValueError("Sample rate kedua file audio tidak sama")
    
#     # Samakan panjang sinyal
#     min_len = min(len(cover), len(stego))
#     cover = cover[:min_len]
#     stego = stego[:min_len]
    
#     # Hitung PSNR
#     numerator = np.sum(stego**2)
#     denominator = np.sum(stego**2 + cover**2 - 2*stego*cover)
    
#     psnr = 10 * np.log10(numerator / denominator)
#     return psnr

# print(hitung_psnr_mp3("lofi7menit.mp3", "output.mp3"))