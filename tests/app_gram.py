# neural-texturize — Copyright (c) 2020, Novelty Factory KG.  See LICENSE for details.

import torch
import pytest

from texturize.commands import Remix
from texturize.api import process_octaves


def test_gram_single(image, size=(96, 88)):
    remix = Remix(image(size))
    for r in process_octaves(remix, mode="gram", octaves=2, size=size):
        assert len(r.images) == 1
        assert isinstance(r.images, torch.Tensor)
        assert r.images.shape[2:] == (size[1] // r.scale, size[0] // r.scale)
        assert r.loss < 1e-0


def test_gram_variations(image, size=(72, 64)):
    remix = Remix(image(size))
    for r in process_octaves(remix, mode="gram", variations=2, octaves=2, size=size):
        assert len(r.images) == 2
        assert isinstance(r.images, torch.Tensor)
        assert r.images.shape[2:] == (size[1] // r.scale, size[0] // r.scale)
        assert r.loss < 1e-0
