from rest_framework import serializers
from inventory.models import Inventory
from .models import Transaction

def full_name(user):
    return f'{user.first_name} {user.last_name}'.strip()

class TransactionSerializer(serializers.ModelSerializer):
    item_label = serializers.CharField(source='item_name.item_name', read_only=True)
    user_label = serializers.SerializerMethodField()
    approver_label = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = '__all__'

    def get_user_label(self, obj):
        return full_name(obj.user)

    def get_approver_label(self, obj):
        return full_name(obj.approver.user) if obj.approver else None


class TransactionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['transaction_id', 'user', 'approver', 'borrow_datetime', 'return_datetime']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError('Quantity must be at least 1.')
        return value

    def validate(self, attrs):
        item = attrs['item_name']
        quantity = attrs.get('quantity', 1)
        if item.status != Inventory.AVAILABLE:
            raise serializers.ValidationError({'item_name': 'This item is not available for borrowing.'})
        if quantity > item.quantity:
            raise serializers.ValidationError({'quantity': f'Only {item.quantity} in stock.'})
        return attrs