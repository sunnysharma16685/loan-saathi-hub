from django.core.management.base import BaseCommand
from loans.models import LoanRequest, LoanLenderStatus
from payments.models import PaymentTransaction

class Command(BaseCommand):
    help = "Clean all applicant and lender test data but keep users safe."

    def handle(self, *args, **kwargs):
        LoanLenderStatus.objects.all().delete()
        PaymentTransaction.objects.all().delete()
        LoanRequest.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("✅ All loan-related data removed successfully! Users retained."))
