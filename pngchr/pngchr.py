from dataclasses import dataclass
from PIL import Image

TILESET_ROWS: int = 16
TILESET_TILES_PER_ROW: int = 16
TILESET_WIDTH: int = 128
TILE_SIZE: int = 8


class TileSetError(RuntimeError):
    pass


def get_tile_pixels(xy: tuple[int, int]) -> list[tuple[int, int]]:
    x, y = xy
    return [
        (
            x + (i % TILE_SIZE),
            y + int(i / TILE_SIZE)
        )
        for i in range(0, TILE_SIZE * TILE_SIZE)
    ]


def get_tile_coords(begin: tuple[int, int], end: tuple[int, int], width: int) -> list[tuple[int, int]]:
    x_begin, y_begin = begin
    x_end, y_end = end

    tiles = (y_end - y_begin + 1) * width - x_begin - (width - x_end)

    return [
        (
            ((x_begin + i) % width) * TILE_SIZE,
            (y_begin + int(i / width)) * TILE_SIZE
        )
        for i in range(0, tiles)
    ]


def convert_pixel(pixel: int, colors: dict[int, int]) -> tuple[bool, bool]:
    return bool(colors[pixel] & 0b01), bool(colors[pixel] & 0b10)


@dataclass
class TileSet:
    """Class, representing a tileset (still as a png file)"""
    image: Image.Image
    colors: dict[int, int]
    dimension: tuple[int, int]
    begin_content: tuple[int, int]
    end_content: tuple[int, int]

    def __init__(self, image_path: str, header_rows: int = 1):
        self.image = Image.open(image_path)

        if header_rows < 1:
            raise ValueError(f'there must be at least one header row, given are {header_rows}')

        if self.image.width != TILESET_WIDTH:
            raise TileSetError(f'Width of file at {image_path} != {TILESET_WIDTH}')
        if self.image.height % 8 != 0:
            raise TileSetError(f'Height of file at {image_path} is not a multiple of 8')

        self.colors = {
            self.image.getpixel((0, 0)): 0,
            self.image.getpixel((0, TILE_SIZE / 2)): 1,
            self.image.getpixel((TILE_SIZE / 2, 0)): 2,
            self.image.getpixel((TILE_SIZE / 2, TILE_SIZE / 2)): 3
        }

        self.begin_content = (0, header_rows)
        self.end_content = (0, int(self.image.height / TILE_SIZE))
        self.dimension = (
            int(TILESET_WIDTH / TILE_SIZE),
            int(self.image.height / TILE_SIZE) - header_rows
        )

        print(self.begin_content, self.end_content)

    def convert_to_chr(self, outfile: str):
        height, width = self.dimension
        tiles_coords = get_tile_coords(self.begin_content, self.end_content, height)
        tile_bits = [
            bit
            for coord in tiles_coords
            for bits in list(zip(*(
                convert_pixel(self.image.getpixel(pixel_coord), self.colors)
                for pixel_coord in get_tile_pixels(coord)
            )))
            for bit in bits
        ]

        x_begin, y_begin = self.begin_content
        x_end, y_end = self.end_content
        padding_bits = [
            False
            for _ in range(0, ((y_end - y_begin + 1) * width - x_begin - (width - x_end)) * TILE_SIZE * TILE_SIZE * 2)
        ]

        bits = tile_bits + padding_bits
        tile_bytes = []
        bit_i = 7
        byte = 0
        for bit in bits:
            if bit_i < 0:
                tile_bytes.append(byte)
                bit_i = 7
                byte = 0
            byte += (int(bit) << bit_i)
            bit_i -= 1

        with open(outfile, 'wb') as file:
            file.write(bytearray(tile_bytes))
