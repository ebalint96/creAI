from creAI.mc.tile import Tile
from creAI.mc.tilemap import Tilemap

import numpy as np

def tile_to_geometry(tile: Tile) -> np.ndarray:
    mdl = tile.model_3d
    txtrs = tile.textures

    if mdl is None:
        return None
    elif 'elements' not in mdl:
        return None

    geometries = []
    for elem in mdl['elements']:
        from_ = np.array(elem['from']) / 16
        to = np.array(elem['to']) / 16
        f_cols = {
            'up':   np.array([0., 0., 0.]),
            'down': np.array([0., 0., 0.]),
            'east': np.array([0., 0., 0.]),
            'west': np.array([0., 0., 0.]),
            'north': np.array([0., 0., 0.]),
            'south': np.array([0., 0., 0.])
        }
        for face in elem['faces']:
            txtr_id = elem['faces'][face]['texture'][1:]
            while txtr_id not in txtrs:
                txtr_id = mdl['textures'][txtr_id]
                if '#' in txtr_id:
                    txtr_id = txtr_id[1:]

            img = txtrs[txtr_id].convert('RGB')
            f_cols[face] = np.average(img, axis=(0, 1))[:3]/256

        geometries.append(
            get_box_geometry(
                from_,
                to,
                f_cols
            )
        )
    geometries = np.concatenate(geometries, axis=1)
    return geometries


def tilemap_to_geometry(tlmp: Tilemap) -> np.ndarray:
    palette = tlmp.palette
    tile_geometries = dict(
        zip(
            palette,
            [tile_to_geometry(tile) for tile in palette]
        )
    )
    air = Tile('minecraft:air')
    geometries = [
        tile_geometries[palette[t]]
        + np.array([i, [0, 0, 0], [0, 0, 0], [0, 0, 0]]).reshape(4, 1, 1, 3)
        for i, t in np.ndenumerate(tlmp.data)
        if palette[t] != air and tile_geometries[palette[t]] is not None
    ]
    return np.concatenate(
        geometries,
        axis=1
    )

def get_box_geometry(from_, to, face_colors) -> np.ndarray:
    v = [None,
         [to[0], 	to[1],		to[2]],
         [to[0], 	from_[1], 	to[2]],
         [to[0], 	to[1], 		from_[2]],
         [to[0], 	from_[1], 	from_[2]],
         [from_[0], 	to[1], 		to[2]],
         [from_[0], 	from_[1], 	to[2]],
         [from_[0], 	to[1], 		from_[2]],
         [from_[0], 	from_[1], 	from_[2]],
         ]
    f = [
        [v[1], v[3], v[5]],
        [v[4], v[8], v[3]],
        [v[8], v[6], v[7]],
        [v[6], v[8], v[2]],
        [v[2], v[4], v[1]],
        [v[6], v[2], v[5]],
        [v[3], v[7], v[5]],
        [v[8], v[7], v[3]],
        [v[6], v[5], v[7]],
        [v[8], v[4], v[2]],
        [v[4], v[3], v[1]],
        [v[2], v[1], v[5]]
    ]
    n = [None,
         [0.0000, 1.0000, 0.0000],
         [0.0000, 0.0000, 1.0000],
         [-1.0000, 0.0000, 0.0000],
         [0.0000, -1.0000, 0.0000],
         [1.0000, 0.0000, 0.0000],
         [0.0000, 0.0000, -1.0000]
         ]
    fn = [
        [n[1], n[1], n[1]],
        [n[2], n[2], n[2]],
        [n[3], n[3], n[3]],
        [n[4], n[4], n[4]],
        [n[5], n[5], n[5]],
        [n[6], n[6], n[6]],
        [n[1], n[1], n[1]],
        [n[2], n[2], n[2]],
        [n[3], n[3], n[3]],
        [n[4], n[4], n[4]],
        [n[5], n[5], n[5]],
        [n[6], n[6], n[6]]
    ]
    c = [None,
         face_colors['up'],
         face_colors['south'],
         face_colors['west'],
         face_colors['down'],
         face_colors['east'],
         face_colors['north'],
         ]
    fc = [
        [c[1], c[1], c[1]],
        [c[2], c[2], c[2]],
        [c[3], c[3], c[3]],
        [c[4], c[4], c[4]],
        [c[5], c[5], c[5]],
        [c[6], c[6], c[6]],
        [c[1], c[1], c[1]],
        [c[2], c[2], c[2]],
        [c[3], c[3], c[3]],
        [c[4], c[4], c[4]],
        [c[5], c[5], c[5]],
        [c[6], c[6], c[6]]
    ]

    return np.array(
        [
            f,
            fn,
            fc,
            np.zeros(shape=np.array(f).shape),
        ]
    )