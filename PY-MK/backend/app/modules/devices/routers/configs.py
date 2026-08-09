from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.deps.auth import CurrentUser, require_roles
from app.common.deps.database import get_db
from app.db.models.enums import RoleCode
from app.modules.devices.schemas import DeviceConfigCreate, DeviceConfigRead
from app.modules.devices.services.config_service import DeviceConfigService

router = APIRouter(prefix="/device-configs", tags=["device-configs"])


def _to_read(config) -> DeviceConfigRead:
    return DeviceConfigRead(
        id=config.id,
        device_id=config.device_id,
        vendor_detected=config.vendor_detected,
        parsed_json=config.parsed_json,
        parse_warnings=config.parse_warnings,
        uploaded_by=config.uploaded_by,
        uploaded_at=config.uploaded_at,
        has_raw_config=config.raw_config is not None,
    )


@router.get("/", response_model=list[DeviceConfigRead])
def list_device_configs(
    device_id: int,
    current_user: CurrentUser = Depends(
        require_roles(
            RoleCode.SUPER_ADMIN.value,
            RoleCode.ADMIN.value,
            RoleCode.COLLABORATOR.value,
        )
    ),
    db: Session = Depends(get_db),
) -> list[DeviceConfigRead]:
    configs = DeviceConfigService(db, current_user).list_for_device(device_id)
    return [_to_read(c) for c in configs]


@router.post("/", response_model=DeviceConfigRead, status_code=status.HTTP_201_CREATED)
def create_device_config(
    payload: DeviceConfigCreate,
    current_user: CurrentUser = Depends(
        require_roles(
            RoleCode.SUPER_ADMIN.value,
            RoleCode.ADMIN.value,
            RoleCode.COLLABORATOR.value,
        )
    ),
    db: Session = Depends(get_db),
) -> DeviceConfigRead:
    config = DeviceConfigService(db, current_user).create(payload)
    return _to_read(config)
