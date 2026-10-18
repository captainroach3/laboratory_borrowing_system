from rest_framework import status
from rest_framework.test import APITestCase

from category.models import Category
from inventory.models import Inventory
from staff.models import Staff
from users.models import User
from .models import Transaction


class BorrowFlowTests(APITestCase):


    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin1', password='AdminPass123',
            first_name='Ada', last_name='Admin', department='IT', role=User.Role.ADMIN,
        )
        self.staff_user = User.objects.create_user(
            username='staff1', password='StaffPass123',
            first_name='Stan', last_name='Staff', department='Lab', role=User.Role.STAFF,
        )
        self.staff_row = Staff.objects.create(user=self.staff_user, position='Lab Technician')
        self.student = User.objects.create_user(
            username='student1', password='StudentPass123',
            first_name='Sam', last_name='Student', department='CpE',
        )
        self.other = User.objects.create_user(
            username='student2', password='OtherPass123',
            first_name='Olive', last_name='Other', department='CpE',
        )
        category = Category.objects.create(category_name='Electronics')
        self.scope = Inventory.objects.create(
            item_name='Oscilloscope', quantity=5, category=category,
            status=Inventory.AVAILABLE, location='Lab A',
        )
        self.broken = Inventory.objects.create(
            item_name='Old Meter', quantity=3, category=category,
            status=Inventory.MAINTENANCE, location='Lab A',
        )

    # ---------- helpers ----------

    def login_as(self, username, password):
        response = self.client.post(
            '/api/login/', {'username': username, 'password': password}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def as_student(self):
        self.login_as('student1', 'StudentPass123')

    def as_staff(self):
        self.login_as('staff1', 'StaffPass123')

    def as_admin(self):
        self.login_as('admin1', 'AdminPass123')

    def request_item(self, item=None, quantity=1):
        """A pending request for the student, created straight in the database."""
        return Transaction.objects.create(
            item_name=item or self.scope, user=self.student, quantity=quantity
        )

    def approve(self, borrow):
        return self.client.put(
            f'/api/transactions/{borrow.pk}/update/',
            {'approver': self.staff_row.pk}, format='json',
        )

    def give_back(self, borrow):
        return self.client.put(
            f'/api/transactions/{borrow.pk}/update/',
            {'return_datetime': '2026-10-20T09:00:00Z'}, format='json',
        )

    def stock(self, item=None):
        item = item or self.scope
        item.refresh_from_db()
        return item.quantity

    # ---------- asking to borrow ----------

    def test_create_requires_login(self):
        response = self.client.post(
            '/api/transactions/create/', {'item_name': self.scope.pk}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_uses_the_logged_in_user_as_borrower(self):
        self.as_student()
        response = self.client.post(
            '/api/transactions/create/',
            {'item_name': self.scope.pk, 'quantity': 2}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        borrow = Transaction.objects.get(pk=response.data['transaction_id'])
        self.assertEqual(borrow.user_id, self.student.pk)
        self.assertEqual(borrow.quantity, 2)
        self.assertIsNone(borrow.approver_id)
        self.assertIsNone(borrow.return_datetime)

    def test_create_ignores_a_user_approver_or_return_date_in_the_body(self):
        self.as_student()
        response = self.client.post(
            '/api/transactions/create/',
            {
                'item_name': self.scope.pk,
                'user': self.other.pk,
                'approver': self.staff_row.pk,
                'return_datetime': '2026-10-20T09:00:00Z',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        borrow = Transaction.objects.get(pk=response.data['transaction_id'])
        self.assertEqual(borrow.user_id, self.student.pk)
        self.assertIsNone(borrow.approver_id)
        self.assertIsNone(borrow.return_datetime)

    def test_create_defaults_to_one_item(self):
        self.as_student()
        response = self.client.post(
            '/api/transactions/create/', {'item_name': self.scope.pk}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['quantity'], 1)

    def test_create_refuses_an_item_that_is_not_available(self):
        self.as_student()
        response = self.client.post(
            '/api/transactions/create/', {'item_name': self.broken.pk}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('item_name', response.data)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_create_refuses_more_than_the_stock(self):
        self.as_student()
        response = self.client.post(
            '/api/transactions/create/',
            {'item_name': self.scope.pk, 'quantity': 6}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('quantity', response.data)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_create_refuses_a_quantity_of_zero(self):
        self.as_student()
        response = self.client.post(
            '/api/transactions/create/',
            {'item_name': self.scope.pk, 'quantity': 0}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_asking_to_borrow_does_not_change_stock(self):
        self.as_student()
        self.client.post(
            '/api/transactions/create/',
            {'item_name': self.scope.pk, 'quantity': 2}, format='json',
        )
        self.assertEqual(self.stock(), 5)

    # ---------- approving ----------

    def test_student_cannot_approve_or_update(self):
        borrow = self.request_item()
        self.as_student()
        response = self.approve(borrow)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        borrow.refresh_from_db()
        self.assertIsNone(borrow.approver_id)
        self.assertEqual(self.stock(), 5)

    def test_student_cannot_edit_their_own_request(self):
        borrow = self.request_item(quantity=1)
        self.as_student()
        response = self.client.put(
            f'/api/transactions/{borrow.pk}/update/',
            {'item_name': self.scope.pk, 'user': self.other.pk, 'quantity': 4}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        borrow.refresh_from_db()
        self.assertEqual(borrow.user_id, self.student.pk)
        self.assertEqual(borrow.quantity, 1)

    def test_staff_approval_lowers_stock(self):
        borrow = self.request_item(quantity=2)
        self.as_staff()
        response = self.approve(borrow)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        borrow.refresh_from_db()
        self.assertEqual(borrow.approver_id, self.staff_row.pk)
        self.assertEqual(self.stock(), 3)

    def test_admin_can_approve_too(self):
        borrow = self.request_item()
        self.as_admin()
        response = self.approve(borrow)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.stock(), 4)

    def test_cannot_approve_twice(self):
        borrow = self.request_item(quantity=2)
        self.as_staff()
        self.approve(borrow)
        response = self.approve(borrow)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.stock(), 3)

    def test_cannot_approve_when_stock_ran_out_in_the_meantime(self):
        borrow = self.request_item(quantity=4)
        self.scope.quantity = 2
        self.scope.save()
        self.as_staff()
        response = self.approve(borrow)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
        borrow.refresh_from_db()
        self.assertIsNone(borrow.approver_id)
        self.assertEqual(self.stock(), 2)

    def test_cannot_approve_when_the_item_is_no_longer_available(self):
        borrow = self.request_item()
        self.scope.status = Inventory.MAINTENANCE
        self.scope.save()
        self.as_staff()
        response = self.approve(borrow)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        borrow.refresh_from_db()
        self.assertIsNone(borrow.approver_id)
        self.assertEqual(self.stock(), 5)

    def test_approval_needs_a_real_staff_id(self):
        borrow = self.request_item()
        self.as_staff()
        response = self.client.put(
            f'/api/transactions/{borrow.pk}/update/', {'approver': 9999}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.stock(), 5)

    def test_update_needs_exactly_one_action(self):
        borrow = self.request_item()
        self.as_staff()
        neither = self.client.put(f'/api/transactions/{borrow.pk}/update/', {}, format='json')
        both = self.client.put(
            f'/api/transactions/{borrow.pk}/update/',
            {'approver': self.staff_row.pk, 'return_datetime': '2026-10-20T09:00:00Z'},
            format='json',
        )
        self.assertEqual(neither.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(both.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.stock(), 5)

    def test_update_of_a_missing_transaction_is_404(self):
        self.as_staff()
        response = self.client.put(
            '/api/transactions/9999/update/', {'approver': self.staff_row.pk}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ---------- returning ----------

    def test_return_puts_stock_back(self):
        borrow = self.request_item(quantity=2)
        self.as_staff()
        self.approve(borrow)
        response = self.give_back(borrow)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        borrow.refresh_from_db()
        self.assertIsNotNone(borrow.return_datetime)
        self.assertEqual(self.stock(), 5)

    def test_cannot_return_before_approval(self):
        borrow = self.request_item()
        self.as_staff()
        response = self.give_back(borrow)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.stock(), 5)

    def test_cannot_return_twice(self):
        borrow = self.request_item(quantity=2)
        self.as_staff()
        self.approve(borrow)
        self.give_back(borrow)
        response = self.give_back(borrow)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.stock(), 5)

    # ---------- deleting ----------

    def test_deleting_a_loan_that_is_still_out_puts_stock_back(self):
        borrow = self.request_item(quantity=2)
        self.as_staff()
        self.approve(borrow)
        self.assertEqual(self.stock(), 3)
        self.as_admin()
        response = self.client.delete(f'/api/transactions/{borrow.pk}/delete/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.stock(), 5)
        self.assertFalse(Transaction.objects.filter(pk=borrow.pk).exists())

    def test_deleting_a_pending_request_leaves_stock_alone(self):
        borrow = self.request_item(quantity=2)
        self.as_admin()
        response = self.client.delete(f'/api/transactions/{borrow.pk}/delete/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.stock(), 5)

    def test_deleting_a_returned_loan_leaves_stock_alone(self):
        borrow = self.request_item(quantity=2)
        self.as_staff()
        self.approve(borrow)
        self.give_back(borrow)
        self.as_admin()
        response = self.client.delete(f'/api/transactions/{borrow.pk}/delete/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.stock(), 5)

    def test_only_admin_can_delete(self):
        borrow = self.request_item()
        self.as_staff()
        response = self.client.delete(f'/api/transactions/{borrow.pk}/delete/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.as_student()
        response = self.client.delete(f'/api/transactions/{borrow.pk}/delete/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Transaction.objects.filter(pk=borrow.pk).exists())

    # ---------- reading ----------

    def test_list_is_for_staff_and_admin_only(self):
        self.request_item()
        self.as_student()
        self.assertEqual(self.client.get('/api/transactions/').status_code, status.HTTP_403_FORBIDDEN)
        self.as_staff()
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_owner_can_read_their_own_request_but_not_someone_elses(self):
        borrow = self.request_item()
        self.as_student()
        self.assertEqual(
            self.client.get(f'/api/transactions/{borrow.pk}/').status_code, status.HTTP_200_OK
        )
        self.login_as('student2', 'OtherPass123')
        self.assertEqual(
            self.client.get(f'/api/transactions/{borrow.pk}/').status_code, status.HTTP_403_FORBIDDEN
        )
        self.as_staff()
        self.assertEqual(
            self.client.get(f'/api/transactions/{borrow.pk}/').status_code, status.HTTP_200_OK
        )

    # ---------- the whole story ----------

    def test_full_story_borrow_approve_return(self):
        self.as_student()
        created = self.client.post(
            '/api/transactions/create/',
            {'item_name': self.scope.pk, 'quantity': 3}, format='json',
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        borrow_id = created.data['transaction_id']
        self.assertEqual(self.stock(), 5)

        self.as_staff()
        approved = self.client.put(
            f'/api/transactions/{borrow_id}/update/',
            {'approver': self.staff_row.pk}, format='json',
        )
        self.assertEqual(approved.status_code, status.HTTP_200_OK)
        self.assertEqual(self.stock(), 2)

        returned = self.client.put(
            f'/api/transactions/{borrow_id}/update/',
            {'return_datetime': '2026-10-20T09:00:00Z'}, format='json',
        )
        self.assertEqual(returned.status_code, status.HTTP_200_OK)
        self.assertEqual(self.stock(), 5)