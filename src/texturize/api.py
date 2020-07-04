# neural-texturize — Copyright (c) 2020, Novelty Factory KG.  See LICENSE for details.

import os

import torch
import torch.nn.functional as F
from creativeai.image.encoders import models

from .critics import GramMatrixCritic, PatchCritic, HistogramCritic
from .app import TextureSynthesizer, Application, Result
from .io import *


@torch.no_grad()
def process_iterations(
    cmd,
    log: object = None,
    size: tuple = None,
    octaves: int = -1,
    variations: int = 1,
    iterations: int = 200,
    threshold: float = 1e-5,
    device: str = None,
    precision: str = None,
):
    """Synthesize a new texture and return a PyTorch tensor at each iteration.
    """

    # Setup the application to use throughout the synthesis.
    app = Application(log, device, precision)

    # Encoder used by all the critics at every octave.
    encoder = models.VGG11(pretrained=True, pool_type=torch.nn.AvgPool2d)
    encoder = encoder.to(device=app.device, dtype=app.precision)
    app.encoder = encoder

    # Coarse-to-fine rendering, number of octaves specified by user.
    seed = None
    for octave, scale in enumerate(2 ** s for s in range(octaves - 1, -1, -1)):
        app.log.info(f"\n OCTAVE #{octave} ")
        app.log.debug("<- scale:", f"1/{scale}")

        critics = cmd.prepare_critics(app, scale)

        result_size = (variations, 3, size[1] // scale, size[0] // scale)
        seed = cmd.prepare_seed_tensor(app, result_size, previous=seed)
        app.log.debug("<- seed:", tuple(seed.shape[2:]), "\n")

        for result in app.process_octave(
            seed,
            app.encoder,
            critics,
            octave,
            scale,
            threshold=threshold,
            iterations=iterations,
        ):
            yield result

        seed = result.images
        del result


@torch.no_grad()
def process_octaves(cmd, **kwargs):
    """Synthesize a new texture from sources and return a PyTorch tensor at each octave.
    """
    for r in process_iterations(cmd, **kwargs):
        if r.iteration >= 0:
            continue

        yield Result(
            r.images, r.octave, r.scale, -r.iteration, r.loss, r.rate, r.retries
        )


def process_single_command(cmd, log: object, output: str = None, **config: dict):
    for result in process_octaves(cmd, log=log, **config):
        images = save_tensor_to_images(result.images)
        filenames = []
        for i, image in enumerate(images):
            # Save the files for each octave to disk.
            filename = output.format(octave=result.octave, variation=i,)
            image.resize(size=config["size"], resample=0).save(filename)
            log.debug("\n=> output:", filename)
            filenames.append(filename)

    return filenames
