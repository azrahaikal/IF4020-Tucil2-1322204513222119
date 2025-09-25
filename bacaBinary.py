# 23 September 2025, 14.53 WIB
# program ini untuk menampilkan representasi biner dari file audio

namaFile = "makan.mp3"

with open(namaFile, "rb") as f:
    data = f.read()

print("Panjang file (bytes):", len(data))
print(f'{type(format(data[0], '08b'))} = {format(data[0], '08b')}')

for i in range(0, 24):
    print(f"{format(data[i], '08b')} ", end="")
    if(i%8 == 0 and  i != 0):
        print("\n")
  
# print per decimal    
# for i in range(0, 20):
#     print(f"{data[i]} ", end=" ")
  
# print format ASCII  
# print(f'\n{data[:20]}')