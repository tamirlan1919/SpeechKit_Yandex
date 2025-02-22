from aiogram import Router
from .admin import router as admin_router
from .generals import router as generals_router
from .payment import router as payment_router
from .text import router as text_handler_router
router = Router()

router.include_routers(admin_router, payment_router,  generals_router, text_handler_router)