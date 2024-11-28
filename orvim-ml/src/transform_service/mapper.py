from common.workflow import (
    EnumConnectionType,
    EnumTransformType
)

available_types = {
    EnumTransformType.txt_parser: ["", "txt", "md"],
    EnumTransformType.clip: ["png", "jpg"],
}
