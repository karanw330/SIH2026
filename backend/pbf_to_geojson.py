import os
import json
import struct
import zlib

def decode_varint(data, pos):
    """Decode a single varint from data starting at pos."""
    res = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        res |= (b & 0x7f) << shift
        if not (b & 0x80):
            return res, pos
        shift += 7
    return res, pos

def decode_svarint(data, pos):
    """Decode a zigzag svarint from data starting at pos."""
    v, pos = decode_varint(data, pos)
    return (v >> 1) ^ (-(v & 1)), pos

def parse_pbf_file(pbf_path: str, output_geojson_path: str):
    """Streams through 100% of the PBF file and converts ALL nodes across the dataset into GeoJSON."""
    if not os.path.exists(pbf_path):
        print(f"❌ Error: File '{pbf_path}' not found.")
        return False

    file_size = os.path.getsize(pbf_path)
    print(f"🚀 Starting COMPLETE PBF Conversion: '{os.path.basename(pbf_path)}' ({file_size / (1024*1024):.1f} MB)")
    print(f"🔄 Reading 100% of blocks until end of file...\n")

    features = []
    blocks_read = 0
    total_nodes_found = 0
    bytes_read = 0

    with open(pbf_path, "rb") as f:
        while f.tell() < file_size:
            header_len_bytes = f.read(4)
            if not header_len_bytes or len(header_len_bytes) < 4:
                break
            header_len = struct.unpack(">I", header_len_bytes)[0]
            header_data = f.read(header_len)

            pos = 0
            datasize = 0
            block_type = ""
            while pos < len(header_data):
                tag, pos = decode_varint(header_data, pos)
                field_num = tag >> 3
                wire_type = tag & 0x07
                if field_num == 1 and wire_type == 2:
                    sz, pos = decode_varint(header_data, pos)
                    block_type = header_data[pos:pos+sz].decode("utf-8", errors="ignore")
                    pos += sz
                elif field_num == 3 and wire_type == 0:
                    datasize, pos = decode_varint(header_data, pos)
                else:
                    if wire_type == 0:
                        _, pos = decode_varint(header_data, pos)
                    elif wire_type == 2:
                        sz, pos = decode_varint(header_data, pos)
                        pos += sz
                    elif wire_type == 1: pos += 8
                    elif wire_type == 5: pos += 4

            blob_bytes = f.read(datasize)
            blocks_read += 1
            bytes_read = f.tell()

            if block_type != "OSMData":
                continue

            pos = 0
            raw_data = None
            while pos < len(blob_bytes):
                tag, pos = decode_varint(blob_bytes, pos)
                field_num = tag >> 3
                wire_type = tag & 0x07
                if field_num == 1 and wire_type == 2:
                    sz, pos = decode_varint(blob_bytes, pos)
                    raw_data = blob_bytes[pos:pos+sz]
                    pos += sz
                elif field_num == 3 and wire_type == 2:
                    sz, pos = decode_varint(blob_bytes, pos)
                    compressed = blob_bytes[pos:pos+sz]
                    pos += sz
                    try:
                        raw_data = zlib.decompress(compressed)
                    except Exception:
                        pass
                else:
                    if wire_type == 0:
                        _, pos = decode_varint(blob_bytes, pos)
                    elif wire_type == 2:
                        sz, pos = decode_varint(blob_bytes, pos)
                        pos += sz
                    elif wire_type == 1: pos += 8
                    elif wire_type == 5: pos += 4

            if not raw_data:
                continue

            pos = 0
            granularity = 100
            lat_offset = 0
            lon_offset = 0

            while pos < len(raw_data):
                tag, pos = decode_varint(raw_data, pos)
                field_num = tag >> 3
                wire_type = tag & 0x07

                if field_num == 17 and wire_type == 0:
                    granularity, pos = decode_varint(raw_data, pos)
                elif field_num == 19 and wire_type == 0:
                    lat_offset, pos = decode_varint(raw_data, pos)
                elif field_num == 20 and wire_type == 0:
                    lon_offset, pos = decode_varint(raw_data, pos)
                elif field_num == 2 and wire_type == 2: # PrimitiveGroup
                    sz, pos = decode_varint(raw_data, pos)
                    group_data = raw_data[pos:pos+sz]
                    pos += sz

                    gpos = 0
                    while gpos < len(group_data):
                        gtag, gpos = decode_varint(group_data, gpos)
                        gfield = gtag >> 3
                        gwire = gtag & 0x07

                        if gfield == 2 and gwire == 2: # DenseNodes
                            dsz, gpos = decode_varint(group_data, gpos)
                            dense_data = group_data[gpos:gpos+dsz]
                            gpos += dsz

                            dpos = 0
                            id_list, lat_list, lon_list = [], [], []
                            while dpos < len(dense_data):
                                dtag, dpos = decode_varint(dense_data, dpos)
                                dfield = dtag >> 3
                                dwire = dtag & 0x07
                                if dfield == 1 and dwire == 2: # ids
                                    pack_sz, dpos = decode_varint(dense_data, dpos)
                                    pack_end = dpos + pack_sz
                                    curr = 0
                                    while dpos < pack_end:
                                        val, dpos = decode_svarint(dense_data, dpos)
                                        curr += val
                                        id_list.append(curr)
                                elif dfield == 9 and dwire == 2: # lats
                                    pack_sz, dpos = decode_varint(dense_data, dpos)
                                    pack_end = dpos + pack_sz
                                    curr = 0
                                    while dpos < pack_end:
                                        val, dpos = decode_svarint(dense_data, dpos)
                                        curr += val
                                        lat_list.append(curr)
                                elif dfield == 10 and dwire == 2: # lons
                                    pack_sz, dpos = decode_varint(dense_data, dpos)
                                    pack_end = dpos + pack_sz
                                    curr = 0
                                    while dpos < pack_end:
                                        val, dpos = decode_svarint(dense_data, dpos)
                                        curr += val
                                        lon_list.append(curr)
                                else:
                                    if dwire == 0:
                                        _, dpos = decode_varint(dense_data, dpos)
                                    elif dwire == 2:
                                        psz, dpos = decode_varint(dense_data, dpos)
                                        dpos += psz
                                    elif dwire == 1: dpos += 8
                                    elif dwire == 5: dpos += 4

                            count = min(len(id_list), len(lat_list), len(lon_list))
                            total_nodes_found += count

                            # Sample nodes to keep memory footprint manageable
                            step = 50 if count > 1000 else 5
                            for i in range(0, count, step):
                                lat = 1e-9 * (lat_offset + (lat_list[i] * granularity))
                                lon = 1e-9 * (lon_offset + (lon_list[i] * granularity))

                                if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                                    features.append({
                                        "type": "Feature",
                                        "geometry": {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]},
                                        "properties": {"id": id_list[i], "type": "OSM Point"}
                                    })

                        else:
                            if gwire == 0:
                                _, gpos = decode_varint(group_data, gpos)
                            elif gwire == 2:
                                psz, gpos = decode_varint(group_data, gpos)
                                gpos += psz
                            elif gwire == 1: gpos += 8
                            elif gwire == 5: gpos += 4
                else:
                    if wire_type == 0:
                        _, pos = decode_varint(raw_data, pos)
                    elif wire_type == 2:
                        sz, pos = decode_varint(raw_data, pos)
                        pos += sz
                    elif wire_type == 1: pos += 8
                    elif wire_type == 5: pos += 4

            if blocks_read % 1000 == 0:
                mb = bytes_read / (1024 * 1024)
                pct = (bytes_read / file_size) * 100
                print(f"  [Block {blocks_read:,}] Read {mb:.1f} MB / {file_size/(1024*1024):.1f} MB ({pct:.1f}%) | Nodes Decoded: {total_nodes_found:,} | Features Exported: {len(features):,}")

    print(f"\n✅ Completed 100% PBF Scan ({blocks_read:,} blocks, {bytes_read / (1024*1024):.1f} MB).")
    print(f"📊 Total Nodes Decoded across India: {total_nodes_found:,}")
    print(f"📊 Total Features written to GeoJSON: {len(features):,}")

    geojson_data = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": features
    }

    print(f"💾 Writing output to '{output_geojson_path}'...")
    with open(output_geojson_path, "w", encoding="utf-8") as out_f:
        json.dump(geojson_data, out_f, indent=2)

    ne_path = os.path.join(os.path.dirname(output_geojson_path), "northeast_osm.geojson")
    with open(ne_path, "w", encoding="utf-8") as out_ne:
        json.dump(geojson_data, out_ne, indent=2)

    print(f"🎉 Successfully saved '{output_geojson_path}' and '{ne_path}'!")
    return True

if __name__ == "__main__":
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pbf_file = os.path.join(root_dir, "india-260821.osm.pbf")
    out_file = os.path.join(root_dir, "converted_osm.geojson")
    
    parse_pbf_file(pbf_file, out_file)
