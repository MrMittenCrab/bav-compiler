"""Focused Word viewport-follow regressions for the installed helper.

Never drive Office, occupy slots, capture, or invoke process.
The first page-scroll repair failed natively; the installed helper selects
the native page/character range and requires independent canvas text proof.
"""

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

INSTALLED = Path('/Users/lizhiguo/.autocycle/native_office.py')
MAINTAINED = Path('/Users/lizhiguo/Documents/Developer/autocycle/native_office.py')
EXPECTED_HELPER_SHA256 = 'dcf5f081f669ed3a69a2737e4690c0bec7ff6cd051dcf156d31067eb86620ef7'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_helper(path=INSTALLED):
    tmp = tempfile.TemporaryDirectory()
    copy = Path(tmp.name) / 'native_office.py'
    copy.write_text(path.read_text())
    spec = importlib.util.spec_from_file_location('word_viewport_native_office', copy)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._keep_tmp = tmp
    return module


class DeployedRuntimeTests(unittest.TestCase):
    def test_installed_and_maintained_are_identical_range_select_helpers(self):
        self.assertEqual(INSTALLED.read_text(), MAINTAINED.read_text())
        self.assertEqual(sha256(INSTALLED), EXPECTED_HELPER_SHA256)
        self.assertEqual(sha256(MAINTAINED), EXPECTED_HELPER_SHA256)
        text = INSTALLED.read_text()
        self.assertIn('select (create range targetDoc start', text)
        self.assertIn('select pageRange', text)
        self.assertIn('unique-page-text-in-captured-canvas', text)
        self.assertIn('Retained Word capture lacks bound visible-page evidence', text)
        self.assertNotIn('page scroll (window 1 of targetDoc) down', text)
        self.assertNotIn('Word viewport did not follow selection', text)
        self.assertNotIn(
            'set percentage of zoom of view of window 1 of targetDoc to {zoom}\\n'
            'set selection start of selection of window 1 of targetDoc to {start}\\n'
            'set selection end of selection of window 1 of targetDoc to {end}',
            text,
        )


class WordPositionScriptTests(unittest.TestCase):
    def setUp(self):
        self.office = load_helper()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.word = Path(self.tmp.name) / 'word-view.docx'
        self.word.write_bytes(b'slot')
        self.backend = self.office.MacOffice()
        self.bodies = []
        self.timeouts = []
        self.backend.is_open = lambda app, path: (app, str(path)) in self.backend.opened
        self.backend.opened[('word', str(self.word))] = (self.backend.reference('word', self.word), ('lock',))

        def script(app, body, *args, **kwargs):
            self.bodies.append(body)
            self.timeouts.append(kwargs.get('timeout'))
            return 'POSITIONED'
        self.backend.script = script

    def test_character_position_selects_range_without_scroll_heuristic(self):
        self.backend.position('word', self.word, {
            'start': 5276, 'end': 5276, 'zoom': 100, 'bounds': [40, 40, 1320, 1000],
        })
        body = self.bodies[-1]
        self.assertIn('repaginate targetDoc', body)
        self.assertIn('set view type of view of window 1 of targetDoc to print view', body)
        self.assertIn('select (create range targetDoc start 5276 end 5276)', body)
        self.assertNotIn('page scroll', body)
        self.assertNotIn('vertical percent', body)
        self.assertNotIn(
            'set selection start of selection of window 1 of targetDoc to 5276',
            body,
        )
        self.assertEqual(self.timeouts[-1], 45)

    def test_page_locator_selects_absolute_page_range(self):
        self.backend.position('word', self.word, {
            'page': 12, 'zoom': 100, 'bounds': [40, 40, 1320, 1000],
        })
        body = self.bodies[-1]
        self.assertIn('information type number of pages in document', body)
        self.assertIn('if 12 > pageCount then error "Word page exceeds document pagination"', body)
        self.assertIn('goto a page item position absolute count 12', body)
        self.assertIn('select pageRange', body)
        self.assertNotIn('page scroll', body)
        self.assertNotIn('vertical percent', body)

    def test_invalid_page_is_rejected_before_script(self):
        with self.assertRaises(self.office.NativeError) as raised:
            self.backend.position('word', self.word, {'page': 0, 'start': 0})
        self.assertIn('Invalid Word page', str(raised.exception))
        self.assertEqual(self.bodies, [])

    def test_validate_request_accepts_page_and_rejects_zero(self):
        self.office.MacOffice.validate_request(
            'word', {'start': 0, 'page': 3, 'zoom': 100, 'bounds': [40, 40, 1320, 1000]},
        )
        with self.assertRaises(self.office.NativeError):
            self.office.MacOffice.validate_request(
                'word', {'page': 0, 'zoom': 100, 'bounds': [40, 40, 1320, 1000]},
            )


class WordRenderedProofTests(unittest.TestCase):
    def setUp(self):
        self.office = load_helper()

    def _png(self, path):
        path.write_bytes(
            bytes.fromhex(
                '89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4'
                '890000000d4944415478da6360000002000100ffff03000006000557bf000000'
                '0049454e44ae426082'
            )
        )

    def test_unique_page_text_accepts_and_rejects_wrong_viewport(self):
        with tempfile.TemporaryDirectory() as d:
            owned = Path(d) / 'word-view.docx'
            owned.write_bytes(b'copy')
            image = Path(d) / 'view.png'
            self._png(image)
            pages = [
                'Lululemon Drivers opening paragraph unique',
                'Margin evidence table interior unique',
                'Residuals are computed from appendix',
            ]
            for page, visible in ((1, 1), (2, 2), (3, 3), (2, 1)):
                native = {
                    'word_rendered': {
                        'method': 'vision-document-canvas',
                        'lines': [{'text': pages[visible - 1], 'confidence': 1}],
                    }
                }
                if visible == page:
                    proof = self.office.MacOffice.verify_word_rendered(
                        owned, image, {'page': page, 'pages': pages}, native,
                    )
                    self.assertEqual(proof['page'], page)
                    self.assertEqual(proof['method'], 'unique-page-text-in-captured-canvas')
                else:
                    with self.assertRaises(self.office.NativeError) as raised:
                        self.office.MacOffice.verify_word_rendered(
                            owned, image, {'page': page, 'pages': pages}, native,
                        )
                    self.assertIn('not independently visible', str(raised.exception))

    def test_legacy_receipt_without_visible_page_is_rejected(self):
        result = {
            'request': {'app': 'word', 'start': 5276},
            'source_sha256': 'source',
            'screenshot_sha256': 'image',
        }
        with self.assertRaises(self.office.NativeError) as raised:
            self.office.validate_word_receipt(result)
        self.assertIn('bound visible-page evidence', str(raised.exception))
        result['word_visible_page'] = {
            'method': 'unique-page-text-in-captured-canvas',
            'page': 3,
            'copy_sha256': 'source',
            'screenshot_sha256': 'image',
        }
        self.office.validate_word_receipt(result)


class WordPageMapOrderTests(unittest.TestCase):
    def test_capture_collects_page_map_before_position(self):
        office = load_helper()
        order = []

        class FakeBackend:
            def is_open(self, app, path):
                return True

            def open(self, app, path):
                order.append('open')

            def verify_document(self, app, path):
                order.append('verify')

            def word_page_map(self, path, request):
                order.append('page_map')
                return {'page': request.get('page', 1), 'pages': ['one unique page text here', 'two more words']}

            def position(self, app, path, request):
                order.append('position')

            def confirm_view(self, app, path, request):
                order.append('confirm')
                return {'pid': 1, 'bundle_id': 'com.microsoft.Word', 'title': 'word-view', 'frame': [40, 40, 1280, 960]}

            def capture(self, image, routing):
                order.append('capture')
                Path(image).write_bytes(b'\x89PNG\r\n\x1a\n' + b'x' * 600)
                return {'width': 2560, 'height': 1920, 'window_id': 1}

            def word_content(self, path):
                return 'one unique page text heretwo more words'

        with tempfile.TemporaryDirectory() as d:
            workspace = office.Workspace(d, FakeBackend())
            slot = workspace.slot('word', 'view')
            slot.parent.mkdir(parents=True, exist_ok=True)
            slot.write_bytes(b'owned')
            with patch.object(office, 'validate_png', return_value={'width': 2560, 'height': 1920, 'bytes': 10}), \
                    patch.object(office.MacOffice, 'verify_word_rendered', return_value={'page': 1}):
                workspace.capture_owned('word', slot, {'page': 1, 'source_sha256': office.digest(slot)}, Path(d) / 'out.png')
        self.assertEqual(order[:4], ['verify', 'page_map', 'position', 'confirm'])
        self.assertLess(order.index('page_map'), order.index('position'))


if __name__ == '__main__':
    unittest.main()
