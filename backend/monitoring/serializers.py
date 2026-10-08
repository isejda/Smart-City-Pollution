from rest_framework import serializers

from .models import Parameter, City, Node, Reading, Settings


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = '__all__'


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'


class NodeSerializer(serializers.ModelSerializer):
    city = serializers.SlugRelatedField(slug_field='name', queryset=City.objects.all())

    class Meta:
        model = Node
        fields = [
            'node_id', 'eui', 'join_eui', 'name', 'city', 'place', 'address',
            'lat', 'lng', 'transport', 'hw', 'tech', 'installed_at', 'interval_s',
            'active', 'public', 'maintenance', 'coverage_m', 'scale', 'sensors',
            'api_id', 'webhook', 'tz', 'notes',
        ]


class ReadingSerializer(serializers.ModelSerializer):
    node = serializers.SlugRelatedField(slug_field='node_id', read_only=True)

    class Meta:
        model = Reading
        fields = ['id', 'node', 'ts', 'pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'pres', 'rain']


class ReadingIngestSerializer(serializers.ModelSerializer):
    """Write path for a live packet from a physical node (identified by its EUI, not its
    internal node_id/PK, since that is the identifier the hardware itself knows)."""
    eui = serializers.CharField(write_only=True)
    node = serializers.SlugRelatedField(slug_field='node_id', read_only=True)

    class Meta:
        model = Reading
        fields = ['id', 'eui', 'node', 'ts', 'pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'pres', 'rain']

    def validate_eui(self, value):
        try:
            self._node = Node.objects.get(eui=value)
        except Node.DoesNotExist:
            raise serializers.ValidationError(f'No node is registered with eui={value!r}.')
        return value

    def create(self, validated_data):
        validated_data.pop('eui', None)
        validated_data['node'] = self._node
        return super().create(validated_data)


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        exclude = ['id']
