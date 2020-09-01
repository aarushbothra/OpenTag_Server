import unittest
import OpenTag_Server
import socket
from unittest import mock
from unittest.mock import MagicMock, patch


class TestOpenTagServer(unittest.TestCase):
    def setUp(self):
        self.mock_openTag = mock.patch.multiple(
            OpenTag_Server, clients=[OpenTag_Server.Player(MagicMock(name='socket', spec=socket.socket), MagicMock())])

    # For this test we expect legacy behavior, and to get a utf-8 encoded string of the input.

    def test_dispatchResponseForLegacyList(self):
        byteList = [0]*20

        self.assertEqual(OpenTag_Server.dispatchResponse(
            byteList), '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,'.encode('utf-8'))

    # For this test we expect future behavior where we get back a JSON string of the input
    def test_dispatchResponseForJsonMap(self):
        payload = {"testNum": 123, "testString": '123'}
        self.assertEqual(OpenTag_Server.dispatchResponse(
            payload), '{"testNum": 123, "testString": "123"}'.encode('utf-8'))

    def test_restartFunctionality(self):
        with self.mock_openTag:
            # We should check for the following
            # Each client listed closes connection
            # the start script recalled

            # Mock this to prove it was called
            closeMock = OpenTag_Server.clients[0].conn = MagicMock()

            # were not testing the start function, but we should make sure it is called.
            OpenTag_Server.start = MagicMock(name='start')

            OpenTag_Server.restart()

            OpenTag_Server.start.assert_called_once()
            closeMock.close.assert_called_once()

    def test_parseMessage(self):
        # @TODO: do this one, it seems to have a bunch of logic in it.
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
