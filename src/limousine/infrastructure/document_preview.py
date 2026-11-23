"""Bounded local text/table previews of OOXML; no external links or execution."""

import posixpath
import re
import zipfile
from xml.etree import ElementTree as ET

MAX_XML_BYTES = 2 * 1024 * 1024
MAX_BLOCKS = 500
MAX_ROWS = 200
MAX_COLUMNS = 30
MAX_CELL_TEXT = 2000
WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SHEET = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


class PreviewUnavailable(ValueError):
    pass


class _NoDTD(ET.TreeBuilder):
    def doctype(
        self,
        name,
        pubid,
        system,
    ):
        raise PreviewUnavailable("Document type declarations are not previewed.")


def _xml(
    archive,
    name,
):
    if archive.getinfo(name).file_size > MAX_XML_BYTES:
        raise PreviewUnavailable("Document part exceeds preview limits.")
    with archive.open(name) as source:
        content = source.read(MAX_XML_BYTES + 1)
    if (
        len(content) > MAX_XML_BYTES
        or b"<!DOCTYPE" in content.upper()
        or b"<!ENTITY" in content.upper()
    ):
        raise PreviewUnavailable("Unsupported XML structure.")
    return ET.fromstring(
        content,
        parser=ET.XMLParser(target=_NoDTD()),
    )


def _text(
    element,
    tag,
):
    return "".join(node.text or "" for node in element.iter(tag))[:MAX_CELL_TEXT]


def _word(archive):
    body = _xml(
        archive,
        "word/document.xml",
    ).find(WORD + "body")
    if body is None:
        raise PreviewUnavailable("Document body is missing.")
    blocks = []
    truncated = len(body) > MAX_BLOCKS
    for item in list(body)[:MAX_BLOCKS]:
        if item.tag == WORD + "p":
            blocks.append(
                {
                    "text": _text(
                        item,
                        WORD + "t",
                    )
                }
            )
        elif item.tag == WORD + "tbl":
            rows = item.findall(WORD + "tr")
            truncated |= len(rows) > MAX_ROWS
            table = []
            for row in rows[:MAX_ROWS]:
                cells = row.findall(WORD + "tc")
                truncated |= len(cells) > MAX_COLUMNS
                table.append(
                    [
                        _text(
                            cell,
                            WORD + "t",
                        )
                        for cell in cells[:MAX_COLUMNS]
                    ]
                )
            blocks.append({"rows": table})
    return {"blocks": blocks, "truncated": truncated}


def _column_index(reference):
    letters = re.match(
        r"^([A-Z]{1,3})[1-9][0-9]*$",
        reference,
    )
    if not letters:
        raise PreviewUnavailable("Unsupported cell reference.")
    value = 0
    for char in letters[1]:
        value = value * 26 + ord(char) - ord("A") + 1
    return value - 1


def _excel(archive):
    strings = []
    if "xl/sharedStrings.xml" in archive.namelist():
        entries = _xml(
            archive,
            "xl/sharedStrings.xml",
        ).findall(SHEET + "si")
        if len(entries) > 10000:
            raise PreviewUnavailable("Shared string table exceeds preview limits.")
        strings = [
            _text(
                item,
                SHEET + "t",
            )
            for item in entries
        ]
    relations = {
        item.get("Id"): item.get("Target")
        for item in _xml(
            archive,
            "xl/_rels/workbook.xml.rels",
        )
        if item.get("TargetMode") != "External"
    }
    sheets = _xml(
        archive,
        "xl/workbook.xml",
    ).findall(SHEET + "sheets/" + SHEET + "sheet")
    blocks = []
    truncated = len(sheets) > 5
    for sheet in sheets[:5]:
        target = relations.get(
            sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        )
        if not target:
            raise PreviewUnavailable("Worksheet is missing.")
        name = posixpath.normpath(target.lstrip("/") if target.startswith("/") else "xl/" + target)
        if not name.startswith("xl/"):
            raise PreviewUnavailable("Invalid worksheet target.")
        root = _xml(
            archive,
            name,
        )
        rows = root.findall(SHEET + "sheetData/" + SHEET + "row")
        truncated |= len(rows) > MAX_ROWS
        table = []
        width = 0
        for row in rows[:MAX_ROWS]:
            values = [""] * MAX_COLUMNS
            for cell in row.findall(SHEET + "c"):
                index = _column_index(
                    cell.get(
                        "r",
                        "",
                    )
                )
                if index >= MAX_COLUMNS:
                    truncated = True
                    continue
                value = cell.findtext(
                    SHEET + "v",
                    "",
                )
                kind = cell.get("t")
                if kind == "s":
                    number = int(value)
                    value = strings[number] if 0 <= number < len(strings) else ""
                elif kind == "inlineStr":
                    value = _text(
                        cell,
                        SHEET + "t",
                    )
                elif kind == "b":
                    value = "TRUE" if value == "1" else "FALSE"
                values[index] = value[:MAX_CELL_TEXT]
                width = max(
                    width,
                    index + 1,
                )
            table.append(values)
        blocks.append(
            {
                "heading": sheet.get(
                    "name",
                    "",
                )[:150],
                "rows": [row[:width] for row in table],
            }
        )
    return {"blocks": blocks, "truncated": truncated}


def office_preview(
    source,
    extension,
):
    try:
        with zipfile.ZipFile(source) as archive:
            if len(archive.infolist()) > 5000:
                raise PreviewUnavailable("Archive exceeds preview limits.")
            return _word(archive) if extension == ".docx" else _excel(archive)
    except (
        zipfile.BadZipFile,
        KeyError,
        ET.ParseError,
        ValueError,
        RuntimeError,
        OSError,
        OverflowError,
    ) as error:
        raise PreviewUnavailable("Preview unavailable; download the original document.") from error
