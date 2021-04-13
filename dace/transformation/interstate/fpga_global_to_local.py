# Copyright 2019-2021 ETH Zurich and the DaCe authors. All rights reserved.
""" Contains a transformation that changes the storage type of a Global FPGA variable to Local when certains
    conditions are met.
"""

import networkx as nx

from dace import registry, properties
from dace.transformation import transformation
from dace import symbolic, dtypes
from dace.sdfg import nodes, trace_nested_access
from dace import config


@registry.autoregister
@properties.make_properties
class FPGAGlobalToLocal(transformation.Transformation):
    """ Implements the FPGAGlobalToLoca transformation, which takes an entire
        SDFG  and changes the storage type of a Global FPGA data container to Local in the following situation:
        - data the is transient,
        - and the data is not a transient shared with other states,
        - and data has a compile-time known size. """
    @staticmethod
    def annotates_memlets():
        return True

    @staticmethod
    def expressions():
        # Match anything
        return [nx.DiGraph()]

    @staticmethod
    def can_be_applied(graph, candidate, expr_index, sdfg, strict=False):
        # It can always be applied
        return True

    @staticmethod
    def match_to_str(graph, candidate):
        return graph.label

    def apply(self, sdfg):

        count = 0

        for sd, name, desc in sdfg.arrays_recursive():
            if desc.transient and name not in sd.shared_transients(
            ) and desc.storage == dtypes.StorageType.FPGA_Global:

                # Get the total size, trying to resolve it to constant if it is a symbol
                total_size = symbolic.resolve_symbol_to_constant(
                    desc.total_size, sdfg)

                if total_size is not None:
                    desc.storage = dtypes.StorageType.FPGA_Local
                    count = count + 1

                    # update all access nodes that refers to this container
                    for state in sd.states():
                        for node, graph in state.all_nodes_recursive():
                            if isinstance(node, nodes.AccessNode):
                                trace = trace_nested_access(
                                    node, graph, graph.parent)
                                outer_node = None
                                for node_trace, memlet_trace, state_trace, sdfg_trace in trace:
                                    # Find the name of the accessed node in our scope
                                    if state_trace == state and sdfg_trace == sd:
                                        _, outer_node = node_trace
                                        if outer_node is not None:
                                            break

                                if outer_node is not None and outer_node.data == name:
                                    nodedesc = node.desc(graph)
                                    nodedesc.storage = dtypes.StorageType.FPGA_Local

        if config.Config.get_bool('debugprint'):
            print(f'Applied {count} GlobalToLocal.')
