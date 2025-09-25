def byte_to_bits(b):
    return format(b, '08b')

def bits_of_bytes(data: bytes) -> str:
    return ''.join(format(b, '08b') for b in data)

def set_bit(byte: int, pos: int, value: int) -> int:
    # pos: 0 = LSB, 7 = MSB
    if value:
        return byte | (1 << pos)
    else:
        return byte & ~(1 << pos)

# ubah bit ke-n dari byte ke-n
def flip_bit_in_bytes(data: bytearray, byte_index: int, bit_pos: int):
    data[byte_index] ^= (1 << bit_pos)

if __name__ == "__main__":
    fn = "makan.mp3"
    out = "makan2.mp3"
    with open(fn, "rb") as f:
        data = bytearray(f.read())

    # contoh: toggle LSB of byte ke-100
    for i in range(0, 80):
        flip_bit_in_bytes(data, i, 0)   # toggle bit LSB
        
        print(f"Byte ke-{i} setelah toggle:", byte_to_bits(data[i]))

    with open(out, "wb") as f:
        f.write(data)

    print("Selesai. Simpan ke", out)