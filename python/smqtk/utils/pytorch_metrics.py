import logging
from enum import Enum

try:
    import torch
except ImportError as ex:
    logging.getLogger(__name__).warning("Failed to import pytorch module: %s",
                                        str(ex))
    torch = None

class DIS_TYPE(Enum):
    L2 = 1
    hik = 2


def L2_dis(t1, t2, dim):
    res = (t1.float() - t2.float()).norm(p=2, dim=dim)

    return res


def his_intersection_dis(t1, t2, dim):

    res = 1.0 - ((t1 + t2) - torch.abs(t1 - t2)).sum(dim=dim) * 0.5

    return res
