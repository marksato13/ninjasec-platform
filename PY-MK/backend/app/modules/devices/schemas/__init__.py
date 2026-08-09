from app.modules.devices.schemas.config import DeviceConfigCreate, DeviceConfigRead
from app.modules.devices.schemas.connection import (
    DeviceConnectionCreate,
    DeviceConnectionRead,
)
from app.modules.devices.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate
from app.modules.devices.schemas.topology import (
    CandidateConnection,
    DeduceConnectionsRequest,
    ParsedInterfaceInput,
    ParsedStaticRouteInput,
    TopologyCluster,
    TopologyEdge,
    TopologyNode,
    TopologyResponse,
)

__all__ = [
    "CandidateConnection",
    "DeduceConnectionsRequest",
    "DeviceConfigCreate",
    "DeviceConfigRead",
    "DeviceConnectionCreate",
    "DeviceConnectionRead",
    "DeviceCreate",
    "DeviceRead",
    "DeviceUpdate",
    "ParsedInterfaceInput",
    "ParsedStaticRouteInput",
    "TopologyCluster",
    "TopologyEdge",
    "TopologyNode",
    "TopologyResponse",
]
