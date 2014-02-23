import unittest
import hashlib

import pieces

class Test_pieces(unittest.TestCase):

    def setUp(self):
        self.testHash = "This is a test"
        self.piece = pieces.Piece(0, 4, hashlib.sha1(self.testHash).digest())

    def testNumBlocks(self):
        self.assertEquals(self.piece.num_blocks, 1)
        self.assertEquals(len(self.piece.blocks), 1)
        self.assertFalse(self.piece.finished)

    def testAddBlockAndCheckHash(self):
        self.piece.addBlock(0, self.testHash)
        self.assertTrue(self.piece.finished)

    def testAddingBadData(self):
        self.piece.addBlock(0, 'garbage')
        self.assertFalse(self.piece.finished)
        self.assertFalse(all(self.piece.bitField))

if __name__ == '__main__':
    unittest.main()