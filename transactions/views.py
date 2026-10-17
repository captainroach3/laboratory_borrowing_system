from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdmin
from inventory.models import Inventory
from staff.models import Staff
from .models import Transaction
from .serializers import TransactionSerializer, TransactionCreateSerializer
from .permissions import IsOwnerStaffOrAdmin, IsStaffOrAdmin


class TransactionList(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        transactions = Transaction.objects.all()
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class MyTransactionList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user)
        return Response(TransactionSerializer(transactions, many=True).data)


class TransactionCreate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransactionCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionDetail(APIView):
    permission_classes = [IsOwnerStaffOrAdmin]

    def get(self, request, pk):
        try:
            transaction = Transaction.objects.get(pk=pk)
        except Transaction.DoesNotExist:
            return Response(data={'message': 'Transaction does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, transaction)
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)


class TransactionApprove(APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, pk):
        with db_transaction.atomic():
            try:
                transaction = Transaction.objects.select_for_update().get(pk=pk)
            except Transaction.DoesNotExist:
                return Response(data={'message': 'Transaction does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            if transaction.approver_id is not None:
                return Response(data={'message': 'This request is already approved.'}, status=status.HTTP_400_BAD_REQUEST)

            item = Inventory.objects.select_for_update().get(pk=transaction.item_name_id)
            if item.status != Inventory.AVAILABLE:
                return Response(data={'message': 'This item is not available for borrowing.'}, status=status.HTTP_400_BAD_REQUEST)
            if transaction.quantity > item.quantity:
                return Response(
                    data={'message': f'Not enough stock: {item.quantity} left, {transaction.quantity} requested.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            staff, _ = Staff.objects.get_or_create(
                user=request.user,
                defaults={'position': request.user.role.title()},
            )
            item.quantity -= transaction.quantity
            item.save(update_fields=['quantity'])
            transaction.approver = staff
            transaction.save(update_fields=['approver'])
        return Response(TransactionSerializer(transaction).data)


class TransactionReturn(APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, pk):
        with db_transaction.atomic():
            try:
                transaction = Transaction.objects.select_for_update().get(pk=pk)
            except Transaction.DoesNotExist:
                return Response(data={'message': 'Transaction does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            if transaction.approver_id is None:
                return Response(data={'message': 'This request has not been approved yet.'}, status=status.HTTP_400_BAD_REQUEST)
            if transaction.return_datetime is not None:
                return Response(data={'message': 'This item was already returned.'}, status=status.HTTP_400_BAD_REQUEST)

            item = Inventory.objects.select_for_update().get(pk=transaction.item_name_id)
            item.quantity += transaction.quantity
            item.save(update_fields=['quantity'])
            transaction.return_datetime = timezone.now()
            transaction.save(update_fields=['return_datetime'])
        return Response(TransactionSerializer(transaction).data)


class TransactionDelete(APIView):
    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        with db_transaction.atomic():
            try:
                transaction = Transaction.objects.select_for_update().get(pk=pk)
            except Transaction.DoesNotExist:
                return Response(data={'message': 'Transaction does not exist.'}, status=status.HTTP_404_NOT_FOUND)

            still_out = transaction.approver_id is not None and transaction.return_datetime is None
            if still_out:
                item = Inventory.objects.select_for_update().get(pk=transaction.item_name_id)
                item.quantity += transaction.quantity
                item.save(update_fields=['quantity'])

            transaction.delete()
        return Response(data={'message': 'Transaction deleted.'}, status=status.HTTP_204_NO_CONTENT)