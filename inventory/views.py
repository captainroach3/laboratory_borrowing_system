
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Inventory
from .serializers import InventorySerializer


class InventoryList(APIView):
    def get(self, request):
        items = Inventory.objects.all()
        serializer = InventorySerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = InventorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventoryDetail(APIView):
    def get(self, request, pk):
        try:
            item = Inventory.objects.get(pk=pk)
        except Inventory.DoesNotExist:
            return Response(data={'message': 'Item does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = InventorySerializer(item)
        return Response(serializer.data)


class InventoryUpdate(APIView):
    def put(self, request, pk):
        try:
            item = Inventory.objects.get(pk=pk)
        except Inventory.DoesNotExist:
            return Response(data={'message': 'Item does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = InventorySerializer(instance=item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventoryDelete(APIView):
    def delete(self, request, pk):
        try:
            item = Inventory.objects.get(pk=pk)
        except Inventory.DoesNotExist:
            return Response(data={'message': 'Item does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response(data={'message': 'Item deleted.'}, status=status.HTTP_204_NO_CONTENT)