# -*- coding: utf-8 -*-
"""
Handling workflows to be run in containers
"""

import os
import shutil


def set_inputs(container, inputs, container_dir, temp_dir):
    if container:
        for i, _ in enumerate(inputs):
            fname = os.path.basename(inputs[i])
            shutil.copyfile(inputs[i], os.path.join(temp_dir, fname))
            inputs[i] = os.path.join(container_dir, fname)

    return inputs
