from rest_framework import serializers
from .models import Book

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class ReconciliationSerializer(serializers.Serializer):
    source_file = serializers.FileField(required=True)
    target_file = serializers.FileField(required=True)
    output_format = serializers.ChoiceField(
        choices=['json', 'csv', 'html'],
        default='json',
        required=False
    )
