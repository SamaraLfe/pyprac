import unittest
import multiprocessing
import asyncio
import time
import socket

import sq_serv
from client import sqrootnet


class TestSqrootserver(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.proc = multiprocessing.Process(target=sqroots_server.serve)
		cls.proc.start()
		time.sleep(1)

	@classmethod
	def tearDownClass(cls):
		cls.proc.kill()
		cls.proc.join()

	def setUp(self):
		host = "localhost"
		port = 1337

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((host, port))

	def test_0_sqrootnet(self):
		self.assertEqual(sqrootnet("0 1 2", self.socket), "Incorrect input.")

	def test_1_sqrootnet(self):
		self.assertEqual(sqrootnet("1 2 3", self.socket), "")

	def test_2_sqrootnet(self):
		self.assertEqual(sqrootnet("1 2 1", self.socket), "-1.0")

	def test_3_sqrootnet(self):
		self.assertEqual(sqrootnet("1 5 6", self.socket), "-3.0 -2.0")

	def tearDown(self):
		self.socket.close()