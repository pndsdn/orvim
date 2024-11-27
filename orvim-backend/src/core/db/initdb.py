from core.db.session import engine, with_database
from settings import settings
import models


def create_initial_user():
    with with_database() as db:
        users_in_system = db.query(models.user.User).count()
        if users_in_system > 0:
            return
        user = models.user.User(username=settings.ADMIN_USERNAME,
                                email=settings.ADMIN_EMAIL,
                                password=settings.ADMIN_PASSWORD)
        db.add(user)
        db.flush()
        user_info = models.user.UserInfo(user_id=user.id,
                                         surname="Admin",
                                         name="Admin",
                                         patronymic="Admin")
        db.add(user_info)
        db.commit()



def create_tables():
    models.base.Base.metadata.create_all(engine)
