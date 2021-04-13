# Copyright 2019-2021 ETH Zurich and the DaCe authors. All rights reserved.
""" FPGA Tests for GlobalToLocal transformation"""

import dace
import numpy as np
from dace.transformation.interstate import FPGATransformSDFG, FPGAGlobalToLocal

N = dace.symbol('N')

def test_global_to_local(size: int):
    '''
    Dace program with numpy reshape, transformed for FPGA
    :return:
    '''
    @dace.program
    def global_to_local(A: dace.float32[N], B: dace.float32[N]):
        for i in range(N):
            tmp = A[i]
            B[i] = tmp + 1

    A = np.random.rand(size).astype(np.float32)
    B = np.random.rand(size).astype(np.float32)

    sdfg = global_to_local.to_sdfg()
    sdfg.apply_transformations([FPGATransformSDFG])
    sdfg.apply_transformations([FPGAGlobalToLocal])
    sdfg(A=A, B=B, N=N)
    assert np.allclose(A+1, B)


if __name__ == "__main__":
    test_global_to_local(8)