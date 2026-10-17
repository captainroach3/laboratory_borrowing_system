from rest_framework import serializers
from inventory.models import Inventory
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = '__all__'


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


class TransactionUpdateSerializer(serializers.ModelSerializer):


    class Meta:
        model = Transaction
        fields = ['approver', 'return_datetime']

    def validate(self, attrs):
        wants_approval = 'approver' in attrs
        wants_return = 'return_datetime' in attrs
        if wants_approval == wants_return:
            raise serializers.ValidationError(
                'Send either approver (to approve) or return_datetime (to record a return), not both or neither.'
            )

        borrow = self.instance
        if wants_approval:
            if attrs['approver'] is None:
                raise serializers.ValidationError({'approver': 'Approver is required.'})
            if borrow.approver_id is not None:
                raise serializers.ValidationError({'approver': 'This request is already approved.'})
        else:
            if attrs['return_datetime'] is None:
                raise serializers.ValidationError({'return_datetime': 'Return date is required.'})
            if borrow.approver_id is None:
                raise serializers.ValidationError({'return_datetime': 'This request has not been approved yet.'})
            if borrow.return_datetime is not None:
                raise serializers.ValidationError({'return_datetime': 'This item was already returned.'})
        return attrs