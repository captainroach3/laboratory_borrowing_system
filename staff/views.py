
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Staff
from .serializers import StaffSerializer


class StaffList(APIView):
    def get(self, request):
        staff = Staff.objects.all()
        serializer = StaffSerializer(staff, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StaffSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDetail(APIView):
    def get(self, request, pk):
        try:
            staff = Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return Response(data={'message': 'Staff does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = StaffSerializer(staff)
        return Response(serializer.data)


class StaffUpdate(APIView):
    def put(self, request, pk):
        try:
            staff = Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return Response(data={'message': 'Staff does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = StaffSerializer(instance=staff, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDelete(APIView):
    def delete(self, request, pk):
        try:
            staff = Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return Response(data={'message': 'Staff does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        staff.delete()
        return Response(data={'message': 'Staff deleted.'}, status=status.HTTP_204_NO_CONTENT)