# Ini buat baca file
namaFile = "makan.mp3"

with open(namaFile, "rb") as f:
    data = f.read()

print("Panjang file (bytes):", len(data))
print(f'{type(format(data[0], '08b'))} = {format(data[0], '08b')}')

# test baca file
for i in range(0, 9):
    print(f"{format(data[i], '08b')} ", end="")
    if(i%8 == 0 and  i != 0):
        print("\n")

# ubah data audio menjadi list supaya bisa diubah per-index
listedData = [""] * len(data)
for i in range(0, len(data)):
    temp = format(data[i], '08b')
    listedData[i] = list(temp)


# ----------------------------------------------------------------
print("### di bawah ini adalah setelah manipulasi ###")
iByte = 1
nLSB = 2        # asumsi ini tidak pernah nol
message = "101100111111111"
# pada kasus ini, bit LSB yang terakhir disimpan di agak kanan (bukan paling kiri)

if((len(message) % nLSB) == 0):
    byteYangDiperlukan = int(len(message) / nLSB)
else:
    byteYangDiperlukan = int((len(message) // nLSB)) + 1

if(byteYangDiperlukan > len(data)):                 # message terlalu panjang untuk disisipkan ke audio
    exit()
else:
    idxByteYgInginDiUbah = [i for i in range(0, byteYangDiperlukan)]
    idxMessage = 0      # index untuk memasukkan message
    for i in idxByteYgInginDiUbah:
        for j in range(8-nLSB, 8):
            if(idxMessage < len(message)):
                listedData[i][j] = message[idxMessage]
                idxMessage = idxMessage+1              
                
    # ------------------------------------------------------------------
        

    # 01001001 = string --> idx 0 ada di paling kiri

    # bikin file audio yang baru
    # gabungkan kembali list of char ke integer
    reconstructed = []
    for i in range(len(listedData)):
        bitstring = "".join(listedData[i])   # misal: ['0','1','0','0','1','0','0','1'] -> "01001001"
        reconstructed.append(int(bitstring, 2))  # string -> integer

    # ubah list of integer ke bytes
    newAudio = bytes(reconstructed)
    
    
    # bandingkan before-after
    print("before ada di kiri      after ada di kanan")
    for i in idxByteYgInginDiUbah:
        print(f"Byte ke-{i}: {format(data[i], '08b')} ... {format(newAudio[i], '08b')}")
    # tulis ke file baru
    # with open("output.mp3", "wb") as f:
    #     f.write(newAudio)

    # print("File baru berhasil ditulis: output.mp3")