"""ML4T 토론 자료의 장별 비교표·회차표·공유 그림·이동 경로 회귀 검사."""

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


SESSION = Path(__file__).resolve().parents[2] / (
    "html/studies/machine-trading/presentations/2026-09-12-next-study-discussion"
)


class Node:
    def __init__(self, tag="", attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def find(self, tag=None, **attrs):
        result = []
        for child in self.children:
            if not isinstance(child, Node):
                continue
            if (tag is None or child.tag == tag) and all(
                child.attrs.get(key) == value for key, value in attrs.items()
            ):
                result.append(child)
            result.extend(child.find(tag, **attrs))
        return result

    def text(self):
        return "".join(c.text() if isinstance(c, Node) else c for c in self.children)


class Document(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.root = Node()
        self.stack = [self.root]
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {"meta", "link", "img", "br", "hr", "input", "source", "wbr"}:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


class NextStudySyncTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = Document(SESSION / "report.html").root
        cls.deck = Document(SESSION / "index.html").root

    def test_chapter_matrix_matches_schedules_and_shared_svg(self):
        matrix = self.report.find("table", id="table-curriculum")[0]
        rows = matrix.find("tbody")[0].find("tr")
        self.assertEqual([int(r.attrs["data-chapter"]) for r in rows], list(range(1, 28)))
        svg = ET.parse(SESSION / "assets/figs/path-coverage.svg").getroot()
        ns = {"s": "http://www.w3.org/2000/svg"}
        for column, (plan, count, y) in enumerate(
            [("a", 29, "105"), ("b", 22, "153"), ("c", 16, "201")]
        ):
            table = self.report.find("table", id="table-path-" + plan)[0]
            schedule = table.find("tbody")[0].find("tr")
            self.assertEqual(len(schedule), count)
            central = set()
            for row in schedule:
                chapter = row.find("td")[2].text()
                match = re.match(r"Ch(\d+)\s", chapter)
                if match:
                    central.add(int(match[1]))
            statuses = [r.find("td")[column].text() for r in rows]
            self.assertEqual(
                {i for i, status in enumerate(statuses, 1) if status == "중심"}, central
            )
            self.assertEqual(len(central), count - 2)
            if plan == "a":
                self.assertEqual(
                    [r.find("th")[0].text() for r in rows],
                    [r.find("td")[2].text() for r in schedule[1:-1]],
                )
            cells = [
                rect for rect in svg.findall("s:rect", ns)
                if rect.get("y") == y and rect.get("width") == "28"
            ]
            self.assertEqual(len(cells), 27)
            visual = [
                "관련 절" if cell.get("fill-opacity") else
                "선택" if cell.get("fill") == "#eef2f7" else "중심"
                for cell in cells
            ]
            self.assertEqual(statuses, visual)

    def test_plans_are_visible_and_have_individual_toc_entries(self):
        for plan in "abc":
            details = self.report.find("details", id="fold-path-" + plan)[0]
            self.assertIn("open", details.attrs)
            self.assertTrue(details.find("summary")[0].attrs.get("data-report-toc"))

    def test_every_slide_has_a_visible_report_link_to_its_evidence(self):
        ids = {node.attrs["id"] for node in self.report.find() if "id" in node.attrs}
        slides = [s for s in self.deck.find("section") if "slide" in s.attrs.get("class", "").split()]
        self.assertEqual(len(slides), 22)
        for index, slide in enumerate(slides, 1):
            with self.subTest(slide=index):
                refs = slide.attrs["data-report-refs"].split()
                self.assertEqual(len(refs), len(set(refs)))
                self.assertTrue(set(refs) <= ids)
                links = [
                    a.attrs["href"].split("#", 1)[1] for a in slide.find("a")
                    if a.attrs.get("href", "").startswith("report.html#") and a.text().strip()
                ]
                self.assertTrue(links)
                self.assertTrue(set(links) <= set(refs))
        self.assertIn("report.html#table-curriculum", [
            a.attrs.get("href") for a in slides[11].find("a")
        ])
        self.assertIn("report.html#table-path-c", [
            a.attrs.get("href") for a in slides[13].find("a")
        ])

    def test_required_figures_use_the_same_assets_in_the_same_order(self):
        figures = self.report.find("figure", **{"data-deck-use": "required"})
        self.assertEqual(len(figures), 8)
        self.assertEqual(
            [f.find("img")[0].attrs["src"] for f in figures],
            [i.attrs["src"] for i in self.deck.find("img")],
        )


if __name__ == "__main__":
    unittest.main()
