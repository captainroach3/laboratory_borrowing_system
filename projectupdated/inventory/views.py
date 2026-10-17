from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdmin
from .models import Inventory
from .serializers import InventorySerializer


class InventoryList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = Inventory.objects.all()
        serializer = InventorySerializer(items, many=True)
        return Response(serializer.data)


class InventoryCreate(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = InventorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventoryDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            item = Inventory.objects.get(pk=pk)
        except Inventory.DoesNotExist:
            return Response(data={'message': 'Item does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = InventorySerializer(item)
        return Response(serializer.data)


class InventoryUpdate(APIView):
    permission_classes = [IsAdmin]

    def put(self, request, pk):
        try:
            item = Inventory.objects.get(pk=pk)
        except Inventory.DoesNotExist:
            return Response(data={'message': 'Item does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = InventorySerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventoryDelete(APIView):
    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            item = Inventory.objects.get(pk=pk)
        except Inventory.DoesNotExist:
            return Response(data={'message': 'Item does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        item.delete()
        return Response(data={'message': 'Item deleted.'}, status=status.HTTP_204_NO_CONTENT)