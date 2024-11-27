from fastapi import APIRouter
from routers.v1.auth import router as auth_router
from routers.v1.user import router as user_router
from routers.v1.integration import router as integration_router
from routers.v1.workflow import router as workflow_router
from routers.v1.query import router as query_router


router = APIRouter(prefix="/v1")
router.include_router(auth_router, prefix="/auth", tags=["Auth"])

router.include_router(user_router, prefix="/user", tags=["User"])
router.include_router(integration_router, prefix="/integration", tags=["Integration"])
router.include_router(workflow_router, prefix="/workflow", tags=["Workflow"])
router.include_router(query_router, prefix="/query", tags=["Query"])
