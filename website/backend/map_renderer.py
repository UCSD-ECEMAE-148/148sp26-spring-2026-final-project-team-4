from PIL import Image, ImageDraw
import math


def render_map(map_json, path, image_manifest):
    width = map_json['width']
    height = map_json['height']
    res = map_json['resolution']
    origin_x = map_json.get('origin_x', 0.0)
    origin_y = map_json.get('origin_y', 0.0)
    data = map_json['data']

    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # draw occupancy
    for y in range(height):
        for x in range(width):
            v = data[y * width + x]
            if v == 0:
                color = (255, 255, 255)
            elif v == 100:
                color = (48, 48, 48)
            else:
                color = (160, 160, 160)
            draw.point((x, y), fill=color)

    def world_to_pixel(px, py):
        ix = int((px - origin_x) / res)
        iy = height - 1 - int((py - origin_y) / res)
        return ix, iy

    # draw path
    if path:
        pts = [world_to_pixel(p['x'], p['y']) for p in path]
        if len(pts) >= 2:
            draw.line(pts, fill=(0, 0, 255), width=2)

    # draw image points
    for m in image_manifest:
        pose = m.get('pose')
        if not pose:
            continue
        x, y = world_to_pixel(pose['x'], pose['y'])
        r = 3
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 0, 0))

    return img
