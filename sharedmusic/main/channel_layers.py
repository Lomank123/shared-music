from channels_redis.pubsub import RedisPubSubChannelLayer
from django.core.serializers.json import DjangoJSONEncoder
import msgpack


class CustomChannelLayer(RedisPubSubChannelLayer):
    """
    Custom channel layer based on RedisPubSubChannelLayer.
    """

    def serialize(self, message):
        # serialize() method uses different encoder to correctly convert datetime.
        return msgpack.packb(message, default=DjangoJSONEncoder().default)
