import io
import zipfile
from unittest.mock import patch
from unittest import TestCase as SimpleTestCase
from limousine.presentation.web.rendering import templates

def render_to_string(name, context):
    return templates.get_template(name).render(**context)
from limousine.infrastructure.document_preview import office_preview, PreviewUnavailable


def office_zip(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, value in files.items():
            archive.writestr(name, value)
    stream.seek(0)
    return stream


class OfficePreviewTests(SimpleTestCase):
    def test_docx_text_is_escaped_in_preview(self):
        source = office_zip({"word/document.xml": '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>&lt;script&gt;alert(1)&lt;/script&gt;</w:t></w:r></w:p></w:body></w:document>'})
        preview = office_preview(source, ".docx")
        html = render_to_string("web/document_preview.html", {"preview": preview, "attachment": {"name": "test.docx"}})
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)

    def test_xlsx_shared_strings_sparse_cells_and_multiple_sheets(self):
        source = office_zip({
            "xl/workbook.xml": '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Cars" r:id="r1"/><sheet name="More" r:id="r2"/></sheets></workbook>',
            "xl/_rels/workbook.xml.rels": '<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/><Relationship Id="r2" Target="worksheets/sheet2.xml"/></Relationships>',
            "xl/sharedStrings.xml": '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>0007</t></si></sst>',
            "xl/worksheets/sheet1.xml": '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c r="C1" t="s"><v>0</v></c></row></sheetData></worksheet>',
            "xl/worksheets/sheet2.xml": '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c r="A1" t="inlineStr"><is><t>Text</t></is></c></row></sheetData></worksheet>',
        })
        preview = office_preview(source, ".xlsx")
        self.assertEqual(preview["blocks"][0]["rows"], [["", "", "0007"]])
        self.assertEqual(preview["blocks"][1]["rows"], [["Text"]])

    def test_broken_entity_and_oversized_xml_do_not_render(self):
        for xml in ('<broken', '<!DOCTYPE x [<!ENTITY a "text">]><x>&a;</x>', 'x' * 100):
            with self.subTest(xml=xml[:10]), patch("limousine.infrastructure.document_preview.MAX_XML_BYTES", 80):
                with self.assertRaises(PreviewUnavailable):
                    office_preview(office_zip({"word/document.xml": xml}), ".docx")

    def test_utf16_document_type_is_rejected_without_expansion(self):
        xml = '<!DOCTYPE x [<!ENTITY a "text">]><x>&a;</x>'.encode("utf-16")
        with self.assertRaises(PreviewUnavailable):
            office_preview(office_zip({"word/document.xml": xml}), ".docx")
