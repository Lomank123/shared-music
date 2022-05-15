from main.repositories import RoomRepository
# from asgiref.sync import sync_to_async


def update_room_expiration_time(func):
    """
    Updates room's last_visited field asynchronously by saving room object after func.
    The purpose of this decorator connected with Celery task which removes expired rooms.
    """
    async def wrapper(self, *args, **kwargs):
        await func(self, *args, **kwargs)
        # Update room's last_visited field
        room = await RoomRepository.get_room_by_id_or_none(self.room_id)
        await RoomRepository.save_room(room)
        # TODO: Remove later
        # For testing
        # room = await RoomRepository.get_room_by_id_or_none(self.room_id)
        # await sync_to_async(print)("Inside decorator, after func", room.last_visited)
    return wrapper
