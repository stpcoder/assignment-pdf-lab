"""Scoped ToUnicode replacement that leaves drawn glyphs and positions intact.

This is a text-reader compatibility experiment, not a way to control vision/OCR.
Unsupported encodings fail closed instead of silently producing a partial result.
"""
from pypdf import PdfReader, PdfWriter
from pypdf._cmap import get_encoding
from pypdf.generic import (ArrayObject, ByteStringObject, ContentStream,
                          DecodedStreamObject, DictionaryObject, NameObject)


def _bytes(value):
    if isinstance(value, bytes):
        return bytes(value)
    return value.original_bytes


def _font_decoder(font):
    encoding, cmap = get_encoding(font)
    width = cmap.get(-1, 1)
    if width not in (1, 2):
        raise ValueError("Only one- and two-byte font encodings are supported")
    if isinstance(encoding, dict):
        if width != 1:
            raise ValueError("Unsupported font encoding dictionary")
        def decode(raw):
            char = encoding.get(raw[0], chr(raw[0]))
            return cmap.get(char, char)
    else:
        def decode(raw):
            char = raw.decode(encoding)
            return cmap.get(char, char)
    return width, decode


def _single_map(raw, text):
    if not text:
        raise ValueError("Empty glyph replacements are not supported")
    width = len(raw)
    mapping = f"<{raw.hex()}> <{text.encode('utf-16-be').hex()}>"
    code = f"""/CIDInit /ProcSet findresource begin
12 dict begin begincmap
/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def
/CMapName /LabUnicode def /CMapType 2 def
1 begincodespacerange
<{'00' * width}> <{'ff' * width}>
endcodespacerange
1 beginbfchar
{mapping}
endbfchar
endcmap CMapName currentdict /CMap defineresource pop end end
"""
    stream = DecodedStreamObject()
    stream.set_data(code.encode("ascii"))
    return stream


def native_alias(source, target, original="print_stairs", replacement="paint_stairs"):
    if len(original) != len(replacement):
        raise ValueError("Native alias currently requires equal-length names")
    writer = PdfWriter()
    writer.clone_document_from_reader(PdfReader(source))
    matches = []
    for page_number, page in enumerate(writer.pages, 1):
        content = ContentStream(page.get_contents(), writer)
        fonts = page["/Resources"]["/Font"]
        decoders = {}
        glyphs, spans, stack, draw_info = [], [], [], {}
        font_name = font_size = None
        for index, (args, op) in enumerate(content.operations):
            if op == b"Tf":
                font_name, font_size = args
            elif op in (b"BDC", b"BMC"):
                props = args[1] if op == b"BDC" and isinstance(args[1], DictionaryObject) else {}
                stack.append((index, len(glyphs), props.get("/ActualText")))
            elif op == b"EMC" and stack:
                start_op, start, actual = stack.pop()
                if actual is not None:
                    records = glyphs[start:]
                    if len(actual) == len(records):
                        for record, char in zip(records, actual):
                            record["logical"] = char
                    elif records:
                        records[0]["logical"] = str(actual)
                        for record in records[1:]:
                            record["logical"] = ""
                    spans.append((start_op, start, len(glyphs)))
            elif op in (b"Tj", b"TJ"):
                if font_name is None:
                    continue
                if font_name not in decoders:
                    decoders[font_name] = _font_decoder(fonts[font_name].get_object())
                width, decode = decoders[font_name]
                strings = args if op == b"Tj" else args[0]
                draw_info[index] = (font_name, font_size)
                for item_index, value in enumerate(strings):
                    if isinstance(value, (int, float)):
                        continue
                    raw = _bytes(value)
                    if len(raw) % width:
                        raise ValueError("Partial glyph in text string")
                    for offset in range(0, len(raw), width):
                        part = raw[offset:offset + width]
                        glyphs.append({"op": index, "item": item_index, "offset": offset,
                                       "raw": part, "font": font_name, "size": font_size,
                                       "logical": decode(part)})
        logical = "".join(g["logical"] for g in glyphs)
        start = 0
        ranges = []
        while (start := logical.find(original, start)) >= 0:
            ranges.append((start, start + len(original)))
            start += len(original)
        if not ranges:
            continue
        affected = set()
        position = 0
        for index, glyph in enumerate(glyphs):
            text = glyph["logical"]
            stop = position + len(text)
            for low, high in ranges:
                if max(low, position) < min(high, stop):
                    # Only whole-character contributions are replaced.
                    left, right = max(low, position), min(high, stop)
                    text = text[:left-position] + replacement[left-low:right-low] + text[right-position:]
                    glyph["replacement"] = text
                    affected.add(index)
            position = stop
        for start_op, low, high in spans:
            span_indices = set(range(low, high))
            if affected & span_indices:
                if not span_indices <= affected:
                    raise ValueError("ActualText spans beyond target name; normalize this PDF first")
                content.operations[start_op][0][1].pop(NameObject("/ActualText"), None)
        cache, overrides = {}, {}
        for index in sorted(affected):
            glyph = glyphs[index]
            key = (str(glyph["font"]), glyph["raw"], glyph["replacement"])
            if key not in cache:
                name = NameObject("/LabUnicode" + str(len(cache) + 1))
                while name in fonts:
                    name = NameObject(str(name) + "x")
                clone = DictionaryObject(fonts[glyph["font"]].get_object().items())
                clone[NameObject("/ToUnicode")] = writer._add_object(_single_map(glyph["raw"], glyph["replacement"]))
                fonts[name] = writer._add_object(clone)
                cache[key] = name
            overrides[(glyph["op"], glyph["item"], glyph["offset"])] = (len(glyph["raw"]), cache[key])
        changed_ops = {g["op"] for g in glyphs if "replacement" in g}
        rewritten = []
        for index, (args, op) in enumerate(content.operations):
            if index not in changed_ops:
                rewritten.append((args, op))
                continue
            original_font, size = draw_info[index]
            strings = args if op == b"Tj" else args[0]
            for item_index, value in enumerate(strings):
                if isinstance(value, (int, float)):
                    rewritten.append(([ArrayObject([value])], b"TJ"))
                    continue
                raw, offset, normal = _bytes(value), 0, bytearray()
                while offset < len(raw):
                    override = overrides.get((index, item_index, offset))
                    if override is None:
                        normal.append(raw[offset]); offset += 1
                        continue
                    if normal:
                        rewritten.append(([ByteStringObject(bytes(normal))], b"Tj")); normal.clear()
                    length, name = override
                    rewritten.extend([([name, size], b"Tf"),
                                      ([ByteStringObject(raw[offset:offset+length])], b"Tj"),
                                      ([original_font, size], b"Tf")])
                    offset += length
                if normal:
                    rewritten.append(([ByteStringObject(bytes(normal))], b"Tj"))
        content.operations = rewritten
        page[NameObject("/Contents")] = writer._add_object(content)
        matches.append({"page": page_number, "occurrences": len(ranges), "glyphs": len(affected)})
    if not matches:
        raise ValueError("Target name could not be decoded; no native alias PDF produced")
    writer.metadata = None
    writer.xmp_metadata = None
    writer.write(target)
    return matches
