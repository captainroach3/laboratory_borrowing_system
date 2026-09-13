from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdmin
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionList(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        transactions = Transaction.objects.all()
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class TransactionCreate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            transaction = Transaction.objects.get(pk=pk)
        except Transaction.DoesNotExist:
            return Response(data={'message': 'Transaction does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)


class TransactionUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            transaction = Transaction.objects.get(pk=pk)
        except Transaction.DoesNotExist:
            return Response(data={'message': 'Transaction does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TransactionSerializer(instance=transaction, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionDelete(APIView):
    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            transaction = Transaction.objects.get(pk=pk)
        except Transaction.DoesNotExist:
            return Response(data={'message': 'Transaction does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        transaction.delete()
        return Response(data={'message': 'Transaction deleted.'}, status=status.HTTP_204_NO_CONTENT)