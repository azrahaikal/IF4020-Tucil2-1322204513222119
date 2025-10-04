i. nama dan deskripsi program

stegomp3.py , sebuah program steganografi dengan opsi penyisipan data berupa pengenkripsian, pilihan titik awal sisip, dan jumlah lsb yang digunakan untuk penyisipan.Sedangkan untuk
mengekstrak suatu data tersembunyi di sebuah stego object, hanya diperlukan input berupa stego-object dan key.Terdapat pula fitur untuk mengkalkulasi PSNR dan memutar file mp3.

ii. kumpulan teknologi yang digunakan (tech stack)

-Bahasa Pemrograman: Python

-Pustaka Audio & Numerik: Librosa, NumPy

-Pustaka Pemutar Suara: Playsound

iii. dependensi

-librosa
-numpy
-playsound

iv. tata cara menjalankan program

1.  Buka terminal atau command prompt.
2.  Navigasikan ke direktori tempat Anda menyimpan program ini.
3.  Jalankan skrip utama dengan perintah:

    stegomp3.py


4.  Setelah program berjalan, akan muncul menu utama di terminal:
    ```
    ========================================
             PROGRAM STEGANOGRAFI FILE LSB
    ========================================
    1. Sembunyikan File
    2. Ekstrak File
    3. Cek PSNR
    4. Mainkan mp3
    5. Keluar

5.  Pilih opsi dengan mengetikkan angka yang sesuai dan tekan Enter. Ikuti instruksi yang muncul di layar untuk memasukkan nama file, kunci, dan pilihan lainnya.