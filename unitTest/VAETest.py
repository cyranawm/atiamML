import unittest
import sys
# Add the src folder path to the sys.path list
sys.path.append('../src')

import numpy
import tensorflow
from tensorflow.examples.tutorials.mnist import input_data
import torch
from torch import optim
from torch.autograd import Variable

from VAE import VAE


class TestVAECreation(unittest.TestCase):

    def test_good_VAE(self):
        X_dim = 513
        Z_dim = 6
        IOh_dims_Enc = [X_dim, 128, Z_dim]
        IOh_dims_Dec = [Z_dim, 128, X_dim]
        NL_types_Enc = ['relu']
        NL_types_Dec = ['relu', 'sigmoid']
        model = VAE(X_dim, Z_dim, IOh_dims_Enc,
                    IOh_dims_Dec, NL_types_Enc, NL_types_Dec)
        self.assertTrue(model.created)

    def test_wrong_EncoderStructure(self):
        X_dim = 513
        Z_dim = 6
        IOh_dims_Enc = [X_dim, Z_dim]
        IOh_dims_Dec = [Z_dim, 128, X_dim]
        NL_types_Enc = ['relu']
        NL_types_Dec = ['relu', 'sigmoid']
        model = VAE(X_dim, Z_dim, IOh_dims_Enc,
                    IOh_dims_Dec, NL_types_Enc, NL_types_Dec)
        self.assertFalse(model.created)

    def test_wrong_DecoderStructure(self):
        X_dim = 513
        Z_dim = 6
        IOh_dims_Enc = [X_dim, 128, Z_dim]
        IOh_dims_Dec = [X_dim]
        NL_types_Enc = ['relu']
        NL_types_Dec = ['relu', 'sigmoid']
        model = VAE(X_dim, Z_dim, IOh_dims_Enc,
                    IOh_dims_Dec, NL_types_Enc, NL_types_Dec)
        self.assertFalse(model.created)

    def test_wrong_EncoderNLFunctionsNb(self):
        X_dim = 513
        Z_dim = 6
        IOh_dims_Enc = [X_dim, 128, Z_dim]
        IOh_dims_Dec = [Z_dim, 128, X_dim]
        NL_types_Enc = ['relu', 'relu']
        NL_types_Dec = ['relu', 'sigmoid']
        model = VAE(X_dim, Z_dim, IOh_dims_Enc,
                    IOh_dims_Dec, NL_types_Enc, NL_types_Dec)
        self.assertFalse(model.created)

    def test_wrong_DecoderNLFunctionsNb(self):
        X_dim = 513
        Z_dim = 6
        IOh_dims_Enc = [X_dim, 128, Z_dim]
        IOh_dims_Dec = [Z_dim, 128, X_dim]
        NL_types_Enc = ['relu']
        NL_types_Dec = ['relu']
        model = VAE(X_dim, Z_dim, IOh_dims_Enc,
                    IOh_dims_Dec, NL_types_Enc, NL_types_Dec)
        self.assertFalse(model.created)

    def test_wrong_EncoderNLfunctionsSyntax(self):
        X_dim = 513
        Z_dim = 6
        IOh_dims_Enc = [X_dim, 128, Z_dim]
        IOh_dims_Dec = [Z_dim, 128, X_dim]
        NL_types_Enc = ['reLu']
        NL_types_Dec = ['relu', 'sigmoid']
        model = VAE(X_dim, Z_dim, IOh_dims_Enc,
                    IOh_dims_Dec, NL_types_Enc, NL_types_Dec)
        self.assertFalse(model.created)

    def test_wrong_DecoderNLfunctionsSyntax(self):
        X_dim = 513
        Z_dim = 6
        IOh_dims_Enc = [X_dim, 128, Z_dim]
        IOh_dims_Dec = [Z_dim, 128, X_dim]
        NL_types_Enc = ['relu']
        NL_types_Dec = ['relu', 'sigmoide']
        model = VAE(X_dim, Z_dim, IOh_dims_Enc,
                    IOh_dims_Dec, NL_types_Enc, NL_types_Dec)
        self.assertFalse(model.created)


class TestVAEFunctions(unittest.TestCase):

    def test_VAE_lonelyForward(self):
        mnist = input_data.read_data_sets('../MNIST_data', one_hot=True)
        mb_size = 64
        X, _ = mnist.train.next_batch(mb_size)
        X = Variable(torch.from_numpy(X))
        X_dim = mnist.train.images.shape[1]
        Z_dim = 40
        IOh_dims_Enc = [X_dim, 400, Z_dim]
        IOh_dims_Dec = [Z_dim, 400, X_dim]
        NL_types_Enc = ['relu']
        NL_types_Dec = ['relu', 'sigmoid']
        vae = VAE(X_dim, Z_dim, IOh_dims_Enc,
                  IOh_dims_Dec, NL_types_Enc, NL_types_Dec, mb_size)

        optimizer = optim.Adam(vae.parameters(), lr=1e-3)
        optimizer.zero_grad()
        out = 0
        out = vae(X)
        vae.encoder.getInfo()
        vae.decoder.getInfo()
        # print(out)
        self.assertTrue((vae.created) and (
            out.size()[1] == X_dim and out.size()[0] == mb_size))

suiteEncoder = unittest.TestLoader().loadTestsFromTestCase(TestVAECreation)
print "\n\n------------------- VAE Creation Test Suite -------------------\n"
unittest.TextTestRunner(verbosity=2).run(suiteEncoder)
suiteEncoder = unittest.TestLoader().loadTestsFromTestCase(TestVAEFunctions)
print "\n\n------------------- VAE functions Test Suite -------------------\n"
unittest.TextTestRunner(verbosity=2).run(suiteEncoder)
