from main.repositories import RoomRepository


def update_room_expiration_time(func):
    """
    Updates room's last_visited field asynchronously by saving room object after func.
    The purpose of this decorator connected with Celery task which removes expired rooms.
    """
    async def wrapper(self, *args, **kwargs):
        await func(self, *args, **kwargs)
        # Update room's last_visited field
        room = await RoomRepository.get_room_by_id(self.room_id)
        await RoomRepository.save(room)
    return wrapper
