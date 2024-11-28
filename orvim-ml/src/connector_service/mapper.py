from common.workflow import (
    EnumConnectionType,
    ConnectionS3,
    TransformTextParser,
    TransformClip,
)

type2connector = {EnumConnectionType.s3: ConnectionS3}

avalible_types = {
    TransformTextParser: ["", "txt", "md"],
    TransformClip: ["png", "jpg"],
}
